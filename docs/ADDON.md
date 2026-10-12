# ORC Mod Tools — separate Blender workflow

[Português](ADDON.pt-BR.md) · [Index](INDEX.md)

The Explorer GUI, legacy `orc_asset_helper.py`, ORC Mod Tools addon and experimental CLI are different components. Explorer's Blender worker does **not** require this addon. The installed ORC Mod Tools **1.1.1 was not changed**. Isolated ZIP **1.1.2** is a candidate, not installed/published; parent approves any installation/release. The exact 10 audited package entries are preserved in [addon/orc_mod_tools](../addon/orc_mod_tools/README.md), including vendor modules and original notices; no installed addon was overwritten.

## Try the candidate without replacing your setup
1. Use a separate Blender profile/factory session and an audited addon ZIP supplied by the final release. Current public v1.0 does not contain this new addon. Back up your existing addon/settings; do not replace installed 1.1.1 implicitly.
2. Blender Preferences → Add-ons → Install from Disk (wording varies by Blender); select the addon ZIP, enable ORC Mod Tools, open the 3D View sidebar. Testing used Blender 5.0.1; do not infer all versions from it.
3. **Files:** select game/work/Blender locations and browse a complete SSG, its flat entry list and previews. Inputs stay private. **Import:** choose a real FM6S model. Missing textures/unsupported layout must be read as limitations, not success.
4. **Configuration:** select needed paths and language. Critical warnings/section captions support English/PT-BR, but not every legacy label is translated.
5. **Export:** save blend for the tested preservation path; FBX is an interchange format with the topology/weight limitations below. Both native game export/conversion operators are intentionally **CANCELLED before writing** with a safety warning.
6. **Validation:** checks demonstrate a specific parsed/exported property only. A success indicator is not in-game acceptance, deforming rig correctness or approval of a different CLI command.

## What changed in isolated 1.1.2
Native skeleton count/parser, native normal decoding and Blender custom-normal API, stride60 UV, and archive-local known MATB diffuse references. Four-u8 native numeric influences are stored in numeric vertex groups, **NO autobind**, no mesh parenting/Armature automatic binding. Parsed Ada 180/Tweed 125 joints do not prove a usable native rig: palette/rest/bind/skin association is **UNVALIDATED** and placeholder remains explicitly unbound.

## Exactness and known problems
- Tested addon blend preserves geometry/UV/material/texture and numeric influences, including Ada duplicates. This is **not** Explorer blend behavior: Explorer removes 12 exact duplicate Ada polygons before every chosen format.
- Ada FBX reimport loses 12 duplicate faces (10 + 1 + 1 in three meshes). Positions/surviving UV do not establish topology exactness.
- Tweed FBX geometry/UV/material/texture test passed but `numeric_skin_preserved: false`. Do not advertise weights preserved in every format.
- Diffuse-only material preview: 12 Tweed / 15 Ada textured meshes in the report; no full original alpha/normal/specular/secondary-UV shaders.
- ZIP execution report: **10/10**, source report **18/20** (Ada FBX and original-six issues), UI tests 6 and separate real draw in factory processes. These scopes do not add up to blanket feature approval.
- ZIP SHA256: `7118df49a6726ba05386e0f0763a5292fbdb187e5996fe70698741c5bb408c17`.

## Experimental CLI — not part of GUI approval
The new [NativeBridge project CLI and complement](../tools/native_bridge/README.md) are separate from this legacy CLI: validated FM6S v18 positions only, immutable template, new output and diff. They do not unlock the blocked general ORC Mod Tools writer or make arbitrary replacements safe.
Legacy CLI remains unchanged and is omitted from this addon ZIP. Known failures: UV seams are dropped, validate raises missing `command_args`, native writer uses an incompatible table/skin layout (legacy 2u16+2half versus native four-u8). Do not use it to overwrite game archives or claim in-game roundtrip. No tested safe CLI recipe for native publication is provided. Preserve original game and backups; use new output folders and await a separate CLI fix/QA.

Legacy vendor writer docstrings retain historical round-trip/count wording for exact audited-source parity; those descriptions are **not current safety evidence**. Both native operators are blocked, and this release does not approve the legacy writer.

Sources: local `DELIVERY_RESULTS.json` and [coverage](COVERAGE.md), sanitized for publication. [Notices](../THIRD_PARTY_NOTICES.md).
