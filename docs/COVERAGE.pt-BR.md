# Evidência e cobertura do candidato

[English — matriz completa por função](COVERAGE.md) · [Índice](INDEX.pt-BR.md)

Resultados **lidos do manifesto real**, não nova execução independente desta tarefa. Aprovação restrita à evidência; clique físico geral, som acústico/loopback, scanout do monitor, navegação browser e aceitação no jogo não são totalmente aprovados. QA geral do pai pode refinar; promoção canônica local conferida por hash, sem publicação remota.

SHA256 FullExport conferido pela tarefa: `478e8d72606bb350536946b9c9af5e93e4c37a635112224f75277983071e1b5c`. EXE canônico local conferido possui o mesmo hash. Hash canônico antigo `737d117f...` e estado não promovido no manifesto são históricos, não estado atual.

- Fonte: **94** testes com sucesso no manifesto.
- Suites frozen: full-export **17**, câmera **60**, Settings **36**, V2 **36**, jornada PT **32**, EN **32**, QA-fixes **30**, editor **15**, sucesso individual. V1 sem flag interna frozen e **zero checks enumerados**; não inventar contagem.
- Inventário seco: **2.144 SSG / 264 bancos / 16.903 loose**. Dois lotes reais de três itens; **sem dump total de 2.144**. Totais v1.0 históricos são separados.
- Blender 5.0.1 reimportado Ada FBX/blend: **15.595 vértices / 22.172 faces / 16 materiais / 180 ossos sem vínculo / zero pesos**. Tweed vanilla: **17.210 / 21.416 / 13 / 125 / zero pesos**.
- GLB Ada **66.378**, Tweed **64.203** vértices; zero ossos armature nos resultados, pode dividir seams. Sem skin GLB aprovado.
- Ada fonte **22.184** faces, **12** duplicatas removidas antes de todos formatos Explorer **inclusive blend**. Blend addon preserva duplicatas separadamente. Teste de triângulos/UV usa job normalizado, não prova topologia nativa exata.

## Funções aprovadas no escopo registrado
Abrir SSG/BNK/PCK, pasta/busca/filtros, prévia geométrica/UV/diffuse/helpers, câmera esquerdo órbita/direito-meio pan/roda/reset/duplo clique, overlay manual, textura pan/zoom/1:1/PNG, áudio PCM/WAV via decoder, Bink decode/play/pause, metadados/hex/inspetor, Settings EN/PT/persistência, URLs/campos de dependência, extração segura/cancelamento, inventário e lote reduzido, FBX/blend/GLB com diffuse PNG e skeleton nativo **sem vínculo** FBX/blend. Valem ressalvas da [matriz completa](COVERAGE.md), não aprovação universal.

## Lacunas e problemas explícitos
- Override manual: fonte aprovada, picker/jornada frozen final não verificados.
- PNG textura: pixels testados, seletor Save físico específico não verificado; PNG quadro Bink não testado separadamente.
- Picker de abrir pasta fonte não pointer-tested separadamente; Blender picker Settings frozen não coberto como FFmpeg/vgmstream. Existência de executável não prova autenticidade.
- URLs mapeadas, browser/rede não testados; áudio PCM não prova som hardware; fps GL não prova scanout.
- Sem full dump, resume ou garantias de espaço; Tweed instalado geometria inválida, raw funciona; vanilla backup usado.
- Paleta/rest/skin **NÃO VALIDADA**, zero pesos Explorer, sem rig deformável/animação. GLB sem armature testada.
- Addon instalado 1.1.1 não modificado, problemas auditados persistem. Isolado 1.1.2 corrige subset; blend preserva duplicatas, Ada FBX perde 12, Tweed FBX não conserva pesos numéricos; writer bloqueado, CLI seams/validate ainda quebrados.

Fontes locais: `full_export_manifest.json`, `FULL_EXPORT_COVERAGE.md`, `FULL_EXPORT_GUIDE.md`, `DELIVERY_RESULTS.json` addon. JSON bruto/caminhos/assets são privados. [Tutorial](EXPLORER.pt-BR.md) · [Addon](ADDON.pt-BR.md) · [Handoff](RELEASE-CHECKLIST.md).

## Readback independente do pai
### Reteste da fonte de publicação NativeBridge
ZIP fonte allowlisted relocado em pasta com espaços e caracteres não ASCII: suite portátil **15 testes, 9 passaram, 6 skips opcionais (uma fixture própria e cinco testes de artefato frozen)**; bridge **4 passaram** com Tweed privado explícito ou **4 skips** sem fixture. Factory Blender Tweed/Ada/Elite Hunter import/save/reopen: **6/6 passaram**, no-op byte-exato, edição de um vértice, parser externo Albam novo e **9 rejeições por caso**. Explorer fonte relocado `open_source → preview → details`: **6 saídas aprovadas**, não QA UI/EXE frozen. Nove arquivos addon idênticos por hash ao ZIP entregue. Sem fixtures/parsers externos/binários do jogo no pacote; in-game/bounds/injeção SSG não validados. [Fluxo](../tools/native_bridge/README.pt-BR.md).

Jornada canônica: **32/32**, frozen=true, success=true, mesmo hash e contexto **NVIDIA RTX 3050 6GB Laptop GPU**. Resultados separados do pai: câmera **60/60**, export **17/17**, Settings **36/36**, QA **30/30**, V2 **36/36**, editor **15/15**, jornada EN **32/32**; contados a partir dos JSON, não retestes desta tarefa. Evidência FullExport anterior registra **Intel UHD 770**. Nenhuma garantia universal de fps/compatibilidade.

Esta preparação executou seis testes core/câmera sem assets e inicialização GUI normal em cópia isolada, com contexto hardware real. Testes portáteis descobertos pulam fixture privada sem `ORC_MODEL_FIXTURE`; não substituem a suite privada de 94 testes. Lacunas da matriz permanecem. As 10 entradas exatas do ZIP addon auditado estão em `addon/orc_mod_tools/`, sem instalação.
