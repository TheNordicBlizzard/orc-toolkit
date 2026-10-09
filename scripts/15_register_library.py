import bpy, sys
argv=sys.argv[sys.argv.index("--")+1:]
lib_name, lib_path = argv[0], argv[1]
libs=bpy.context.preferences.filepaths.asset_libraries
for l in list(libs):
    if l.name==lib_name:
        libs.remove(l)
new=libs.new(name=lib_name, directory=lib_path)
print("REGISTERED:", new.name, "->", new.path)
print("ALL LIBS:", [(l.name, l.path) for l in libs])
bpy.ops.wm.save_userpref()
print("SAVED_USERPREFS")
