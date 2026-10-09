import bpy, os, sys, json, traceback

# args: <manifest.json> <out_dir>   manifest = [[model_path, out_name], ...]
argv = sys.argv[sys.argv.index("--") + 1:]
manifest, outdir = argv[0], argv[1]
items = json.load(open(manifest, encoding="utf-8"))
os.makedirs(outdir, exist_ok=True)

# importador do repo (configuravel por ORC_IMPORTER)
script = os.environ.get("ORC_IMPORTER") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "03_orc_import_blender.py")
src = open(script, encoding="utf-8").read().replace("bpy.ops.reorc.open_asset('INVOKE_DEFAULT')", "pass")
ns = {"__name__": "orc_import_blender"}
exec(compile(src, script, "exec"), ns)   # also builds the asset index once

ok = fail = nomesh = 0
for model, name in items:
    fbx = os.path.join(outdir, name + ".fbx")
    if os.path.exists(fbx):
        continue
    bpy.ops.wm.read_factory_settings(use_empty=True)
    try:
        ns["parse_file"](model, True, True)
    except Exception as e:
        fail += 1
        if fail <= 3:
            print("PARSE_FAIL", name, repr(e))
            traceback.print_exc()
        continue
    if not any(o.type == "MESH" for o in bpy.data.objects):
        nomesh += 1; continue
    for o in [o for o in bpy.data.objects if o.type == "MESH" and "LOD0" not in o.name]:
        bpy.data.objects.remove(o, do_unlink=True)
    try:
        bpy.ops.export_scene.fbx(filepath=fbx, use_selection=False, add_leaf_bones=False,
                                 path_mode='COPY', embed_textures=True, mesh_smooth_type='FACE')
        ok += 1
    except Exception:
        fail += 1
        if os.path.exists(fbx): os.remove(fbx)

print(f"BATCH_DONE ok={ok} fail={fail} nomesh={nomesh}")
