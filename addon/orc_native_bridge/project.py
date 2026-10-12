"""Original MIT file contract. No archive repack, game write or generic writer."""
import json,hashlib,struct
from pathlib import Path
from .native_template import Template
SCHEMA='orc.native-project.v1'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def checked(raw):
 if len(raw)<208 or raw[:4]!=b'FM6S' or struct.unpack_from('<I',raw,4)[0]!=18:raise ValueError('Only verified FM6S v18 / Somente v18 verificado')
 t=Template(raw)
 spans=sorted((m['vertex_offset'],m['vertex_offset']+m['vertex_size']) for m in t.meshes)
 if any(b>c for (a,b),(c,d) in zip(spans,spans[1:])):raise ValueError('Ambiguous overlapping vertex buffers / buffers sobrepostos')
 protected=[(0,208+144*len(t.meshes))]
 bone_count,bone_offset=struct.unpack_from('<2I',raw,28);protected.append((bone_offset,bone_offset+48*bone_count))
 material_count=struct.unpack_from('<I',raw,144)[0]
 if material_count>64:raise ValueError('Unproven material table')
 for m in t.meshes:
  protected.extend([(m['header'],m['header']+128),(m['index_offset'],m['index_offset']+m['index_size']),(m['weight_offset'],m['weight_offset']+m['weight_size']),(m['material_offset'],m['material_offset']+4*material_count)])
  for j in range(material_count):
   ptr=struct.unpack_from('<I',raw,m['material_offset']+4*j)[0];end=raw.find(b'\0',ptr)
   if end<ptr:raise ValueError('Invalid material reference')
   protected.append((ptr,end+1))
 footer=struct.unpack_from('<I',raw,152)[0]
 if footer+4>len(raw):raise ValueError('Invalid relocation footer')
 count=struct.unpack_from('<I',raw,footer)[0]
 if footer+4+count*4!=len(raw):raise ValueError('Unproven relocation footer')
 protected.append((footer,len(raw)))
 for i in range(count):
  field=struct.unpack_from('<I',raw,footer+4+i*4)[0]
  protected.append((field,field+4))
 if any(a<d and c<b for a,b in spans for c,d in protected):raise ValueError('Vertex buffer aliases immutable native fields')
 return t
def create_project(template,destination,sidecar=None):
 template=Path(template);raw=template.read_bytes();t=checked(raw)
 provenance={}
 if sidecar:
  provenance=json.loads(Path(sidecar).read_text(encoding='utf8'))
  if provenance.get('source',{}).get('native_sha256')!=t.sha256:raise ValueError('Sidecar template SHA mismatch')
 destination=Path(destination);destination.mkdir(parents=True,exist_ok=False)
 (destination/'template.edgemodel').write_bytes(raw)
 meta={'schema':SCHEMA,'template':'template.edgemodel','template_sha256':t.sha256,'template_size':len(raw),'blocks':t.meshes,'provenance':provenance,'mode':'positions-only','coordinate_transform':'identity','rig':'native bytes preserved; no new rig','in_game':'UNVERIFIED'}
 p=destination/'project.orcmeta.json';p.write_text(json.dumps(meta,indent=2),encoding='utf8');return p

def load_project(path):
 p=Path(path).resolve();meta=json.loads(p.read_text(encoding='utf8'))
 if meta.get('schema')!=SCHEMA or meta.get('mode')!='positions-only' or meta.get('template')!='template.edgemodel':raise ValueError('Unsupported project contract')
 raw=(p.parent/'template.edgemodel').read_bytes();t=checked(raw)
 if t.sha256!=meta.get('template_sha256') or len(raw)!=meta.get('template_size') or meta.get('blocks')!=t.meshes:raise ValueError('Reference SHA / blocks mismatch; referência alterada')
 return t,meta

def write_export(t,captures,destination,project_path):
 destination=Path(destination).resolve();project_path=Path(project_path).resolve()
 if destination.suffix.lower()!='.edgemodel':raise ValueError('Use a new .edgemodel destination')
 if destination==project_path.parent/'template.edgemodel':raise ValueError('Source overwrite forbidden')
 report_path=destination.with_suffix(destination.suffix+'.diff.json')
 if destination.exists() or report_path.exists():raise ValueError('New destination required / destino NOVO obrigatório')
 fresh,_=load_project(project_path)
 if fresh.sha256!=t.sha256:raise ValueError('Changed template')
 out=t.export_positions(captures,baseline_sha256=t.sha256)
 changed=[];allowed=set()
 for bi,(m,positions) in enumerate(zip(t.meshes,captures,strict=True)):
  for vi,pos in enumerate(positions):
   off=m['vertex_offset']+vi*m['stride'];allowed.update(range(off,off+12))
   if out[off:off+12]!=t.raw[off:off+12]:changed.append({'block':bi,'vertex_id':vi,'field':'position.f32x3','offset':off,'before_hex':t.raw[off:off+12].hex(),'after_hex':out[off:off+12].hex()})
 diff=[i for i,(a,b) in enumerate(zip(t.raw,out,strict=True)) if a!=b]
 if any(i not in allowed for i in diff):raise ValueError('Non-position bytes changed')
 report={'schema':'orc.native-diff.v1','source_sha256':t.sha256,'output_sha256':sha(out),'same_size':len(out)==len(t.raw),'changed_bytes':diff,'fields':changed,'rig':'preserved bytes; not a new rig','in_game':'UNVERIFIED'}
 destination.parent.mkdir(parents=True,exist_ok=True)
 # Exclusive creation: do not overwrite any existing output, even after a race.
 with report_path.open('x',encoding='utf8') as f:json.dump(report,f,indent=2)
 try:
  with destination.open('xb') as f:f.write(out)
 except Exception:
  report_path.unlink();raise
 if destination.read_bytes()!=out or load_project(project_path)[0].sha256!=t.sha256:raise RuntimeError('Readback/source integrity failure')
 return report
