from pathlib import Path
from dataclasses import dataclass
from ssg_parser import parse_ssg
@dataclass
class Asset:
 name: str
 data: bytes | None = None
 path: Path | None = None
 source: Path | None = None
 @property
 def size(self): return len(self.data) if self.data is not None else self.path.stat().st_size
 def read(self): return self.data if self.data is not None else self.path.read_bytes()
 def read_head(self,n):
  if self.data is not None:return self.data[:n]
  with self.path.open('rb') as f:return f.read(n)
 def chunks(self):
  if self.data is not None:
   for i in range(0,len(self.data),1024*1024):yield self.data[i:i+1024*1024]
  else:
   with self.path.open('rb') as f:
    while chunk:=f.read(1024*1024):yield chunk
def extract(assets,destination,progress=lambda n,total:None,cancel=None):
 import re,stat
 def reject_reparse(path):
  for parent in (Path(path),*Path(path).parents):
   if parent.exists():
    s=parent.lstat()
    if stat.S_ISLNK(s.st_mode) or getattr(s,'st_file_attributes',0)&0x400:raise ValueError('Reparse / junction não permitido: '+str(parent))
 reject_reparse(destination)
 root=Path(destination).resolve()
 protected=[Path('C:/ORC-COMPLETO').resolve(),Path('C:/Program Files').resolve(),Path('C:/Program Files (x86)').resolve(),Path('C:/Windows').resolve()]
 protected += [a.source if a.source.is_dir() else a.source.parent for a in assets if a.source]
 if any(root==p or root.is_relative_to(p) for p in protected): raise ValueError('Destino protegido: escolha uma pasta fora da origem, biblioteca e jogo.')
 targets=[];used=set()
 for a in assets:
  if cancel is not None and cancel.is_set():raise InterruptedError('Cancelado antes da extração.')
  parts=a.name.replace('\\','/').split('/')
  if any(not p or p in ('.','..') or p.endswith((' ','.')) or re.search(r'[<>:"|?*\x00-\x1f]',p) or p.split('.')[0].upper() in {'CON','PRN','AUX','NUL',*[f'COM{i}' for i in range(1,10)],*[f'LPT{i}' for i in range(1,10)]} for p in parts): raise ValueError('Caminho inseguro no arquivo: '+a.name)
  reject_reparse(root.joinpath(*parts))
  target=root.joinpath(*parts).resolve()
  if not target.is_relative_to(root) or target.exists(): raise ValueError('Destino existente ou inseguro: '+str(target))
  base=target; duplicate=1
  while str(target).casefold() in used:
   target=base.with_name(base.stem+f'__duplicado_{duplicate}'+base.suffix); duplicate+=1
  if target.exists(): raise ValueError('Destino já existente: '+str(target))
  targets.append(target);used.add(str(target).casefold())
 # All file/ancestor conflicts must be rejected before any mkdir/write.
 for target in targets:
  for parent in target.parents:
   if parent==root:break
   if str(parent).casefold() in used or (parent.exists() and not parent.is_dir()):
    raise ValueError('Conflito arquivo/diretório: '+str(parent)+' ↔ '+str(target))
 for i,(a,p) in enumerate(zip(assets,targets),1):
  if cancel is not None and cancel.is_set(): raise ValueError('Cancelado; arquivos concluídos foram preservados.')
  reject_reparse(p)
  p.parent.mkdir(parents=True,exist_ok=True)
  reject_reparse(p)
  if not p.resolve().is_relative_to(root): raise ValueError('Destino redirecionado para fora da pasta.')
  created=False
  try:
   with p.open('xb') as f:
    created=True
    chunks=a.chunks() if hasattr(a,'chunks') else (a.read(),)
    for chunk in chunks:
     if cancel is not None and cancel.is_set(): raise InterruptedError('Cancelado; arquivo parcial removido.')
     f.write(chunk)
  except Exception:
   # Remove only the file this operation successfully created, never an existing target.
   if created:p.unlink(missing_ok=True)
   raise
  progress(i,len(assets))
 return targets

