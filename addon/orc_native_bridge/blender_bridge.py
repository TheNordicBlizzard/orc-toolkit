"""Original MIT Blender bridge. Strict native identity, positions only."""
import json,struct,hashlib,zlib,base64
from pathlib import Path
import bpy
from .project import load_project,write_export

def attribute_values(attr):
 props=[p for p in attr.data[0].bl_rna.properties if p.identifier!='rna_type' and not p.is_readonly] if len(attr.data) else []
 result=[]
 for item in attr.data:
  row={}
  for p in props:
   value=getattr(item,p.identifier)
   row[p.identifier]=list(value) if p.is_array else value
  result.append(row)
 return result

def snapshot(ob):
 me=ob.data
 return {'attributes':sorted([(a.name,a.data_type,a.domain,attribute_values(a)) for a in me.attributes if a.name not in ('position','sharp_edge','sharp_face') and not a.name.startswith(('.select_','.hide_','.uv_select_'))],key=lambda a:a[0]),
 'edge_sharp':[e.use_edge_sharp for e in me.edges],
 'uv':[(u.name,[list(x.uv) for x in u.data]) for u in me.uv_layers],
 'loops':[l.vertex_index for l in me.loops], 'edges':[list(e.vertices) for e in me.edges],
 'polygons':[(p.loop_start,p.loop_total,p.material_index,p.use_smooth) for p in me.polygons],
 'groups':[(g.name,g.lock_weight) for g in ob.vertex_groups],
 'weights':[[(g.group,g.weight) for g in v.groups] for v in me.vertices],
 'materials':[m.name if m else None for m in me.materials],
 'shape_keys':bool(me.shape_keys),'custom_normals':me.has_custom_normals,
 'matrix':[list(row) for row in ob.matrix_world],
 'transform':{'location':list(ob.location),'scale':list(ob.scale),'rotation_mode':ob.rotation_mode,'rotation_euler':list(ob.rotation_euler),'rotation_quaternion':list(ob.rotation_quaternion),'rotation_axis_angle':list(ob.rotation_axis_angle),'delta_location':list(ob.delta_location),'delta_scale':list(ob.delta_scale),'delta_rotation_euler':list(ob.delta_rotation_euler),'delta_rotation_quaternion':list(ob.delta_rotation_quaternion)},
 'parent':ob.parent.name if ob.parent else None,
 'metadata':{k:ob[k] for k in ('orc_block','native_lod','native_material_offset','template_sha256')}}

def canonical(ob):return json.dumps(snapshot(ob),sort_keys=True,separators=(',',':'))

