from pathlib import Path
import qa_paths
import hashlib,json,time,tkinter as tk,io,wave,subprocess
import core
from PIL import ImageGrab

def run(destination):
 from app import Explorer
 out=Path(destination); out.mkdir(parents=True,exist_ok=True)
 source=qa_paths.fixture('tweed.ssg.original.bak'); second=qa_paths.fixture('adawong.ssg.original.bak')
 sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 before=sha(source); before2=sha(second); assets=core.open_source(source); ada=core.open_source(second)
 result={'source':str(source),'source_sha256_before':before,'archive_assets':len(assets),'second_archive_assets':len(ada)}
 paths=core.extract(assets,out/'extracted'); result['extracted_files']=len(paths); result['extracted_equal']=all(a.read()==p.read_bytes() for a,p in zip(assets,paths))
 root=tk.Tk(); app=Explorer(root)
 def wait():
  deadline=time.monotonic()+30
  while app.busy and time.monotonic()<deadline:root.update();time.sleep(.01)
  root.update()
  if app.busy:raise RuntimeError('Timeout no worker')
 try:
  app.load(source); wait(); result['ui_assets']=len(app.assets)
  meshid=next(i for i,a in enumerate(app.assets) if a.name.endswith('.edgemodel') and 'shadow' not in a.name)
  app.tree.selection_set(str(meshid)); app.select(); wait(); result['ui_mesh']=app.mesh is not None
  if app.mesh is None:raise RuntimeError('Malha não carregada')
  result['vertices']=len(app.mesh[0]); result['triangles']=len(app.mesh[1]); result['mesh_asset']=app.assets[meshid].name
  app.yaw+=.7;app.pitch+=.3;app.zoom=1.2;app.draw();wait()
  app.photo._PhotoImage__photo.write(str(out/'mesh_render.png'),format='png')
  ImageGrab.grab(bbox=(root.winfo_rootx(),root.winfo_rooty(),root.winfo_rootx()+root.winfo_width(),root.winfo_rooty()+root.winfo_height())).save(out/'ui_mesh.png')
  texid=next(i for i,a in enumerate(app.assets) if a.name.endswith('.dds') and a.size>128)
  app.set_category('Todos');app.tree.selection_set(str(texid)); app.select();wait(); result['ui_texture']=app.image is not None; result['texture_asset']=app.assets[texid].name; result['texture_size']=app.image.size
  app.image.save(out/'texture.png');ImageGrab.grab(bbox=(root.winfo_rootx(),root.winfo_rooty(),root.winfo_rootx()+root.winfo_width(),root.winfo_rooty()+root.winfo_height())).save(out/'ui_texture.png')
  app.load(out/'extracted'); wait(); result['folder_open']=len(app.assets)==len(assets)
  app.search.set('tweed'); app.kind.set('.edgemodel');app.filter();result['filter_matches']=len(app.tree.get_children())
  b=io.BytesIO()
  with wave.open(b,'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(8000);w.writeframes(b'\0\0'*800)
  result['audio_wav']=app.player.play(core.Asset('smoke.wav',b.getvalue()));app.player.stop()
  if app.player.ffmpeg:
   wav=out/'audio.wav';wav.write_bytes(b.getvalue());mp3=out/'audio.mp3'
   subprocess.run([app.player.ffmpeg,'-v','error','-y','-i',str(wav),str(mp3)],check=True,creationflags=subprocess.CREATE_NO_WINDOW)
   result['audio_mp3']=app.player.play(core.Asset('smoke.mp3',mp3.read_bytes()));app.player.stop()
  result['ffmpeg']=app.player.ffmpeg;result['vgmstream']=app.player.vgmstream
 finally:app.close()
 result['source_sha256_after']=sha(source);result['source_unchanged']=before==sha(source) and before2==sha(second)
 (out/'results.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
 return result
