"""Real native-dialog + Tk input user journey and WGL completion benchmark.
Owned local fixtures only; sources hashed and never modified.
"""
from pathlib import Path
import qa_paths
import os,sys,time,json,hashlib,threading,ctypes,traceback
from ctypes import wintypes as W
import tkinter as tk
import numpy as np
from PIL import ImageGrab

BASE=qa_paths.required('ORC_QA_FIXTURE_ROOT')
GAME=qa_paths.game()/'dlc/pack1/Characters'

def digest(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  while b:=f.read(1024*1024):h.update(b)
 return h.hexdigest()

def owned_file_dialogs():
 """Visible native modal windows of this process, independent of UI locale."""
 user=ctypes.WinDLL('user32',use_last_error=True);found=[]
 @ctypes.WINFUNCTYPE(W.BOOL,W.HWND,W.LPARAM)
 def enum(hwnd,param):
  pid=W.DWORD();user.GetWindowThreadProcessId(hwnd,ctypes.byref(pid));name=ctypes.create_unicode_buffer(256);user.GetClassNameW(hwnd,name,256)
  if pid.value==os.getpid() and name.value=='#32770' and user.IsWindowVisible(hwnd):found.append(hwnd)
  return True
 user.EnumWindows(enum,0);return found

def choose_mode(app,label):
 app.mode_combo.set(app.tr(label));app.mode_combo.event_generate('<<ComboboxSelected>>')
def choose_category(app,label):
 app.combo.set(app.tr(label));app.combo.event_generate('<<ComboboxSelected>>')

def run(destination,benchmark=True):
 from app import Explorer
 out=Path(destination);out.mkdir(parents=True,exist_ok=True)
 sources=[('ada_game',GAME/'adawong.ssg'),('ada_vanilla',BASE/'adawong.ssg.original.bak'),('tweed_vanilla',BASE/'tweed.ssg.original.bak'),('elitehunter_game',GAME/'elitehunter.ssg')]
 result={'frozen':bool(getattr(sys,'frozen',False)),'executable':sys.executable,'executable_sha256':digest(sys.executable),'source_hashes_before':{str(p):digest(p) for _,p in sources},'checks':{},'journeys':{},'benchmark':{},'callback_errors':[]}
 def save(): (out/'results.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
 def check(name,value):
  result['checks'][name]=bool(value);save()
  if not value:raise AssertionError(name)
 root=tk.Tk();app=Explorer(root);root.geometry('1360x850+5+0')
 root.report_callback_exception=lambda typ,error,tb:result['callback_errors'].append(''.join(traceback.format_exception(typ,error,tb)))
 user=ctypes.WinDLL('user32',use_last_error=True);user.GetDlgItem.restype=W.HWND;user.GetParent.restype=W.HWND;user.SendMessageW.argtypes=[W.HWND,W.UINT,W.WPARAM,W.LPARAM];user.SendMessageW.restype=W.LPARAM
 def wait():
  end=time.monotonic()+60
  while time.monotonic()<end:
   root.update()
   if not app.busy and app.render_id is None:
    root.update()
    if not app.busy and app.render_id is None:break
   time.sleep(.002)
  check('worker_timeout',not app.busy)
  if app.status.get().startswith('Erro:'):raise RuntimeError(app.status.get())
 def shot(name):
  root.update();from editor_style import capture_window;capture_window(app).save(out/name)
 def click(widget):
  widget.event_generate('<ButtonPress-1>',x=20,y=10);widget.event_generate('<ButtonRelease-1>',x=20,y=10);root.update()
 def top_button(label):
  return next(w for frame in root.winfo_children() for w in frame.winfo_children() if w.winfo_class()=='TButton' and w.cget('text')==label)
 def dialog_open(source,label):
  state={};ended=threading.Event()
  def native():
   try:
    end=time.monotonic()+15
    while time.monotonic()<end:
     for hwnd in owned_file_dialogs():
      control=user.GetDlgItem(hwnd,1148)
      if not control:continue
      time.sleep(.15);ImageGrab.grab(window=hwnd).save(out/(label+'_dialog.png'))
      text=ctypes.create_unicode_buffer(str(source));user.SendMessageW(control,0x000C,0,ctypes.addressof(text));user.PostMessageW(hwnd,0x0111,1,0)
      state.update(path=str(source),filename_control=int(control))
      accepted_until=time.monotonic()+15
      while user.IsWindowVisible(hwnd) and time.monotonic()<accepted_until:time.sleep(.02)
      if user.IsWindowVisible(hwnd):state['acceptance_timeout']=True;return
      state['native_dialog']=True;return
     time.sleep(.02)
    state['timeout']=True
   except Exception:state['error']=traceback.format_exc()
   finally:
    if not state.get('native_dialog'):
     for hwnd in owned_file_dialogs():user.PostMessageW(hwnd,0x0111,2,0)
    ended.set()
  thread=threading.Thread(target=native,daemon=True);thread.start();app.open_menu.invoke(0);wait();thread.join(1);check(label+'_native_dialog',state.get('native_dialog',False));return state
 def tree_click(iid):
  app.tree.see(iid);root.update();box=app.tree.bbox(iid);app.tree.event_generate('<ButtonPress-1>',x=box[0]+30,y=box[1]+box[3]//2);app.tree.event_generate('<ButtonRelease-1>',x=box[0]+30,y=box[1]+box[3]//2);root.update();wait()
 def mode(label):
  choose_mode(app,label);wait()
 def bench(label):
  mode('Texturizado');gpu=app.gpu;check(label+'_gpu_ready',gpu.ready)
  gpu.event_generate('<ButtonPress-1>',x=120,y=120)
  for i in range(30):
   gpu.event_generate('<B1-Motion>',x=121+i,y=120,state=256);root.update()
  uploads=gpu.upload_count;frames=[];dispatch=[];heartbeat=[];last_beat=time.perf_counter();running=[True]
  def beat():
   nonlocal last_beat
   now=time.perf_counter();heartbeat.append((now-last_beat)*1000);last_beat=now
   if running[0]:root.after(1,beat)
  timer=root.after(1,beat);begin=time.perf_counter();initial_frames=gpu.completed_frames
  for i in range(600):
   queued=time.perf_counter();gpu.event_generate('<B1-Motion>',x=120+(i%200),y=120+(i%10),state=256)
   if i%30==0:gpu.event_generate('<MouseWheel>',delta=120 if i%60==0 else -120)
   root.update();dispatch.append((time.perf_counter()-queued)*1000);frames.append(gpu.last_frame_ms)
  wall=time.perf_counter()-begin;running[0]=False;root.after_cancel(timer)
  check(label+'_actual_completed_frames',gpu.completed_frames-initial_frames==len(frames))
  # A second, paced 60-Hz actual input loop reports completion intervals,
  # not a synthetic timer counter. GL glFinish + SwapBuffers is in every sample.
  intervals=[];last=time.perf_counter();start=last
  for i in range(180):
   due=start+(i+1)/60
   while time.perf_counter()<due:
    root.update();time.sleep(.0005)
   gpu.event_generate('<B1-Motion>',x=120+i,y=120+(i%10),state=256);root.update();now=time.perf_counter();intervals.append((now-last)*1000);last=now
  paced=180/(last-start)
  check(label+'_static_gpu_uploads',gpu.upload_count==uploads)
  entry={'context':gpu.context_info,'window':[root.winfo_width(),root.winfo_height()],'viewport':list(gpu.fbo_size),'mode':'Texturizado','triangles':len(app.mesh[1]),'resolved_textures':len(app.detail['textures']),'frames':len(frames),'warmup_frames':30,'frame_ms_p50':float(np.percentile(frames,50)),'frame_ms_p95':float(np.percentile(frames,95)),'frame_ms_max':max(frames),'swap_completed_fps_wall':len(frames)/wall,'input_to_update_ms_p50':float(np.percentile(dispatch,50)),'input_to_update_ms_p95':float(np.percentile(dispatch,95)),'ui_heartbeat_1ms_actual_p50':float(np.percentile(heartbeat,50)) if heartbeat else None,'ui_heartbeat_1ms_actual_p95':float(np.percentile(heartbeat,95)) if heartbeat else None,'paced_target_hz':60,'paced_swap_completed_fps':paced,'paced_interval_ms_p50':float(np.percentile(intervals,50)),'paced_interval_ms_p95':float(np.percentile(intervals,95)),'static_upload_count':uploads,'measurement':'Wall time through GPU glFinish and native SwapBuffers; visible WGL window, NOT offscreen/headless. No physical scanout/presentation timestamp or monitor-refresh guarantee. GPU draws on Tk thread; measured blocking time is reported separately from UI heartbeat.'}
  result['benchmark'][label]=entry;save();gpu.snapshot().save(out/(label+'_gpu_frame.png'));shot(label+'_textured_ui.png')
  check(label+'_render_capacity_60fps',entry['swap_completed_fps_wall']>=60 and entry['frame_ms_p95']<=1000/60)
 try:
  root.update();shot('new_initial.png')
  for label,source in sources:
   started=time.perf_counter();dialog=dialog_open(source,label);elapsed=(time.perf_counter()-started)*1000
   check(label+'_auto_model',app.mesh is not None and bool(app.tree.selection()) and app.kind.get()=='Modelos')
   check(label+'_textured_default',app.render_mode.get()=='Texturizado' if app.detail['textures'] else app.render_mode.get()=='Sólido')
   result['journeys'][label]={'source':str(source),'dialog':dialog,'open_including_dialog_ms':elapsed,'sections':len(app.assets),'models':app.categories.count('Modelos'),'textures_including_references':app.categories.count('Texturas'),'selected':app.selected().name,'vertices':len(app.mesh[0]),'triangles':len(app.mesh[1]),'diffuse_materials':len(app.detail['textures']),'summary':app.source_info.get(),'status':app.status.get()};save();shot(label+'_auto_solid.png')
   choose_category(app,'Modelos');root.update();iid=app.tree.get_children()[0];tree_click(iid);check(label+'_tree_input_preview',app.mesh is not None)
   check(label+'_basename_visible',app.tree.item(iid,'text')==Path(app.selected().name).name)
   if benchmark and label in ('ada_game','tweed_vanilla'):bench(label)
   else:mode('Texturizado');shot(label+'_textured_ui.png');app.gpu.snapshot().save(out/(label+'_gpu_frame.png'))
  app.context_tabs.buttons[1].invoke();wait();texid=next(i for i in app.tree.get_children() if app.assets[int(i)].size>128);tree_click(texid);check('texture_input_preview',app.image is not None);shot('texture_user_input.png')
  check('no_tk_callback_errors',not result['callback_errors'])
 except Exception:
  result['failure']=traceback.format_exc();save();raise
 finally:
  while app.busy:root.update();time.sleep(.01)
  app.close();result['source_hashes_after']={str(p):digest(p) for _,p in sources};result['checks']['sources_unchanged']=result['source_hashes_before']==result['source_hashes_after'];save()
 result['success']=all(result['checks'].values());save();return result
