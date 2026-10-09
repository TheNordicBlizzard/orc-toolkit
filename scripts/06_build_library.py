import bpy, os, sys, time, json, math, mathutils
argv=sys.argv[sys.argv.index("--")+1:]
manifest, out_blend = argv[0], argv[1]
items=json.load(open(manifest,encoding="utf-8"))
# pasta onde as texturas PNG serao externalizadas (configuravel por env ORC_TEXDIR)
TEXDIR=os.environ.get("ORC_TEXDIR") or os.path.join(os.path.dirname(os.path.abspath(out_blend)), "ORC_textures")
os.makedirs(TEXDIR, exist_ok=True)

def orient_model(new):
    meshes=[o for o in new if o.type=="MESH"]; arms=[o for o in new if o.type=="ARMATURE"]
    if not meshes: return
    mins=mathutils.Vector((1e9,)*3); maxs=mathutils.Vector((-1e9,)*3)
    for o in meshes:
        for c in o.bound_box:
            w=o.matrix_world@mathutils.Vector(c)
            for i in range(3): mins[i]=min(mins[i],w[i]); maxs[i]=max(maxs[i],w[i])
    dim=maxs-mins; roots=[o for o in new if o.parent is None]
    pivot=mathutils.Vector(((mins.x+maxs.x)/2,(mins.y+maxs.y)/2,mins.z))
    if arms: rot=mathutils.Matrix.Rotation(math.radians(90),4,'X')
    else:
        ax='X' if (dim.x>=dim.y and dim.x>=dim.z) else ('Y' if dim.y>=dim.z else 'Z')
        rot=(mathutils.Matrix.Rotation(math.radians(90),4,'X') if ax=='Y'
             else mathutils.Matrix.Rotation(math.radians(-90),4,'Y') if ax=='X'
             else mathutils.Matrix.Identity(4))
    M=mathutils.Matrix.Translation(pivot)@rot@mathutils.Matrix.Translation(pivot).inverted()
    for o in roots: o.matrix_world=M@o.matrix_world
    bpy.context.view_layer.update()

def externalize_textures(seen):
    for img in list(bpy.data.images):
        if img.size[0]==0:
            try: bpy.data.images.remove(img, do_unlink=True)
            except Exception: pass
            continue
        if img.name in seen: continue
        seen.add(img.name)
        out=os.path.join(TEXDIR, img.name.replace('.dds','')+".png")
        if os.path.exists(out):
            try:
                img.source='FILE'; img.filepath=out
                if img.packed_file: img.unpack(method='REMOVE')
            except Exception: pass
            continue
        # Convert to external PNG. If anything fails (broken/missing source DDS),
        # drop the image so Blender never re-reads packed DDS on save (crashes
        # OpenImageIO).
        try:
            img.filepath_raw=out; img.file_format='PNG'
            img.save()
            img.source='FILE'; img.filepath=out
            if img.packed_file: img.unpack(method='REMOVE')
        except Exception:
            try: bpy.data.images.remove(img, do_unlink=True)
            except Exception: pass

bpy.ops.wm.read_factory_settings(use_empty=True)
CAT={"characters":"Characters","weapons":"Weapons","vfx":"VFX","worlds":"Props"}
cols={}
for k,v in CAT.items():
    c=bpy.data.collections.new(v); bpy.context.scene.collection.children.link(c); cols[k]=c
seen=set(); t0=time.time(); ok=fail=0
for fbx,rel in items:
    cat,name=rel.split("/",1)
    before=set(bpy.data.objects)
    try: bpy.ops.import_scene.fbx(filepath=fbx, use_image_search=False)
    except Exception: fail+=1; continue
    new=[o for o in bpy.data.objects if o not in before]
    if not new: fail+=1; continue
    externalize_textures(seen)
    orient_model(new)
    holder=bpy.data.objects.new(name,None); cols.get(cat,bpy.context.scene.collection).objects.link(holder)
    for o in new:
        if o.parent is None: o.parent=holder
    holder.asset_mark(); ok+=1
    if ok%200==0: print("PROGRESS %d/%d t=%.0f"%(ok,len(items),time.time()-t0),flush=True)
print("BUILD_DONE ok=%d fail=%d"%(ok,fail),flush=True)
bpy.ops.wm.save_as_mainfile(filepath=out_blend, compress=True)
print("SAVED %.0f MB %.0fs"%(os.path.getsize(out_blend)/1024/1024,time.time()-t0),flush=True)
