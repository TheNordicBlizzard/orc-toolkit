#!/usr/bin/env python3
"""Corrige a biblioteca:
1. Centraliza cada modelo: X/Y no centro do mundo, base (Z min) em 0.
2. Mostra os ossos na frente da malha (show_in_front=True) em todas as armaduras.
"""
import bpy, os, sys, mathutils, time

argv = sys.argv[sys.argv.index("--") + 1:]
BLEND = argv[0]

bpy.ops.wm.open_mainfile(filepath=BLEND)
CATS = ["Characters", "Weapons", "VFX", "Props"]

def descendants(o):
    out = []
    for ch in o.children:
        out.append(ch)
        out.extend(descendants(ch))
    return out

def bbox(objs):
    mn = mathutils.Vector((1e18,) * 3)
    mx = mathutils.Vector((-1e18,) * 3)
    got = False
    for o in objs:
        if o.type != "MESH":
            continue
        for c in o.bound_box:
            w = o.matrix_world @ mathutils.Vector(c)
            for i in range(3):
                mn[i] = min(mn[i], w[i]); mx[i] = max(mx[i], w[i])
            got = True
    return (mn, mx) if got else (None, None)

total = centered = noarm = 0
t0 = time.time()
for cat in CATS:
    catcol = bpy.data.collections.get(cat)
    if not catcol:
        continue
    for sub in list(catcol.children):
        objs = [o for o in sub.all_objects]
        if not objs:
            continue
        total += 1
        # 1) ossos na frente
        for o in objs:
            if o.type == "ARMATURE":
                o.show_in_front = True
            else:
                noarm += 0
        # 2) centralizar
        mn, mx = bbox(objs)
        if mn is not None:
            ctr = (mn + mx) / 2
            off = mathutils.Vector((-ctr.x, -ctr.y, -mn.z))
            roots = [o for o in objs if o.parent is None]
            if not roots:
                roots = [o for o in sub.objects]
            for r in roots:
                r.location = r.location + off
            centered += 1
        if total % 500 == 0:
            print(f"  {total} processados {time.time()-t0:.0f}s", flush=True)

bpy.context.view_layer.update()
print(f"TOTAL {total} | centralizados {centered} | {time.time()-t0:.0f}s", flush=True)
bpy.ops.wm.save_as_mainfile(filepath=BLEND, compress=True)
print("SAVED %.0f MB" % (os.path.getsize(BLEND) / 1024 / 1024), flush=True)
