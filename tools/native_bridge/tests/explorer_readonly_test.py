"""Read-only installed Explorer file-contract check. Does not copy/change Explorer."""
import sys,json,hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[3]/'addon'
explorer=Path(sys.argv[1]);evidence=Path(sys.argv[2]);sys.path.insert(0,str(explorer))
import core,models
sys.path.insert(0,str(ROOT))
from orc_native_bridge.project import load_project
results=[]
for asset in ('tweed','adawong','elitehunter'):
 folder=evidence/asset;t,meta=load_project(folder/'project/project.orcmeta.json')
 all_assets=core.open_source(folder)
 for name in ('reopen-noop.edgemodel','reopen-edit.edgemodel'):
  a=next(a for a in all_assets if Path(a.name).name==name)
  kind,geometry=core.preview(a);detail=models.details(a.read())
  assert kind=='mesh' and len(geometry[0])==sum(m['vertices'] for m in t.meshes)
  assert len(geometry[1])==sum(m['indices']//3 for m in t.meshes)
  assert np.array_equal(geometry[0],detail['vertices'])
  raw=a.read();native_positions=np.array([np.frombuffer(raw,dtype='<f4',count=3,offset=m['vertex_offset']+i*m['stride']) for m in t.meshes for i in range(m['vertices'])])
  assert np.array_equal(geometry[0],native_positions)
  results.append({'asset':asset,'file':name,'vertices':len(geometry[0]),'triangles':len(geometry[1]),'sha256':hashlib.sha256(a.read()).hexdigest(),'open_source_preview_details':True,'UI_or_frozen_exe_tested':False})
(evidence/'explorer-readonly-proof.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2));assert len(results)==6
