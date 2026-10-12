"""AI-original isolated FM6S template writer. No game writes, no rig claims.
License: MIT. Layout evidence: Albam Hexane CC0 schema, pinned in references.
"""
import struct,math,hashlib
class Template:
 def __init__(self,raw):
  self.raw=bytes(raw)
  if self.raw[:4]!=b'FM6S' or struct.unpack_from('<I',raw,4)[0]!=18:raise ValueError('Unsupported native FM6S: verified v18 only')
  self.meshes=[]
  count=struct.unpack_from('<I',raw,12)[0];table=struct.unpack_from('<I',raw,24)[0]
  if table!=208 or not 0<count<=10000:raise ValueError('Unproven header/table variant')
  for i in range(count):
   h=table+i*144;groups,offset,lod,mat=struct.unpack_from('<4I',raw,h)
   if groups!=1:raise ValueError('Unproven group variant: only observed one-group records supported')
   for j in range(groups):
    s=offset+j*144;vc,ic=struct.unpack_from('<2H',raw,s+8);io,isz=struct.unpack_from('<2I',raw,s+16);vo,vsz=struct.unpack_from('<2I',raw,s+44);wsz,wo=struct.unpack_from('<2I',raw,s+60)
    if not vc or vsz%vc or ic%3:raise ValueError('Invalid counts')
    stride=vsz//vc
    if stride not in (12,52):raise ValueError('Unproven vertex layout')
    for start,size in ((io,isz),(vo,vsz),(wo,wsz)):
     if start+size>len(raw):raise ValueError('Buffer span outside baseline')
    if isz<ic*2 or wsz<vc*8:raise ValueError('Truncated buffers')
    ids=struct.unpack_from('<'+str(ic)+'H',raw,io)
    if max(ids,default=0)>=vc:raise ValueError('Index outside vertex range')
    self.meshes.append(dict(mesh=i,group=j,header=s,mesh_header=h,vertices=vc,indices=ic,index_offset=io,index_size=isz,vertex_offset=vo,vertex_size=vsz,stride=stride,weight_offset=wo,weight_size=wsz,lod=lod,material_offset=mat))
  self.sha256=hashlib.sha256(raw).hexdigest()
 def export(self):
  return self.raw
 def export_positions(self,captures,*,baseline_sha256):
  if baseline_sha256!=self.sha256:raise ValueError('Baseline mismatch')
  if len(captures)!=len(self.meshes):raise ValueError('Topology changes blocked')
  out=bytearray(self.raw)
  for positions,m in zip(captures,self.meshes,strict=True):
   if len(positions)!=m['vertices']:raise ValueError('Topology changes blocked')
   for vi,pos in enumerate(positions):
    if len(pos)!=3 or not all(math.isfinite(x) for x in pos):raise ValueError('Invalid position')
    struct.pack_into('<3f',out,m['vertex_offset']+vi*m['stride'],*pos)
  return bytes(out)
