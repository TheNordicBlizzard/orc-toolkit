"""Real Tk input + hardware framebuffer camera QA, with private local evidence."""
from pathlib import Path
import qa_paths
import tkinter as tk
import numpy as np
import sys,time,json,hashlib,traceback

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def run(destination):
 from app import Explorer
 from editor_style import capture_window
 import media
 out=Path(destination);out.mkdir(parents=True,exist_ok=True)
 source=qa_paths.game()/'dlc/pack1/Characters/adawong.ssg'
 settings=[media.home()/'ui_language.json',media.home()/'dependencies.json']
 original={str(p):p.read_bytes() if p.exists() else None for p in settings}
 result={'frozen':bool(getattr(sys,'frozen',False)),'executable':sys.executable,'executable_sha256':digest(sys.executable),'checks':{},'frames':{},'languages':{},'callback_errors':[],'source_sha256_before':digest(source),'projection':'Existing orthographic fit preserved; screen-space camera translation, orbit and zoom, not free-flight or perspective dolly.','capture_method':'Target Tk client PrintWindow plus same-process real WGL framebuffer at measured viewport coordinates (editor_style.capture_window). GPU images are direct framebuffer snapshots.'}
 def save():
  result['check_count']=len(result['checks']);(out/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 def check(name,value):
  result['checks'][prefix+name]=bool(value);save()
  if not value:raise AssertionError(prefix+name)
 prefix=''
 try:
  for language in ('pt-BR','en'):
   prefix=language+'_';root=tk.Tk();a=Explorer(root)
   root.report_callback_exception=lambda typ,e,tb:result['callback_errors'].append(''.join(traceback.format_exception(typ,e,tb)))
   def wait():
    end=time.monotonic()+45
    while time.monotonic()<end:
     root.update()
     if not a.busy and a.render_id is None:root.update();return
     time.sleep(.002)
    raise AssertionError('worker/render timeout: '+a.status.get())
   def frame(name,ui=False):
    image=a.gpu.snapshot();image.save(out/(prefix+name+'.png'));pixels=np.array(image)
    result['frames'][prefix+name]={'pixel_sha256':hashlib.sha256(image.tobytes()).hexdigest(),'png_sha256':digest(out/(prefix+name+'.png')),'size':list(image.size),'yaw':a.yaw,'pitch':a.pitch,'zoom':a.zoom,'pan':list(a.camera_pan),'uploads':a.gpu.upload_count,'completed_frames':a.gpu.completed_frames}
    if ui:capture_window(a).save(out/(prefix+name+'_ui.png'))
    save();return pixels
   def drag(button,dx,dy):
    a.gpu.event_generate('<ButtonPress-%s>'%button,x=100,y=100)
    a.gpu.event_generate('<B%s-Motion>'%button,x=100+dx,y=100+dy,state={1:256,2:512,3:1024}[button])
    a.gpu.event_generate('<ButtonRelease-%s>'%button,x=100+dx,y=100+dy);wait()
   try:
    a.language=language;a.refresh_language();a.load(source);wait()
    check('hardware_gpu',a.gpu.ready and a.gpu.hardware_renderer(a.gpu.context_info.get('GL_RENDERER','')))
    result['languages'][language]={'context':a.gpu.context_info,'hint':a.viewport_hint.cget('text')};save()
    check('hint_pan',('Direito/meio' if language=='pt-BR' else 'Right/middle') in a.viewport_hint.cget('text'))
    check('model_ready',a.mesh is not None and a.detail is not None)
    vertices=a.detail['vertices'].copy();uploads=a.gpu.upload_count;before=frame('before',True)
    drag(1,35,20);check('left_orbit_state',abs(a.yaw-.75)<1e-6 and abs(a.pitch-.3)<1e-6)
    check('left_orbit_frame',not np.array_equal(before,frame('orbit')))
    a.reset();wait();before=frame('before_pan');drag(3,40,25);after=frame('pan',True)
    check('right_pan_state',a.camera_pan==(40,25) and a.yaw==.4 and a.pitch==.1)
    check('right_pan_frame',not np.array_equal(before,after))
    check('right_pan_pixel_translation',np.abs(before[:-25,:-40].astype(int)-after[25:,40:].astype(int)).max()<=1)
    a.reset();wait();drag(2,-30,20);check('middle_pan_state',a.camera_pan==(-30,20))
    check('middle_pan_frame',not np.array_equal(before,frame('middle_pan')))
    a.gpu.event_generate('<MouseWheel>',delta=120);wait();check('wheel_zoom',abs(a.zoom-1.1)<1e-6)
    check('wheel_frame',not np.array_equal(after,frame('zoom')))
    button=next(b for b in a.modern_buttons if a.label_sources[b]=='Resetar câmera')
    button.invoke();wait();check('reset_state',(a.yaw,a.pitch,a.zoom,a.camera_pan)==(.4,.1,1,(0,0)))
    check('reset_frame',np.array_equal(before,frame('reset',True)))
    drag(3,40,25)
    for stamp in (1000,1100):
     a.gpu.event_generate('<ButtonPress-1>',x=20,y=20,time=stamp);a.gpu.event_generate('<ButtonRelease-1>',x=20,y=20,time=stamp+10)
    wait();check('double_click_reset',a.camera_pan==(0,0) and np.array_equal(before,frame('double_reset')))
    check('camera_no_upload',a.gpu.upload_count==uploads)
    check('asset_unchanged',np.array_equal(vertices,a.detail['vertices']))
    for geometry,zoom in (('1024x680',.5),('1360x850',1.5)):
     root.geometry(geometry);root.update();a.reset();a.zoom=zoom;a.draw();wait();base=frame('size_'+geometry)
     drag(3,20,12);moved=frame('size_'+geometry+'_pan')
     check('aspect_zoom_pan_'+geometry,np.abs(base[:-12,:-20].astype(int)-moved[12:,20:].astype(int)).max()<=1)
    a.reset();a.bones=(np.array([[0,0,0],[0,50,0]],dtype='f4'),np.array([-1,0]));a.show_bones.set(True);a.draw();wait()
    base=frame('skeleton');bones_key=a.gpu.bones_key;drag(3,20,12);moved=frame('skeleton_pan')
    check('skeleton_uniform',all(a.gpu.program[u].read()==a.gpu.bone_program[u].read() for u in ('rotation','center','scale','pan')))
    check('skeleton_frame',not np.array_equal(base,moved))
    check('skeleton_static_buffer',a.gpu.bones_key is bones_key)
    check('skeleton_pixel_translation',np.abs(base[:-12,:-20].astype(int)-moved[12:,20:].astype(int)).max()<=1)
    a.show_bones.set(False);a.set_category('Modelos');root.update();a.tree.selection_set(a.tree.get_children()[0]);a.tree.event_generate('<<TreeviewSelect>>');wait()
    check('reselection_reset',a.camera_pan==(0,0) and a.zoom==1)
    a.set_category('Texturas');root.update();texid=next(i for i in a.tree.get_children() if a.assets[int(i)].size>128)
    a.tree.selection_set(texid);wait();check('texture_ready',a.image is not None)
    image_uploads=a.gpu.image_upload_count;drag(3,20,12)
    check('texture_separate_pan',a.pan==(20,12) and a.camera_pan==(0,0))
    check('texture_no_upload',a.gpu.image_upload_count==image_uploads)
    a.clear_preview();state=(a.yaw,a.pitch,a.zoom,a.camera_pan);drag(3,20,12);a.wheel(type('Event',(),{'delta':120})());wait()
    check('no_model_safe',(a.yaw,a.pitch,a.zoom,a.camera_pan)==state)
    check('no_callback_errors',not result['callback_errors'])
   finally:
    while a.busy:root.update();time.sleep(.01)
    a.close()
  prefix='';check('source_unchanged',digest(source)==result['source_sha256_before'])
  check('settings_bytes_unchanged',all((p.read_bytes() if p.exists() else None)==original[str(p)] for p in settings))
  result['success']=all(result['checks'].values());save();return result
 except Exception:
  result['failure']=traceback.format_exc();save();raise
