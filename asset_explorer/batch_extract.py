"""Read-only root-bound game inventory and sequential streamed extraction."""
from pathlib import Path
import os,stat,json,hashlib,shutil,struct
import core
LOOSE={'.dds','.matb','.edgemodel','.hkx','.wem','.wav','.ogg','.mp3','.fsb','.bik','.bk2','.png','.tga'}
BANKS={'.bnk','.pck'}
def reparse(path):
 s=Path(path).lstat()
 return stat.S_ISLNK(s.st_mode) or bool(getattr(s,'st_file_attributes',0)&0x400)
def bound(path,root):
 p=Path(path);r=Path(root).resolve()
 if not p.resolve().is_relative_to(r):raise ValueError('Path escapes root: '+str(p))
 for ancestor in (p,*p.parents):
  if ancestor.exists() and reparse(ancestor):raise ValueError('Reparse point rejected: '+str(ancestor))
  if ancestor==r:break
 return p

def inventory(root,loose=True,banks=False,cancel=None):
 root=Path(root).absolute();bound(root,root)
 if not root.is_dir():raise ValueError('Installation directory not found.')
 result={'root':str(root.resolve()),'items':[],'excluded':0,'reparse_skipped':[],'input_bytes':0,'estimated_output_bytes':0,'estimate_unknown':0}
 for directory,dirs,files in os.walk(root,followlinks=False):
  if cancel is not None and cancel.is_set():raise InterruptedError('Cancelado.')
  keep=[]
  for name in sorted(dirs,key=str.casefold):
   p=Path(directory)/name
   if reparse(p):result['reparse_skipped'].append(str(p.relative_to(root)))
   else:keep.append(name)
  dirs[:]=keep
  for name in sorted(files,key=str.casefold):
   p=Path(directory)/name
   if reparse(p):result['reparse_skipped'].append(str(p.relative_to(root)));continue
   ext=p.suffix.lower();kind='ssg' if ext=='.ssg' else 'bank' if banks and ext in BANKS else 'loose' if loose and ext in LOOSE else None
   if not kind:result['excluded']+=1;continue
   size=p.stat().st_size;estimate=size
   if kind=='ssg':
    try:
     with p.open('rb') as f:
      h=f.read(32);e='>' if struct.unpack_from('<I',h)[0]>65535 else '<';version,_,infos=struct.unpack_from(e+'3I',h)
      if version not in (5,6) or infos%32 or infos>size-32:raise ValueError('invalid header')
      estimate=0
      for _ in range(infos//32):estimate+=struct.unpack_from(e+'I',f.read(32),8)[0]
    except (OSError,ValueError,struct.error):estimate=None;result['estimate_unknown']+=1
   result['items'].append({'relative':p.relative_to(root).as_posix(),'kind':kind,'bytes':size,'estimated_bytes':estimate})
   result['input_bytes']+=size;result['estimated_output_bytes']+=estimate or 0
 result['items'].sort(key=lambda x:x['relative'].casefold());return result

def destination_safe(destination,root):
 dest=Path(destination).absolute();source=Path(root).resolve()
 protected=[source if source.is_dir() else source.parent,Path('C:/ORC-COMPLETO'),Path('C:/Windows'),Path('C:/Program Files'),Path('C:/Program Files (x86)')]
 # Archive source directories can be deep under an installation. Protect the
 # installation above dlc too, not merely Characters/skel.
 for ancestor in (source,*source.parents):
  if ancestor.name.casefold()=='dlc':protected.append(ancestor.parent)
 for p in protected:
  if dest.resolve()==p.resolve() or dest.resolve().is_relative_to(p.resolve()):raise ValueError('Protected destination: '+str(dest))
 for p in (dest,*dest.parents):
  if p.exists() and reparse(p):raise ValueError('Destination reparse point rejected.')
 return dest

def run(inv,destination,cancel=None,progress=lambda n,total:None,extract_banks=False,archive_progress=lambda archive,n,total:None):
 root=Path(inv['root']);dest=destination_safe(destination,root)
 if dest.exists() and any(dest.iterdir()):raise ValueError('Choose a new or empty destination; existing files are never overwritten.')
 parent=dest
 while not parent.exists():parent=parent.parent
 estimate=inv['estimated_output_bytes'];reserve=max(64*1024**2,min(4*1024**3,estimate))
 if shutil.disk_usage(parent).free<estimate+reserve:raise ValueError('Insufficient space for estimated output + temporary archive cache; estimate is not an exact guarantee.')
 dest.mkdir(parents=True,exist_ok=True)
 report={'root':str(root),'destination':str(dest),'total':len(inv['items']),'processed':0,'failed':0,'unsupported':0,'cancelled':False,'not_started':0,'outputs':[],'entries':[],'estimate_unknown':inv['estimate_unknown'],'estimated_output_bytes':estimate,'space_estimate_exact':False}
 def output_done(paths):
  for p in paths:
   h=hashlib.sha256()
   with p.open('rb') as f:
    while b:=f.read(1024*1024):h.update(b)
   report['outputs'].append({'path':p.relative_to(dest).as_posix(),'bytes':p.stat().st_size,'sha256':h.hexdigest()})
 for item in inv['items']:
  if cancel is not None and cancel.is_set():report['cancelled']=True;break
  entry={'source':item['relative'],'status':'failed'};assets=[];folder=None
  try:
   source=bound(root/item['relative'],root)
   if source.stat().st_size!=item['bytes']:raise ValueError('Source changed since inventory.')
   if item['kind']=='ssg':
    from archive import MAX_INPUT
    if item['bytes']>MAX_INPUT:raise NotImplementedError('SSG exceeds supported 1 GiB input safety limit.')
    if item['bytes']>=32:
     with source.open('rb') as f:head=f.read(4)
     version=struct.unpack('<I',head)[0]
     if version>65535:version=struct.unpack('>I',head)[0]
     if 1<=version<=255 and version not in (5,6):raise NotImplementedError('Unsupported SSG version: '+str(version))
   if item['kind']=='ssg' or (item['kind']=='bank' and extract_banks):
    assets=core.open_source(source,cancel);folder=dest/('ssg_unpacked' if item['kind']=='ssg' else 'bank_media')/item['relative']
   else:assets=[core.Asset(item['relative'],path=source,source=root)];folder=dest/'loose'
   paths=core.extract(assets,folder,progress=lambda n,total:archive_progress(item['relative'],n,total),cancel=cancel);output_done(paths);entry['status']='processed';entry['files']=len(paths);report['processed']+=1
  except Exception as e:
   if cancel is not None and cancel.is_set():report['cancelled']=True;entry['status']='cancelled'
   elif isinstance(e,NotImplementedError):report['unsupported']+=1;entry['status']='unsupported'
   else:report['failed']+=1
   entry['reason']=str(e)
   # Fresh operation-owned archive folder: core removed only its partial file.
   # Read back completed outputs without following reparse points.
   if folder and folder.exists():
    known={x['path'] for x in report['outputs']};completed=[]
    for directory,dirs,files in os.walk(folder,followlinks=False):
     dirs[:]=[n for n in dirs if not reparse(Path(directory)/n)]
     for name in files:
      p=Path(directory)/name
      if not reparse(p) and p.relative_to(dest).as_posix() not in known:completed.append(p)
    output_done(completed);entry['completed_files_preserved']=len(completed)
  finally:
   owners={id(a.owner):a.owner for a in assets if getattr(a,'owner',None)}
   for owner in owners.values():owner.cleanup()
   assets.clear()
  report['entries'].append(entry)
  # Completion count is not a success percentage; failed runs never claim 100%.
  progress(report['processed'],report['total'])
  if report['cancelled']:break
 report['not_started']=report['total']-len(report['entries'])
 report['success']=report['processed']==report['total'] and not report['failed'] and not report['cancelled']
 with (dest/'batch_report.json').open('x',encoding='utf-8') as f:json.dump(report,f,indent=2,ensure_ascii=False)
 return report
