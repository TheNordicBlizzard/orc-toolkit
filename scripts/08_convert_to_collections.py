#!/usr/bin/env python3
"""Converte a biblioteca de OBJECT-assets (holders vazios, que nao arrastam os
filhos) para COLLECTION-assets (padrao do Blender: arrastar traz tudo).

Cada holder vira uma colecao propria (asset) contendo holder+armature+mesh.
"""
import bpy, os, sys, glob, time

argv = sys.argv[sys.argv.index("--") + 1:]
BLEND, THUMBDIR = argv[0], argv[1]

bpy.ops.wm.open_mainfile(filepath=BLEND)
CATS = ["Characters", "Weapons", "VFX", "Props"]

def descendants(o):
    out = []
    for ch in o.children:
        out.append(ch)
        out.extend(descendants(ch))
    return out

# name -> thumbnail
name2thumb = {}
for f in glob.glob(os.path.join(THUMBDIR, "*.jpg")):
    b = os.path.basename(f)[:-4]
    nm = b.split("__", 1)[1] if "__" in b else b
    name2thumb.setdefault(nm, f)

total = 0
t0 = time.time()
for cat in CATS:
    catcol = bpy.data.collections.get(cat)
    if not catcol:
        continue
    holders = [o for o in catcol.objects if o.asset_data is not None]
    print(f"{cat}: {len(holders)} holders", flush=True)
    for h in holders:
        objs = [h] + descendants(h)
        sub = bpy.data.collections.new(h.name)
        catcol.children.link(sub)
        for o in objs:
            try:
                sub.objects.link(o)
            except Exception:
                pass
            for c in list(o.users_collection):
                if c is not sub:
                    try:
                        c.objects.unlink(o)
                    except Exception:
                        pass
        h.asset_clear()          # remove a marca de object-asset
        sub.asset_mark()         # colecao vira asset
        th = name2thumb.get(h.name)
        if th:
            try:
                for ob in bpy.context.view_layer.objects:
                    ob.select_set(False)
                with bpy.context.temp_override(id=sub):
                    bpy.ops.ed.lib_id_load_custom_preview(filepath=th)
            except Exception:
                pass
        total += 1
        if total % 500 == 0:
            print(f"  {total} convertidos {time.time()-t0:.0f}s", flush=True)

print(f"CONVERTED {total} collections {time.time()-t0:.0f}s", flush=True)
bpy.ops.wm.save_as_mainfile(filepath=BLEND, compress=True)
print("SAVED %.0f MB" % (os.path.getsize(BLEND) / 1024 / 1024), flush=True)
