# File formats — Hexane Engine (RE: Operation Raccoon City)

The game does **not** use Unreal Engine. It uses the **Hexane Engine**
(Slant Six Games), DirectX 9 + Havok 7.0.

## `.ssg` — container

An archive that packs almost all the game's content.

**Header (32 bytes):**

| Offset | Field | Description |
|--------|-------|-------------|
| 0 | `version` | u32 LE. If `> 0xFFFF` → the file is **big-endian** |
| 4 | `pad1` | |
| 8 | `secInfosSize` | size of the section table |
| 12 | `secNamesSize` | size of the names |
| 16 | `secDataSize` | size of the data |
| 20 | `pad2` | |
| 24 | `compBlocksSize` | size of the compressed-block table |
| 28 | `alignment` | u16 (section alignment) |
| 30 | `pad3` | u16 |

**Section info (32 bytes each):**

```
nameCRC32, nameOffset, uncompSize, unk(=1), dataOffset, type, uncompCRC32, compSize
```

**Data:**
- Compressed with **zlib, 64 KB blocks** of output.
- `compBlocksSize` = size of the block-size table (u32 each, terminated by 0).
- Sections with `compSize != 0` are compressed (a **negative** value = shares the
  block with the previous one).
- **Layout:** `[uncompressed sections][compressed blocks]`. The start of the
  compressed blocks = `data_off + sum(align(uncompSize))` of **all** uncompressed
  sections (the `dataOffset` of compressed ones is garbage).
- **Cutscenes (NIS)** mix compressed and uncompressed sections — the calculation
  above handles it.
- **Padding gap:** large files (level chunks) have a small non-zlib block
  (e.g. 128 bytes) between compressed blocks, desyncing the fixed stride.
  Fix in `01_ssg_extract.py`: on `zlib.error`, look for the next valid zlib
  header (`78 01/5e/9c/da`) and resume from there.

## `.edgemodel` — mesh

- Magic **`FM6S`** = real mesh (version `0x12`).
- Magic **`IM6S`** (version 2) = model **metadata only** — NOT a mesh. Filter it!
- Contains LODs 0..4 and submeshes. Supported mesh versions: `0x11` (17), `0x12` (18).
  `0x0f` (15) only appears in shadow/LOD1 meshes — skip it.

## Other

| Extension | Content |
|-----------|---------|
| `.matb` | material (magic `MAT`), references textures by relative path |
| `.dds` | textures (DXT1/DXT5) |
| `.hkx` | Havok physics (can be ignored for models) |
| *(no ext.)* | skeleton (magic `ES02`/`20SE`) or animation (magic `40AE`/`EA04`) |

## Game folder structure

```
dlc/packN/Characters/<name>/models/<name>.edgemodel
dlc/packN/Characters/<name>/materials/*.matb
dlc/packN/Characters/<name>/textures/*.dds
Characters/skel/<name>          (skeleton, no extension)
Animation/Projects/*.anims.ssg  (animations)
```

The importer needs the **model + skeleton with the same name** (no extension)
**side by side**, and the `dlc/...` tree preserved to resolve the materials.

## Import pitfalls (crashes)

- **`EXCEPTION_ACCESS_VIOLATION`** when importing: caused by (a) stride-12
  "shadow" meshes with no normals, or (b) vertices with zero-length/NaN normals
  passed to `normals_split_custom_set_from_vertices` (Blender 4.1+/5.x). Fix by
  sanitizing the normals (zeros/NaN → `(0,0,1)`) and only calling the function if
  **all** are valid. **This is NOT catchable with try/except** — it's a native crash.
- **Importing an FBX with a packed texture** re-reads the DDS and crashes
  (OpenImageIO). Use `use_image_search=False` on import.
