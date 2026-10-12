# NativeBridge 0.1.0 — source tools

[Português](README.pt-BR.md) · [File contract](../../addon/orc_native_bridge/PROJECT_CONTRACT.md) · [License](../../addon/orc_native_bridge/LICENSE) · [Notices](../../addon/orc_native_bridge/THIRD_PARTY_NOTICES.md)

Independent Blender 5.0 complement, **positions only; IN-GAME UNVERIFIED**. This source tree includes all nine original addon package entries unchanged. No game fixtures, original private source manifest, external reference parsers or duplicated addon tree are included. The Python importer is maintainer-owned; NativeBridge is a separate original MIT implementation, not a replacement licensing grant for unrelated code.

## Extract → project → Blender → new file → Explorer

1. In Explorer, open your own SSG and extract the original `.edgemodel` into a private work folder. Keep the original unchanged. Optional research `.orcmeta.json` sidecar must match that template; it is not the v1 project contract.
2. From the toolkit root, create a **new** project directory:
   ```text
   python tools/native_bridge/create_native_project.py "WORK/template.edgemodel" "WORK/new-project"
   ```
   If available, append `--sidecar "WORK/reference.orcmeta.json"`. Without it, no external provenance is invented. CLI help works with standard Python, without Blender.
3. Install the separate NativeBridge addon ZIP attached to the **future candidate release**, once actually published. This draft provides no promised download URL. For developers, a ZIP containing the nine files under `addon/orc_native_bridge/`, with top-level `orc_native_bridge/`, is Blender-installable. Use a separate test profile; this preparation did not install it or update the existing ORC Mod Tools addon.
4. In Blender 5.0, open the sidebar **ORC Complemento**. **Open native project** → choose `project.orcmeta.json`. Edit only vertex positions in Edit Mode, then return to Object Mode. **Validate reference** → **Export NEW edgemodel**. Select EN/PT in this panel as needed.
5. Read the accompanying `.edgemodel.diff.json`: source/output SHA256, vertex/block IDs, original/new field bytes and changed-byte offsets. Output and diff must be new files; overwrite is rejected. A no-op preserves every native byte.
6. In Explorer, **Open extracted folder**, choose the export folder and select the new file. Compare preview/details with your baseline. This is explicit file integration, **not an automatic Explorer menu/launcher or archive injection**. Readback demonstrates structure, not acceptance by the game.

## Supported boundary

Verified template scope: FM6S v18, one observed group per mesh record; MeshInfo stride 144, fixed group/segment prefix 128, vertex strides 12/52; unchanged vertex/index counts and order. This does not claim an Explorer multi-group parser fix. FM6S v17, new topology, arbitrary replacement models and general format conversion are not supported.

Rejects unsupported topology/seams/IDs, UV/normal/tangent edits, skin/groups/weights, material references/LOD, transforms, modifiers and shape keys instead of silently discarding them. Selection/hiding is edit state only. Native normals and bounds are not updated; keep edits small. Rig/skin/bind/relocation/material/padding/unknown bytes are preserved, **not a new bound or posed rig**; no Armature is created. External textures/materials do not travel automatically. No SSG repacking, injection, animation or in-game mission/deformation validation is provided.

## Reproduce without publishing assets

Run from the toolkit root; replace placeholders with paths to your own fixtures and licensed independent references. Keep all output private and outside the checkout.

```text
python -B -m unittest discover -s tests -p "test_*.py" -v
python -B -m unittest discover -s tools/native_bridge/tests -p "test_*.py" -v
python tools/native_bridge/run_factory_suite.py "BLENDER_EXECUTABLE" "OWNED_FIXTURES" "INDEPENDENT_REFERENCE" "NEW_PRIVATE_EVIDENCE"
```

The four bridge unit tests skip unless `ORC_FIXTURE` points to an owned native `.edgemodel`; no implicit developer-home fixture is searched. The factory runner expects `tweed-0.edgemodel`, `adawong-0.edgemodel`, `elitehunter-0.edgemodel`, and external `references/albam/hexane_edgemodel.py` plus `deps/kaitaistruct.py`. Six new factory processes import/save/reopen, check no-op/one-vertex export, fresh independent parse and rejection guards. These parsers are test references, not shipped runtime.

Additional parameterized scripts: `tests/operator_test.py` (project/output/proof after Blender `--`), `tests/ui_test.py` (proof path; owned graphical factory process), `tests/explorer_readonly_test.py` (Explorer source directory, factory evidence directory). They do not claim frozen-EXE or physical file-dialog QA. Runtime requires Blender/Python standard library only; Explorer readback tests additionally use its NumPy dependency.
