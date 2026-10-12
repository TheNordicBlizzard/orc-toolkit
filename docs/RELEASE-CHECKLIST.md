# Historical preparation checklist / Checklist histórico de preparação

The draft below records preparation-stage decisions; it is not the current release verdict. Read [the final v1.1.0-rc.1 scoped review](RELEASE-AUDIT.md) for exact candidate hash, final dependency handling and unverified areas. / O rascunho abaixo registra decisões da preparação, não o veredito atual: consulte a auditoria final para hash, dependências e lacunas.

## Current verdict / Veredito atual
**SOURCE_READY:** original importer ownership and publication permission confirmed by TheNordicBlizzard under existing MIT; applicable historical third-party credits retained. NativeBridge source, explicit package entries and bilingual workflow are included. Source readiness does not promise rig fidelity or in-game compatibility.

**BINARY_READY: conditional, not declared by this task.** The parallel frozen-DLL rebuild/audit must supply exact final artifact hashes, notices, relocated QA and parent acceptance. Historical FullExport results below apply only to that historical hash, not automatically to a new rebuild. Version proposed: **v1.1.0-rc.1**, Unreleased; live GitHub readback showed only v1.0.

**PT-BR:** fonte autorizada e preparada, não HOLD global por importador desconhecido. Binário depende da auditoria/rebuild final do outro agente; resultados históricos não se transferem a hashes novos. Nenhum add/commit/push/release feito aqui.

## State / Estado
- No git add/commit/push/tag/release by the documentation task. Existing dirty drafts were backed up outside the repository; no reset. Legacy code/history and LICENSE preserved.
- Public master inspected: `9efe8f2`; tag v1.0 `6bcac967156d98ed53216cec270a3e8f88233523`, published 2026-10-09. Four subsequent public menu/promo/workflow commits, no new Explorer release assumed.
- Toolkit **v1.1.0-rc.1 is proposed / Unreleased**, addon isolated **1.1.2** separate, installed **1.1.1 unchanged**. NativeBridge **0.1.0** separate, not installed or integrated into Explorer menus. Reviewed source entries included locally; historical canonical EXE promotion was hash-verified, not performed here.
- FullExport candidate verified SHA256 `478e8d72606bb350536946b9c9af5e93e4c37a635112224f75277983071e1b5c`; the local canonical EXE independently hashes to the same FullExport value. Old manifest canonical `737d117f...` and not-promoted state are historical. Completed parent outputs were read, not rerun/polled: canonical journey 32/32; camera 60/60, export 17/17, Settings 36/36, QA 30/30, V2 36/36, editor 15/15, EN journey 32/32, all success=true with exact candidate hash.
- Source manifest 94 tests; scoped frozen coverage and gaps in [coverage](COVERAGE.md). Native rig remains unbound, zero Explorer weights, no palette/skin validation. Two three-item batch tests, no new full 2144 dump.

## Parent source-import allowlist / Allowlist de importação pelo pai
The original reviewed 17-module snapshot is in `asset_explorer/`; the parallel rebuild task owns subsequent app/spec/runtime changes. Legacy scripts/helper and LICENSE unchanged. Original Python importer ownership/publication authorization is confirmed, not an unresolved global source-provenance gate.

Reviewed runtime source (17):
`app.py`, `archive.py`, `audio.py`, `batch_extract.py`, `blender_export.py`, `blender_worker.py`, `containers.py`, `core.py`, `editor_style.py`, `full_export_ui.py`, `gpu_preview.py`, `i18n.py`, `media.py`, `models.py`, `modern_ui.py`, `settings_ui.py`, `ssg_parser.py`.

Staged path-independent build spec includes Blender worker; QA/runtime hooks are owned by the parallel rebuild task, so use its final manifest rather than assuming the initial snapshot unchanged. Original design notices preserved. Historical six asset-free core/camera tests and isolated GUI startup passed; owned Ada run proved pan/frame-change/reset and unchanged fixture bytes (15,595 vertices, 22,184 faces). Current discoverable test totals are recorded in the final scratch handoff; optional owned fixtures skip when absent. They do not replace the 94 private regressions or prove a frozen rebuild.

