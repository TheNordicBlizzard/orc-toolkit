"""Original MIT bilingual minimal UI. No automatic game writes."""
import bpy
from bpy.props import StringProperty,EnumProperty
from bpy_extras.io_utils import ImportHelper,ExportHelper
from .blender_bridge import open_project,validate_project,export_project

def label(context,pt,en):return pt if context.scene.orc_bridge_language=='PT' else en
class ORC_OT_open(bpy.types.Operator,ImportHelper):
 bl_idname='orc_bridge.open_project';bl_label='Abrir projeto nativo / Open native project'
 filename_ext='.json';filter_glob:StringProperty(default='*.orcmeta.json',options={'HIDDEN'})
 def execute(self,context):
  try:open_project(context,self.filepath)
  except Exception as e:self.report({'ERROR'},str(e));return {'CANCELLED'}
  self.report({'INFO'},'Positions only / somente posições; rig bytes preserved; no new rig');return {'FINISHED'}
class ORC_OT_validate(bpy.types.Operator):
 bl_idname='orc_bridge.validate';bl_label='Validar referência / Validate reference'
 @classmethod
 def poll(cls,context):return bool(context.scene.get('orc_project'))
 def execute(self,context):
  try:validate_project(context)
  except Exception as e:self.report({'ERROR'},str(e));return {'CANCELLED'}
  self.report({'INFO'},'Reference and unsupported edits checked / referência validada; in-game UNVERIFIED');return {'FINISHED'}
class ORC_OT_export(bpy.types.Operator,ExportHelper):
 bl_idname='orc_bridge.export';bl_label='Exportar NOVO edgemodel / Export NEW edgemodel'
 filename_ext='.edgemodel';filter_glob:StringProperty(default='*.edgemodel',options={'HIDDEN'})
 @classmethod
 def poll(cls,context):return bool(context.scene.get('orc_project'))
 def execute(self,context):
  try:r=export_project(context,self.filepath)
  except Exception as e:self.report({'ERROR'},str(e));return {'CANCELLED'}
  context.scene['orc_last_output']=self.filepath
  self.report({'INFO'},str(len(r['changed_bytes']))+' changed bytes / bytes alterados; .diff.json; in-game UNVERIFIED');return {'FINISHED'}
class ORC_PT_bridge(bpy.types.Panel):
 bl_label='ORC Complemento | Positions only';bl_idname='ORC_PT_bridge';bl_space_type='VIEW_3D';bl_region_type='UI';bl_category='ORC Complemento'
 def draw(self,context):
  layout=self.layout;layout.prop(context.scene,'orc_bridge_language',text='Language / Idioma')
  layout.label(text=label(context,'Somente posições • FM6S v18','Positions only • FM6S v18'))
  layout.operator('orc_bridge.open_project',text=label(context,'Abrir projeto nativo','Open native project'))
  layout.operator('orc_bridge.validate',text=label(context,'Validar referência','Validate reference'))
  layout.operator('orc_bridge.export',text=label(context,'Exportar NOVO edgemodel','Export NEW edgemodel'))
  layout.label(text=label(context,'Rig: bytes preservados, não novo rig','Rig: preserved bytes, not a new rig'))
  layout.label(text=label(context,'JOGO: NÃO VERIFICADO','IN-GAME: UNVERIFIED'),icon='ERROR')
  layout.label(text=label(context,'Explorer: abrir arquivo exportado','Explorer: open exported file'))
  layout.label(text=label(context,'Não modifica arquivos do jogo','Does not modify game files'))
classes=(ORC_OT_open,ORC_OT_validate,ORC_OT_export,ORC_PT_bridge)
def register():
 for c in classes:bpy.utils.register_class(c)
 bpy.types.Scene.orc_bridge_language=EnumProperty(items=[('PT','Português',''),('EN','English','')],default='PT')
def unregister():
 del bpy.types.Scene.orc_bridge_language
 for c in reversed(classes):bpy.utils.unregister_class(c)
