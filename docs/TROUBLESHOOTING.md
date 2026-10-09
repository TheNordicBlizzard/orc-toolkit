# Troubleshooting

## Extraction

**`.ssg` fails with `zlib.error`**
Large files (level chunks) have a small non-zlib block between compressed
blocks. `01_ssg_extract.py` already handles it: on error, it looks for the next
valid zlib header (`78 01/5e/9c/da`) and resumes. If it still fails, check
`_errors.txt`.

**Cutscenes come out corrupted**
Cutscenes (NIS) mix compressed and uncompressed sections. The current version
computes the correct offset — update the script.

## Blender / Import

**`EXCEPTION_ACCESS_VIOLATION` when importing a model**
Native crash (not catchable by try/except). Cause: zero-length/NaN normals.
The importer sanitizes them — if it persists, the model is a shadow LOD; skip it.

**Blender crashes opening the library `.blend`**
**RAM pressure.** The library loads ~28,000 images (~4 GB). Close other
Blender instances/heavy programs. Opening is intermittent: with the machine free,
it opens fine.

**"Cannot edit library linked or non-editable override object"**
The asset came in as **LINK** (read-only). Fixes:
- In the Asset Browser: **Import Method = Append** (Preferences ▸ File Paths ▸ Asset Libraries)
- Or: `Object ▸ Relations ▸ Make Local ▸ All`
- The `orc_asset_helper` addon does this automatically.

**Dragging an asset brings only an Empty (no mesh/bones)**
You're dragging an **object asset** or an **instance**. Use **collection
assets** (the build already converts them). Or uncheck **Instance** in the Asset
Browser header before dragging.

**Bones don't move / can't click them**
1. Enter **Pose Mode** (select the Armature → `Ctrl+Tab`).
2. Bones need to be **in front of** the mesh: `armature.show_in_front = True`
   (`13_fix_center_bones.py` does this).

**Model appears far from center / floating**
The armature comes offset from the engine. `13_fix_center_bones.py` centers it
(X/Y at origin, base at Z=0).

**Body/hair is transparent**
DXT5 texture with degenerate alpha (all 0 or all 255). `14_fix_degenerate_alpha.py`
forces alpha to 255 while keeping the color.

## Asset Library

**Assets don't show in the Asset Browser**
- Confirm the library in *Preferences ▸ File Paths ▸ Asset Libraries*.
- Click the **⟳** (refresh) icon in the Asset Browser header.
- Restart Blender.

**Assets appear duplicated**
You have more than one `.blend` in the same library folder. Put each version in
its **own subfolder** with its own `blender_assets.cats.txt`.

**The folders (catalogs) appear empty**
The `blender_assets.cats.txt` must be **next to** the `.blend`, and the assets'
`catalog_id`s must exist in it. See `11_organize_catalogs.py`.

**Textures disappear when moving the `.blend`**
Paths are **relative** (`//ORC_textures/...`). Move the `.blend` **together**
with the `ORC_textures` folder. Or `File ▸ External Data ▸ Find Missing Files`.

## Performance

**The library build crashes around 1,000 models**
Don't build in a single process. Use chunks (`05_build_chunks.py`) with recursive split.

**Each Blender process takes a long time to start**
The asset index is missing. Run `02_build_index.py` and set `ORC_ASSET_INDEX_FILE`.
