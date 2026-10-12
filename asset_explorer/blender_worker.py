"""Fixed Blender background worker. JSON is data, never executable code."""
import bpy,json,sys,hashlib
from pathlib import Path
from mathutils import Matrix
import numpy as np

def clear():bpy.ops.wm.read_factory_settings(use_empty=True)
def snapshot(name):
 meshes=[o for o in bpy.context.scene.objects if o.type=='MESH' and o.name==name];triangles=[];uvs=[];refs=[]
 for o in meshes:
  m=o.data;m.calc_loop_triangles()
  for tri in m.loop_triangles:
   triangles.append(sorted([tuple(round(float(x),4) for x in o.matrix_world@m.vertices[i].co) for i in tri.vertices]))
   if m.uv_layers.active:
    uvs.extend([tuple(round(float(x),4) for x in m.uv_layers.active.data[i].uv) for i in tri.loops])
 for image in bpy.data.images:
  if image.source=='FILE':refs.append({'path':image.filepath,'exists':Path(bpy.path.abspath(image.filepath)).is_file(),'width':image.size[0]})
 bones={}
 for o in bpy.context.scene.objects:
  if o.type=='ARMATURE':
   for b in o.data.bones:bones[b.name]={'parent':b.parent.name if b.parent else None,'matrix':(o.matrix_world@b.matrix_local).to_4x4()[:],'weights':0}
 return {'vertices':sum(len(o.data.vertices) for o in meshes),'faces':sum(len(o.data.polygons) for o in meshes),'triangles':sorted(triangles),'uv':sorted(uvs),'texture_refs':refs,'bones':bones,'materials':sum(len(o.data.materials) for o in meshes)}

def triangles_equal(left,right,tolerance=2e-4):
 if len(left)!=len(right):return False
 # Fast path; lexicographic sorting may swap adjacent nearly equal coordinates.
 x=np.array(left);y=np.array(right)
 if np.allclose(x,y,atol=tolerance,rtol=0):return True
 from collections import defaultdict
 from itertools import product,permutations
 buckets=defaultdict(list);cell=.001
 for triangle in right:buckets[tuple(np.floor(np.mean(triangle,axis=0)/cell).astype(int))].append(triangle)
 for triangle in left:
  center=np.floor(np.mean(triangle,axis=0)/cell).astype(int);found=False;values=np.array(triangle)
  for delta in product((-1,0,1),repeat=3):
   key=tuple(center+delta)
   for i,candidate in enumerate(buckets.get(key,())):
    candidate=np.array(candidate)
    if any(np.allclose(values,candidate[list(order)],atol=tolerance,rtol=0) for order in permutations(range(3))):
     buckets[key].pop(i);found=True;break
   if found:break
  if not found:return False
 return True