def open_project(context,path):
 t,meta=load_project(path)
 if context.scene.get('orc_project'):raise ValueError('One native project per scene / um projeto por cena; use New')
 collection=bpy.data.collections.new('ORC Complemento | positions only');context.scene.collection.children.link(collection)
 made=[]
 try:
  for bi,m in enumerate(t.meshes):
   raw=t.raw;vc=m['vertices'];vo=m['vertex_offset'];stride=m['stride'];wo=m['weight_offset']
   ids=struct.unpack_from('<'+str(m['indices'])+'H',raw,m['index_offset'])
   me=bpy.data.meshes.new('ORC native block '+str(bi));ob=bpy.data.objects.new(me.name,me);collection.objects.link(ob);made.append(ob)
   pos=[struct.unpack_from('<3f',raw,vo+i*stride) for i in range(vc)]
   me.from_pydata(pos,[],[ids[i:i+3] for i in range(0,len(ids),3)]);me.update()
   if list(ids)!=[l.vertex_index for l in me.loops]:raise ValueError('Native faces rejected or reordered by Blender')
   ob['orc_block']=bi;ob['native_lod']=m['lod'];ob['native_material_offset']=m['material_offset'];ob['template_sha256']=t.sha256
   attr=me.attributes.new('native_vertex_id','INT','POINT');attr.data.foreach_set('value',list(range(vc)))
   records=list(struct.iter_unpack('8B',raw[wo:wo+vc*8]))
   for j in range(8):
    attr=me.attributes.new('native_skin_'+str(j),'INT','POINT');attr.data.foreach_set('value',[r[j] for r in records])
   if stride==52:
    uv=[struct.unpack_from('<2e',raw,vo+i*stride+24) for i in range(vc)]
    norms=[struct.unpack_from('<3f',raw,vo+i*stride+12) for i in range(vc)]
    layer=me.uv_layers.new(name='NativeUV');layer.data.foreach_set('uv',[c for l in me.loops for c in (uv[l.vertex_index][0],1-uv[l.vertex_index][1])])
    attr=me.attributes.new('native_normal','FLOAT_VECTOR','POINT');attr.data.foreach_set('vector',[c for n in norms for c in n])
    me.polygons.foreach_set('use_smooth',[True]*len(me.polygons));me.normals_split_custom_set([norms[l.vertex_index] for l in me.loops])
   baseline=canonical(ob);encoded=base64.b64encode(zlib.compress(baseline.encode())).decode()
   text=bpy.data.texts.new('ORC baseline '+str(bi));text.write('\n'.join(encoded[i:i+120] for i in range(0,len(encoded),120)));ob['orc_baseline_text']=text.name;ob['orc_baseline_sha']=hashlib.sha256(baseline.encode()).hexdigest()
  context.scene['orc_project']=str(Path(path).resolve());context.scene['orc_template_sha256']=t.sha256
  context.scene['orc_collection']=collection.name;context.scene['orc_objects']=json.dumps([o.name for o in made])
 except Exception:
  for ob in made:bpy.data.objects.remove(ob,do_unlink=True)
  bpy.data.collections.remove(collection);raise
 return made

def validate_project(context):
 if context.mode!='OBJECT':raise ValueError('Return to Object mode / volte ao modo Objeto')
 path=context.scene.get('orc_project')
 if not path:raise ValueError('Open native project / abra projeto nativo')
 t,meta=load_project(path)
 if context.scene.get('orc_template_sha256')!=t.sha256:raise ValueError('Another template / outro template')
 expected=json.loads(context.scene['orc_objects']);collection=bpy.data.collections.get(context.scene['orc_collection'])
 if collection is None or sorted(o.name for o in collection.all_objects)!=sorted(expected):raise ValueError('New/deleted/duplicated objects blocked')
 project_objects=[o for o in context.scene.objects if o.get('orc_block') is not None]
 if sorted(o.name for o in project_objects)!=sorted(expected):raise ValueError('Ambiguous blocks / blocos ambíguos')
 captures=[]
 for bi,(name,m) in enumerate(zip(expected,t.meshes,strict=True)):
  ob=bpy.data.objects.get(name)
  if ob is None or ob.type!='MESH' or ob.get('orc_block')!=bi or len(ob.data.vertices)!=m['vertices']:raise ValueError('Topology/identity changed')
  if ob.modifiers or ob.constraints or ob.animation_data or ob.data.animation_data:raise ValueError('Modifiers/constraints/animation unsupported')
  text=bpy.data.texts.get(ob.get('orc_baseline_text',''))
  if not text:raise ValueError('Baseline missing')
  baseline=zlib.decompress(base64.b64decode(text.as_string())).decode()
  if hashlib.sha256(baseline.encode()).hexdigest()!=ob.get('orc_baseline_sha'):raise ValueError('Baseline changed')
  if canonical(ob)!=baseline:raise ValueError('Unsupported change: normals/UV/skin/IDs/topology/materials/transform; only positions / somente posições')
  captures.append([tuple(v.co) for v in ob.data.vertices])
 # Validation also rejects nonfinite/overflow positions without writing.
 t.export_positions(captures,baseline_sha256=t.sha256)
 return t,captures,path

def export_project(context,destination):
 t,captures,path=validate_project(context)
 return write_export(t,captures,destination,path)
