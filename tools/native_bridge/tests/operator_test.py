"""Actual registered Blender operators, private project via args."""
import bpy,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]/'addon';sys.path.insert(0,str(ROOT))
args=sys.argv[sys.argv.index('--')+1:]
import orc_native_bridge as addon
addon.register()
assert bpy.ops.orc_bridge.open_project(filepath=str(Path(args[0]).resolve()))=={'FINISHED'}
assert bpy.ops.orc_bridge.validate()=={'FINISHED'}
assert bpy.ops.orc_bridge.export(filepath=str(Path(args[1]).resolve()))=={'FINISHED'}
# Blender error reports raise RuntimeError from bpy.ops; either cancellation surface is valid.
try:r=bpy.ops.orc_bridge.export(filepath=str(Path(args[1]).resolve()))
except RuntimeError:r={'CANCELLED'}
assert r=={'CANCELLED'}
Path(args[2]).write_text(json.dumps({'open_operator':True,'validate_operator':True,'export_operator':True,'existing_destination_rejected':True,'in_game':'UNVERIFIED'},indent=2))
addon.unregister();print('OPERATORS_PASS')