Addon: exact 10 audited ZIP entries included under `addon/orc_mod_tools/`, original vendor/README/notices preserved and hashes matched. No external CLI/writer siblings or game fixtures copied. Installed 1.1.1 untouched; not installed by this task. Native export operators safely blocked; Ada FBX failure and palette/bind limitation remain. Original package SHA256 `7118df49a6726ba05386e0f0763a5292fbdb187e5996fe70698741c5bb408c17`. [Addon](ADDON.md).

Do not import: caches, backups, logs, evidence, private manifests/configs, job/skeleton JSON, EXE/DLL/ZIP, generated model/texture/audio/video output, original game archives. Docs `screenshots/` only individually reviewed images.

## Licensing / Licença
- Existing MIT/LICENSE and PiMoNFeeD upstream complete notice preserved. Maintainer-created Python importer and project vendor scripts are authorized for publication; no automatic license inference from C# or unrelated domain. Four `ssg_parser.py` functions match existing public MIT source.
- Addon Albam inspiration distinct from maintainer ORC scripts. Complete Albam notice retained; NativeBridge ships its standalone MIT and Albam notice without external parser code.
- Host dependency metadata freshly audited, including CustomTkinter 6.0.0 CC0 metadata, darkdetect and packaging; not final EXE SBOM. Audit actual native DLL/CPython/Tcl/Tk/Pillow/NumPy/PyOpenGL licenses and PyInstaller exception.
- Keep FFmpeg/vgmstream/Blender external; no decoder binaries or game DLLs in source/package. Links accompany release. [Notices](../THIRD_PARTY_NOTICES.md).

## Mandatory gates / Gates obrigatórios
- [ ] Parent independent final QA; update scope only from actual output, especially Bink frame PNG, manual texture picker, native folder/Blender path pickers, external links, physical pointer/audio/DPI/portable location.
- [x] Runtime allowlist imported/hash-compared, portable tests use opt-in owned fixture, legacy LICENSE/history preserved.
- [x] Maintainer ownership/publication authorization confirmed; actual third-party credits preserved, no blanket unknown-importer HOLD or automatic unrelated license grant.
- [ ] Test clean portable copy with writable data directory, spaces/non-ASCII, no original source/config/dependency fallbacks; Blender absence does not prevent raw extraction.
- [ ] Verify exact frozen dependency/licenses/SBOM and trusted user-selected binaries; detected file is not authenticity/version proof.
- [x] Release workflow uses intended-tag checkout, stdlib-only packaging tests and exact `release-files.txt` allowlist; no GPU CI assumption. Packager tests RED/GREEN and local execution verified; GitHub Actions itself was not run/claimed green.
- [ ] Build package source/docs separately from EXE/addon assets. No game content/config/cache/backups/logs/private JSON. Compute final ZIP SHA256 and inspect entries.
- [x] Four asset-free real-source screenshots inspected, blank configuration/no private paths/game imagery, no pixel rewrite. Backed-up provisional preview removed from staging, source evidence untouched.
- [ ] Parent final git diff/check, commit/push/tag/release only after user-authorized approval; verify remote target/tag/release and download asset hash. Never announce proposed v1.1.0 as existing until then.

## Portability findings / Achados
Legacy menu/library scripts have machine-oriented defaults; use explicit configuration and prove clean-machine behavior. Explorer media fallback can discover a home tool path; source data is adjacent, portable data beside EXE, recognized dist layout can use sibling source. QA modules/hooks in the final snapshot are parameterized and owned by the parallel rebuild task; exact packaging allowlist replaces recursive ZIP. Final frozen build and clean relocation/dependency-absence/DPI validation remain gates. General native writer/legacy CLI remain unapproved; separate NativeBridge positions-only structural export is documented, still in-game unverified.

Planned assets: source/docs toolkit ZIP, Windows Explorer portable ZIP with exact runtime notices, separate ORC Mod Tools and NativeBridge addon ZIPs. Binaries belong in release assets, never git. **SOURCE_READY; BINARY_READY conditional on final frozen audit/rebuild and parent acceptance.** No new release/tag or downloadable candidate asserted. / **Fonte pronta; binário condicionado à auditoria/rebuild final e aceitação do pai.**
