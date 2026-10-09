#!/usr/bin/env python3
"""Driver: export each ORC character to FBX in its OWN Blender process,
so a crash on one model doesn't abort the whole batch."""
import os, sys, glob, subprocess

BLENDER = os.environ.get("ORC_BLENDER") or r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe"
HERE = os.path.dirname(os.path.abspath(__file__))
READY = os.path.join(HERE, "ready_all")
OUT = os.path.join(HERE, "fbx_all")
IMPORTER = os.path.join(HERE, "04d_import_one.py")
os.makedirs(OUT, exist_ok=True)

models = sorted(glob.glob(os.path.join(READY, "*", "dlc", "pack1", "characters", "*", "models", "*.edgemodel")))
print(f"Found {len(models)} models")
ok = fail = 0
for i, m in enumerate(models, 1):
    name = os.path.splitext(os.path.basename(m))[0]
    fbx = os.path.join(OUT, name + ".fbx")
    if os.path.exists(fbx):
        print(f"[{i}/{len(models)}] {name}: skip (exists)"); ok += 1; continue
    r = subprocess.run([BLENDER, "--background", "--factory-startup", "--python", IMPORTER, "--", m, fbx],
                       capture_output=True, text=True, timeout=300)
    if r.returncode == 0 and os.path.exists(fbx):
        print(f"[{i}/{len(models)}] {name}: OK ({os.path.getsize(fbx)/1024:.0f} KB)"); ok += 1
    else:
        err = (r.stdout + r.stderr).strip().splitlines()[-1] if (r.stdout + r.stderr).strip() else f"code {r.returncode}"
        print(f"[{i}/{len(models)}] {name}: FAIL ({err[:80]})"); fail += 1
print(f"\nDONE ok={ok} fail={fail}")
