"""SSG metadata + mmap, bounded streaming decompression to disposable disk cache."""
import mmap,struct,zlib,tempfile
from pathlib import Path
from containers import SliceAsset
class CacheOwner:
 def __init__(self,dir):self.temp=tempfile.TemporaryDirectory(prefix='ssg_',dir=dir);self.name=self.temp.name
 def cleanup(self):self.temp.cleanup()
 def __del__(self):self.cleanup()
MAX_INPUT=1024**3
MAX_CACHE=4*1024**3

def open_ssg(path,cancel=None):
 p=Path(path).resolve()
 if p.stat().st_size>MAX_INPUT:raise ValueError('SSG acima de 1 GB: limite de segurança mantido.')
 def check():
  if cancel is not None and cancel.is_set():raise InterruptedError('Cancelado.')
 with p.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as raw:
  if len(raw)<32:raise ValueError('Cabeçalho SSG truncado.')
  e='>' if struct.unpack_from('<I',raw)[0]>65535 else '<'
  u=lambda off:struct.unpack_from(e+'I',raw,off)[0]
  version=u(0);infos=u(8);names=u(12);comp=u(24) if version==6 else 0;alignment=struct.unpack_from(e+'H',raw,28)[0] or 16
  if version not in (5,6) or infos%32 or 32+infos+comp+names>len(raw):raise ValueError('Cabeçalho SSG inválido.')
  if version==5:alignment=16
  namesoff=32+infos+comp;dataoff=namesoff+names;descs=[]
  for pos in range(32,32+infos,32):
   check();no=u(pos+4);n=u(pos+8);offset=u(pos+16);cs=u(pos+28) if comp else 0
   if no>=names:raise ValueError('Nome SSG fora da tabela.')
   start=namesoff+no;end=raw.find(b'\0',start,namesoff+names)
   if end<0:raise ValueError('Nome SSG não terminado.')
   descs.append((raw[start:end].decode('utf-8','replace'),n,offset,cs))
  owner=None;cache=None
  if any(cs for _,_,_,cs in descs):
   import media
   scratch=media.home()/'cache';scratch.mkdir(parents=True,exist_ok=True)
   owner=CacheOwner(scratch);cache=Path(owner.name)/'decompressed.bin'
   compstart=dataoff+sum((n+alignment-1)//alignment*alignment for _,n,_,cs in descs if not cs)
   sizes=[]
   for pos in range(32+infos,32+infos+comp,4):
    n=u(pos)
    if not n:break
    sizes.append(n)
   offset=compstart;total=0
   try:
    with cache.open('wb') as out:
     for n in sizes:
      check()
      if offset+n>len(raw):raise ValueError('Bloco SSG truncado.')
      d=zlib.decompressobj();end=offset+n
      # Same bounded padding recovery as legacy parser, but reject invalid blocks.
      if raw[offset:offset+2] not in (b'\x78\x9c',b'\x78\x01',b'\x78\x5e',b'\x78\xda'):
       candidates=[raw.find(m,offset+2,min(len(raw),offset+n+64)) for m in (b'\x78\x9c',b'\x78\x01',b'\x78\x5e',b'\x78\xda')];candidates=[x for x in candidates if x>=0]
       if not candidates:raise ValueError('Bloco zlib SSG inválido.')
       offset=min(candidates);end=min(len(raw),offset+n)
      pos=offset
      while pos<end:
       check();chunk=raw[pos:min(end,pos+65536)];pos+=len(chunk)
       while chunk:
        b=d.decompress(chunk,1024*1024);chunk=d.unconsumed_tail;total+=len(b)
        if total>MAX_CACHE:raise ValueError('Cache SSG acima de 4 GB: interrompido por segurança.')
        out.write(b)
      if not d.eof:raise ValueError('Fluxo zlib SSG incompleto.')
      offset=end
   except Exception:owner.cleanup();raise
  result=[];decomp=0
  for name,n,offset,cs in descs:
   check();target=cache if cs else p;start=decomp if cs else dataoff+offset
   if start+n>target.stat().st_size:
    if owner:owner.cleanup()
    raise ValueError('Seção SSG truncada.')
   result.append(SliceAsset(name,target,start,n,p,owner));decomp+=(n+alignment-1)//alignment*alignment
  return result
