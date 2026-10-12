# Fonte, build e portabilidade

[English — comandos de build](BUILD.md) · [Índice](INDEX.pt-BR.md)

## Fonte atual e execução
Árvore local contém os 17 módulos runtime Explorer em `asset_explorer/`, byte-idênticos à fonte viva, avisos originais `DESIGN_NOTICES.md` e spec candidato sem caminhos privados. Entradas exatas do ZIP addon isolado em `addon/orc_mod_tools/`. Menu/scripts/helper legados e LICENSE/histórico preservados. Importação não libera licença de parser/vendor: [handoff](RELEASE-CHECKLIST.md).

Legado: Python 3.10+, `python orc_menu.py`, configure jogo/trabalho/Blender explicitamente; [pipeline manual](PIPELINE.pt-BR.md) documenta cada etapa. Defaults de alguns scripts dependem da máquina e não provam portabilidade.

Explorer testado Python 3.14 / Blender 5.0.1. Precisa Tcl/Tk Windows e driver GPU. Use venv e **mesmo Python para instalar/build**: pip avulso pode apontar outro interpretador.

```bash
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements-explorer.txt
.venv/Scripts/python.exe asset_explorer/app.py
```

Seis testes core/câmera sem assets e startup GUI normal foram executados de cópia isolada do staging. Instalação venv/build limpa não executada nesta tarefa; comandos não equivalem à aprovação de build frozen. Fixar versões para release; metadata observada em [avisos](../THIRD_PARTY_NOTICES.md) não é lockfile/SBOM final. darkdetect/packaging são transitivas da UI; bpy vem do Blender. ffprobe é inspeção externa opcional, **não executado pelo app**.

## Build candidata
Spec staging: `asset_explorer/ORC_Asset_Explorer.spec`, inclui worker Blender como dados e coleta GPU/UI. A partir da raiz do repo, após revisão de proveniência:

```bash
.venv/Scripts/python.exe -m pip install PyInstaller
.venv/Scripts/python.exe -m PyInstaller --clean --noconfirm asset_explorer/ORC_Asset_Explorer.spec
```

Não reconstruir/substituir candidato enquanto outro QA o usa. Spec gera candidato, não promoção. Spec staging inclui QA opt-in com fixtures configuradas explicitamente por ambiente, sem caminhos pessoais/instalação do jogo. Consulte [build redistribuível auditada](../asset_explorer/BUILD_REDISTRIBUTION.md). Mesma spec filtrada e bundle de licenças geram candidato revisado; switches QA exigem fixtures autorizadas locais e evidência fora da árvore pública. Workflow usa allowlist exata e checkout da tag pretendida, sem job GPU. Packager executado localmente; CI GitHub não executado nem afirmado verde.

## Checks portáteis de fonte
Na raiz do repo (pasta scratch existente e própria):
```bash
python -B tests/portable_smoke.py --scratch "C:/ORC-Work/qa"
python -B -m unittest discover -s tests -v
python -B tests/portable_smoke.py --gui --scratch "C:/ORC-Work/qa"
# Fixture própria opcional, nunca distribuída:
python -B tests/portable_smoke.py --gui --fixture "C:/ORC-Work/vanilla.ssg" --scratch "C:/ORC-Work/qa"
python -B tools/package_source.py --output "C:/ORC-Work/ORC-Toolkit.zip"
```
Configure `TMPDIR` para seu scratch antes do unittest; `ORC_MODEL_FIXTURE` só para optar em checks de jogo/GPU. Sem ela o teste privado é pulado explicitamente, não falha. `--gui` exige Windows/Tk/GPU hardware e **não** roda no CI Ubuntu. Checks sem assets cobrem roundtrip/recusa de extração e estado câmera; startup GUI não substitui QA por função. ZIP destino deve ser novo; packager inclui somente `release-files.txt`.

## Hardware, limites e casos
- Windows 11 x64 testado / WGL OpenGL **3.3+** de hardware (`require=330`) obrigatório para prévia. Intel UHD 770 e NVIDIA RTX 3050 6GB Laptop GPU são contextos comprovados, não modelos mínimos exigidos. Sem fallback CPU/software; parsing/decompressão/decodificação são CPU. Sem mínimo fixo CPU/RAM/VRAM/GPU e sem fps universal comprovados.
- Cliente mínimo 1024×680; Settings 620×480, diálogos lote/export 680×560. Use resize/rolagem. DPI múltiplo não integralmente verificado.
- SSG ≤1 GiB, cache descomprimido ≤4 GiB, áudio 256 MB, vídeo ≤10s/120 quadros/12fps. Estimativa de disco não é garantia; PCK grande indexado sem corpo completo.
- Dados portable: `ORC_Asset_Explorer_data` ao lado do EXE; layout reconhecido `dist` pode usar fonte irmã. Diretório precisa ser gravável; revisar logs/config antes de compartilhar.
- Destino existente/protegido/inseguro/reparse: novo destino vazio fora do jogo/fonte/biblioteca; não force sobrescrita/junction.
- Lote failed/unsupported/cancelled/not_started: consulte `batch_report.json`, concluídos ficam, parcial atual removido. Sem resume; repetir em novo destino.
- Tweed instalado: tabela inválida impede exportação geométrica, não extração bruta. QA usa backup vanilla preservado; não reparar jogo automaticamente.
- DDS de quatro bytes não contém pixels: abra DDS completo, confira referências. Override manual não reproduz shader.
- GPU indisponível/renderer remoto software: GPU de hardware/driver oficial; confira Detalhes.
- PCM/vídeo recusados: vgmstream/FFmpeg compatíveis confiáveis; confira erro. Não reconstrói HIRC/prefetch/trilha completa.
- Exportação Blender falhou/timeout: veja `export_failure.json`/`export_report.json`, mantenha bundle diagnóstico; nunca chamar falha de sucesso.
- Skeleton não deforma: comportamento SEM VÍNCULO esperado, zero pesos Explorer, associação paleta/skin não comprovada, sem animação.
- GLB mais vértices/Ada menos faces: GLB divide seams, Explorer remove 12 duplicatas Ada inclusive blend, sem topologia exata.
- Texturas perdidas ao mover: mantenha bundle/PNG relativo FBX/blend; GLB embute PNG.
- Idioma/caminhos não persistem: diretório gravável e caminhos válidos; cancelar seletor preserva campo, falha de gravação não é sucesso. Detecção é existência, não autenticidade/versão.

## Frozen redistribution candidate / Candidato frozen redistribuível
The artifact-specific candidate passed source 94 tests, frozen camera 60, Settings 36, QA-fixes 30, v2 36, full-export 17, editor 15 and both PT-BR/English journeys 32 each. Native inventory: 52 hash-matched files; 50 notice/support files. The reviewed candidate used **Intel UHD Graphics 770**, WGL OpenGL 4.6. RTX 3050 6GB Laptop GPU is detected on the machine but was **not the renderer of these candidate runs**. Other binaries' GPU evidence is not evidence for this candidate. Physical scanout/acoustic/multiple-DPI/clean-machine coverage is not established. Full source-revision trace for the official LibTomMath DLL remains an explicit open limit. See redistribution manifest and full prerequisite/build details linked above. Canonical EXE was not replaced; parent performs final promotion/retest/publication.

## Publicação
Testar relocação limpa com espaços/não ASCII e ausência de decoders; auditar DLLs/codecs/Python/Tk reais da build; sem assets/config/cache/evidence. Binários apenas em release assets aprovados, não Git. Pai faz commit/tag/push/publicação após revisão.
