"""Local real Tk editor acceptance; target-window captures avoid other apps."""
import tkinter as tk
import ctypes,json,time,sys,traceback,tempfile,hashlib
from pathlib import Path
import qa_paths
from PIL import ImageGrab

def settings_contract(app):
 required={'ffmpeg_download':'https://ffmpeg.org/download.html','ffmpeg_repo':'https://github.com/FFmpeg/FFmpeg','ffmpeg_windows':'https://www.gyan.dev/ffmpeg/builds/','vgmstream_download':'https://github.com/vgmstream/vgmstream/releases','vgmstream_repo':'https://github.com/vgmstream/vgmstream','blender_download':'https://www.blender.org/download/','blender_repo':'https://github.com/blender/blender'}
 fields={'ffmpeg','vgmstream','blender'}
 return (app.settings_window.winfo_viewable() and app.dependency_panel.winfo_ismapped() and app.inspector_tabs.index('current')==1
  and all(app.dependency_links.get(key)==url for key,url in required.items())
  and fields<=set(app.dep_vars) and fields<=set(app.dependency_status) and fields<=set(app.dependency_entries))

def run(destination):
 from app import Explorer
 out=Path(destination);out.mkdir(parents=True,exist_ok=True)
 result={'frozen':bool(getattr(sys,'frozen',False)),'executable':sys.executable,'executable_sha256':hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest(),'checks':{},'callback_errors':[],'screenshots':[],'capture_method':'Actual native target Tk client capture + same-process actual GPU framebuffer pixels at native viewport coordinates; PrintWindow omits NVIDIA WGL children. No game assets or UI mockups substituted.'}
 root=tk.Tk();app=Explorer(root);root.geometry('1360x850+0+0');root.update();app.fit_editor_panes()
 root.report_callback_exception=lambda typ,error,tb:result['callback_errors'].append(''.join(traceback.format_exception(typ,error,tb)))
 def save():(out/'results.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
 def check(name,value):
  result['checks'][name]=bool(value);save()
  if not value:raise AssertionError(name)
 def wait():
  end=time.monotonic()+60
  while time.monotonic()<end:
   root.update()
   if not app.busy and app.render_id is None:
    root.update()
    if not app.busy and app.render_id is None:return
   time.sleep(.004)
  raise TimeoutError(app.status.get())
 def shot(name):
  root.update();handle=ctypes.windll.user32.GetAncestor(root.winfo_id(),2)
  from editor_style import capture_window
  capture_window(app).save(out/name);result['screenshots'].append(name);save()
 try:
  with tempfile.TemporaryDirectory(dir=qa_paths.scratch()) as temp:
   app.language_settings=Path(temp)/'language.json';app.set_language('pt-BR');wait();shot('welcome_pt.png')
   check('welcome_real_open_action',app.welcome.winfo_ismapped())
   app.load(qa_paths.fixture('adawong.ssg.original.bak'));wait();shot('ada_pt.png')
   check('auto_textured',app.render_mode.get()=='Texturizado' and app.mesh is not None)
   check('hardware_gpu',app.gpu.ready and app.gpu.hardware_renderer(app.gpu.context_info['GL_RENDERER']))
   result['context']=dict(app.gpu.context_info);result['viewport']=list(app.gpu.fbo_size)
   selector=next(w for w in app.toolbar.winfo_children() if w.winfo_class()=='TCombobox')
   selector.set('English');selector.event_generate('<<ComboboxSelected>>');wait();shot('ada_en.png')
   check('language_selector_input_persists',app.language=='en' and json.loads(app.language_settings.read_text())['language']=='en')
   check('english_tabs',app.context_tabs.tab(0,'text')=='Model' and app.inspector_tabs.tab(1,'text')=='Dependencies')
   app.show_settings();app.inspector_tabs.select(1);wait();shot('dependencies_en.png');check('official_links_and_settings_page',settings_contract(app))
   app.settings_window.withdraw();app.inspector_tabs.select(0);app.context_tabs.select(1);wait();shot('texture_en.png');check('texture_context_real',app.image is not None and app.gpu.ready)
   app.gpu.event_generate('<MouseWheel>',delta=120);wait();check('texture_zoom_input',app.texture_zoom>1)
   app.context_tabs.select(0);wait();app.context_tabs.select(4);wait();shot('metadata_en.png');check('metadata_context',not app.canvas.winfo_ismapped() and bool(app.text.get('1.0','end').strip()))
   app.context_tabs.select(0);wait();app.toggle_inspector();wait();shot('inspector_collapsed_en.png');check('inspector_collapsed',str(app.inspector) not in app.editor_pane.panes());app.toggle_inspector();wait()
   original=app.editor_pane.sashpos(0);app.editor_pane.sashpos(0,original+30);root.update();check('adjustable_pane',app.editor_pane.sashpos(0)==original+30);app.fit_editor_panes()
   check('single_location_file_menus',all(app.extract_menu.entrycget(i,'label')==app.tr(label) for i,label in enumerate(('Extrair selecionados','Extrair todos','Extrair jogo completo…','Exportar modelos (Blender)…'))))
   root.geometry('1024x740+0+0');root.update();app.fit_editor_panes();wait();shot('small_en.png');check('small_viewport',app.viewport.winfo_width()>460);root.geometry('1360x850+0+0');root.update();app.fit_editor_panes()
   app.help();root.update();check('help_action_visible',app.text.winfo_ismapped() and 'GPU' in app.text.get('1.0','end'))
   app.set_language('pt-BR');app.present_context(0);wait();shot('final_pt.png')
   check('no_callback_errors',not result['callback_errors'])
   result['success']=all(result['checks'].values());save()
 except Exception:result['failure']=traceback.format_exc();save();raise
 finally:
  while app.busy:root.update();time.sleep(.01)
  app.close();save()
 return result
