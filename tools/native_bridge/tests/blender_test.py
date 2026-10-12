"""Factory Blender end-to-end test; private fixtures supplied by args, never bundled."""
import sys,json,struct
from pathlib import Path
import bpy,faulthandler
faulthandler.dump_traceback_later(30,repeat=True)
print('TEST_STARTED',flush=True)
ROOT=Path(__file__).resolve().parents[3]/'addon';sys.path.insert(0,str(ROOT))
args=sys.argv[sys.argv.index('--')+1:];fixture=Path(args[0]);out=Path(args[1]);mode=args[2] if len(args)>2 else 'import';out.mkdir(exist_ok=True,parents=True)
import orc_native_bridge as addon
assert hasattr(addon,'register'),'Missing usable bridge operators / UI'
addon.register()
from orc_native_bridge.project import create_project,load_project
from orc_native_bridge.blender_bridge import open_project,validate_project,export_project
p=out/'project/project.orcmeta.json'
if mode=='import':
 if not p.exists():create_project(fixture,out/'project')
 open_project(bpy.context,p)
 assert len([o for o in bpy.context.scene.objects if o.get('orc_block') is not None])>0
 bpy.ops.wm.save_as_mainfile(filepath=str(out/'project.blend'))
else:bpy.ops.wm.open_mainfile(filepath=str(out/'project.blend'))
validate_project(bpy.context)
# Real editable workflow: select vertex in Edit mode, move it, return to Object mode.
import bmesh
edit_ob=next(o for o in bpy.context.scene.objects if o.get('orc_block')==0)
bpy.context.view_layer.objects.active=edit_ob;edit_ob.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
bm=bmesh.from_edit_mesh(edit_ob.data);bm.verts.ensure_lookup_table();original=bm.verts[0].co.copy()
for v in bm.verts:v.select_set(False)
bm.verts[0].select_set(True);bm.verts[0].co.x+=0.001;bmesh.update_edit_mesh(edit_ob.data)
bpy.ops.object.mode_set(mode='OBJECT')
try:validate_project(bpy.context)
except ValueError:
 import zlib,base64
 from orc_native_bridge.blender_bridge import snapshot
 baseline=json.loads(zlib.decompress(base64.b64decode(bpy.data.texts[edit_ob['orc_baseline_text']].as_string())))
 actual=json.loads(json.dumps(snapshot(edit_ob)))
 print('DIFFERING_KEYS',[k for k in baseline if actual[k]!=baseline[k]],flush=True)
 print('ATTRS_BEFORE',[(a[0],a[1]) for a in baseline['attributes']],flush=True)
 print('ATTRS_AFTER',[(a[0],a[1]) for a in actual['attributes']],flush=True)
 print('ATTR_DIFFS',[a[0] for a in actual['attributes'] if a not in baseline['attributes']],flush=True)
 raise
edit_ob.data.vertices[0].co=original
report=export_project(bpy.context,out/(mode+'-noop.edgemodel'));assert not report['changed_bytes']
ob=next(o for o in bpy.context.scene.objects if o.get('orc_block')==0);ob.data.vertices[0].co.x+=0.001
report=export_project(bpy.context,out/(mode+'-edit.edgemodel'));assert len(report['fields'])==1
assert report['fields'][0]['vertex_id']==0
assert fixture.read_bytes()==(out/'project/template.edgemodel').read_bytes()
# Independent public parser provided by external local reference path.
reference=Path(args[3])
sys.path[:0]=[str(reference/'deps'),str(reference/'references/albam')]
from hexane_edgemodel import HexaneEdgemodel
for name in (mode+'-noop.edgemodel',mode+'-edit.edgemodel'):
 raw=(out/name).read_bytes();ref=HexaneEdgemodel.from_bytes(raw);ref._read()
 template,_=load_project(p)
 assert len(ref.meshes_header)==len(template.meshes)
 for h,m in zip(ref.meshes_header,template.meshes,strict=True):
  for field,prefix in (('buffer_vertices','vertex'),('buffer_indices','index'),('buffer_weights','weight')):
   start=m[prefix+'_offset'];size=m[prefix+'_size']
   assert getattr(h.mesh,field)==raw[start:start+size]
  assert h.lod==m['lod']
checks=[]
def reject(name,change,restore):
 change()
 try:validate_project(bpy.context)
 except (ValueError,RuntimeError):checks.append(name)
 else:raise AssertionError('Accepted unsupported edit: '+name)
 finally:restore()
# Tests state-changing unsupported edits against baseline.
me=ob.data
old=me.attributes['native_vertex_id'].data[0].value
reject('renumber',lambda:setattr(me.attributes['native_vertex_id'].data[0],'value',123456),lambda:setattr(me.attributes['native_vertex_id'].data[0],'value',old))
old=me.attributes['native_skin_0'].data[0].value
reject('skin',lambda:setattr(me.attributes['native_skin_0'].data[0],'value',old^1),lambda:setattr(me.attributes['native_skin_0'].data[0],'value',old))
reject('modifier',lambda:ob.modifiers.new('BLOCKED','SUBSURF'),lambda:ob.modifiers.clear())
old=ob.location.x
reject('transform',lambda:setattr(ob.location,'x',1),lambda:setattr(ob.location,'x',old))
original_mesh=ob.data
ob.data=original_mesh.copy()
def add_vertex():
 bm=bmesh.new();bm.from_mesh(ob.data);bm.verts.new((0,0,0));bm.to_mesh(ob.data);bm.free()
reject('new_topology',add_vertex,lambda:setattr(ob,'data',original_mesh))
reject('new_weight_group',lambda:ob.vertex_groups.new(name='unsupported'),lambda:ob.vertex_groups.clear())
old=ob['native_material_offset']
reject('material_reference',lambda:ob.__setitem__('native_material_offset',old+1),lambda:ob.__setitem__('native_material_offset',old))
if me.uv_layers:
 old=me.uv_layers[0].data[0].uv.copy()
 reject('uv',lambda:setattr(me.uv_layers[0].data[0],'uv',(0.234,0.345)),lambda:setattr(me.uv_layers[0].data[0],'uv',old))
 normals=[tuple(n.vector) for n in me.corner_normals]
 # Restoring encoded normal data after this test is not needed; it is last.
 reject('custom_normals',lambda:me.normals_split_custom_set([(1,0,0)]*len(me.loops)),lambda:None)
(out/(mode+'-proof.json')).write_text(json.dumps({'fixture_sha256':load_project(p)[0].sha256,'mode':mode,'noop':True,'one_vertex':True,'fresh_albam':True,'rejects':checks,'in_game':'UNVERIFIED','blender':bpy.app.version_string},indent=2))
addon.unregister()
print('BRIDGE_FACTORY_PASS',mode,checks)
