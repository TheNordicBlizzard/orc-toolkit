import bpy, os, sys, glob, time
argv=sys.argv[sys.argv.index("--")+1:]
parts_dir, out_blend = argv[0], argv[1]
parts=sorted(glob.glob(os.path.join(parts_dir,"part_*.blend")))
print("merging",len(parts),"parts",flush=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
CATS=["Characters","Weapons","VFX","Props"]
master={c:bpy.data.collections.new(c) for c in CATS}
for c in CATS: bpy.context.scene.collection.children.link(master[c])

def cat_of(obj):
    root=obj
    while root.parent: root=root.parent
    for c in root.users_collection:
        for k in CATS:
            if c.name==k or c.name.startswith(k): return k
    return None

t0=time.time(); nobj=0
for pi,p in enumerate(parts):
    with bpy.data.libraries.load(p, link=False) as (df, dt):
        dt.objects=list(df.objects)
        dt.collections=list(df.collections)
    newobjs=[o for o in dt.objects if o]
    nobj+=len(newobjs)
    for o in newobjs:
        k=cat_of(o)
        if k is None: k="Props"
        try: master[k].objects.link(o)
        except Exception: pass
    print(f"  part_{pi+1:03d}: +{len(newobjs)} (total {nobj}) {time.time()-t0:.0f}s",flush=True)

for c in list(bpy.data.collections):
    if c.name not in master:
        try: bpy.data.collections.remove(c)
        except Exception: pass

print("total:",nobj,flush=True)
for k in CATS:
    t={}
    for o in master[k].objects: t[o.type]=t.get(o.type,0)+1
    print(f"  {k}: {len(master[k].objects)} {t}",flush=True)
bpy.ops.wm.save_as_mainfile(filepath=out_blend, compress=True)
print("SAVED %.0f MB"%(os.path.getsize(out_blend)/1024/1024),flush=True)
