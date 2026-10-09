import bpy, os, sys, time, json, math, mathutils
argv=sys.argv[sys.argv.index("--")+1:]
manifest, thumb_dir = argv[0], argv[1]
items=json.load(open(manifest,encoding="utf-8"))
os.makedirs(thumb_dir, exist_ok=True)

def setup_render(sc):
    # compat: BLENDER_EEVEE (<=4.1 e >=5.0) / BLENDER_EEVEE_NEXT (4.2-4.x)
    for _eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try:
            sc.render.engine = _eng
            break
        except Exception:
            continue
    sc.render.resolution_x=320; sc.render.resolution_y=320
    sc.render.image_settings.file_format='JPEG'; sc.render.image_settings.quality=82
    try:
        sc.view_settings.view_transform='Standard'; sc.view_settings.look='None'
    except Exception: pass
    if sc.world is None: sc.world=bpy.data.worlds.new("W")
    sc.world.use_nodes=True
    bg=sc.world.node_tree.nodes["Background"]
    bg.inputs[0].default_value=(0.55,0.58,0.62,1); bg.inputs[1].default_value=1.0

def add_lights(sc):
    for nm,rot,en in [("key",(math.radians(55),0,math.radians(35)),3.0),
                      ("fill",(math.radians(70),0,math.radians(-120)),1.2),
                      ("rim",(math.radians(120),0,math.radians(180)),2.0)]:
        l=bpy.data.lights.new(nm,type='SUN'); l.energy=en; l.angle=math.radians(20)
        o=bpy.data.objects.new(nm,l); sc.collection.objects.link(o); o.rotation_euler=rot

def orient_model():
    meshes=[o for o in bpy.data.objects if o.type=="MESH"]
    arms=[o for o in bpy.data.objects if o.type=="ARMATURE"]
    mins=mathutils.Vector((1e9,)*3); maxs=mathutils.Vector((-1e9,)*3)
    for o in meshes:
        for c in o.bound_box:
            w=o.matrix_world@mathutils.Vector(c)
            for i in range(3): mins[i]=min(mins[i],w[i]); maxs[i]=max(maxs[i],w[i])
    dim=maxs-mins
    roots=[o for o in bpy.data.objects if o.parent is None]
    pivot=mathutils.Vector(((mins.x+maxs.x)/2,(mins.y+maxs.y)/2,mins.z))
    if arms:
        rot=mathutils.Matrix.Rotation(math.radians(90),4,'X')
    else:
        ax='X' if (dim.x>=dim.y and dim.x>=dim.z) else ('Y' if dim.y>=dim.z else 'Z')
        rot=(mathutils.Matrix.Rotation(math.radians(90),4,'X') if ax=='Y'
             else mathutils.Matrix.Rotation(math.radians(-90),4,'Y') if ax=='X'
             else mathutils.Matrix.Identity(4))
    M=mathutils.Matrix.Translation(pivot)@rot@mathutils.Matrix.Translation(pivot).inverted()
    for o in roots: o.matrix_world=M@o.matrix_world
    bpy.context.view_layer.update()

def frame_and_render(sc, path):
    meshes=[o for o in bpy.data.objects if o.type=="MESH"]
    mins=mathutils.Vector((1e9,)*3); maxs=mathutils.Vector((-1e9,)*3)
    for o in meshes:
        for c in o.bound_box:
            w=o.matrix_world@mathutils.Vector(c)
            for i in range(3): mins[i]=min(mins[i],w[i]); maxs[i]=max(maxs[i],w[i])
    if mins.x>maxs.x: return False
    center=(mins+maxs)/2; size=max((maxs-mins).length,0.001)
    cd=bpy.data.cameras.new("Cam"); cam=bpy.data.objects.new("Cam",cd)
    sc.collection.objects.link(cam); sc.camera=cam
    cam.location=center+mathutils.Vector((0,-size*1.35,size*0.05))
    d=center-cam.location; cam.rotation_euler=d.to_track_quat('-Z','Y').to_euler()
    add_lights(sc)
    sc.render.filepath=path
    bpy.ops.render.render(write_still=True)
    return True

ok=fail=skip=0
for i,(fbx,name) in enumerate(items):
    fn=name.replace("/","__")+".jpg"
    out=os.path.join(thumb_dir,fn)
    if os.path.exists(out): skip+=1; continue
    bpy.ops.wm.read_factory_settings(use_empty=True)
    try: bpy.ops.import_scene.fbx(filepath=fbx, use_image_search=False)
    except Exception: fail+=1; continue
    sc=bpy.context.scene; setup_render(sc); orient_model()
    try:
        if not frame_and_render(sc,out): fail+=1
        else: ok+=1
    except Exception: fail+=1
    if (i+1)%100==0: print(f"PROGRESS {i+1}/{len(items)} ok={ok} fail={fail} skip={skip}",flush=True)
print(f"THUMBS_DONE ok={ok} fail={fail} skip={skip}",flush=True)
