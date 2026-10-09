# -*- coding: utf-8 -*-
"""
Compatibilidade entre versoes do Blender (3.x / 4.x / 5.x).

Importe este modulo nos scripts do toolkit para nao depender de uma versao fixa:

    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import _compat as C
    sc.render.engine = C.eevee_engine()
    C.set_material_alpha(mat, True)
    C.purge_orphans()
"""
import bpy
import os
import sys

# ---------------------------------------------------------------- versao

def version():
    """(major, minor, patch) do Blender em execucao."""
    try:
        return tuple(bpy.app.version)  # ex.: (5, 0, 1)
    except Exception:
        return (0, 0, 0)

def version_str():
    try:
        return bpy.app.version_string
    except Exception:
        return "?"

def at_least(major, minor=0):
    v = version()
    return (v[0], v[1]) >= (major, minor)


# ---------------------------------------------------------------- render

def eevee_engine():
    """Retorna o identificador valido do EEVEE para esta versao.

    - Blender <= 4.1 : 'BLENDER_EEVEE'
    - Blender 4.2-4.x: 'BLENDER_EEVEE_NEXT'
    - Blender >= 5.0 : 'BLENDER_EEVEE'  (o '_NEXT' foi removido)
    """
    sc = bpy.context.scene
    for cand in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try:
            sc.render.engine = cand
            if sc.render.engine == cand:
                return cand
        except Exception:
            continue
    # ultimo recurso: mantem o que estiver
    try:
        return sc.render.engine
    except Exception:
        return "BLENDER_EEVEE"

def setup_render_engine(sc):
    """Configura o engine de render de forma compativel."""
    for cand in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try:
            sc.render.engine = cand
            break
        except Exception:
            continue


# ---------------------------------------------------------------- materiais

def set_material_alpha(mat, alpha_meaningful):
    """Configura a transparencia do material de forma compativel.

    alpha_meaningful=True  -> usa o canal alpha (HASHED/BLENDED)
    alpha_meaningful=False -> opaco

    Blender < 4.2 : mat.blend_method = 'HASHED' | 'OPAQUE'
    Blender >=4.2 : mat.surface_render_method = 'DITHERED' | 'BLENDED'
    """
    if alpha_meaningful:
        # tentativa 1: blend_method (mais antigo, ainda aceito em 5.0)
        try:
            mat.blend_method = 'HASHED'
            return
        except Exception:
            pass
        # tentativa 2: surface_render_method (4.2+)
        try:
            mat.surface_render_method = 'DITHERED'
            return
        except Exception:
            pass
    else:
        try:
            mat.blend_method = 'OPAQUE'
            return
        except Exception:
            pass
        try:
            mat.surface_render_method = 'DITHERED'
        except Exception:
            pass


def set_blend_method_hashed(mat):
    set_material_alpha(mat, True)


# ---------------------------------------------------------------- purga

def purge_orphans(max_rounds=20):
    """Purga datablocks orfaos, compativel com varias versoes."""
    total = 0
    for _ in range(max_rounds):
        n = 0
        try:
            n = bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
        except TypeError:
            try:
                n = bpy.data.orphans_purge(do_recursive=True)
            except TypeError:
                try:
                    n = bpy.data.orphans_purge()
                except Exception:
                    n = 0
        except Exception:
            n = 0
        total += n
        if not n:
            break
    return total


# ---------------------------------------------------------------- previews

def load_custom_preview(id_block, filepath):
    """Define um preview customizado num datablock (asset). Compativel.

    Retorna True se conseguiu.
    """
    try:
        for ob in bpy.context.view_layer.objects:
            try:
                ob.select_set(False)
            except Exception:
                pass
    except Exception:
        pass
    # tenta com temp_override (4.x/5.x) e sem (fallback)
    try:
        if hasattr(bpy.context, "temp_override"):
            with bpy.context.temp_override(id=id_block):
                bpy.ops.ed.lib_id_load_custom_preview(filepath=filepath)
        else:
            bpy.ops.ed.lib_id_load_custom_preview(filepath=filepath)
        return True
    except Exception:
        return False


# ---------------------------------------------------------------- addons

def addons_dir():
    """Pasta de addons do Blender em execucao (varia por versao)."""
    v = version()
    ver = f"{v[0]}.{v[1]}"
    appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
    return os.path.join(appdata, "Blender Foundation", "Blender", ver, "scripts", "addons")


# ---------------------------------------------------------------- normais

def set_custom_normals(mesh_data, normals):
    """Aplica normais customizadas com seguranca (evita crash 4.1+/5.x)."""
    import math
    valid = True
    for n in normals:
        try:
            L = (n[0] * n[0] + n[1] * n[1] + n[2] * n[2]) ** 0.5
        except Exception:
            valid = False
            break
        if not (L == L) or L < 1e-8:  # NaN ou zero
            valid = False
            break
    if not valid:
        return False
    try:
        mesh_data.normals_split_custom_set_from_vertices(normals)
        return True
    except Exception:
        return False
