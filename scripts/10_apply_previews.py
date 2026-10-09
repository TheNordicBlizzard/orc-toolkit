import bpy, os, sys, glob, time
argv=sys.argv[sys.argv.index("--")+1:]
blend, thumbdir = argv[0], argv[1]
bpy.ops.wm.open_mainfile(filepath=blend)
# map model-name -> thumbnail (strip category prefix "cat__")
name2thumb={}
for f in glob.glob(os.path.join(thumbdir,"*.jpg")):
    b=os.path.basename(f)[:-4]
    nm=b.split("__",1)[1] if "__" in b else b
    name2thumb.setdefault(nm, f)
print("thumbnails indexed:", len(name2thumb), flush=True)
assets=[o for o in bpy.data.objects if o.asset_data]
print("assets:", len(assets), flush=True)
ok=miss=0; t0=time.time()
for i,o in enumerate(assets):
    th=name2thumb.get(o.name)
    if not th: miss+=1; continue
    for ob in bpy.context.view_layer.objects: ob.select_set(False)
    o.select_set(True); bpy.context.view_layer.objects.active=o
    try:
        with bpy.context.temp_override(id=o, active_object=o, object=o, selected_objects=[o]):
            bpy.ops.ed.lib_id_load_custom_preview(filepath=th)
        ok+=1
    except Exception:
        miss+=1
    if (i+1)%500==0: print(f"  {i+1}/{len(assets)} ok={ok} miss={miss} {time.time()-t0:.0f}s", flush=True)
print(f"PREVIEWS_DONE ok={ok} miss={miss} {time.time()-t0:.0f}s", flush=True)
bpy.ops.wm.save_as_mainfile(filepath=blend, compress=True)
print("SAVED %.0f MB"%(os.path.getsize(blend)/1024/1024), flush=True)
