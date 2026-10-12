# Source, build and portability

[Português](BUILD.pt-BR.md) · [Index](INDEX.md)

## Current repository versus candidate source
The working tree contains the 17 reviewed Explorer runtime modules in `asset_explorer/`, all byte-identical to the live source, plus original `DESIGN_NOTICES.md` and a path-independent candidate build spec. Exact isolated addon ZIP entries are under `addon/orc_mod_tools/`. Legacy menu/scripts/helper and LICENSE/history remain unchanged. Source import does not clear parser/vendor licensing: [handoff](RELEASE-CHECKLIST.md).

## Dependencies and run
Legacy: Python 3.10+ then `python orc_menu.py`; configure your game, work directory and Blender. Existing [manual pipeline](PIPELINE.md) describes each extraction/FBX/library step and environment variables. Those scripts have machine-oriented fallback defaults; use explicit configuration, do not treat defaults as portable.

Explorer source was tested with Python 3.14 and Blender 5.0.1. A compatible Windows Tcl/Tk installation and GPU drivers are necessary. From the repository root, create an isolated environment; use the same Python executable for package installation and build (bare pip may target another interpreter):

```bash
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements-explorer.txt
.venv/Scripts/python.exe asset_explorer/app.py
```

The six asset-free core/camera tests and ordinary GUI startup were executed from an isolated staging source copy. A fresh venv install/build was not executed here; the following instructions are not a frozen-build approval. Resolve/pin dependency versions for your release; [observed metadata](../THIRD_PARTY_NOTICES.md) is not a final lockfile or SBOM. `darkdetect` and `packaging` are transitive UI dependencies. `bpy` is provided by Blender, not pip-installed for the main GUI. `ffprobe` is external optional inspection and is **not executed by the app**.

## Build a candidate
Staged spec: `asset_explorer/ORC_Asset_Explorer.spec`; it includes `blender_worker.py` as data and collects GPU/UI modules. From repository root after provenance review:

```bash
.venv/Scripts/python.exe -m pip install PyInstaller
.venv/Scripts/python.exe -m PyInstaller --clean --noconfirm asset_explorer/ORC_Asset_Explorer.spec
```

Do not rebuild or overwrite the live candidate while another QA process owns it. Spec output is a candidate, not a promoted canonical release. The staged spec now includes opt-in QA modules with explicit environment-configured fixtures, without personal/game-installation paths. See [artifact-specific redistribution build](../asset_explorer/BUILD_REDISTRIBUTION.md). The same filtered spec and complete license bundle produce the reviewed candidate; legacy QA switches require authorized local fixtures and must write evidence outside the public tree. The existing release workflow now uses an exact file allowlist and intended-tag checkout, with no GPU job. Its packager was executed locally; GitHub CI itself has not been run or claimed green.

## Portable source checks
From the repository root (replace the scratch example with your own existing writable folder):
```bash
python -B tests/portable_smoke.py --scratch "C:/ORC-Work/qa"
python -B -m unittest discover -s tests -v
python -B tests/portable_smoke.py --gui --scratch "C:/ORC-Work/qa"
# Optional owned fixture; never bundled in Git:
python -B tests/portable_smoke.py --gui --fixture "C:/ORC-Work/vanilla.ssg" --scratch "C:/ORC-Work/qa"
python -B tools/package_source.py --output "C:/ORC-Work/ORC-Toolkit.zip"
```
Set `TMPDIR` to your owned scratch before unittest discovery; set `ORC_MODEL_FIXTURE` only when deliberately opting into real game/GPU checks. Without it the private-fixture test explicitly skips, not fails. `--gui` needs Windows/Tk/hardware GPU and is **not** run on Ubuntu CI. The asset-free tests verify extraction refusal/roundtrip and camera state; source GUI checks ordinary startup, not all function QA. Packager refuses an existing output ZIP; only `release-files.txt` entries are packaged.

