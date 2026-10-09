"""Cria 2 versoes da biblioteca:
   - ORC_AssetLibrary_NoProps.blend   (Characters + Enemies + Weapons + VFX)
   - ORC_AssetLibrary_PropsOnly.blend (somente Props)
Purga os dados orfaos (malhas, materiais, imagens) para reduzir o tamanho.
"""
import bpy, os, sys

# pasta da biblioteca (configuravel: 1o argumento apos -- , ou env ORC_LIBDIR)
_argv = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
LIBDIR = _argv[0] if _argv else (os.environ.get("ORC_LIBDIR") or r"C:\ORC-COMPLETO\ORC-Asset-Library")
MASTER = os.path.join(LIBDIR, "ORC_AssetLibrary.blend")
NO_PROPS = os.path.join(LIBDIR, "ORC_AssetLibrary_NoProps.blend")
PROPS_ONLY = os.path.join(LIBDIR, "ORC_AssetLibrary_PropsOnly.blend")


def _descendants(col):
    out = [col]
    for ch in col.children:
        out.extend(_descendants(ch))
    return out


def drop_collections(names):
    """Remove as colecoes de topo dadas + TODAS as suas descendentes + objetos, e purga orfaos."""
    to_remove = []
    for name in names:
        col = bpy.data.collections.get(name)
        if not col:
            continue
        to_remove.extend(_descendants(col))
    # objetos de toda a subarvore
    seen = set()
    for col in to_remove:
        for o in list(col.objects):
            if o.name not in seen:
                seen.add(o.name)
                try:
                    bpy.data.objects.remove(o, do_unlink=True)
                except Exception:
                    pass
    # colecoes (de baixo para cima)
    for col in reversed(to_remove):
        try:
            bpy.data.collections.remove(col)
        except Exception:
            pass
    # purga recursiva (compat entre versoes)
    total = 0
    for _ in range(20):
        n = 0
        try:
            n = bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
        except TypeError:
            try:
                n = bpy.data.orphans_purge(do_recursive=True)
            except Exception:
                n = 0
        except Exception:
            n = 0
        total += n
        if not n:
            break
    return total


def report(tag):
    print(f"[{tag}] objects={len(bpy.data.objects)} meshes={len(bpy.data.meshes)} "
          f"mats={len(bpy.data.materials)} images={len(bpy.data.images)} "
          f"collections={len(bpy.data.collections)}", flush=True)


# ---------- 1) NO PROPS ----------
bpy.ops.wm.open_mainfile(filepath=MASTER)
p = drop_collections(["Props"])
print("purgados (NoProps):", p, flush=True)
report("NoProps")
bpy.ops.wm.save_as_mainfile(filepath=NO_PROPS, compress=True)
print("SAVED NoProps:", round(os.path.getsize(NO_PROPS)/1024/1024), "MB", flush=True)

# ---------- 2) PROPS ONLY ----------
bpy.ops.wm.open_mainfile(filepath=MASTER)
p = drop_collections(["Characters", "Weapons", "VFX"])
print("purgados (PropsOnly):", p, flush=True)
report("PropsOnly")
bpy.ops.wm.save_as_mainfile(filepath=PROPS_ONLY, compress=True)
print("SAVED PropsOnly:", round(os.path.getsize(PROPS_ONLY)/1024/1024), "MB", flush=True)
print("DONE", flush=True)
