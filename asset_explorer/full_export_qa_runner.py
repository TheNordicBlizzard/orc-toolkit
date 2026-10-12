"""Real reduced extraction, Blender outputs and owned bilingual dialog QA."""
from pathlib import Path
import qa_paths
import sys,os,json,time,hashlib,threading,ctypes,traceback,shutil,collections
from ctypes import wintypes as W
import tkinter as tk
import core,batch_extract,blender_export,media
SCRATCH=qa_paths.scratch()
GAME=qa_paths.game()
def digest(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  while b:=f.read(1024*1024):h.update(b)
 return h.hexdigest()
def run(destination):
 from app import Explorer
 from PIL import ImageGrab
 from smoke_journey import owned_file_dialogs
 out=Path(destination);out.mkdir(parents=True,exist_ok=True);work=SCRATCH/('orc_full_export_'+str(os.getpid()));work.mkdir()
 configs=[media.home()/'dependencies.json',media.home()/'ui_language.json'];original={p:p.read_bytes() if p.exists() else None for p in configs}
 sources=[GAME/'dlc/pack1/Characters/adawong.ssg',GAME/'dlc/pack1/Characters/tweed.ssg'];before={str(p):digest(p) for p in sources}
 r={'frozen':bool(getattr(sys,'frozen',False)),'executable':sys.executable,'executable_sha256':digest(sys.executable),'work':str(work),'checks':{},'callback_errors':[],'coverage_gaps':['Owned Tk button events/native-dialog messages; not physical pointer or scanout.','Full inventory only, no 2144-SSG extraction.','Native skin palette association remains unproved: zero skin weights exported.','Only diffuse PNG channels are reproduced, not original game shader.']}
 def save():(out/'results.json').write_text(json.dumps(r,indent=2,ensure_ascii=False),encoding='utf-8')
 def check(name,value):
  r['checks'][name]=bool(value);save()
  if not value:raise AssertionError(name)
 root=tk.Tk();a=Explorer(root);a.language_settings=work/'language.json';root.geometry('1024x680+0+0');root.update()
 root.report_callback_exception=lambda t,e,tb:r['callback_errors'].append(''.join(traceback.format_exception(t,e,tb)))
 u=ctypes.WinDLL('user32');u.GetAncestor.restype=W.HWND;u.GetDlgItem.restype=W.HWND;u.SendMessageW.argtypes=[W.HWND,W.UINT,W.WPARAM,W.LPARAM];u.PostMessageW.argtypes=[W.HWND,W.UINT,W.WPARAM,W.LPARAM]
 def wait():
  deadline=time.monotonic()+600
  while time.monotonic()<deadline:
   root.update()
   if not a.busy and a.render_id is None:root.update();return
   time.sleep(.005)
  raise TimeoutError(a.status.get())
 def click(button):
  button.event_generate('<ButtonPress-1>',x=15,y=10);button.event_generate('<ButtonRelease-1>',x=15,y=10);root.update()
 def shot(w,name):
  root.update();hwnd=u.GetAncestor(w.winfo_id(),2);ImageGrab.grab(window=hwnd).save(out/name)
 def folder_picker(w,path):
  state={}
  def drive():
   deadline=time.monotonic()+15
   while time.monotonic()<deadline:
    for h in owned_file_dialogs():
     edit=u.GetDlgItem(h,1152)
     if not edit:continue
     time.sleep(.15);text=ctypes.create_unicode_buffer(str(path));u.SendMessageW(edit,0xC,0,ctypes.addressof(text));u.PostMessageW(h,0x111,1,0)
     time.sleep(.3)
     if u.IsWindowVisible(h):
      blank=ctypes.create_unicode_buffer('');u.SendMessageW(edit,0xC,0,ctypes.addressof(blank));u.PostMessageW(h,0x111,1,0)
     state['native']=True;return
    time.sleep(.02)
   state['timeout']=True
   for h in owned_file_dialogs():u.PostMessageW(h,0x111,2,0)
  thread=threading.Thread(target=drive,daemon=True);thread.start()
  # First Browse button in first path row (not a mocked filedialog).
  button=next(x for frame in w.winfo_children() for row in frame.winfo_children() for x in row.winfo_children() if x.winfo_class()=='TButton' and x.cget('text')==a.tr('Selecionar…'))
  click(button);thread.join(1);check('native_installation_picker',state.get('native',False));check('native_installation_path_readback',Path(w.source_var.get()).resolve()==path.resolve())
 try:
  inv=batch_extract.inventory(GAME,True,True);(out/'full_inventory.json').write_text(json.dumps(inv,indent=2),encoding='utf-8');r['inventory_counts']=dict(collections.Counter(i['kind'] for i in inv['items']));r['estimated_output_bytes']=inv['estimated_output_bytes'];r['estimate_unknown']=inv['estimate_unknown'];check('all_root_ssg_inventory',r['inventory_counts']['ssg']==2144)
  fixtures=work/'fixtures';fixtures.mkdir()
  for p in sources:shutil.copy2(p,fixtures/p.name)
  # One real loose DDS plus excluded executable/credential fixtures.
  loose=next(p for p in (GAME/'dlc').rglob('*.dds') if p.stat().st_size>128);shutil.copy2(loose,fixtures/'real.dds');(fixtures/'game.exe').write_bytes(b'excluded executable fixture');(fixtures/'credentials.ini').write_bytes(b'excluded credential fixture')
  for language in ('pt-BR','en'):
   a.set_language(language);a.extract_menu.invoke(2);root.update();w=next(x for x in root.winfo_children() if isinstance(x,tk.Toplevel) and x is not a.settings_window)
   if language=='pt-BR':folder_picker(w,fixtures)
   else:w.source_var.set(str(fixtures))
   w.destination_var.set(str(work/('batch_'+language)));shot(w,'batch_'+language+'.png');click(w.inventory_button);wait();check('ui_inventory_'+language,len(w.inventory['items'])==3)
   click(w.start_button);wait();report=w.last_report;r['batch_'+language]={k:v for k,v in report.items() if k!='outputs'};check('ui_batch_real_'+language,report['success'] and report['processed']==3);check('ui_batch_hashes_'+language,all(digest(Path(report['destination'])/p['path'])==p['sha256'] for p in report['outputs']));shot(w,'batch_done_'+language+'.png');w.destroy()
   a.load(sources[0]);wait();a.extract_menu.invoke(3);root.update();w=next(x for x in root.winfo_children() if isinstance(x,tk.Toplevel) and x is not a.settings_window)
   w.destination_var.set(str(work/('export_'+language)))
   for v in w.format_vars.values():v.set(True)
   shot(w,'export_'+language+'.png');click(w.start_button);wait();report=w.last_report;r['export_'+language]=report;check('ui_blender_three_formats_'+language,report['processed']==1 and report['failed']==0);shot(w,'export_done_'+language+'.png');w.destroy()
  reduced=batch_extract.inventory(fixtures);cancel=threading.Event()
  report=batch_extract.run(reduced,work/'cancel_batch',cancel,lambda n,total:cancel.set() if n>=1 else None);r['cancellation']=report;check('cancel_preserves_complete',report['cancelled'] and report['processed']==1 and report['not_started']==2 and bool(report['outputs']))
  broken=work/'broken_fixture';broken.mkdir();(broken/'broken.ssg').write_bytes(b'bad');(broken/'good.dds').write_bytes(b'fixture');report=batch_extract.run(batch_extract.inventory(broken),work/'failed_batch');r['failure_report']=report;check('failure_never_success',report['failed']==1 and report['processed']==1 and not report['success'])
  assets=core.open_source(qa_paths.fixture('tweed.ssg.original.bak'));asset=next(x for x in assets if x.read_head(4)==b'FM6S');r['tweed_export']=blender_export.export(asset,assets,work/'tweed_export',['blend','fbx','glb'],manual_skeleton=GAME/'dlc/pack1/Characters/skel/tweed.ssg');r['tweed_source_note']='Current installed Tweed FM6S is structurally unsupported (invalid submesh count); vanilla original backup used for Blender verification, installed archive retained read-only in batch.';check('tweed_blender_reimport',r['tweed_export']['success'])
  r['source_hashes_before']=before;r['source_hashes_after']={str(p):digest(p) for p in sources};check('game_sources_unchanged',before==r['source_hashes_after']);check('no_callback_errors',not r['callback_errors']);r['success']=all(r['checks'].values());save()
 except Exception:r['failure']=traceback.format_exc();save();raise
 finally:
  while a.busy:root.update();time.sleep(.01)
  a.close()
  for p,data in original.items():
   if data is None:p.unlink(missing_ok=True)
   else:p.write_bytes(data)
  check('settings_restored',all((p.read_bytes() if p.exists() else None)==data for p,data in original.items()));r['check_count']=len(r['checks']);save()
 return r
