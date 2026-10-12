"""Owned, asset-free real Tk event/native dialog acceptance for Settings."""
import ctypes,os,sys,time,threading,json,hashlib,traceback
from ctypes import wintypes as W
from pathlib import Path
import qa_paths
import tkinter as tk

def run(destination):
 from app import Explorer
 import media
 from PIL import ImageGrab
 out=Path(destination);out.mkdir(parents=True,exist_ok=True)
 configs=[media.home()/'dependencies.json',media.home()/'ui_language.json']
 originals={p:p.read_bytes() if p.exists() else None for p in configs}
 result={'frozen':bool(getattr(sys,'frozen',False)),'executable':sys.executable,'executable_sha256':hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest(),'checks':{},'screenshots':[],'dialogs':[],'capture_method':'Pillow ImageGrab(window=owned Settings HWND), real Tk rendering; asset-free','coverage_gaps':['No physical mouse or display scanout assertion; CTk accessible Return and combobox Tk events used.','DPI tested at runtime scaling only, not multiple Windows display DPI settings.','Detection validates file existence, not decoder authenticity/version.']}
 def save():(out/'results.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
 def check(name,value):
  result['checks'][name]=bool(value);save()
  if not value:raise AssertionError(name)
 u=ctypes.WinDLL('user32');u.GetDlgItem.restype=W.HWND;u.SendMessageW.argtypes=[W.HWND,W.UINT,W.WPARAM,W.LPARAM];u.PostMessageW.argtypes=[W.HWND,W.UINT,W.WPARAM,W.LPARAM]
 root=tk.Tk();app=Explorer(root);root.geometry('1024x680+0+0');root.update()
 errors=[];root.report_callback_exception=lambda t,e,tb:errors.append(''.join(traceback.format_exception(t,e,tb)))
 def event(button):button._canvas.focus_force();root.update();button._canvas.event_generate('<Return>');root.update()
 def language(value):
  app.language_display.set('English' if value=='en' else 'Português (Brasil)');app.language_selector.event_generate('<<ComboboxSelected>>');root.update()
 def open_settings():event(next(b for b in app.modern_buttons if app.label_sources[b]=='Configurações'))
 def shot(name):
  root.update();w=app.settings_window;hwnd=u.GetAncestor(w.winfo_id(),2);ImageGrab.grab(window=hwnd).save(out/name);result['screenshots'].append(name);save()
 def native(path=None,cancel=False,key='ffmpeg'):
  state={};title=app.tr('Selecionar executável oficial '+key)
  def drive():
   end=time.monotonic()+20
   while time.monotonic()<end:
    found=[]
    @ctypes.WINFUNCTYPE(W.BOOL,W.HWND,W.LPARAM)
    def enum(h,p):
     pid=W.DWORD();u.GetWindowThreadProcessId(h,ctypes.byref(pid));text=ctypes.create_unicode_buffer(512);u.GetWindowTextW(h,text,512);cls=ctypes.create_unicode_buffer(64);u.GetClassNameW(h,cls,64)
     if pid.value==os.getpid() and text.value==title and cls.value=='#32770':found.append(h)
     return True
    u.EnumWindows(enum,0)
    if found:
     h=found[0];edit=u.GetDlgItem(h,1148)
     if not edit:time.sleep(.05);continue
     if path:
      text=ctypes.create_unicode_buffer(str(path));u.SendMessageW(edit,0xC,0,ctypes.addressof(text))
     ImageGrab.grab(window=h).save(out/(key+('_native_cancel.png' if cancel else '_native_select.png')))
     u.PostMessageW(h,0x111,2 if cancel else 1,0);state.update(native=True,pid=os.getpid(),cancel=cancel,path=str(path) if path else None);return
    time.sleep(.02)
   state['timeout']=True
  t=threading.Thread(target=drive,daemon=True);t.start();event(app.dependency_choose[key]);t.join(2);result['dialogs'].append(state);check(key+('_native_cancel' if cancel else '_native_select'),state.get('native',False))
 try:
  check('no_assets_loaded',not app.assets);check('hardware_context',app.gpu.ready);result['gl_info']=app.gpu.context_info;result['tk_scaling']=root.tk.call('tk','scaling')
  open_settings();check('settings_opened_by_event',app.settings_window.state()=='normal')
  for lang in ['pt-BR','en']:
   language(lang);event(app.inspector_tabs.buttons[0]);check('information_'+lang,app.settings_information.winfo_ismapped());shot('information_'+lang+'.png')
   event(app.inspector_tabs.buttons[1]);check('dependencies_'+lang,app.dependency_panel.winfo_ismapped());shot('dependencies_'+lang+'.png')
   check('select_label_'+lang,app.dependency_choose['ffmpeg'].cget('text')==('Select…' if lang=='en' else 'Selecionar…'))
   check('status_localized_'+lang,('Detection:' if lang=='en' else 'Detecção:') in app.dependency_status['ffmpeg'].get())
  original_values={k:v.get() for k,v in app.dep_vars.items()}
  check('actual_decoders_exist',all(p and Path(p).is_file() for p in original_values.values()))
  native(cancel=True);check('cancel_keeps_paths',{k:v.get() for k,v in app.dep_vars.items()}==original_values)
  native(original_values['ffmpeg']);check('select_path_readback',app.dep_vars['ffmpeg'].get().replace('\\','/').casefold()==original_values['ffmpeg'].replace('\\','/').casefold())
  native(cancel=True,key='vgmstream');check('vgmstream_cancel_keeps_path',app.dep_vars['vgmstream'].get()==original_values['vgmstream'])
  native(original_values['vgmstream'],key='vgmstream');check('vgmstream_select_readback',app.dep_vars['vgmstream'].get().replace('\\','/').casefold()==original_values['vgmstream'].replace('\\','/').casefold())
  e=app.dependency_entries['ffmpeg'];e._entry.focus_force();e._entry.selection_range(0,'end');e._entry.event_generate('<Control-c>');root.update();check('path_copy_exact',root.clipboard_get()==app.dep_vars['ffmpeg'].get());e._entry.xview_moveto(1);check('path_horizontal_scroll',e._entry.xview()[1]==1)
  before=configs[0].read_bytes() if configs[0].exists() else None
  e.delete(0,'end');e.insert(0,str(out/'missing.exe'));event(app.settings_save);check('invalid_inline_error','Path not found' in app.settings_feedback.get());check('invalid_no_config_write',(configs[0].read_bytes() if configs[0].exists() else None)==before);shot('invalid_path_en.png')
  e.delete(0,'end');e.insert(0,original_values['ffmpeg']);event(app.settings_save)
  saved=json.loads(configs[0].read_text(encoding='utf-8'));check('paths_saved_exact',saved=={k:v.get().strip() for k,v in app.dep_vars.items()});check('save_feedback','Paths saved.'==app.settings_feedback.get());shot('saved_paths_en.png')
  app.settings_window.withdraw();open_settings();check('reopen_same_paths',saved=={k:v.get().strip() for k,v in app.dep_vars.items()})
  app.close();root=tk.Tk();app=Explorer(root);root.geometry('1024x680+0+0');root.update();root.report_callback_exception=lambda t,e,tb:errors.append(str(e))
  open_settings();event(app.inspector_tabs.buttons[1]);check('restart_persistent_paths',saved=={k:v.get().strip() for k,v in app.dep_vars.items()})
  app.settings_window.geometry('620x480+20+20');root.update()
  result['compact']={'client':[app.settings_window.winfo_width(),app.settings_window.winfo_height()],'entry_widths':{k:e.winfo_width() for k,e in app.dependency_entries.items()},'save_bottom':app.settings_save.winfo_rooty()+app.settings_save.winfo_height()-app.settings_window.winfo_rooty()}
  check('compact_save_visible',result['compact']['save_bottom']<=480);check('compact_path_width',min(result['compact']['entry_widths'].values())>=300)
  for lang in ['en','pt-BR']:
   language(lang);app.dependency_panel._parent_canvas.yview_moveto(0);shot('compact_dependencies_'+lang+'.png')
   canvas=app.dependency_panel._parent_canvas;canvas.event_generate('<MouseWheel>',delta=-1200);root.update();check('compact_dependency_scroll_'+lang,canvas.yview()[0]>0);shot('compact_dependencies_scrolled_'+lang+'.png')
   event(app.inspector_tabs.buttons[0]);app.settings_information._parent_canvas.yview_moveto(0);shot('compact_information_'+lang+'.png')
   canvas=app.settings_information._parent_canvas;canvas.event_generate('<MouseWheel>',delta=-1200);root.update();check('compact_information_scroll_'+lang,canvas.yview()[0]>0);shot('compact_information_scrolled_'+lang+'.png');event(app.inspector_tabs.buttons[1])
  check('no_callback_errors',not errors);result['callback_errors']=errors;result['success']=all(result['checks'].values());save()
 except Exception:
  result['failure']=traceback.format_exc();save();raise
 finally:
  app.close()
  for p,b in originals.items():
   if b is None:p.unlink(missing_ok=True)
   else:p.write_bytes(b)
  check('configs_restored',all((p.read_bytes() if p.exists() else None)==b for p,b in originals.items()))
  result['check_count']=len(result['checks']);result['passed_count']=sum(result['checks'].values());save()
 return result
