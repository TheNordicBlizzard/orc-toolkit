"""Owned graphical factory process: actual panel draw and bilingual operators."""
import bpy,sys,json,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]/'addon';sys.path.insert(0,str(ROOT))
output=Path(sys.argv[sys.argv.index('--')+1]).resolve()
owned_temp=output.parent/'gui-temp';owned_temp.mkdir(parents=True,exist_ok=True)
bpy.context.preferences.filepaths.temporary_directory=str(owned_temp)
import orc_native_bridge as addon
addon.register()
from orc_native_bridge.ui import ORC_PT_bridge
original=ORC_PT_bridge.draw;seen=[];errors=[]
def draw(self,context):
 try:original(self,context);seen.append(context.scene.orc_bridge_language)
 except Exception:errors.append(traceback.format_exc())
ORC_PT_bridge.draw=draw
output=Path(sys.argv[sys.argv.index('--')+1]);state=[0]
def tick():
 try:
  area=next(a for a in bpy.context.screen.areas if a.type=='VIEW_3D');region=next(r for r in area.regions if r.type=='WINDOW')
  if state[0]<2:
   bpy.context.scene.orc_bridge_language=('PT','EN')[state[0]]
   with bpy.context.temp_override(area=area,region=region):bpy.ops.wm.call_panel(name='ORC_PT_bridge',keep_open=False)
   state[0]+=1;return 1.0
  result={'draw_languages':sorted(set(seen)),'errors':errors,'poll_without_project':not bpy.ops.orc_bridge.validate.poll(),'blender':bpy.app.version_string}
  output.write_text(json.dumps(result,indent=2));assert sorted(set(seen))==['EN','PT'] and not errors
  addon.unregister();bpy.ops.wm.quit_blender()
 except Exception:
  output.write_text(json.dumps({'error':traceback.format_exc(),'seen':seen},indent=2));bpy.ops.wm.quit_blender()
 return None
bpy.app.timers.register(tick,first_interval=1)
