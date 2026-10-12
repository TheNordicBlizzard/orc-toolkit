"""ORC sidebar. Original implementation inspired by Albam's panel/UIList pattern.
No Albam engine/parser code is used. See THIRD_PARTY_NOTICES.md.
"""
import os
import bpy
from . import _ui
from bpy.props import StringProperty, IntProperty, BoolProperty, CollectionProperty, PointerProperty
from bpy.types import PropertyGroup, Operator, Panel, UIList
from bpy_extras.io_utils import ImportHelper


def core():
    from . import ensure_mod_path
    ensure_mod_path()
    from ssg_extract_full import parse_ssg
    from roundtrip_edgemodel import scan_fm6s_blocks, validate
    return parse_ssg, scan_fm6s_blocks, validate


class ORCFileEntry(PropertyGroup):
    kind: StringProperty()
    size: IntProperty()


class ORCUIState(PropertyGroup):
    archive_path: StringProperty(name='Arquivo SSG / edgemodel', subtype='FILE_PATH')
    indexed_path: StringProperty()
    entries: CollectionProperty(type=ORCFileEntry)
    active_index: IntProperty(default=0, min=0)
    import_bones: BoolProperty(name='Armature / pesos', default=True)
    import_uvs: BoolProperty(name='UVs', default=True)
    import_materials: BoolProperty(name='Basic MATB/DDS / Materiais básicos', default=True)
    status: StringProperty(default='Nenhuma validação executada')


def selected_entry(context):
    state = context.scene.orc_tools
    if state.indexed_path != bpy.path.abspath(state.archive_path):
        return None
    if 0 <= state.active_index < len(state.entries):
        return state.entries[state.active_index]
    return None


