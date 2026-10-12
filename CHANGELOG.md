# Changelog — English

## v1.1.0-rc.1 — prerelease

Scoped prerelease compared with v1.0. [Final build audit and limitations](docs/RELEASE-AUDIT.md). The clean candidate excludes unused GLUT/GLE and bundled Microsoft runtime files; the official Visual C++ x64 runtime is an external prerequisite. Artifact-specific third-party notices accompany the Windows package. Historical developer QA is distinguished from final candidate checks.

### Explorer
- Native dark editor, contextual library/inspector, persistent EN/PT-BR program selector, segmented scrollable Settings and official dependency links.
- FM6S 17/18 geometry/UV/resolved diffuse; honest missing-material fallback, wireframe/solid/textured/helpers; texture pan/zoom/PNG, metadata/hex.
- Camera: left orbit, right/middle pan, wheel zoom, exact reset/double-click; orthographic, shared skeleton transform.
- Read-only SSG/folders, Wwise BNK/PCK inventory, safe no-overwrite extraction/cancellation; optional external audio/video decoders, no HIRC reconstruction/synchronized Bink audio.
- Installation inventory and sequential batch, loose/bank options, estimates/progress/reports/hashes. 2,144 SSG inventoried; two three-item batches tested, **no complete 2,144 dump**, no resume.
- Optional Blender 5.0.1 FBX/blend/GLB, diffuse PNG and actual reimport verification. Native UNBOUND Ada 180/Tweed 125 hierarchy/rest matrices in FBX/blend; zero weights, `rig_validated: false`; tested GLB has no armature.
- Ada 12 duplicate polygons removed **including Explorer blend**, LODs retained together, no native normal/tangent preservation claim; installed Tweed geometry rejected, vanilla backup used for QA.
- Manifest records 94 source tests; scoped frozen results in [coverage](docs/COVERAGE.md), separate parent results independently read back for this preparation, not universal hardware approval. The local canonical executable now matches the FullExport hash.

### NativeBridge / original native findings
- Independent MIT NativeBridge 0.1.0 addon (nine unchanged package entries), project CLI, bilingual extract/project/edit/export/readback workflow and parameterized optional-owned-fixture tests. File integration only, not automatic Explorer menus.
- FM6S v18 positions-only templates: MeshInfo stride 144, fixed group/segment prefix 128, one observed group, vertex strides 12/52. No-op byte-exact; new-file export changes only positions, preserves rig/skin/relocation bytes and rejects unsupported edits. Bounds unchanged, no new Armature, no arbitrary model conversion or in-game approval.
- Static layout findings documented without game binaries, decompiled assembly or pseudocode; multigroup Explorer traversal remains a separate investigation, not a fix claimed here.
- Maintainer confirmed Python importer authorship with another AI and authorized publication under existing MIT; historical credits retained, no automatic license transfer from a distinct C# project.

### Source delivery
- Reviewed 17-module Explorer snapshot, path-independent candidate spec, original design notices, asset-free portable tests with optional-fixture skip, and explicit source ZIP allowlist. No game fixtures, EXE/DLL or decoders in Git.

### Separate addon / CLI
- Isolated **1.1.2** candidate fixes normals/API, stride60 UV and archive-local diffuse; numeric four-u8 influences stored **NO autobind**. Installed **1.1.1 unchanged**.
- Addon blend preserves duplicate topology; Ada FBX loses 12 duplicates; Tweed FBX numeric weights not preserved. Palette/rest/skin association unvalidated; native writer operators safely blocked.
- CLI remains experimental: UV seam loss and validate `command_args` bug. GUI approval does not approve CLI. [Limits](docs/ADDON.md).

## After v1.0 — existing public commits

These are the **only four commits after the v1.0 tag** in the clone inspected for this preparation, in chronological order:
- `6990d93`: release ZIP GitHub Actions workflow and Portuguese promo posts.
- `d964e68`: English/Portuguese Discord sharing text mentioning other asset types. Promotional wording is not a feature implementation/test.
- `bc11ebc`: menu ASCII title/signature and menu image refresh.
- `9efe8f2`: correction of the ASCII title lettering and menu image refresh.

## v1.0 — first public release (2026-10-09)

Tag `v1.0` resolves to `6bcac96`; release published `2026-10-09T16:25:01Z`.
- Interactive Python menu with game/Blender detection, English default and Portuguese option; Blender compatibility helpers, SSG extraction, model-to-FBX and library-building scripts, editable asset helper addon, English/Portuguese documentation.
- The release notes reported 2,144 SSG archives, 113,829 extracted files and 2,337 library models. These are the first release's reference claims, not newly repeated measurements.
- Public asset: `ORC-Toolkit.zip`, 128341 bytes; published API digest `sha256:ecc86aa9e80241f80d11343d64975fda164e70ef328c69d8703a193185a4a9ce`.
- Scripts/docs only; no redistribution permission for game assets.

Sources: [release](https://github.com/TheNordicBlizzard/orc-toolkit/releases/tag/v1.0), [public comparison](https://github.com/TheNordicBlizzard/orc-toolkit/compare/v1.0...9efe8f2). Local evidence provenance is summarized without machine/user paths in `docs/RELEASE-CHECKLIST.md`.