def main():
 path=Path(sys.argv[sys.argv.index('--')+1]).resolve();root=path.parent;job=json.loads(path.read_text(encoding='utf-8'))
 clear();mesh=bpy.data.meshes.new(job['name']);mesh.from_pydata(job['vertices'],[],job['faces']);mesh.update()
 obj=bpy.data.objects.new(job['name'],mesh);bpy.context.scene.collection.objects.link(obj)
 uv=mesh.uv_layers.new(name='UV')
 for loop in mesh.loops:
  u,v=job['uv'][loop.vertex_index];uv.data[loop.index].uv=(u,1-v)
 for i,name in enumerate(job['materials']):
  mat=bpy.data.materials.new(name or f'material_{i}');mat.use_nodes=True;bsdf=mat.node_tree.nodes.get('Principled BSDF')
  if str(i) in job['textures']:
   rel=job['textures'][str(i)];p=(root/rel).resolve()
   if not p.is_relative_to(root):raise ValueError('Texture escaped bundle.')
   image=bpy.data.images.load(str(p),check_existing=True);image.filepath='//'+rel
   node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=image;mat.node_tree.links.new(node.outputs['Color'],bsdf.inputs['Base Color'])
  mesh.materials.append(mat)
 for p,i in zip(mesh.polygons,job['face_materials']):p.material_index=i
 skel=job.get('skeleton')
 if skel:
  arm=bpy.data.armatures.new('NativeSkeleton_UNBOUND');rig=bpy.data.objects.new('NativeSkeleton_UNBOUND',arm);bpy.context.scene.collection.objects.link(rig);rig.show_in_front=True
  rig['orc_binding_warning']=job['rig_warning'];bpy.context.view_layer.objects.active=rig;rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
  bones=[]
  for name,matrix in zip(skel['names'],skel['world_matrices']):
   b=arm.edit_bones.new(name);b.head=(0,0,0);b.tail=(0,.1,0);b.matrix=Matrix(matrix);bones.append(b)
  for i,parent in enumerate(skel['parents']):
   if parent>=0:bones[i].parent=bones[parent]
  bpy.ops.object.mode_set(mode='OBJECT')
 obj['orc_rig_warning']=job['rig_warning'];bpy.context.view_layer.objects.active=obj
 for o in bpy.context.scene.objects:o.select_set(True)
 # A .blend establishes correct relative image paths before FBX/glTF exporters.
 bpy.ops.wm.save_as_mainfile(filepath=str(root/'model.blend'),check_existing=False)
 expected=snapshot(job['name']);reports={}
 for fmt in job['formats']:
  output=root/('model.'+fmt)
  if fmt=='fbx':bpy.ops.export_scene.fbx(filepath=str(output),use_selection=True,object_types={'MESH','ARMATURE'},add_leaf_bones=False,bake_anim=False,path_mode='RELATIVE',embed_textures=False)
  elif fmt=='glb':bpy.ops.export_scene.gltf(filepath=str(output),export_format='GLB',use_selection=True,export_animations=False,export_yup=True,export_skins=False)
  elif fmt!='blend':raise ValueError('Unsupported format.')
  # Reimport in an empty scene, compare triangle coordinate multiset and UVs.
  clear()
  if fmt=='blend':bpy.ops.wm.open_mainfile(filepath=str(output))
  elif fmt=='fbx':bpy.ops.import_scene.fbx(filepath=str(output),use_image_search=False)
  else:bpy.ops.import_scene.gltf(filepath=str(output))
  actual=snapshot(job['name'])
  geometry=triangles_equal(actual['triangles'],expected['triangles']);uv_ok=len(actual['uv'])==len(expected['uv']) and np.allclose(np.array(actual['uv']),np.array(expected['uv']),atol=2e-4,rtol=0)
  # glTF embeds PNG; Blender importer produces packed images instead of FILE refs.
  texture_ok=(all(x['exists'] and x['width']>0 for x in actual['texture_refs']) and bool(actual['texture_refs'])) if job['textures'] and fmt!='glb' else (any(i.size[0]>0 for i in bpy.data.images) if job['textures'] else True)
  bones_ok=True
  if skel and fmt!='glb':
   bones_ok=set(actual['bones'])==set(expected['bones']) and all(actual['bones'][n]['parent']==v['parent'] and np.allclose(np.array(actual['bones'][n]['matrix']),np.array(v['matrix']),atol=1e-3) for n,v in expected['bones'].items())
  reports[fmt]={'verified':geometry and uv_ok and texture_ok and bones_ok,'geometry_verified':geometry,'uv_verified':uv_ok,'textures_verified':texture_ok,'native_unbound_skeleton_verified':bones_ok if skel and fmt!='glb' else None,'vertices':actual['vertices'],'faces':actual['faces'],'materials':actual['materials'],'texture_refs':actual['texture_refs'] or [{'packed_png':True,'width':i.size[0]} for i in bpy.data.images if i.size[0]],'bone_count':len(actual['bones']),'skin_weights':0,'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'bytes':output.stat().st_size}
  # Reload source scene for the next exporter.
  bpy.ops.wm.open_mainfile(filepath=str(root/'model.blend'))
 if 'blend' not in job['formats']:(root/'model.blend').unlink()
 report={'success':all(x['verified'] for x in reports.values()),'formats':reports,'rig_validated':False,'rig_warning':job['rig_warning'],'native_skeleton':bool(skel),'warnings':job['warnings'],'material_scope':job['material_scope'],'blender_version':bpy.app.version_string}
 (root/'export_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
 if not report['success']:raise ValueError('Reimport verification failed: '+str(reports))
if __name__=='__main__':main()
