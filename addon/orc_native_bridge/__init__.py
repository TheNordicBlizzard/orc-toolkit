"""AI-original clean native bridge; MIT; independent of unlicensed importer."""
bl_info={'name':'ORC Complemento — Native positions only','author':'ORC clean bridge contributors (AI-original)','version':(0,1,0),'blender':(5,0,0),'location':'View3D > Sidebar > ORC Complemento','description':'FM6S v18 template positions only; preserved rig bytes; in-game UNVERIFIED','category':'Import-Export'}
def register():
 from .ui import register as run
 run()
def unregister():
 from .ui import unregister as run
 run()
