"""Read-only Wwise indexes; no event simulation or repacking."""
from pathlib import Path
import struct
from dataclasses import dataclass
@dataclass
class SliceAsset:
 name:str
 path:Path
 offset:int
 length:int
 source:Path
 owner:object=None
 @property
 def data(self):return None
 @property
 def size(self):return self.length
 def read(self):
  with self.path.open('rb') as f:f.seek(self.offset);data=f.read(self.length)
  if len(data)!=self.length:raise ValueError('Seção truncada.')
  return data
 def read_head(self,n):
  with self.path.open('rb') as f:f.seek(self.offset);return f.read(min(n,self.length))
 def chunks(self):
  with self.path.open('rb') as f:
   f.seek(self.offset);remaining=self.length
   while remaining:
    b=f.read(min(remaining,1024*1024))
    if not b:raise ValueError('Seção truncada.')
    remaining-=len(b);yield b

def open_wwise(path,cancel=None):
 p=Path(path).resolve();size=p.stat().st_size;out=[]
 def check():
  if cancel is not None and cancel.is_set():raise InterruptedError('Cancelado.')
 def add(name,offset,length):
  if offset<0 or length<0 or offset+length>size:raise ValueError('Índice Wwise fora do arquivo.')
  out.append(SliceAsset(name,p,offset,length,p))
 with p.open('rb') as f:
  magic=f.read(4)
  if magic==b'BKHD':
   chunks={};pos=0
   while pos+8<=size:
    check();f.seek(pos);tag,length=struct.unpack('<4sI',f.read(8))
    if pos+8+length>size:raise ValueError('Chunk BNK truncado.')
    chunks[tag]=(pos+8,length);pos+=8+length
   if b'DIDX' not in chunks or b'DATA' not in chunks:raise ValueError('BNK sem mídia embutida (eventos não são áudio).')
   start,length=chunks[b'DIDX'];base,available=chunks[b'DATA']
   if length%12:raise ValueError('DIDX inválido.')
   f.seek(start);index=f.read(length)
   for ident,offset,n in struct.iter_unpack('<3I',index):
    if offset+n>available:raise ValueError('Mídia BNK truncada.')
    add(f'{ident}.wem',base+offset,n)
  elif magic==b'AKPK':
   header=f.read(24)
   hs,endian,langs,banks,streams,external=struct.unpack('<6I',header)
   if endian!=1:raise ValueError('PCK big-endian não validado.')
   pos=28+langs
   for label,length in [('banks',banks),('streams',streams),('external',external)]:
    check();f.seek(pos);count=struct.unpack('<I',f.read(4))[0]
    if count>1000000 or length!=4+count*20:raise ValueError('Tabela PCK não suportada.')
    table=f.read(count*20)
    for ident,block,n,offset,lang in struct.iter_unpack('<5I',table):
     check();add(f'{label}/{lang}/{ident}'+('.bnk' if label=='banks' else '.wem'),offset*block,n)
    pos+=length
  else:raise ValueError('Magic não é BNK/PCK Wwise.')
 return out
