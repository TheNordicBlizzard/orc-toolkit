# Full pipeline (exact order)

All commands assume:
```bash
set GAME=<game folder>
set WORK=<work folder>
set BLENDER="C:\Program Files\Blender Foundation\Blender 5.0\blender.exe"
```

---

## Phase A — Extraction (pure Python)

### A1. Unpack all `.ssg`
```bash
python scripts/01_ssg_extract.py "%GAME%" "%WORK%\ssg_unpacked"
```
→ 2,144 `.ssg` files → ~113,829 files (internal paths preserved).
Resumable: re-running skips what's already done (`_done.txt`).

### A2. Asset index (essential for performance)
```bash
python scripts/02_build_index.py "%WORK%\ssg_unpacked" "%WORK%\_asset_index.json"
```
Generates a JSON `name → absolute path`. Without it, every Blender process
re-scans 113k files (~40 s each).

### A3. (Optional) collect loose files by category
Organize `ssg_unpacked` into `loose/` (models, textures, materials, skeletons...)
— see `build_final.py` in the project history if you need it.

---

## Phase B — FBX export

### B1. Model manifest
List every `.edgemodel` with magic `FM6S` (filtering out the `IM6S`):
```
format: [[fbx_path, "category/name"], ...]
categories: characters / weapons / vfx / worlds
```

### B2. Export
```bash
"%BLENDER%" --background --factory-startup --python scripts/04_export_all_models.py -- ^
  "%WORK%\ssg_unpacked" "%WORK%\fbx_models"
```
Runs **one Blender process per batch** with **split-retry** (isolates crashing models).

Useful environment variables:
```
ORC_ASSET_INDEX_FILE=%WORK%\_asset_index.json
ORC_ASSET_ROOT=%WORK%\ssg_unpacked
```

---

## Phase C — Asset Library (Blender)

### C1. Build in chunks (avoids memory crash)
```bash
"%BLENDER%" --background --factory-startup --python scripts/05_build_chunks.py -- ^
  "%WORK%" "%WORK%\_all_manifest.json" "%WORK%\ORC_AssetLibrary.blend" 300
```
> A single process with 2,347 FBX crashes (~1,000 models). Chunks of 300 fix it.
> `05_build_chunks.py` has **recursive split**: a chunk that fails is halved and
> retried, isolating the bad model.

### C2. Merge into a single `.blend`
```bash
"%BLENDER%" --background --factory-startup --python scripts/07_merge_library.py -- ^
  "%WORK%\_chunks" "%WORK%\ORC_AssetLibrary.blend"
```
Classifies each object by its **parent chain** (mesh → armature → holder)
using the `name → category` map from the manifest.

### C3. Convert to *collection assets*
```bash
"%BLENDER%" --background --factory-startup --python scripts/08_convert_to_collections.py -- ^
  "%WORK%\ORC_AssetLibrary.blend" "%WORK%\thumbnails"
```
> **Critical:** each model becomes a **Collection** marked as an asset. If you use
> *object assets* (the Empty holder), dragging brings **only the Empty**, no mesh.

### C4. Thumbnails + previews
```bash
"%BLENDER%" --background --factory-startup --python scripts/09_gen_thumbnails.py -- ^
  "%WORK%\_all_manifest.json" "%WORK%\thumbnails"

"%BLENDER%" --background --factory-startup --python scripts/10_apply_previews.py -- ^
  "%WORK%\ORC_AssetLibrary.blend" "%WORK%\thumbnails"
```

### C5. Catalogs (folders)
```bash
"%BLENDER%" --background --factory-startup --python scripts/11_organize_catalogs.py -- ^
  "%WORK%\ORC-Asset-Library"
```
Classifies into Characters / Enemies / Weapons / VFX / Props (+ subfolders) and
writes `blender_assets.cats.txt`.

---

## Phase D — Final touches

### D1. Center + visible bones
```bash
"%BLENDER%" --background --factory-startup --python scripts/13_fix_center_bones.py -- ^
  "%WORK%\ORC-Asset-Library\ORC_AssetLibrary.blend"
```

### D2. Light / props-only versions (optional)
```bash
"%BLENDER%" --background --factory-startup --python scripts/12_make_versions.py -- ^
  "%WORK%\ORC-Asset-Library"
```

### D3. Register the library in Blender
```bash
"%BLENDER%" --background --python scripts/15_register_library.py -- ^
  "ORC Assets" "%WORK%\ORC-Asset-Library"
```

### D4. Helper addon
Copy `addon/orc_asset_helper.py` into Blender's addons folder and enable it.

---

## Expected final structure

```
%WORK%\
├── ssg_unpacked\              (113k files)
├── _asset_index.json
├── fbx_models\                (FBX by category)
├── _chunks\                   (intermediate parts)
├── thumbnails\                (2,337 JPG 320×320)
└── ORC-Asset-Library\
    ├── ORC_AssetLibrary.blend
    ├── ORC_textures\          (externalized PNGs)
    ├── thumbnails\
    └── blender_assets.cats.txt
```

## Performance (reference, i5 + 16 GB RAM)

| Step | Time |
|------|------|
| `.ssg` extraction | ~6 min |
| FBX export (all models) | ~1 h |
| Library build (chunks) | ~35 min |
| Merge | ~17 min |
| Thumbnails | ~20 min |
| Previews | ~5 min |
