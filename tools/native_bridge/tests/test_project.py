import unittest,sys,tempfile,json,struct,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]/'addon';sys.path.insert(0,str(ROOT))
FIXTURE=Path(os.environ['ORC_FIXTURE']) if os.environ.get('ORC_FIXTURE') else None
@unittest.skipUnless(FIXTURE and FIXTURE.is_file(),'Optional owned ORC_FIXTURE not configured')
class ProjectTests(unittest.TestCase):
 def test_project_reference_and_noop(self):
  self.assertTrue((ROOT/'orc_native_bridge'/'project.py').exists(),'Missing native project contract implementation')
  from orc_native_bridge.project import create_project,load_project
  fixture=FIXTURE
  with tempfile.TemporaryDirectory(dir=ROOT) as td:
   p=create_project(fixture,Path(td)/'project');t,meta=load_project(p)
   self.assertEqual(t.raw,fixture.read_bytes());self.assertEqual(meta['schema'],'orc.native-project.v1')
   self.assertEqual(meta['blocks'],t.meshes)
 def test_vertex_buffer_aliasing_header_is_rejected(self):
  from orc_native_bridge.project import checked
  fixture=FIXTURE
  raw=bytearray(fixture.read_bytes());t=checked(raw)
  struct.pack_into('<I',raw,t.meshes[0]['header']+44,0)
  with self.assertRaises(ValueError):checked(raw)
 def test_source_and_destination_guards(self):
  from orc_native_bridge.project import create_project,load_project,write_export
  fixture=FIXTURE
  with tempfile.TemporaryDirectory(dir=ROOT) as td:
   folder=Path(td);p=create_project(fixture,folder/'project');t,meta=load_project(p)
   positions=[[struct.unpack_from('<3f',t.raw,m['vertex_offset']+i*m['stride']) for i in range(m['vertices'])] for m in t.meshes]
   target=folder/'new.edgemodel';report=write_export(t,positions,target,p)
   self.assertEqual(report['changed_bytes'],[]);self.assertEqual(target.read_bytes(),t.raw)
   with self.assertRaises(ValueError):write_export(t,positions,target,p)
   with self.assertRaises(ValueError):write_export(t,positions,p.parent/'template.edgemodel',p)
   meta['blocks'][0]['lod']+=1;p.write_text(json.dumps(meta))
   with self.assertRaises(ValueError):load_project(p)
   meta['blocks']=t.meshes;p.write_text(json.dumps(meta));raw=bytearray(t.raw);raw[-1]^=1;(p.parent/'template.edgemodel').write_bytes(raw)
   with self.assertRaises(ValueError):load_project(p)
 def test_v17_is_blocked(self):
  from orc_native_bridge.project import checked
  raw=bytearray(FIXTURE.read_bytes());struct.pack_into('<I',raw,4,17)
  with self.assertRaises(ValueError):checked(raw)
if __name__=='__main__':unittest.main(verbosity=2)
