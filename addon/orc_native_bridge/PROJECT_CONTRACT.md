# Native file contract v1 / Contrato de arquivos nativos v1

**Positions only / somente posições. IN-GAME UNVERIFIED.**

Project directory (private, never distributed):
- `template.edgemodel`: immutable native FM6S v18 baseline.
- `project.orcmeta.json`: UTF-8 JSON, schema `orc.native-project.v1`, fixed relative template filename, SHA256, byte size, exact parsed `blocks`, `mode=positions-only`, identity coordinate transform, rig/game status and optional original sidecar `provenance`.

Each block records mesh/group ID, 128-byte group header location, 144-byte MeshInfo location, vertex/index counts, buffer offsets/allocation sizes, stride, native LOD and material-table reference. Source sidecar offsets are NOT trusted: reparse the template and compare block records. v0-spike Explorer research sidecars can be validated as input via `create_native_project.py --sidecar`; they are not accepted directly by the Blender open operator. Full skeleton/skin/material/unknown data remain in the byte template, not regenerated from JSON.

Blend identity:
- Scene: absolute project path, template SHA, collection and ordered object names.
- Object: native block ID, LOD, material reference, template SHA and compressed baseline text/hash.
- Mesh: `native_vertex_id`, `native_skin_0..7` (four native u8 weights then four numeric u8 IDs), `native_normal` when stride52, native corner UV and custom normal encoding.
- No palette inference or Blender Armature; numerical skin data stay authoritative in native bytes.

The baseline records all native identity/index/corner multiplicity and unsupported Blender attributes; no `eval`, pickle or executable text input. Selection/hide/UV selection state is excluded; sparse sharp/smooth storage is compared semantically. Stored compressed baseline is an editing guard, NOT a security signature against someone deliberately rewriting scene metadata with Python. Project files may contain private archive paths: do not publish them.

Export:
- chosen NEW `.edgemodel` plus NEW `.edgemodel.diff.json`, exclusive creation;
- same byte size; only f32x3 at native position slots may differ;
- diff schema `orc.native-diff.v1` gives source/output hashes, changed-byte offsets, block/vertex IDs, original/new hex and rig/in-game status;
- template re-read, hash checked before and after export; output readback checked;
- skin/bind/relocation/material/LOD/index/padding bytes preserved, not recalculated.

Explorer consumes the new file through **Open extracted folder**, not a Python plugin, JSON execution or game archive injection. The bridge does not add a launcher/menu to the stable Explorer. Read-only `core.open_source`, `core.preview`, `models.details` checks are source-level contract evidence, not frozen/UI QA.

## Parser follow-up (plan only; shared core UNCHANGED)
MeshInfo stride remains 144. Multi-group mesh records have 128-byte fixed prefixes; the Explorer `subtable + s*144` path must be investigated separately with a native multi-group fixture. Current bridge admits only one observed group, so `s=0` is unaffected. Before any future readonly parser correction: RED multi-group fixture; compare every index/position/UV/skin with Albam and loader field evidence; validate flag-dependent data, pointer spans and relocation independently. Use a 128-byte candidate only when its bounds/layout validate. A fallback must be read-only analysis with an explicit uncertain-layout verdict, never a writer permission or max-index heuristic. No shared parser was patched in this phase.
