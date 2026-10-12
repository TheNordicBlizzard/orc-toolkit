"""Native WGL viewport embedded in Tk. Static uploads; measured GPU completion + swap.
No continuous redraw timer: caller renders on interaction/resize only.
"""
import math,time
import numpy as np
import moderngl
from PIL import Image
from pyopengltk import OpenGLFrame

VERTEX='''#version 330
in vec3 position; in vec2 uv; in vec3 normal;
uniform mat3 rotation; uniform vec3 center; uniform vec3 scale; uniform vec2 pan;
out vec2 texcoord; out float light;
void main(){vec3 p=rotation*(position-center);gl_Position=vec4(p*scale+vec3(pan,0),1.0);texcoord=uv;light=.25+.75*abs((rotation*normal).z);}
'''
FRAGMENT='''#version 330
in vec2 texcoord;in float light;uniform sampler2D diffuse;uniform int textured;uniform int wire;
out vec4 color;
void main(){vec4 sampleColor=textured==1?texture(diffuse,texcoord):vec4(.392,.725,.765,1.0);if(wire==0&&textured==1&&sampleColor.a<=.001)discard;vec3 base=wire==1?vec3(.41,.85,.87):sampleColor.rgb;color=vec4(base*(wire==1?1.0:light),1.0);}
'''
class GPUPreview(OpenGLFrame):
 @staticmethod
 def hardware_renderer(renderer):
  value=renderer.casefold()
  return bool(value) and not any(tag in value for tag in ('gdi generic','llvmpipe','softpipe','swiftshader','software','basic render','lavapipe'))
 def __init__(self,parent,on_error=None,on_context=None,**kwargs):
  self.ready=False;self.error='';self.context_info={};self.ctx=None;self.resources=[];self.groups=[];self.loaded=None;self.upload_count=0;self.last_frame_ms=0;self.frame_times=[];self.fbo=None;self.fbo_size=None;self.target_resources=[];self.on_error=on_error;self.bones_key=None;self.bone_resources=[];self.bone_vao=None
  super().__init__(parent,**kwargs)
  self.completed_frames=0;self.on_context=on_context;self.image_upload_count=0;self.image_key=None;self.image_texture=None
 def initgl(self):
  if self.ctx:return
  try:
   self.ctx=moderngl.create_context(require=330)
   self.context_info={k:self.ctx.info[k] for k in ('GL_VENDOR','GL_RENDERER','GL_VERSION')};self.context_info['backend']='native WGL / visible Tk child window'
   if not self.hardware_renderer(self.context_info['GL_RENDERER']):raise RuntimeError('Renderer software recusado: '+self.context_info['GL_RENDERER'])
   if self.on_context:self.on_context(self.context_info)
   self.program=self.ctx.program(vertex_shader=VERTEX,fragment_shader=FRAGMENT)
   self.bone_program=self.ctx.program(vertex_shader='#version 330\nin vec3 position;uniform mat3 rotation;uniform vec3 center;uniform vec3 scale;uniform vec2 pan;void main(){gl_Position=vec4((rotation*(position-center))*scale+vec3(pan,0),1.0);}',fragment_shader='#version 330\nout vec4 color;void main(){color=vec4(1.0,.75,.27,1.0);}')
   self.program['diffuse'].value=0;self.ctx.enable(moderngl.DEPTH_TEST);self.ctx.depth_func='<=';self.ready=True
   self.image_program=self.ctx.program(vertex_shader='#version 330\nin vec2 pos;uniform vec2 scale;uniform vec2 pan;out vec2 uv;void main(){gl_Position=vec4(pos*scale+pan,0,1);uv=vec2((pos.x+1)*.5,(1-pos.y)*.5);}',fragment_shader='#version 330\nin vec2 uv;uniform sampler2D image;out vec4 color;void main(){color=texture(image,uv);}')
   self.quad_buffer=self.ctx.buffer(np.array([[-1,-1],[1,-1],[-1,1],[1,1]],dtype='f4').tobytes());self.quad=self.ctx.vertex_array(self.image_program,[(self.quad_buffer,'2f','pos')]);self.image_program['image'].value=0
   # Presentation timing includes SwapBuffers. Disable driver swap interval if supported;
   # the benchmark reports actual completion, never an invented 16-ms frame counter.
   try:
    import ctypes
    gl=ctypes.WinDLL('opengl32');gl.wglGetProcAddress.restype=ctypes.c_void_p
    address=gl.wglGetProcAddress(b'wglSwapIntervalEXT')
    if address and address not in (1,2,3,ctypes.c_void_p(-1).value):ctypes.WINFUNCTYPE(ctypes.c_int,ctypes.c_int)(address)(0)
   except Exception:pass
  except Exception as e:
   self.error=str(e);self.ready=False
   if self.on_error:self.on_error('GPU obrigatória indisponível: '+self.error+'; render CPU desativado.')
 def tkResize(self,event):
  self.width,self.height=event.width,event.height
 def tkExpose(self,event):pass
 def redraw(self):pass
 def release_model(self):
  for obj in reversed(self.resources):obj.release()
  self.resources=[];self.groups=[];self.loaded=None
 def upload(self,d):
  if d is self.loaded:return
  self.tkMakeCurrent();self.release_model()
  vertices=d['vertices'];faces=d['faces'];uv=d.get('uv',np.zeros((len(vertices),2),np.float32));mats=d.get('face_mats',np.zeros(len(faces),np.int32))
  self.center=(vertices.min(axis=0)+vertices.max(axis=0))/2;self.extent=max(float(np.ptp(vertices,axis=0).max()),1e-6)
  normals=np.cross(vertices[faces[:,1]]-vertices[faces[:,0]],vertices[faces[:,2]]-vertices[faces[:,0]]);normals/=np.maximum(np.linalg.norm(normals,axis=1)[:,None],1e-6)
  packed=np.concatenate((vertices[faces].reshape(-1,3),uv[faces].reshape(-1,2),np.repeat(normals,3,axis=0)),axis=1).astype('f4')
  buffer=self.ctx.buffer(packed.tobytes());self.resources.append(buffer)
  for material in np.unique(mats):
   faceids=np.flatnonzero(mats==material);indices=(faceids[:,None]*3+np.arange(3)).astype('u4').ravel();ibo=self.ctx.buffer(indices.tobytes());vao=self.ctx.vertex_array(self.program,[(buffer,'3f 2f 3f','position','uv','normal')],ibo)
   self.resources.extend([ibo,vao]);image=d.get('textures',{}).get(int(material));texture=None
   if image is not None:
    image=image.convert('RGBA');texture=self.ctx.texture(image.size,4,image.tobytes());texture.filter=(moderngl.LINEAR,moderngl.LINEAR);texture.repeat_x=True;texture.repeat_y=True;self.resources.append(texture)
   self.groups.append((vao,texture,d.get('material_info',{}).get(int(material),{}).get('role','surface')))
  self.loaded=d;self.upload_count+=1
 def target(self,width,height):
  if self.fbo_size==(width,height):return
  for obj in reversed(self.target_resources):obj.release()
  color=self.ctx.texture((width,height),3);depth=self.ctx.depth_renderbuffer((width,height));self.fbo=self.ctx.framebuffer(color,depth);self.target_resources=[color,depth,self.fbo];self.fbo_size=(width,height)
 def render_scene(self,d,yaw,pitch,zoom,mode,bones=None,show_helpers=False,pan=(0,0)):
  if not self.ready:raise RuntimeError(self.error or 'OpenGL context not ready')
  start=time.perf_counter();self.tkMakeCurrent();self.upload(d)
  width,height=max(self.winfo_width(),1),max(self.winfo_height(),1);self.target(width,height);self.fbo.use();self.ctx.viewport=(0,0,width,height);self.fbo.clear(21/255,33/255,43/255,1,depth=1)
  cy,sy=math.cos(yaw),math.sin(yaw);cp,sp=math.cos(pitch),math.sin(pitch)
  rotation=np.array([[cy,0,sy],[sy*sp,cp,-cy*sp],[-sy*cp,sp,cy*cp]],dtype='f4');self.program['rotation'].write(rotation.T.tobytes());self.program['center'].value=tuple(self.center)
  self.program['scale'].value=(min(width,height)*1.6/self.extent*zoom/width,min(width,height)*1.6/self.extent*zoom/height,-1/(self.extent*4))
  self.program['pan'].value=(2*pan[0]/width,-2*pan[1]/height)
  self.ctx.wireframe=mode=='Wireframe';self.program['wire'].value=int(mode=='Wireframe')
  for vao,texture,role in self.groups:
   if role=='named_shadow_helper' and not show_helpers:continue
   self.program['textured'].value=int(mode=='Texturizado' and texture is not None)
   if texture is not None:texture.use(0)
   vao.render(moderngl.TRIANGLES)
  self.ctx.wireframe=False
  if bones is not None:
   if bones is not self.bones_key:
    for obj in reversed(self.bone_resources):obj.release()
    points,parents=bones;ids=np.flatnonzero(parents>=0);lines=np.stack([points[ids],points[parents[ids]]],axis=1).astype('f4');buffer=self.ctx.buffer(lines.tobytes());self.bone_vao=self.ctx.vertex_array(self.bone_program,[(buffer,'3f','position')]);self.bone_resources=[buffer,self.bone_vao];self.bones_key=bones
   for uniform in ('rotation','center','scale','pan'):self.bone_program[uniform].write(self.program[uniform].read())
   self.ctx.disable(moderngl.DEPTH_TEST);self.ctx.line_width=2;self.bone_vao.render(moderngl.LINES);self.ctx.enable(moderngl.DEPTH_TEST)
  self.ctx.copy_framebuffer(self.ctx.screen,self.fbo);self.ctx.finish();self.tkSwapBuffers()
  self.completed_frames+=1;self.last_frame_ms=(time.perf_counter()-start)*1000;self.frame_times.append(self.last_frame_ms)
  if len(self.frame_times)>600:self.frame_times.pop(0)
  return self.last_frame_ms
 def snapshot(self):
  self.tkMakeCurrent();return Image.frombytes('RGB',self.fbo_size,self.fbo.read(components=3,alignment=1)).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
 def render_image(self,image,zoom,pan):
  if not self.ready:raise RuntimeError(self.error or 'GPU obrigatória indisponível')
  start=time.perf_counter();self.tkMakeCurrent()
  if image is not self.image_key:
   if self.image_texture:self.image_texture.release()
   rgba=image.convert('RGBA');self.image_texture=self.ctx.texture(rgba.size,4,rgba.tobytes());self.image_texture.filter=(moderngl.LINEAR,moderngl.LINEAR);self.image_texture.repeat_x=False;self.image_texture.repeat_y=False;self.image_key=image;self.image_upload_count+=1
  width,height=max(self.winfo_width(),1),max(self.winfo_height(),1);self.target(width,height);self.fbo.use();self.ctx.viewport=(0,0,width,height);self.fbo.clear(21/255,33/255,43/255,1,depth=1)
  factor=min(width/image.width,height/image.height)*zoom;self.image_program['scale'].value=(image.width*factor/width,image.height*factor/height);self.image_program['pan'].value=(pan[0]*2/width,-pan[1]*2/height)
  self.ctx.disable(moderngl.DEPTH_TEST);self.image_texture.use(0);self.quad.render(moderngl.TRIANGLE_STRIP);self.ctx.enable(moderngl.DEPTH_TEST);self.ctx.copy_framebuffer(self.ctx.screen,self.fbo);self.ctx.finish();self.tkSwapBuffers();self.completed_frames+=1;self.last_frame_ms=(time.perf_counter()-start)*1000
 def destroy(self):
  if self.ctx:
   self.tkMakeCurrent();self.release_model()
   for obj in reversed(self.target_resources):obj.release()
   for obj in reversed(self.bone_resources):obj.release()
   if hasattr(self,'bone_program'):self.bone_program.release()
   if hasattr(self,'program'):self.program.release()
   if self.image_texture:self.image_texture.release()
   for name in ('quad','quad_buffer','image_program'):
    if hasattr(self,name):getattr(self,name).release()
   self.ctx.release()
  # pyopengltk does not destroy its WGL context/DC itself.
  try:
   from OpenGL.WGL import wglMakeCurrent,wglDeleteContext
   import ctypes
   from ctypes import wintypes
   ReleaseDC=ctypes.WinDLL('user32').ReleaseDC;ReleaseDC.argtypes=[wintypes.HWND,wintypes.HDC]
   context=getattr(self,'_OpenGLFrame__context',None);dc=getattr(self,'_OpenGLFrame__window',None)
   if context:wglMakeCurrent(None,None);wglDeleteContext(context)
   if dc:ReleaseDC(self.winfo_id(),dc)
  except Exception:pass
  super().destroy()