## Hardware and operational limits
- Windows 11 x64 tested / native WGL hardware OpenGL **3.3+** (`require=330`). Intel UHD 770 and NVIDIA RTX 3050 6GB Laptop GPU are evidenced contexts, not minimum GPU specifications. No software/CPU preview fallback; GPU-context error is actionable. Parsing, decompression and media decoding still use CPU. No fixed minimum GPU model/RAM/VRAM or universal 60 fps proven.
- Main client minimum 1024×680; Settings 620×480, batch/export dialogs 680×560. Resize/scroll instead of assuming controls disappeared. Other DPI scales not comprehensively validated.
- SSG ≤1 GiB input, decompressed disk cache ≤4 GiB, audio safety limit 256 MB, video ≤10 s/120 frames/12 fps. Disk output estimates are not guarantees. Large PCK indexing is not a full body load.
- Keep application/output writable. Portable copies store data beside EXE in `ORC_Asset_Explorer_data`; recognized `dist` layout can select a sibling source directory. Review logs/config for private paths.
- External Blender/media binaries are user-selected trusted dependencies; detection checks file existence, not authenticity or version. Keep bundle-relative PNG for FBX/blend; moving only the model can lose textures.

## Troubleshooting cases
| Symptom | Safe action |
|---|---|
| Destination exists, protected, unsafe or reparse | Use a fresh empty output outside game/source/library; do not force overwrite or follow junctions. |
| Batch has failed/unsupported/cancelled/not_started | Read `batch_report.json`; completed outputs remain, current partial removed; no resume. Use a new empty destination. |
| Installed Tweed invalid submesh count | Raw extraction still works; geometry honestly fails. Do not repair the game automatically. QA used a preserved vanilla backup. |
| Four-byte DDS / missing diffuse | Open complete DDS; inspect material references. A reference has no pixels. Manual override is not original shader reconstruction. |
| No GPU / remote software renderer | Use hardware GPU and official driver; no CPU fallback. Details shows actual renderer. |
| No Wwise PCM / refused video | Configure official compatible vgmstream/FFmpeg, read decoder errors; HIRC/prefetch/complete soundtrack not reconstructed. |
| Model export fails or times out | Read `export_failure.json`/`export_report.json`; check official Blender and keep failed bundle for diagnosis, do not report success. |
| Skeleton present but does not deform | Expected UNBOUND behavior; zero Explorer weights, palette/skin unvalidated. No animation. |
| More vertices / fewer Ada faces | GLB can split seams; Explorer removes 12 duplicate Ada polygons, even blend. Not exact topology. |
| Language or paths do not save | Confirm writable app-data location and valid configured paths; picker cancel preserves field; write failure must not be called success. |

## Frozen redistribution candidate / Candidato frozen redistribuível
The artifact-specific candidate passed source 94 tests, frozen camera 60, Settings 36, QA-fixes 30, v2 36, full-export 17, editor 15 and both PT-BR/English journeys 32 each. Native inventory: 52 hash-matched files; 50 notice/support files. The reviewed candidate used **Intel UHD Graphics 770**, WGL OpenGL 4.6. RTX 3050 6GB Laptop GPU is detected on the machine but was **not the renderer of these candidate runs**. Other binaries' GPU evidence is not evidence for this candidate. Physical scanout/acoustic/multiple-DPI/clean-machine coverage is not established. Full source-revision trace for the official LibTomMath DLL remains an explicit open limit. See redistribution manifest and full prerequisite/build details linked above. Canonical EXE was not replaced; parent performs final promotion/retest/publication.

## Publication gates
Build from explicit source allowlist, test clean portable relocation with spaces/non-ASCII and missing decoders, audit actual frozen DLL/codec/Python/Tk licenses, package no game assets/config/cache/evidence. Binaries belong in approved GitHub release assets, not Git. Parent alone commits/tags/pushes/publishes after review.
