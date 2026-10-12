"""Owned-window regression acceptance. Native dialogs and real file IO, no game writes."""
import ctypes,os,sys,time,threading,json,hashlib,traceback,tempfile
from ctypes import wintypes as W
from pathlib import Path
import qa_paths
import tkinter as tk

def digest(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  while b:=f.read(1024*1024):h.update(b)
 return h.hexdigest()

def run(destination):
 from app import Explorer
 import core
 from editor_style import capture_window
 out=Path(destination);out.mkdir(parents=True,exist_ok=True)
 scratch=qa_paths.scratch()
 sources=[qa_paths.fixture('adawong.ssg.original.bak'),qa_paths.asset('loose/audio/Audio/Streamed.pck')]
 result={'frozen':bool(getattr(sys,'frozen',False)),'executable':sys.executable,'executable_sha256':digest(sys.executable),'checks':{},'screenshots':[],'dialogs':[], 'source_hashes_before':{str(p):digest(p) for p in sources},'capture_method':'Target Tk window + actual same-process WGL framebuffer at measured child coordinates; no substituted assets. Native dialogs captured separately.'}
 def save():(out/'results.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
 def check(name,value):
  result['checks'][name]=bool(value);save()
  if not value:raise AssertionError(name)
 root=tk.Tk();app=Explorer(root);root.geometry('1360x850+0+0');root.update()
 u=ctypes.WinDLL('user32');u.GetDlgItem.restype=W.HWND;u.SendMessageW.argtypes=[W.HWND,W.UINT,W.WPARAM,W.LPARAM];u.PostMessageW.argtypes=[W.HWND,W.UINT,W.WPARAM,W.LPARAM]
 def wait():
  end=time.monotonic()+90
  while time.monotonic()<end:
   root.update()
   if not app.busy and app.render_id is None:
    root.update()
    if not app.busy and app.render_id is None:return
   time.sleep(.003)
  raise TimeoutError(app.status.get())
 def shot(name):
  root.update();capture_window(app).save(out/name);result['screenshots'].append(name);save()
 def pointer(button):
  # The application's explicit accessible Return binding is deterministic.
  button._canvas.focus_force();root.update();button._canvas.event_generate('<Return>');root.update()
 def tree(iid):
  app.tree.see(iid);root.update();x,y,w,h=app.tree.bbox(iid)
  app.tree.event_generate('<ButtonPress-1>',x=x+30,y=y+h//2);app.tree.event_generate('<ButtonRelease-1>',x=x+30,y=y+h//2);wait()
 def native(title,path=None,cancel=False,control=1152,label='dialog'):
  state={}
  def driver():
   end=time.monotonic()+20
   while time.monotonic()<end:
    found=[]
    @ctypes.WINFUNCTYPE(W.BOOL,W.HWND,W.LPARAM)
    def enum(h,param):
     pid=W.DWORD();u.GetWindowThreadProcessId(h,ctypes.byref(pid));text=ctypes.create_unicode_buffer(512);u.GetWindowTextW(h,text,512)
     cls=ctypes.create_unicode_buffer(128);u.GetClassNameW(h,cls,128)
     if pid.value==os.getpid() and text.value==title and cls.value=='#32770':found.append(h)
     return True
    u.EnumWindows(enum,0)
    if found:
     h=found[0];time.sleep(.15)
     from PIL import ImageGrab
     try:ImageGrab.grab(window=h).save(out/(label+'.png'))
     except Exception as e:state['capture_error']=str(e)
     if path is not None:
      edit=u.GetDlgItem(h,control) or u.GetDlgItem(h,1152)
      if not edit:
       candidates=[]
       @ctypes.WINFUNCTYPE(W.BOOL,W.HWND,W.LPARAM)
       def child(c,param):
        cls=ctypes.create_unicode_buffer(128);u.GetClassNameW(c,cls,128)
        if cls.value=='Edit' and u.GetDlgCtrlID(c) in (1148,1152,1001):candidates.append(c)
        return True
       u.EnumChildWindows(h,child,0)
       if candidates:edit=candidates[0]
      ready_until=time.monotonic()+10
      while not edit and time.monotonic()<ready_until:
       time.sleep(.05);edit=u.GetDlgItem(h,control) or u.GetDlgItem(h,1152)
       if not edit:
        candidates.clear();u.EnumChildWindows(h,child,0)
        if candidates:edit=candidates[0]
      state['filename_control']=int(edit or 0)
      if not edit:state['error']='No native edit control';u.PostMessageW(h,0x111,2,0);return
      ImageGrab.grab(window=h).save(out/(label+'.png'))
      text=ctypes.create_unicode_buffer(str(path));u.SendMessageW(edit,0xC,0,ctypes.addressof(text))
     command=2 if cancel or (path is None and not u.GetDlgItem(h,1)) else 1
     u.PostMessageW(h,0x111,command,0)
     state['native_button_id']=command
     # Folder picker first navigates to a typed absolute path, then accepts.
     if path is not None and control==1152 and not cancel:
      time.sleep(.3)
      if u.IsWindow(h):
       empty=ctypes.create_unicode_buffer('');u.SendMessageW(edit,0xC,0,ctypes.addressof(empty));u.PostMessageW(h,0x111,1,0)
     state.update(title=title,path=str(path) if path else None,cancel=cancel,hwnd=int(h),native=True);return
    time.sleep(.01)
   state['timeout']=True
  t=threading.Thread(target=driver,daemon=True);t.start();return t,state
 def extraction(index,dest=None,cancel=False,label='extract_dialog'):
  t,state=native(app.tr('Pasta fora da origem/jogo; nunca sobrescreve'),dest,cancel,label=label)
  # Invoke the real Tk menu command; Windows TrackPopupMenu blocks Tcl
  # after callbacks, so pointer automation of this menu is not claimed.
  app.extract_menu.invoke(index)
  root.update();wait();t.join(2);result['dialogs'].append(state);check(label+'_native',state.get('native',False));return state
 def open_native(path,label):
  t,state=native(app.tr('Abrir SSG / Wwise'),path,control=1148,label=label)
  root.event_generate('<Control-o>');root.update();wait();t.join(2);result['dialogs'].append(state);check(label+'_native',state.get('native',False))
 try:
  with tempfile.TemporaryDirectory(dir=scratch,prefix='qa_fix_owned_') as td:
   temp=Path(td);result['owned_temp_root']=str(temp)
   app.language_settings=temp/'language.json';app.set_language('pt-BR')
   shot('welcome_pt.png');app.set_language('en');shot('welcome_en.png');app.set_language('pt-BR')
   open_native(sources[0],'open_ada_dialog');check('auto_selected_footer',Path(app.selected().name).name in app.library_status.get())
   root.geometry('1024x680+0+0');root.update();wait()
   inspector=next(b for b in app.modern_buttons if app.label_sources[b]=='Inspetor')
   pointer(inspector);wait();check('inspector_hidden_by_keyboard',str(app.inspector) not in app.editor_pane.panes());pointer(inspector);wait();shot('compact_1024x680_inspector_reopened.png')
   result['compact_geometry']={'client':[root.winfo_width(),root.winfo_height()],'inspector_width':app.inspector.winfo_width(),'status_y':app.statusbar.winfo_y(),'status_height':app.statusbar.winfo_height(),'cancel_bottom':app.cancel_button.winfo_rooty()+app.cancel_button.winfo_height()-root.winfo_rooty()}
   check('compact_inspector_readable',app.inspector.winfo_width()>=220)
   check('compact_status_cancel_inside',result['compact_geometry']['cancel_bottom']<=680)
   root.geometry('1360x850+0+0');root.update();wait()
   selected=app.selected();sd=temp/'selected';sd.mkdir();extraction(0,sd,label='extract_selected_native')
   files=[p for p in sd.rglob('*') if p.is_file()];check('selected_exact_hash',len(files)==1 and digest(files[0])==hashlib.sha256(selected.read()).hexdigest())
   all_dir=temp/'all';all_dir.mkdir();extraction(1,all_dir,label='extract_all_native')
   outputs=[p for p in all_dir.rglob('*') if p.is_file()];used=set();hashes=[]
   for a in app.assets:
    p=all_dir/a.name;base=p;n=1
    while str(p).casefold() in used:p=base.with_name(base.stem+f'__duplicado_{n}'+base.suffix);n+=1
    used.add(str(p).casefold());hashes.append({'name':a.name,'relative_output':str(p.relative_to(all_dir)),'expected':hashlib.sha256(a.read()).hexdigest(),'actual':digest(p)})
   result['all_extraction_hashes']=hashes
   check('all_exact_count_hashes',len(outputs)==len(app.assets) and all(x['expected']==x['actual'] for x in hashes))
   before={str(p):digest(p) for p in outputs}
   t,modal=native('ORC Asset Explorer',label='no_overwrite_error')
   extraction(1,all_dir,label='existing_destination_native');t.join(2);result['dialogs'].append(modal)
   check('no_overwrite_native_error',modal.get('native',False) and 'existente' in app.status.get())
   check('existing_hashes_preserved',before=={str(p):digest(p) for p in outputs})
   extraction(0,cancel=True,label='folder_cancel_native');check('folder_cancel_no_worker',not app.busy)
   pointer(app.context_tabs.buttons[1]);wait();check('full_dds_before_empty',app.image is not None)
   app.search_entry.focus_set();app.search_entry.delete(0,'end');app.search_entry.insert(0,'zzzz-not-found');wait();shot('empty_search_pt.png')
   check('empty_state_clear',app.selected() is None and app.image is None and app.mesh is None and app.detail is None and not app.gpu.winfo_ismapped() and app.inspector_name.get()=='—')
   check('empty_exports_disabled',all(b.cget('state')=='disabled' for b in app.modern_buttons if app.label_sources[b] in ('Exportar PNG…','Exportar WAV…','Reproduzir','Exportar quadro PNG…')))
   app.search_entry.delete(0,'end');wait();iid=next(i for i in app.tree.get_children() if app.assets[int(i)].size==4 and app.assets[int(i)].name.lower().endswith('.dds'));tree(iid);shot('dds4_reference_pt.png')
   check('dds4_explained_pt', 'referência DDS de 4 bytes' in app.status.get() and 'BytesIO' not in app.status.get())
   app.set_language('en');shot('dds4_reference_en.png');check('dds4_explained_en','4-byte DDS reference' in app.status.get());app.set_language('pt-BR')
   open_native(sources[1],'open_pck_dialog');app.search_entry.insert(0,'6970.wem');wait();tree(app.tree.get_children()[0]);shot('wem6970_metadata_pt.png')
   check('wem6970_audio_metadata',app.active_context==2 and 'metadados' in app.text.get('1.0','end') and 'SSG inválido' not in app.status.get())
   app.set_language('en');shot('wem6970_metadata_en.png');check('wem6970_english','Audio media' in app.text.get('1.0','end'));app.set_language('pt-BR')
   wav=temp/'6970.wav';t,state=native(app.tr('Exportar WAV (não sobrescreve)'),wav,control=1148,label='wem_wav_save_dialog');pointer(next(b for b in app.modern_buttons if app.label_sources[b]=='Exportar WAV…'));wait();t.join(2);result['dialogs'].append(state)
   result['wav_export_operation']={'dialog':state,'busy':app.busy,'status':app.status.get(),'selected':app.selected().name if app.selected() else None,'destination':str(wav),'exists':wav.exists()};save()
   check('wav_save_native_completed',state.get('native',False) and not app.busy and wav.exists())
   import wave
   with wave.open(str(wav),'rb') as w:pcm=w.readframes(w.getnframes());result['wav']={'frames':w.getnframes(),'rate':w.getframerate(),'sha256':digest(wav),'nonzero_bytes':sum(b!=0 for b in pcm)}
   check('wem_actual_nonzero_pcm',result['wav']['nonzero_bytes']>0)
   # Actual large sparse file, normal filesystem read/write chunks, no injected delays.
   src=temp/'large_source';src.mkdir();(src/'a_completed.bin').write_bytes(b'completed-safe')
   large=src/'z_large.bin'
   with large.open('wb') as f:f.truncate(2*1024**3)
   app.load(src);wait();dest=temp/'large_cancel';dest.mkdir();partial=dest/'z_large.bin';cancel_state={}
   def cancel_when_written():
    if app.busy and partial.exists() and partial.stat().st_size>=1024*1024:
     cancel_state['observed_bytes']=partial.stat().st_size;pointer(app.cancel_button);cancel_state['pointer_sent']=True
    elif not cancel_state.get('pointer_sent'):root.after(1,cancel_when_written)
   root.after(1,cancel_when_written);extraction(1,dest,label='large_cancel_native');wait();shot('large_file_cancelled_pt.png')
   result['large_cancel']={'source_size':large.stat().st_size,**cancel_state,'status':app.status.get(),'source_hash_before':'not calculated before cancellation (sparse owned fixture)','completed_hash':digest(dest/'a_completed.bin') if (dest/'a_completed.bin').exists() else None}
   check('cancel_actual_large_file_in_progress',cancel_state.get('observed_bytes',0)>=1024*1024 and cancel_state.get('pointer_sent'))
   check('cancel_partial_removed',not partial.exists())
   check('cancel_completed_preserved',result['large_cancel']['completed_hash']==hashlib.sha256(b'completed-safe').hexdigest())
   check('cancel_status_explicit','Cancelado' in app.status.get())
   app.load(sources[0]);wait();app.help();shot('limitations_pt.png');app.set_language('en');shot('limitations_en.png')
   app.show_settings();app.inspector_tabs.select(1);wait();shot('settings_dependencies_en.png');app.settings_window.withdraw()
   app.set_language('pt-BR');wait()
  result['success']=all(result['checks'].values());save()
 except Exception:
  result['failure']=traceback.format_exc();save();raise
 finally:
  while app.busy:root.update();time.sleep(.01)
  app.close();result['source_hashes_after']={str(p):digest(p) for p in sources};result['checks']['sources_unchanged']=result['source_hashes_after']==result['source_hashes_before'];save()
 return result
