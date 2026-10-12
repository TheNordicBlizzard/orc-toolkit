# v1.1.0-rc.1 — scoped release review / revisão delimitada

## English

This is a **prerelease**, not an assertion that every feature works on every machine. The historical developer build and this public-tree build have different hashes and test scopes.

Final public-tree executable: `ORC_Asset_Explorer_Redistributable_Candidate.exe`

SHA256: `08ea94a8fb9fc8537ffcce32def19b896b56d146b24b7515e93521d39b9f1916`

- 52 native components inventoried and hash-matched to recorded upstream binary archives. No bundled Microsoft VC/UCRT/API-set DLLs, GLUT or GLE. Windows 11 x64 tested; install Microsoft's official Visual C++ v14 x64 prerequisite: https://aka.ms/vc14/vc_redist.x64.exe . No automatic prerequisite installation.
- OpenSSL, libffi, LibTomMath, zlib, CPython, Tcl/Tk, image/math dependencies and other included packages have artifact-specific notices. CustomTkinter's actual shipped MIT license is retained, not the conflicting CC0 metadata.
- LibTomMath binary origin is matched to the official Python-build-standalone archive; its shipped Unlicense explicitly permits source and compiled-binary redistribution. The exact LibTomMath source/compiler revision is not supplied by that archive and remains unknown. No claim of reproducible reconstruction of this dependency is made. This limited provenance uncertainty is documented, not treated as a nonexistent source-disclosure obligation under Unlicense.
- The final build passed 60 camera, 36 Settings, 30 prior-bug regression, 36 V2 and 15 editor checks (177 numbered checks). These are local frozen tests, not remote CI. Parent independently reran the 60 camera checks against this exact executable hash. Actual renderer: Intel UHD Graphics 770, hardware WGL/OpenGL 4.6.
- Parent public test run: 15 discovered tests, 14 passed, one optional game-fixture test skipped. Runtime/dependency artifact tests passed with the explicit final executable. The worker extracted from this EXE exported and reimported Ada/Tweed FBX/BLEND/GLB in separate jobs; this is not final frozen export-dialog coverage.
- Reduced native extraction/cancellation was tested. The original installed-game drive was unavailable for the final full-installation frozen smoke and EliteHunter PT/EN journeys. A fixture-specific check expecting 2,144 archives cannot validate a two-archive test root. No full installed-game dump or universal format support is claimed.
- Clean Windows without the VC runtime, multi-DPI/physical pointer/acoustic output and all new export-dialog paths have not been validated for this hash. Native rig binding, arbitrary topology writing and in-game acceptance remain unsupported/unverified as described in the feature guides.

The parent release decision is **candidate redistribution with the declared prerequisites, notices and coverage limitations**, not a blanket legal assurance or stable acceptance. The original developer EXE and user-installed addon were not overwritten. Do not redistribute game assets.

## Português (BR)

Este é um **pré-release**, não uma declaração de que todas as funções estão aprovadas em qualquer máquina. O EXE de desenvolvimento antigo e esta build da árvore pública têm hashes e escopos diferentes.

- EXE final e SHA256: os indicados acima. Foram inventariados 52 componentes nativos e conferidos seus bytes com os pacotes de origem registrados. A build não distribui DLLs Microsoft VC/UCRT/API-set, GLUT ou GLE.
- Windows 11 x64 foi testado. Instale o pré-requisito **Microsoft Visual C++ v14 x64 oficial**, pelo link acima. Não há instalação automática.
- As licenças dos componentes incluídos acompanham o pacote. CustomTkinter usa a MIT efetivamente entregue, não a metadata CC0 conflitante.
- O binário LibTomMath coincide com o pacote oficial Python-build-standalone e acompanha a Unlicense, que permite distribuir código-fonte e binários compilados. A revisão exata de fonte/compilador não foi declarada pelo fornecedor e permanece desconhecida; não se promete reconstrução reproduzível dessa dependência.
- A build passou nos 177 checks frozen locais especificados acima. O pai repetiu independentemente os 60 checks de câmera no hash final. GPU observada: Intel UHD 770, WGL/OpenGL 4.6 de hardware.
- O reteste público do pai encontrou 15 testes: 14 aprovados e uma fixture opcional pulada. O worker deste EXE exportou/reimportou Ada/Tweed em jobs separados; isso não equivale a cobrir todos os diálogos de exportação do EXE.
- Extração e cancelamento foram testados em lote reduzido. O disco original do jogo estava indisponível para a última rodada de dump integral e jornadas EliteHunter PT/EN. Não se afirma ter executado uma extração completa do jogo nesta build.
- Máquina Windows limpa sem runtime VC, todos os DPIs/cliques físicos/saída acústica e todos os novos diálogos de exportação não estão validados neste hash. Rig deformável, topologia arbitrária e aceitação no jogo continuam limitados ou não verificados.

A decisão é disponibilizar uma **candidata com pré-requisitos, avisos e cobertura delimitada**, não anunciar versão estável ou garantia jurídica geral. O EXE de desenvolvimento e o addon instalado do usuário foram preservados.

[Feature coverage / Cobertura](COVERAGE.md) · [Cobertura em português](COVERAGE.pt-BR.md) · [Dependencies / Dependências](../DEPENDENCIES.md)
