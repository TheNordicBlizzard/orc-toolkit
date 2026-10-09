import bpy, os, sys, traceback

# args after "--"
argv = sys.argv[sys.argv.index("--") + 1:]
model, fbx = argv[0], argv[1]

# start from an empty scene so the default Cube/Camera/Light don't leak into the FBX
bpy.ops.wm.read_factory_settings(use_empty=True)

# importador do repo (configuravel por ORC_IMPORTER)
script = os.environ.get("ORC_IMPORTER") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "03_orc_import_blender.py")
src = open(script, encoding="utf-8").read().replace("bpy.ops.reorc.open_asset('INVOKE_DEFAULT')", "pass")
ns = {"__name__": "orc_import_blender"}
exec(compile(src, script, "exec"), ns)

try:
    ns["parse_file"](model, True, True)
except Exception:
    print("PARSE_ERROR"); traceback.print_exc(); sys.exit(2)

for o in [o for o in bpy.data.objects if o.type == "MESH" and "LOD0" not in o.name]:
    bpy.data.objects.remove(o, do_unlink=True)

bpy.ops.export_scene.fbx(filepath=fbx, use_selection=False, add_leaf_bones=False,
                         path_mode='COPY', embed_textures=True, mesh_smooth_type='FACE')
n = len([o for o in bpy.data.objects if o.type == "MESH"])
print(f"EXPORT_OK meshes={n} size={os.path.getsize(fbx)/1024:.0f}KB")
