"""Packaged executable test: real Tk, vanilla archives and real decoders.
Local fixtures are intentional. No game files are written; extracted test files
live in a dedicated temporary scratch directory, outside the source tree.
"""
from pathlib import Path
import qa_paths
import hashlib,json,time,tkinter as tk,tempfile,threading,sys,wave
from types import SimpleNamespace
from PIL import ImageGrab
import core,models,media

def digest(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  while b:=f.read(1024*1024):h.update(b)
 return h.hexdigest()

def run(destination):
 from app import Explorer
 out=Path(destination);out.mkdir(parents=True,exist_ok=True)
 base=qa_paths.required('ORC_QA_FIXTURE_ROOT');sources=[base/'tweed.ssg.original.bak',base/'adawong.ssg.original.bak',qa_paths.asset('loose/audio/Audio/Biohazard.bnk'),qa_paths.asset('loose/audio/Audio/Streamed.pck'),qa_paths.asset('loose/video/dlc/pack1/FMV/SPEC01/SPEC01_FMV01.bik')]
 before={str(p):digest(p) for p in sources};result={'version':2,'frozen':bool(getattr(sys,'frozen',False)),'executable':sys.executable,'source_hashes_before':before,'dependencies':media.dependencies(),'checks':{},'failures':[]}
 def save(): (out/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 def check(name,value):
  result['checks'][name]=bool(value);save()
  if not value:raise AssertionError(name)
 scratch=qa_paths.scratch();scratch.mkdir(parents=True,exist_ok=True)
 root=tk.Tk();app=Explorer(root);root.geometry(f'{min(1380,root.winfo_screenwidth()-20)}x{min(800,root.winfo_screenheight()-100)}+5+5');callback_errors=[]
 root.report_callback_exception=lambda typ,error,tb:callback_errors.append(str(error))
 def wait():
  end=time.monotonic()+90
  while app.busy and time.monotonic()<end:root.update();time.sleep(.01)
  root.update();check('worker_timeout',not app.busy)
  if app.status.get().startswith('Erro:'):raise RuntimeError(app.status.get())
 def pick(index):
  if not app.tree.exists(str(index)):app.set_category('Todos')
  app.tree.selection_set(str(index));app.select();wait()
 def shot(name):
  root.update();from editor_style import capture_window;capture_window(app).save(out/name)
 def invoke(section,label):
  b=next(w for w in app.modern_buttons if str(w).startswith(str(app.sections[section])) and w.cget('text')==label);b.invoke();root.update()
 try:
  with tempfile.TemporaryDirectory(prefix='orc_v2_',dir=scratch) as temp:
   result['extraction_test_directory']=temp
   for source in sources[:2]:
    assets=core.open_source(source);paths=core.extract(assets,Path(temp)/source.stem);expected=__import__('ssg_parser').parse_ssg(source.read_bytes())
    check(source.name+'_lazy',all(a.data is None for a in assets));check(source.name+'_bytes_match_legacy',all(a.read()==e[2] for a,e in zip(assets,expected)))
    hashes=[{'name':a.name,'destination':str(p.relative_to(temp)),'source_sha256':hashlib.sha256(a.read()).hexdigest(),'output_sha256':digest(p)} for a,p in zip(assets,paths)]
    result[source.name]={'sections':len(assets),'extracted':len(paths),'hashes':hashes};check(source.name+'_extraction_hashes',all(x['source_sha256']==x['output_sha256'] for x in hashes))
   assets=core.open_source(sources[0]);cancel=threading.Event()
   try:core.extract(assets,Path(temp)/'cancelled',lambda n,total:cancel.set(),cancel)
   except (InterruptedError,ValueError):pass
   check('vanilla_cancel_between_sections',len(list((Path(temp)/'cancelled').rglob('*.*')))==1)
   try:core.extract(assets,Path(temp)/'cancelled')
   except ValueError:check('no_overwrite_existing',True)
   else:check('no_overwrite_existing',False)
   app.load(sources[0]);wait();check('ui_vanilla_42',len(app.assets)==42)
   root.update();check('advanced_folded_default',not app.advanced_model.body.winfo_ismapped());shot('ui_context_inspector.png')
   app.advanced_model.header.invoke();root.update();check('advanced_models_expanded',app.advanced_model.body.winfo_ismapped())
   meshid=next(i for i,a in enumerate(app.assets) if a.name.endswith('.edgemodel') and 'shadow' not in a.name);pick(meshid);check('ui_mesh_real',app.mesh is not None)
   result['model']={'name':app.assets[meshid].name,'vertices':len(app.mesh[0]),'triangles':len(app.mesh[1]),'materials':len(app.detail['materials']),'resolved_diffuse':len(app.detail['textures'])}
   app.render_mode.set('Sólido');app.draw();wait();shot('ui_solid.png')
   app.render_mode.set('Texturizado');app.draw();wait();check('resolved_texture_materials',len(app.detail['textures'])>0);app.photo._PhotoImage__photo.write(str(out/'textured_render.png'),format='png');shot('ui_textured.png')
   skeleton=qa_paths.asset('ssg_unpacked/skel/Player_Male_Skeleton/skel/player_male_skeleton');app.set_skeleton(models.skeleton(skeleton.read_bytes()));root.update();result['skeleton']={'source':str(skeleton),'joints':len(app.bones[0]),'association':'manually chosen generic skeleton; no binding/animation claim'};shot('ui_skeleton_overlay.png');check('skeleton_finite',__import__('numpy').isfinite(app.bones[0]).all())
   app.advanced_model.header.invoke()
   texid=next(i for i,a in enumerate(app.assets) if a.name.endswith('_d.dds') and a.size>128);pick(texid);check('ui_texture_real',app.image is not None);app.wheel(SimpleNamespace(delta=120));app.drag=(0,0);app.orbit(SimpleNamespace(x=40,y=25));check('texture_zoom_pan',app.texture_zoom>1 and app.pan==(40,25));invoke('Texturas','Pixels 1:1');shot('ui_texture_zoom.png');invoke('Texturas','Ajustar');check('texture_reset',app.texture_zoom==1 and app.pan==(0,0))
   from tkinter import filedialog
   original_save=filedialog.asksaveasfilename
   try:
    png=Path(temp)/'exported_texture.png';filedialog.asksaveasfilename=lambda **kwargs:str(png);invoke('Texturas','Exportar PNG…')
    from PIL import Image
    with Image.open(png) as im:check('ui_png_export_pixels',im.convert('RGBA').tobytes()==app.image.convert('RGBA').tobytes())
   finally:filedialog.asksaveasfilename=original_save
   app.present_context(2)
   for source in sources[2:4]:
    app.load(source);wait();bank_assets=list(app.assets);label=source.suffix[1:];result[label]={'source':str(source),'media_count':len(bank_assets),'file_size':source.stat().st_size}
    check(label+'_lazy',all(a.data is None for a in bank_assets));check(label+'_listed',len(bank_assets)>0)
    sample=[bank_assets[0],bank_assets[len(bank_assets)//2],bank_assets[-1]] if len(bank_assets)>6 else bank_assets
    paths=core.extract(sample,Path(temp)/label);check(label+'_extraction_hashes',all(hashlib.sha256(a.read()).hexdigest()==digest(p) for a,p in zip(sample,paths)))
    result[label]['sample_hashes']=[{'name':a.name,'sha256':digest(p)} for a,p in zip(sample,paths)]
    pick(0);invoke('Áudio','Reproduzir');wait();info=dict(app.player.last_decode);wav=Path(app.player.temp.name)/'preview.wav'
    with wave.open(str(wav)) as w:pcm=w.readframes(min(w.getframerate(),w.getnframes()))
    info['nonzero_pcm_first_second']=any(pcm);result[label]['decode']=info;check(label+'_real_decoded_frames',info['frames']>0 and info['bytes']>44);check(label+'_nonzero_pcm',any(pcm));result[label]['playback']='winsound asynchronous playback accepted; no loopback/listening verification';shot('ui_'+label+'.png');invoke('Áudio','Parar')
    original_save=filedialog.asksaveasfilename
    try:
     exported=Path(temp)/(label+'_exported.wav');filedialog.asksaveasfilename=lambda **kwargs:str(exported);invoke('Áudio','Exportar WAV…');wait()
     with wave.open(str(exported)) as w:check(label+'_ui_wav_export',w.getnframes()==info['frames'])
    finally:filedialog.asksaveasfilename=original_save
   app.present_context(3);video=sources[4];app.load(video.parent);wait();vid=next(i for i,a in enumerate(app.assets) if Path(a.name).name==video.name);pick(vid);invoke('Vídeo','Decodificar 10 segundos');wait();check('bink_real_frames',len(app.frames)>1);app.stop_video();app.image=app.frames[min(30,len(app.frames)-1)];app.draw();root.update();shot('ui_bink.png');app.image.save(out/'bink_frame.png');result['video']={'source':str(video),'frames':len(app.frames),'preview_fps':12,'frame_size':list(app.frames[0].size),'audio_synchronized':False}
   invoke('Vídeo','Reproduzir');first=app.video_index;until=time.monotonic()+.35
   while time.monotonic()<until:root.update();time.sleep(.01)
   check('bink_ui_frame_advances',app.video_index>first);invoke('Vídeo','Pausar')
   # Real Tk cancel control against actual source indexing.
   app.worker(lambda:core.open_source(sources[3],app.cancel_event),lambda assets:None);app.cancel_button.invoke()
   until=time.monotonic()+15
   while app.busy and time.monotonic()<until:root.update();time.sleep(.01)
   check('ui_cancel_cooperative',not app.busy and app.cancel_event.is_set())
   check('no_tk_callback_errors',not callback_errors)
 finally:
  app.close();result['tk_callback_errors']=callback_errors;result['source_hashes_after']={str(p):digest(p) for p in sources};result['source_unchanged']=before==result['source_hashes_after'];result['checks']['all_sources_unchanged']=result['source_unchanged'];save()
 check('all_sources_unchanged',result['source_unchanged']);result['success']=all(result['checks'].values());save();return result