def parse_mesh(data):
 # Table traversal adapted from orc_import_blender.py parse_model (1053-1201).
 # No scanning, Blender, rigging or material interpretation.
 import struct,numpy as np
 def unpack(fmt,offset):
  size=struct.calcsize('<'+fmt)
  if offset<0 or offset+size>len(data): raise ValueError('Tabela de modelo truncada.')
  return struct.unpack_from('<'+fmt,data,offset)
 if data[:4]!=b'FM6S': raise ValueError('Este arquivo não contém uma malha FM6S.')
 version,unknown,count=unpack('3i',4)
 if version not in (17,18): raise ValueError(f'Versão FM6S {version} não suportada (somente 17/18).')
 table=unpack('i',24)[0]
 if count<1 or count>10000: raise ValueError('Contagem de malhas inválida.')
 vertices=[]; faces=[]; total=0
 for m in range(count):
  subcount,subtable,skel,mat=unpack('4i',table+m*144)
  if subcount<0 or subcount>10000: raise ValueError('Contagem de submalhas inválida.')
  for s in range(subcount):
   pos=subtable+s*144
   vc,ic,color,istart,isz=unpack('2H2iH',pos+8)
   vstart,vsize=unpack('2i',pos+44)
   if not vc or not ic: continue
   stride=vsize//vc
   if vsize%vc or stride not in (12,24,28,32,40,44,52,56,60): raise ValueError(f'Stride {stride} não suportado.')
   if vstart<0 or vstart+vsize>len(data) or istart<0 or istart+ic*2>len(data) or ic%3: raise ValueError('Buffers de geometria inválidos.')
   v=np.ndarray((vc,3),dtype='<f4',buffer=data,offset=vstart,strides=(stride,4)).copy()
   f=np.frombuffer(data,dtype='<u2',count=ic,offset=istart).astype(np.int32).reshape(-1,3)
   if not np.isfinite(v).all() or f.max()>=vc: raise ValueError('Vértices/índices inválidos.')
   vertices.append(v); faces.append(f+total); total+=vc
 if not vertices: raise ValueError('Nenhuma geometria disponível.')
 return np.concatenate(vertices),np.concatenate(faces)

def project(vertices,yaw,pitch,zoom,width,height):
 import numpy as np,math
 v=vertices-(vertices.min(axis=0)+vertices.max(axis=0))/2
 scale=max(float(np.ptp(vertices,axis=0).max()),1e-6)
 cy,sy=math.cos(yaw),math.sin(yaw); cp,sp=math.cos(pitch),math.sin(pitch)
 r=np.array([[cy,0,sy],[sy*sp,cp,-cy*sp],[-sy*cp,sp,cy*cp]])
 xy=(v@r.T)[:,:2]*min(width,height)*.8/scale*zoom
 xy[:,1]*=-1
 return xy+np.array([width/2,height/2])

def preview(asset):
 import io
 from PIL import Image
 ext=Path(asset.name).suffix.lower()
 data=asset.read() if ext in ('.dds','.png','.jpg','.jpeg','.bmp','.tga','.edgemodel') else asset.read_head(4096)
 if ext=='.dds' and len(data)==4:
  raise ValueError('Esta referência DDS de 4 bytes não contém pixels. Abra a textura DDS completa correspondente.')
 if ext in ('.dds','.png','.jpg','.jpeg','.bmp','.tga'):
  with Image.open(io.BytesIO(data)) as im: return 'image',im.convert('RGBA')
 if ext=='.edgemodel': return 'mesh',parse_mesh(data)
 head=data[:4096]
 text=''.join(chr(b) if b in (9,10,13) or 32<=b<127 else '.' for b in head)
 hexview='\n'.join(f'{i:08X}  '+head[i:i+16].hex(' ') for i in range(0,min(1024,len(head)),16))
 if asset_category(asset)=='Áudio' and ext not in ('.bnk','.pck'):
  return 'audio',f'{asset.name}\nTamanho: {asset.size:,} bytes\nMídia de áudio • metadados; use Reproduzir ou Exportar WAV para decodificar.\n\n'+hexview
 return 'text',f'{asset.name}\nTamanho: {asset.size:,} bytes\n\nTexto (primeiros 4096 bytes):\n{text}\n\nHex (primeiros 1024 bytes):\n{hexview}'

def asset_category(asset):
 ext=Path(asset.name).suffix.lower()
 if ext=='.edgemodel':
  return 'Modelos' if asset.read_head(4)==b'FM6S' else 'Outros'
 if ext in ('.dds','.png','.jpg','.jpeg','.bmp','.tga'):return 'Texturas'
 if ext in ('.wem','.wav','.ogg','.mp3','.fsb','.bnk','.pck'):return 'Áudio'
 if ext in ('.bik','.bk2','.mp4','.avi'):return 'Vídeo'
 return 'Outros'

def open_source(path,cancel=None):
 p=Path(path).resolve()
 if p.is_dir():
  result=[]
  for f in p.rglob('*'):
   if cancel is not None and cancel.is_set():raise InterruptedError('Cancelado.')
   if f.is_file() and not f.is_symlink():result.append(Asset(str(f.relative_to(p)).replace('\\','/'),path=f,source=p))
  return sorted(result,key=lambda a:a.name.casefold())
 if p.suffix.lower() in ('.wem','.wav','.ogg','.mp3','.fsb','.bik','.bk2','.mp4','.avi'):
  return [Asset(p.name,path=p,source=p)]
 if p.suffix.lower() in ('.bnk','.pck'):
  from containers import open_wwise
  return open_wwise(p,cancel)
 from archive import open_ssg
 return open_ssg(p,cancel)