class ORC_UL_files(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        icons = {'MODEL': 'MESH_DATA', 'SKELETON': 'ARMATURE_DATA', 'TEXTURE': 'TEXTURE', 'OTHER': 'FILE'}
        layout.label(text=item.name, icon=icons.get(item.kind, 'FILE'))
        layout.label(text=f'{item.size:,} B')


class ORC_OT_index_archive(Operator):
    bl_idname = 'orc.index_archive'
    bl_label = 'Indexar arquivo'
    bl_description = 'Ler as seções SSG ou o índice de um edgemodel; não altera arquivos'

    @classmethod
    def poll(cls, context):
        return bool(context.scene and os.path.isfile(bpy.path.abspath(context.scene.orc_tools.archive_path)))

    def execute(self, context):
        state = context.scene.orc_tools
        try:
            parse_ssg, scan, _ = core()
            path = bpy.path.abspath(state.archive_path)
            with open(path, 'rb') as handle:
                raw = handle.read()
            sections = [(os.path.basename(path), 0, raw)] if raw[:4] == b'FM6S' else parse_ssg(raw)
            state.entries.clear()
            for name, _, data in sections:
                entry = state.entries.add()
                entry.name, entry.size = name, len(data)
                entry.kind = ('MODEL' if data[:4] == b'FM6S' else 'SKELETON' if data[:4] in (b'20SE', b'ES02')
                              else 'TEXTURE' if name.lower().endswith('.dds') else 'OTHER')
            state.indexed_path = path
            state.active_index = 0
            state.status = f'{len(sections)} seções indexadas'
            return {'FINISHED'}
        except Exception as ex:
            state.entries.clear()
            state.indexed_path = ''
            state.status = f'Falha ao indexar: {ex}'
            self.report({'ERROR'}, state.status)
            return {'CANCELLED'}


class ORC_OT_browse_archive(Operator, ImportHelper):
    bl_idname = 'orc.browse_archive'
    bl_label = 'Abrir SSG / edgemodel'
    filter_glob: StringProperty(default='*.ssg;*.edgemodel;*.bak', options={'HIDDEN'})

    def execute(self, context):
        context.scene.orc_tools.archive_path = self.filepath
        return bpy.ops.orc.index_archive()


class ORC_OT_import_indexed(Operator):
    bl_idname = 'orc.import_indexed'
    bl_label = 'Importar modelo selecionado'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        entry = selected_entry(context)
        return context.mode == 'OBJECT' and entry is not None and entry.kind == 'MODEL' and os.path.isfile(context.scene.orc_tools.indexed_path)

    def execute(self, context):
        state = context.scene.orc_tools
        return bpy.ops.orc.import_ssg(filepath=state.indexed_path, import_bones=state.import_bones,
                                      import_uvs=state.import_uvs, import_materials=state.import_materials,
                                      edgemodel_entry=selected_entry(context).name)


class ORC_OT_validate_archive(Operator):
    bl_idname = 'orc.validate_archive'
    bl_label = 'Validar arquivo'
    bl_description = 'Verificar parsing SSG e campos/offsets FM6S; não valida no jogo'

    @classmethod
    def poll(cls, context):
        return ORC_OT_index_archive.poll(context)

    def execute(self, context):
        state = context.scene.orc_tools
        try:
            parse_ssg, scan, validate = core()
            with open(bpy.path.abspath(state.archive_path), 'rb') as handle:
                raw = handle.read()
            sections = [('', 0, raw)] if raw[:4] == b'FM6S' else parse_ssg(raw)
            models = 0
            for name, _, data in sections:
                if data[:4] != b'FM6S':
                    continue
                from . import _import_fm6s_blocks
                parsed = _import_fm6s_blocks(data)
                if not parsed['blocks']:
                    raise ValueError(f'Sem blocos FM6S nativos: {name}')
                models += 1
            state.status = f'OK estrutural: {len(sections)} seções, {models} modelos. Não validado no jogo.'
            self.report({'INFO'}, state.status)
            return {'FINISHED'}
        except Exception as ex:
            state.status = f'Falha: {ex}'
            self.report({'ERROR'}, state.status)
            return {'CANCELLED'}


class ORCPanel:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'ORC'
    bl_options = {'DEFAULT_CLOSED'}


class ORC_PT_files(ORCPanel, Panel):
    def draw_header(self, context):
        self.layout.label(text=_ui('files'))
    bl_idname = 'ORC_PT_files'
    bl_label = 'Arquivos'
    bl_options = set()

    def draw(self, context):
        state = context.scene.orc_tools
        self.layout.prop(state, 'archive_path')
        row = self.layout.row(align=True)
        row.operator('orc.browse_archive', icon='FILE_FOLDER')
        row.operator('orc.index_archive', text='', icon='FILE_REFRESH')
        self.layout.template_list('ORC_UL_files', '', state, 'entries', state, 'active_index', rows=6)
        entry = selected_entry(context)
        if entry:
            self.layout.label(text=f'{entry.kind} | {entry.size:,} bytes')


class ORC_PT_import(ORCPanel, Panel):
    def draw_header(self, context):
        self.layout.label(text=_ui('import'))
    bl_idname = 'ORC_PT_import'
    bl_label = 'Importação'

    def draw(self, context):
        state = context.scene.orc_tools
        self.layout.label(text='Malhas: modelo FM6S selecionado')
        for prop in ('import_bones', 'import_uvs', 'import_materials'):
            self.layout.prop(state, prop)
        self.layout.operator('orc.import_indexed', icon='IMPORT')
        self.layout.operator('orc.import_ssg', text='Importar SSG completo…')
        self.layout.label(text=_ui('materials_preview'))
        self.layout.label(text=_ui('rig_unvalidated'), icon='ERROR')


class ORC_PT_export(ORCPanel, Panel):
    def draw_header(self, context):
        self.layout.label(text=_ui('export'))
    bl_idname = 'ORC_PT_export'
    bl_label = 'Exportação'

    def draw(self, context):
        self.layout.label(text='Malhas selecionadas → SSG (template original)')
        op = self.layout.operator('orc.export_ssg', text='Exportar SSG…', icon='EXPORT')
        state = context.scene.orc_tools
        if not state.archive_path.lower().endswith('.edgemodel'):
            op.original_ssg = bpy.path.abspath(state.archive_path)
        entry = selected_entry(context)
        op.edgemodel_path = entry.name if entry and entry.kind == 'MODEL' else ''
        self.layout.operator('orc.convert_edgemodel', text='Converter malha ativa → edgemodel…')
        self.layout.label(text=_ui('native_blocked'), icon='ERROR')
        self.layout.label(text='FBX: File > Export / Arquivo > Exportar; BLEND: Save As / Salvar Como')


class ORC_PT_validation(ORCPanel, Panel):
    def draw_header(self, context):
        self.layout.label(text=_ui('validation'))
    bl_idname = 'ORC_PT_validation'
    bl_label = 'Validação'

    def draw(self, context):
        self.layout.operator('orc.validate_archive', icon='CHECKMARK')
        self.layout.label(text=context.scene.orc_tools.status)
        self.layout.label(text='Releitura não garante round-trip byte-exact')


class ORC_PT_config(ORCPanel, Panel):
    def draw_header(self, context):
        self.layout.label(text=_ui('configuration'))
    bl_idname = 'ORC_PT_config'
    bl_label = 'Configuração'

    def draw(self, context):
        addon = context.preferences.addons.get(__package__)
        if addon:
            for name in ('mod_path', 'game_path', 'language'):
                self.layout.prop(addon.preferences, name)
        else:
            self.layout.label(text='Ative o addon nas Preferências para configurar')
        self.layout.label(text='Engine: Hexane / ORC — não MT Framework')
        self.layout.operator('orc.open_documentation', text='Documentação')


classes = [ORCFileEntry, ORCUIState, ORC_UL_files, ORC_OT_index_archive, ORC_OT_browse_archive,
           ORC_OT_import_indexed, ORC_OT_validate_archive, ORC_PT_files, ORC_PT_import,
           ORC_PT_export, ORC_PT_validation, ORC_PT_config]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.orc_tools = PointerProperty(type=ORCUIState)


def unregister():
    del bpy.types.Scene.orc_tools
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
