"""FM6S/Edge skeleton layouts adapted from read-only orc_import_blender.py.
Software orthographic rendering; not a game shader or animated skinning.
"""
import struct,math,io
import numpy as np
from PIL import Image,ImageDraw
import core

def string(data,offset):
 end=data.find(b'\0',offset)
 if offset<0 or end<0:raise ValueError('String inválida.')
 return data[offset:end].decode('utf-8','replace').replace('\\','/')

def details(data):
 vertices,faces=core.parse_mesh(data);count=struct.unpack_from('<i',data,12)[0];table=struct.unpack_from('<i',data,24)[0];uv=[];materials=[];face_mats=[]
 for m in range(count):
  subcount,subtable,skel,mat=struct.unpack_from('<4i',data,table+m*144)
  materials.append(string(data,struct.unpack_from('<i',data,mat)[0]) if 0<=mat<=len(data)-4 else '')
  for s in range(subcount):
   pos=subtable+s*144;vc,ic=struct.unpack_from('<2H',data,pos+8);start,size=struct.unpack_from('<2i',data,pos+44)
   if not vc or not ic:continue
   stride=size//vc;offset=28 if stride in (32,44,56,60) else 24 if stride in (28,40,52) else None
   coords=np.ndarray((vc,2),dtype='<f2',buffer=data,offset=start+offset,strides=(stride,2)).astype(np.float32) if offset is not None else np.zeros((vc,2),np.float32)
   if not np.isfinite(coords).all():raise ValueError('UV inválida.')
   uv.append(coords);face_mats.extend([m]*(ic//3))
 return {'vertices':vertices,'faces':faces,'uv':np.concatenate(uv),'materials':materials,'face_mats':np.array(face_mats),'textures':{},'references':[]}

def material_refs(data):
 if data[:3]!=b'MAT' or len(data)<24:raise ValueError('Material MAT inválido.')
 count=struct.unpack_from('<I',data,8)[0];offset=struct.unpack_from('<I',data,16)[0]
 if count>1024 or offset+count*8>len(data):raise ValueError('Tabela MAT inválida.')
 return [(tag,string(data,ptr)) for tag,ptr in struct.iter_unpack('<2I',data[offset:offset+count*8])]

def resolve(d,assets):
 index={}
 for a in assets:
  key=a.name.replace('\\','/').casefold();previous=index.get(key)
  if previous and key.endswith('.dds') and previous.size>128 and a.size<=128:continue
  index[key]=a
 def find(name):
  key=name.casefold();exact=index.get(key)
  if exact:return exact
  candidates=[a for n,a in index.items() if n.endswith('/'+key)]
  return candidates[0] if len(candidates)==1 else None
 d['material_info']={};d['warnings']=[]
 for i,name in enumerate(d['materials']):
  role='named_shadow_helper' if name.replace('\\','/').rsplit('/',1)[-1].casefold()=='gsh_shadow_skinned.matb' else 'surface'
  d['material_info'][i]={'id':i,'material':name,'role':role,'diffuse_path':None}
  if role=='named_shadow_helper':d['warnings'].append(f'Grupo {i}: shadow helper por nome explícito, oculto por padrão; shader do jogo não interpretado.')
  a=find(name)
  if not a:d['references'].append('Material não localizado: '+name);continue
  try:
   refs=material_refs(a.read());d['references'].extend([f'{tag}: {path}' for tag,path in refs])
   diffuse=[path for tag,path in refs if tag in (3014450751,3154041481,2002049559,439570611)]
   for path in diffuse:
    tex=find(path)
    if tex and tex.size>128:
     with Image.open(io.BytesIO(tex.read())) as im:d['textures'][i]=im.convert('RGBA')
     d['material_info'][i]['diffuse_path']=tex.name
     if d['textures'][i].getchannel('A').getextrema()[0]<255:d['warnings'].append(f'Grupo {i}: alpha DDS preservado; recorte alpha zero na prévia, sem equivalência ao shader do jogo.')
     break
  except Exception as e:d['references'].append(str(e))
  if i not in d['textures'] and role=='surface':d['warnings'].append(f'Grupo {i}: sem diffuse resolvido; geometria mantida com fallback diagnóstico.')
 return d

def skeleton(data):
 if data[:4] not in (b'20SE',b'ES02'):raise ValueError('Não é Edge skeleton.')
 # Existing PC parser uses little endian for both tags.
 count=struct.unpack_from('<H',data,16)[0];pose,parent=struct.unpack_from('<2I',data,24)
 if not count or count>4096 or pose+24+count*48>len(data) or parent+28+count*2>len(data):raise ValueError('Skeleton truncado.')
 parents=np.frombuffer(data,dtype='<i2',count=count,offset=parent+28).copy();local=[]
 for i in range(count):
  x,y,z,w=struct.unpack_from('<4f',data,pose+24+i*48);t=struct.unpack_from('<3f',data,pose+40+i*48)
  norm=math.sqrt(x*x+y*y+z*z+w*w)
  if not math.isfinite(norm) or norm<1e-6:raise ValueError('Quaternion inválido.')
  x,y,z,w=np.array([x,y,z,w])/norm
  mat=np.eye(4);mat[:3,:3]=[[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]];mat[:3,3]=t;local.append(mat)
 world={}
 def visit(i,seen):
  if i in world:return world[i]
  if i in seen:raise ValueError('Skeleton cíclico.')
  p=int(parents[i])
  if p < -1 or p>=count:raise ValueError('Pai inválido.')
  world[i]=(visit(p,seen|{i})@local[i]) if p>=0 else local[i];return world[i]
 points=np.array([visit(i,set())[:3,3] for i in range(count)])
 if not np.isfinite(points).all():raise ValueError('Skeleton inválido.')
 return points,parents

def render(d,yaw,pitch,zoom,width,height,mode='Sólido',bones=None):
 vertices=d['vertices'];faces=d['faces'];points=core.project(vertices,yaw,pitch,zoom,width,height)
 cy,sy=math.cos(yaw),math.sin(yaw);cp,sp=math.cos(pitch),math.sin(pitch);r=np.array([[cy,0,sy],[sy*sp,cp,-cy*sp],[-sy*cp,sp,cy*cp]])
 rotated=vertices@r.T;depth=rotated[:,2];order=np.argsort(depth[faces].mean(axis=1))
 image=Image.new('RGB',(width,height),'#15212b');draw=ImageDraw.Draw(image)
 if mode=='Wireframe':
  for a,b,c in faces:draw.line([tuple(points[a]),tuple(points[b]),tuple(points[c]),tuple(points[a])],fill='#69d9df')
 else:
  # Painter solid pass; true UV barycentric rasterization + depth buffer for textured pass.
  normals=np.cross(rotated[faces[:,1]]-rotated[faces[:,0]],rotated[faces[:,2]]-rotated[faces[:,0]]);length=np.linalg.norm(normals,axis=1);shade=.25+.75*np.abs(normals[:,2])/np.maximum(length,1e-6)
  for i in order:draw.polygon([tuple(x) for x in points[faces[i]]],fill=tuple(int(c*shade[i]) for c in (100,185,195)))
  if mode=='Texturizado' and d['textures']:
   pixels=np.array(image);zbuf=np.full((height,width),-np.inf);textures={i:np.array(im) for i,im in d['textures'].items()}
   for i in order:
    tex=textures.get(int(d['face_mats'][i]))
    if tex is None:continue
    ids=faces[i];p=points[ids];x0=max(0,int(np.floor(p[:,0].min())));x1=min(width-1,int(np.ceil(p[:,0].max())));y0=max(0,int(np.floor(p[:,1].min())));y1=min(height-1,int(np.ceil(p[:,1].max())))
    if x1<x0 or y1<y0:continue
    a,b,c=p;den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
    if abs(den)<1e-8:continue
    yy,xx=np.mgrid[y0:y1+1,x0:x1+1];wa=((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/den;wb=((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/den;wc=1-wa-wb;z=wa*depth[ids[0]]+wb*depth[ids[1]]+wc*depth[ids[2]];region=zbuf[y0:y1+1,x0:x1+1];mask=(wa>=0)&(wb>=0)&(wc>=0)&(z>=region)
    coords=wa[...,None]*d['uv'][ids[0]]+wb[...,None]*d['uv'][ids[1]]+wc[...,None]*d['uv'][ids[2]];tx=((coords[...,0]%1)*tex.shape[1]).astype(int)%tex.shape[1];ty=((coords[...,1]%1)*tex.shape[0]).astype(int)%tex.shape[0];patch=pixels[y0:y1+1,x0:x1+1];patch[mask]=(tex[ty[mask],tx[mask]]*shade[i]).astype(np.uint8);region[mask]=z[mask]
   image=Image.fromarray(pixels);draw=ImageDraw.Draw(image)
 if bones is not None:
  bp,parents=bones
  # Same center and scale as mesh; do not recenter skeleton independently.
  center=(vertices.min(axis=0)+vertices.max(axis=0))/2;scale=max(float(np.ptp(vertices,axis=0).max()),1e-6);q=((bp-center)@r.T)[:,:2]*min(width,height)*.8/scale*zoom;q[:,1]*=-1;q+=np.array([width/2,height/2])
  for i,p in enumerate(parents):
   if p>=0:draw.line([tuple(q[i]),tuple(q[p])],fill='#ffbf46',width=2)
 return image
