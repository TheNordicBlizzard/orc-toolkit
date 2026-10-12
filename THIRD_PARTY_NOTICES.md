# Third-party provenance and redistribution gate / Atribuições e gate de licença

## Existing public scripts / Scripts já públicos

- Toolkit original code: repository `LICENSE` says MIT, Copyright (c) 2026 ORC-Toolkit contributors.
- PiMoNFeeD / ORCToolKit: [source](https://github.com/PiMoNFeeD/ORCToolKit), [license](https://github.com/PiMoNFeeD/ORCToolKit/blob/master/LICENSE). GitHub license API read during preparation returned **MIT, Copyright (c) 2025 Evgeniy Sidorenko**. Preserve the complete upstream copyright/permission text, not merely an author link, for derived substantial portions.
- Szkaradek123: original Xentax script credit is present in existing repository README/LICENSE. A separate original licensing chain was not established by this preparation; do not infer rights beyond evidenced upstream terms.

## Owner clarification / Esclarecimento do autor

**PT-BR:** o mantenedor TheNordicBlizzard esclareceu que criou o importador Python anteriormente com outra IA e já autorizou a publicação do projeto. Essa declaração corrige a hipótese anterior de que o arquivo local seria necessariamente um importador de terceiros: a ausência de licença no arquivo local, por si só, não impede publicar o código original do mantenedor. A auditoria encontrou funções coincidentes com um arquivo distribuído separadamente; coincidência de código não estabelece a direção de derivação. Preservar os créditos existentes e verificar separadamente eventuais trechos efetivamente incorporados de terceiros, sem atribuir automaticamente ao importador a licença de um projeto C# distinto.

**English:** maintainer TheNordicBlizzard states that he previously created the Python importer with another AI and has authorized project publication. This corrects the earlier assumption that the local file necessarily originated with a third party: a missing file-level license does not by itself block publication of the maintainer's original code. The audit found matching functions in a separately distributed file; matching code does not establish the direction of derivation. Preserve existing credits and separately review any actual third-party portions; do not automatically apply the license of a distinct C# project to this importer.

## Candidate parser/addon code / Código parser/addon candidato

Explorer `core.py::parse_mesh` records adaptation from the maintainer's local `orc_import_blender.py::parse_model`. Four functions in `ssg_parser.py` (`parse_ssg`, `u32`, `i32`, `u16`) were AST-matched to already-public MIT `scripts/01_ssg_extract.py`. The maintainer's ownership/publication authorization applies to the original Python importer and project scripts; no blanket unknown-importer grant HOLD remains. Applicable third-party notices and existing source headers are preserved, without asserting that another project's C# license licenses unrelated Python code.

ORC Mod Tools `THIRD_PARTY_NOTICES.md` credits Albam UI/API inspiration: **Sebastian C. Aguirre Brachi and contributors**, MIT Copyright (c) 2025 Sebastian C. Aguirre Brachi, reviewed revision `98ee31d759eb65f0b65ade5fe556e073c2f765c4`. [Pinned MIT text](https://github.com/Brachi/albam/blob/98ee31d759eb65f0b65ade5fe556e073c2f765c4/LICENSE). Complete notice remains with the addon. Its four vendor files are maintainer-supplied ORC project scripts, not Albam; authorization above covers original project code, not unrelated third-party rights.

NativeBridge is a separate original MIT implementation; all nine addon-package entries are preserved byte-for-byte, including LICENSE, ALBAM_LICENSE and notices. No Google Drive importer or external reference parser is shipped. Historical wording such as "unlicensed importer" in the unchanged original bridge module describes its development separation, not a current legal finding about the maintainer-owned importer. [English workflow](tools/native_bridge/README.md) / [Português](tools/native_bridge/README.pt-BR.md).

## GPU/runtime inventory / Inventário GPU/runtime

Versions below were freshly read from installed **host Python** metadata during final documentation preparation, not proof of what the final frozen EXE embeds. Regenerate from its actual build interpreter and preserve all packaged third-party notices, including bundled native libraries.

| Distribution | Observed version | Observed license metadata / audit |
|---|---|---|
| NumPy | 2.5.2 | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0; many subcomponent notices |
| Pillow | 12.3.0 | MIT-CMU; native image codecs may require additional notices |
| ModernGL | 5.13.0 | MIT |
| glcontext | 3.1.0 | MIT |
| pyopengltk | 0.0.4 | MIT |
| PyOpenGL | 3.1.10 | Complete primary license from official 3.1.10 repository tag, included in THIRD_PARTY_LICENSES. GLUT/GLE wheel DLLs and obsolete MSVCR100 are excluded before analysis. |
| CustomTkinter | 6.0.0 | Shipped LICENSE is MIT, Copyright Tom Schimansky 2023; metadata CC0 is not the actual notice. Bundled Roboto 2.137 (2017) is separately Apache-2.0; exact font hashes/name-table notices are supplied. |
| darkdetect | 0.8.0 | BSD-3-Clause |
| packaging | 26.3 | Apache-2.0 OR BSD-2-Clause; preserve both shipped notices |
| PyInstaller (build tool) | 6.22.3 | GPLv2-or-later with special distribution exception; preserve applicable bootloader notice |

Also audit CPython/Tcl/Tk and any native codec/math/OpenGL DLLs included by PyInstaller. Version/license list is not legal clearance of the EXE.

## Artifact-specific native review / Revisão nativa por artefato
The redistribution candidate has **52 native files**, down from 109 in the preserved canonical EXE. Every included DLL/PYD is hash-matched against its Analysis source and an official standalone Python archive or PyPI wheel; the SPDX inventory has one entry per native file. Complete shipped notices plus exact upstream supplements form 50 notice/support files, embedded in the EXE and copied into the release ZIP. See [manifest](asset_explorer/compliance_manifest.json), [native SPDX](asset_explorer/native.spdx.json) and [build/prerequisites](asset_explorer/BUILD_REDISTRIBUTION.md). These findings are not a blanket legal assurance.

Resolved provenance includes CPython 3.14.7 standalone release 20260901, OpenSSL 3.5.8, Windows libffi 3.4.2 at the pinned CPython source-deps commit (not the Linux recipe's 3.4.8), Tcl/Tk 9.0.4, zlib 1.3.2, NumPy/OpenBLAS and Pillow's statically bundled codec notices. Standalone PYTHON.json contains stale Tcl/OpenSSL link names; actual PE imports, official binary hashes and pinned Windows build recipe take precedence. Expat reports 2.8.2 at runtime, not the recipe's unrelated global 2.8.4. LibTomMath is identified by the official Tcl/Tk binary-package commit and matched shipped Unlicense header/full notice; exact DLL compiler/source revision and independent numeric version remain **Open**, not invented.

UCRT/API sets and Microsoft runtimes are **not bundled**. Windows 10/11 x64 supplies UCRT; Microsoft Visual C++ v14 x64 is an explicit external prerequisite. NumPy imports a hash-renamed MSVCP DLL: the runtime hook creates a process-private extraction-directory alias of the installed System32 runtime, without shipping a Microsoft DLL or changing Windows files. Initial removal without this alias failed NumPy import; the corrected candidate passed frozen QA. A clean machine lacking this prerequisite is not verified. No decoder, Blender, GPU-driver DLL or game content is included.

**PT-BR:** 52 nativos mapeados 1:1 por hashes e proveniência oficial; 50 arquivos de avisos/suporte acompanham EXE e ZIP. UCRT/API sets são componentes externos do Windows 10/11, e VC v14 x64 é pré-requisito oficial externo. Alias MSVCP do NumPy é cópia local de runtime já instalado apenas na extração temporária do processo. Revisão exata da fonte/compiler LibTomMath permanece aberta, embora proveniência binária e aviso Unlicense estejam verificados. Não declarar liberação jurídica irrestrita, máquina limpa ou todas as GPUs validadas.


## Optional external tools / Ferramentas externas opcionais

[FFmpeg / ffprobe and vgmstream links](DEPENDENCIES.md) accompany the release. FFmpeg license varies with configuration; local examined external build reported GPLv3-or-later. vgmstream has its own COPYING plus codec-specific DLL licenses. Neither is included in this staging release preparation. Do not bundle decoder DLLs before exact redistribution/source-obligation review.

## Game content / Conteúdo do jogo

Resident Evil: Operation Raccoon City content is © CAPCOM / Slant Six Games. No game assets, extracted textures/models/audio/video, skeleton JSON, game DLLs or fixture archives belong in the package. UI-only screenshots are allowed by the request; use images without private paths or exported game texture content. Nothing in the tooling license grants game-content redistribution rights.

**PT-BR:** fonte original do mantenedor autorizada sob MIT; preservar créditos reais. Inventário/atribuição não é liberação jurídica do binário: a build final deve corresponder à auditoria e aos textos completos. Preferir links oficiais a redistribuir decoders.

## Current candidate and inspiration
Blender is an external user-installed GPL application, not vendored addon or native writer source. Explorer uses a fixed original Blender worker; check licensing of actual parser-derived portions separately. Fresh asset-free source UI screenshots contain no model/texture/game data or personal paths, no pixel rewrite.

Native editor design reference report states visual inspiration only (no copied source/assets) from REE Content Editor/shadowcookie (MIT, Copyright 2025) and Uiverse/galaxy (MIT, Copyright 2023 Uiverse.io). Reference links: https://github.com/kagenocookie/REE-Content-Editor and https://github.com/uiverse-io/galaxy . The original [DESIGN_NOTICES.md](asset_explorer/DESIGN_NOTICES.md) is included in the reviewed source snapshot; visual inspiration is not parser provenance clearance.

**PT-BR:** metadata do host não substitui SBOM/licenças da build congelada. Blender/decoders externos; autoria original do importador confirmada pelo mantenedor e publicação autorizada. MIT legado permanece inalterado; status binário depende do rebuild final auditado.
