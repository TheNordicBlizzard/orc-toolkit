bl_info = {
    "name": "ORC Asset Library Helper",
    "author": "Hermes",
    "version": (1, 1, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > ORC / automatico ao importar",
    "description": "Garante que os assets da ORC Asset Library venham EDITAVEIS: converte instancias de colecao em objetos reais e torna local qualquer objeto vindo como LINK (library linked / read-only).",
    "category": "Import-Export",
}

import bpy
from bpy.app.handlers import persistent


def _orc_model_collections():
    return {c.name: c for c in bpy.data.collections if c.get("orc_model")}


def _is_orc_library(lib):
    """True se a Library aponta para a ORC Asset Library."""
    try:
        p = bpy.path.abspath(lib.filepath).replace("\\", "/").lower()
    except Exception:
        return False
    return "orc-asset-library" in p or "orc_assetlibrary" in p


def make_orc_assets_editable():
    """1) Instancias de colecao ORC -> objetos reais.
       2) Objetos LINKADOS da ORC Library -> locais (editaveis).
       Retorna (n_instancias, n_locais)."""
    cols = _orc_model_collections()
    scene_col = bpy.context.scene.collection

    # 1) desinstanciar colecoes ORC
    n_inst = 0
    for o in list(bpy.data.objects):
        if (o.instance_type == 'COLLECTION' and o.instance_collection is not None
                and (o.instance_collection.name in cols or o.instance_collection.get("orc_model"))):
            col = o.instance_collection
            dest = o.users_collection[0] if o.users_collection else scene_col
            for obj in list(col.objects):
                try:
                    if dest not in obj.users_collection:
                        dest.objects.link(obj)
                    if col in obj.users_collection:
                        col.objects.unlink(obj)
                except Exception:
                    pass
            try:
                bpy.data.objects.remove(o, do_unlink=True)
            except Exception:
                pass
            try:
                if len(col.objects) == 0 and len(col.children) == 0:
                    bpy.data.collections.remove(col)
            except Exception:
                pass
            n_inst += 1

    # 2) tornar locais os objetos LINKADOS da ORC Library
    linked = [o for o in bpy.data.objects
              if o.library is not None and _is_orc_library(o.library)]
    n_local = 0
    if linked:
        try:
            for o in bpy.data.objects:
                o.select_set(False)
        except Exception:
            pass
        for o in linked:
            try:
                o.select_set(True)
            except Exception:
                pass
        try:
            bpy.context.view_layer.objects.active = linked[0]
        except Exception:
            pass
        try:
            bpy.ops.object.make_local(type='ALL')
            n_local = len(linked)
        except Exception:
            n_local = 0

    return n_inst, n_local


def _fix_timer():
    try:
        make_orc_assets_editable()
    except Exception:
        pass
    return None  # roda uma vez


def _import_is_orc(ctx):
    try:
        for it in ctx.import_items:
            ident = it.id
            if ident is None:
                continue
            if ident.bl_rna.identifier == 'Collection' and ident.get("orc_model"):
                return True
            lib = getattr(ident, "library", None)
            if lib is not None and _is_orc_library(lib):
                return True
    except Exception:
        pass
    return False


@persistent
def _on_import(ctx):
    try:
        if _import_is_orc(ctx):
            try:
                make_orc_assets_editable()
            except Exception:
                pass
            if not bpy.app.timers.is_registered(_fix_timer):
                bpy.app.timers.register(_fix_timer, first_interval=0.4)
    except Exception:
        pass


class ORC_OT_make_editable(bpy.types.Operator):
    bl_idname = "orc_asset.make_editable"
    bl_label = "Tornar Assets ORC Editáveis"
    bl_description = ("Converte instâncias de coleção em objetos reais e torna local "
                      "qualquer objeto linkado da ORC Library (remove o read-only)")
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        ni, nl = make_orc_assets_editable()
        if ni or nl:
            self.report({'INFO'}, f"{ni} instância(s) convertida(s), {nl} objeto(s) tornados locais")
        else:
            self.report({'INFO'}, "Nada para converter (nenhum asset ORC linkado/instanciado)")
        return {'FINISHED'}


class ORC_PT_panel(bpy.types.Panel):
    bl_label = "ORC Assets"
    bl_idname = "ORC_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "ORC"

    def draw(self, context):
        col = self.layout.column()
        col.operator("orc_asset.make_editable", icon='UNLOCKED')
        col.separator()
        col.label(text="Se ainda vier travado:", icon='INFO')
        col.label(text="• Import Method = Append")
        col.label(text="• desmarque 'Instance' no", icon='BLANK1')
        col.label(text="  cabeçalho do Asset Browser", icon='BLANK1')


_classes = (ORC_OT_make_editable, ORC_PT_panel)


def register():
    for c in _classes:
        bpy.utils.register_class(c)
    if _on_import not in bpy.app.handlers.blend_import_post:
        bpy.app.handlers.blend_import_post.append(_on_import)


def unregister():
    if _on_import in bpy.app.handlers.blend_import_post:
        bpy.app.handlers.blend_import_post.remove(_on_import)
    for c in reversed(_classes):
        try:
            bpy.utils.unregister_class(c)
        except Exception:
            pass


if __name__ == "__main__":
    register()
