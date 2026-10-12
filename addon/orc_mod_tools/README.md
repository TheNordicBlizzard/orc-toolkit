# ORC Mod Tools 1.1.2 — Blender 5.0.1

Native FM6S v17/v18 import addon for Resident Evil: Operation Raccoon City.
This release is a candidate for review, not an in-game validated exporter.
[Português (Brasil)](README_PTBR.md).

## Use
Install the reviewed ZIP with Blender Preferences > Add-ons > Install from Disk,
then enable ORC Mod Tools. Open the 3D View sidebar (`N`), tab **ORC**.
Files indexes an SSG or standalone edgemodel; select a MODEL and import it.
Import options genuinely control numeric skin/placeholder rig, UVs and materials.
The package uses its bundled vendor parsers. External `C:/ORC-Modding` is not
required. The legacy path preference is retained for configuration compatibility.
Game Directory is optional, used only for read-only skeleton lookup.
No automatic installation, scene reload, game modification or mod injection.

## Proven fixes and limits
- Custom corner normals use vectors, never flattened floats; errors are not swallowed.
  Normal directions match an independent mesh using Blender's supported API.
  Blender's own compressed custom-normal storage is not float-byte exact.
- Stride 60 primary UVs are half floats at offset 28; secondary UVs are not imported.
- `20SE` joint count is at 0x10 (0x08 is custom-data size). Names, parent indices
  and local position/quaternion data are decoded from decompressed skeleton SSGs
  in `dlc/**/Characters/skel`. Buffer spans and parent cycles are checked.
- **Rig remains an unbound placeholder.** Mesh bone palette and bind/rest matrices
  are NOT validated. All four native u8 influences are kept in numeric groups.
  No parenting or Armature modifier is added. Matching bone counts are not proof.
  Ambiguous skeleton variants produce a warning without blocking geometry import.
- **Basic diffuse preview only:** native mesh material references resolve archive-local
  MATB to DDS; known diffuse semantic 3014450751 is linked to Principled Base Color.
  Real DDS bytes are packed in Blender images. No original shaders, alpha behavior,
  normal/specular/emission maps or loose resource search are claimed. Standalone
  edgemodels without MATB/DDS receive explicit unresolved-resource warnings.
- **SSG/edgemodel export and conversion are BLOCKED**, returning CANCELLED before
  any output file. The legacy writer has incompatible native tables and writes two
  u16 indices/two half weights rather than four u8 weights/four u8 indices. Heuristic
  header scans are not native acceptance. Sidebar validation now uses native tables.

## FBX / BLEND are different from game export
Use Blender File > Export > FBX for selected meshes; Save As for `.blend`.
Real Ada/Tweed exports were reopened/reimported in separate factory processes.
Geometry, triangles, UVs, material slots and decoded diffuse image hashes were
checked. Tweed FBX passed; Ada FBX is NOT topology-exact: the Blender importer
removed 12 duplicate faces across three meshes (see delivered diagnostic).
BLEND passed for both assets and retains numeric skin groups and packed images. **FBX mesh-only
export does not prove or provide native animation rig/skin.** Blender's FBX importer
may reconstruct separate Color/Alpha nodes; original Hexane shader fidelity is not
preserved. Do not equate these formats with a game-compatible SSG.
The standalone Asset Explorer/CLI is a separate application and is not packaged or
changed here. Its legacy CLI seam and validate defects remain recommendations
for a separate task. Vendor legacy writer modules remain for compatibility only;
they are not exposed as a working native export path.

## Verification
Blender 5.0.1 factory-startup only, real vanilla Tweed/Ada backups and elitehunter.
Tests/evidence are delivered beside this ZIP in `orc-addon-fix`, including RED logs,
`execution.json`, native geometry/UV/skin oracle comparisons and round-trip files.
No game load/deformation test was performed. Installed copy and original source
were not changed: the parent must review before installation/publication.
Critical warnings and section captions support EN/PT-BR; some legacy property and
button labels remain bilingual or PT-BR. There is no full translated Blender locale.
Credits: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

