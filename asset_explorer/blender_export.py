"""Optional Blender export; no game/addon writes or synthetic armatures."""
from pathlib import Path
import json,struct,math,hashlib,shutil
import numpy as np
import models,core,media,batch_extract
FORMATS={'blend','fbx','glb'}
def blender_path():
 try:configured=json.loads((media.home()/'dependencies.json').read_text(encoding='utf-8')).get('blender')
 except (OSError,ValueError):configured=None
 default=Path('C:/Program Files/Blender Foundation/Blender 5.0/blender.exe')
 return configured or shutil.which('blender') or (str(default) if default.is_file() else None)

def native_skeleton(data):
 points,parents=models.skeleton(data)
 count=len(parents);pose,parent=struct.unpack_from('<2I',data,24);custom=struct.unpack_from('<I',data,48)[0]
 start=custom+count*4+48;names=[]
 for i in range(count):
  end=data.find(b'\0',start)
  if start<0 or end<0:raise ValueError('Skeleton name table truncated.')
  name=data[start:end].decode('ascii');start=end+1
  if not name or name in names:raise ValueError('Skeleton names invalid or repeated.')
  names.append(name)
 locals=[]
 for i in range(count):
  values=struct.unpack_from('<12f',data,pose+24+i*48)
  if not all(math.isfinite(x) for x in values):raise ValueError('Skeleton transform nonfinite.')
  if not np.allclose(values[8:11],(1,1,1),atol=1e-5):raise ValueError('Non-unit native bone scale unsupported.')
  x,y,z,w=values[:4];n=math.sqrt(x*x+y*y+z*z+w*w);x,y,z,w=np.array([x,y,z,w])/n
  m=np.eye(4);m[:3,:3]=[[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]];m[:3,3]=values[4:7];locals.append(m)
 world={}
 def visit(i):
  if i not in world:world[i]=(visit(int(parents[i]))@locals[i]) if parents[i]>=0 else locals[i]
  return world[i]
 matrices=[visit(i).tolist() for i in range(count)]
 return {'names':names,'parents':parents.tolist(),'world_matrices':matrices,'local_matrices':[x.tolist() for x in locals],'native_sha256':hashlib.sha256(data).hexdigest(),'binding':'unbound: native bone palette / skin association not yet proven'}

def resolve_skeleton(asset,assets,manual=None):
 candidates=[a for a in assets if a.read_head(4) in (b'20SE',b'ES02') and Path(a.name).name.casefold()==Path(asset.name).stem.casefold()]
 owners=[]
 if manual:
  p=Path(manual)
  if p.suffix.lower()=='.ssg':candidates=core.open_source(p);owners=candidates
  else:candidates=[core.Asset(p.name,path=p)]
 elif not candidates and asset.source and Path(asset.source).is_file():
  source=Path(asset.source);p=source.parent/'skel'/source.name
  if p.is_file() and not batch_extract.reparse(p):candidates=core.open_source(p);owners=candidates
 try:
  candidates=[a for a in candidates if a.read_head(4) in (b'20SE',b'ES02')]
  if len(candidates)==1:return native_skeleton(candidates[0].read())
  return None
 finally:
  for owner in {id(a.owner):a.owner for a in owners if getattr(a,'owner',None)}.values():owner.cleanup()

def prepare(asset,assets,destination,formats,manual_skeleton=None,cancel=None):
 if not formats or not set(formats)<=FORMATS:raise ValueError('Select FBX, blend or GLB.')
 dest=batch_extract.destination_safe(destination,asset.source or Path(asset.path).parent if asset.path else asset.source or media.home())
 if dest.exists():raise ValueError('Export bundle already exists; choose a new folder.')
 if cancel is not None and cancel.is_set():raise InterruptedError('Cancelado.')
 data=asset.read();d=models.resolve(models.details(data),assets)
 # Blender/FBX reject repeated polygons. Drop only exact duplicate native index
 # triangles (not coincident vertices/seams), preserving first material assignment.
 seen=set();keep=[]
 for i,face in enumerate(d['faces']):
  key=tuple(sorted(map(int,face)))
  if key not in seen:seen.add(key);keep.append(i)
 duplicate_faces_removed=len(d['faces'])-len(keep)
 d['faces']=d['faces'][keep];d['face_mats']=d['face_mats'][keep]
 if duplicate_faces_removed:d['warnings'].append(f'{duplicate_faces_removed} exact duplicate index polygons removed for Blender topology validation.')
 skel=None;warning='Native rig not bound: bone palette / skin association not proven. Geometry, UV, materials and resolved diffuse textures exported; no placeholder rig.'
 try:skel=resolve_skeleton(asset,assets,manual_skeleton)
 except Exception as e:warning+=' Skeleton unavailable: '+str(e)
 dest.mkdir(parents=True);(dest/'textures').mkdir()
 textures={}
 for i,image in d['textures'].items():
  if cancel is not None and cancel.is_set():raise InterruptedError('Cancelado; completed export preparation preserved.')
  rel=f'textures/material_{i:04d}.png';image.save(dest/rel);textures[str(i)]=rel
 job={'name':Path(asset.name).stem,'source_name':asset.name,'source_sha256':hashlib.sha256(data).hexdigest(),'formats':list(formats),'vertices':d['vertices'].tolist(),'faces':d['faces'].tolist(),'uv':d['uv'].tolist(),'face_materials':d['face_mats'].tolist(),'materials':d['materials'],'textures':textures,'skeleton':skel,'rig_validated':False,'rig_warning':warning,'warnings':d['warnings']+d['references'],'material_scope':'Resolved diffuse only; original game shaders and other channels are not reproduced.'}
 with (dest/'job.json').open('x',encoding='utf-8') as f:json.dump(job,f)
 return job

def export(asset,assets,destination,formats,blender=None,manual_skeleton=None,cancel=None):
 executable=blender or blender_path()
 if not executable or not Path(executable).is_file():raise ValueError('Configure official Blender in Settings; raw extraction needs no Blender.')
 dest=Path(destination);job=prepare(asset,assets,dest,formats,manual_skeleton,cancel)
 script=Path(__file__).with_name('blender_worker.py').resolve()
 # Fixed trusted script; user paths only occur as argument-list data, never Python/shell source.
 command=[str(executable),'--background','--factory-startup','--python-exit-code','1','--python',str(script),'--',str((dest/'job.json').resolve())]
 try:media.run(command,cancel,timeout=600)
 except Exception as e:
  (dest/'export_failure.json').write_text(json.dumps({'error':str(e),'command':command,'completed_files_preserved':True}),encoding='utf-8');raise
 report=json.loads((dest/'export_report.json').read_text(encoding='utf-8'))
 if not report['success']:raise ValueError('Blender reimport verification failed; inspect export_report.json.')
 for fmt in formats:
  p=dest/('model.'+fmt)
  if not p.is_file() or not p.stat().st_size:raise ValueError('Blender output absent: '+fmt)
 return report
