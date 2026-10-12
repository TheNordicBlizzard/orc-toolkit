# Histórico — Português (BR)

## v1.1.0-rc.1 — pré-release

Pré-release com cobertura delimitada, comparado ao v1.0. [Auditoria final e limitações](docs/RELEASE-AUDIT.md). A candidata limpa exclui GLUT/GLE não usados e DLLs Microsoft empacotadas; o runtime Visual C++ x64 oficial é um pré-requisito externo. Os avisos de terceiros do artefato acompanham o pacote Windows. QA histórica do desenvolvimento é distinguida dos checks da candidata final.

### Explorer
- Editor nativo escuro, biblioteca/inspetor contextual, seletor EN/PT-BR persistente no programa, Configurações segmentadas roláveis e links oficiais de dependências.
- Geometria/UV/diffuse resolvido FM6S 17/18; fallback honesto de material ausente, wireframe/sólido/texturizado/helpers; textura pan/zoom/PNG e metadados/hex.
- Câmera: esquerdo orbita, direito/meio pan, roda zoom, reset exato/duplo clique; ortográfica, transformação compartilhada pelo skeleton.
- SSG/pastas somente leitura, índices Wwise BNK/PCK, extração sem sobrescrita/cancelamento; decoders externos opcionais, sem HIRC/áudio Bink sincronizado.
- Inventário seco/lote sequencial do jogo, opções loose/bancos, estimativas/progresso/relatórios/hashes. 2.144 SSG inventariados e dois lotes de três itens, **não dump completo de 2.144**; sem resume.
- FBX/blend/GLB via Blender 5.0.1 opcional, PNG diffuse e reimportação real. Ada 180/Tweed 125: hierarquia/rest pose nativa SEM VÍNCULO em FBX/blend; zero pesos e `rig_validated: false`; GLB testado sem armature.
- Ada remove 12 polígonos duplicados **inclusive blend Explorer**, LODs juntos, sem promessa de normais/tangentes nativas; Tweed instalado rejeitado, QA com backup vanilla.
- Manifesto fonte: 94 testes; checks frozen detalhados em [cobertura](docs/COVERAGE.pt-BR.md), resultados independentes do pai relidos nesta preparação, sem aprovação universal de hardware. EXE canônico local coincide com o hash FullExport.

### NativeBridge / achados nativos originais
- Addon MIT independente NativeBridge 0.1.0 (nove arquivos originais sem alterações), CLI projeto, fluxo EN/PT extrair/projeto/editar/exportar/reler e testes parametrizados com fixtures próprias opcionais. Contrato por arquivos, sem menu automático Explorer.
- Templates FM6S v18 somente posições: MeshInfo stride 144, prefixo fixo grupo/segmento 128, um grupo observado, strides vértice 12/52. No-op byte-exato; novo arquivo altera só posições, preserva rig/skin/relocation e rejeita edições não suportadas. Bounds intactos, sem nova Armature, conversão arbitrária ou aprovação no jogo.
- Achados estáticos de layout documentados sem binários do jogo, assembly decompilado ou pseudocódigo; travessia multigrupo Explorer permanece investigação separada, não correção anunciada.
- Mantenedor confirmou criação do importador Python com outra IA e autorizou publicação sob MIT existente; créditos históricos mantidos, sem transferir licença de projeto C# distinto.

### Entrega de fonte
- Snapshot revisado de 17 módulos Explorer, spec candidato sem caminhos privados, avisos originais de design, testes portáteis sem assets/fixture opcional pulada e allowlist explícita do ZIP fonte. Sem fixtures/EXE/DLL/decoders em Git.

### Addon / CLI separados
- Candidato isolado **1.1.2** corrige normais/API, UV stride60 e diffuse local ao arquivo; preserva influências numéricas four-u8 **SEM autobind**. Instalado **1.1.1 permanece inalterado**.
- Blend do addon preserva duplicatas; Ada FBX perde 12 e Tweed FBX não preserva pesos numéricos. Associação paleta/rest/skin não validada; operadores writer nativo bloqueados por segurança.
- CLI legado experimental: perda de seams UV e bug validate `command_args`. Aprovação GUI não o inclui. [Limites](docs/ADDON.pt-BR.md).

## Depois de v1.0 — commits públicos existentes

O clone inspecionado contém **quatro commits após a tag v1.0**, em ordem cronológica:
- `6990d93`: workflow GitHub Actions para ZIP de release e posts em português.
- `d964e68`: texto Discord EN/PT-BR citando outros tipos de asset. Divulgação não comprova implementação/teste das funções citadas.
- `bc11ebc`: título/assinatura ASCII e atualização da imagem do menu.
- `9efe8f2`: correção das letras do título ASCII e atualização da imagem do menu.

## v1.0 — primeiro release público (2026-10-09)

Tag `v1.0` aponta para `6bcac96`; publicação `2026-10-09T16:25:01Z`.
- Menu Python com detecção jogo/Blender, inglês padrão e opção português; helpers Blender, extração SSG, scripts FBX/biblioteca, addon de assets editáveis e documentação EN/PT-BR.
- Notas originais reportaram 2.144 SSG, 113.829 arquivos e 2.337 modelos em biblioteca. São alegações de referência do primeiro release, não medições repetidas nesta preparação.
- Asset público `ORC-Toolkit.zip`, 128341 bytes; digest publicado pela API `sha256:ecc86aa9e80241f80d11343d64975fda164e70ef328c69d8703a193185a4a9ce`.
- Apenas scripts/docs; nenhuma permissão para redistribuir assets do jogo.

Fontes: [release](https://github.com/TheNordicBlizzard/orc-toolkit/releases/tag/v1.0), [comparação pública](https://github.com/TheNordicBlizzard/orc-toolkit/compare/v1.0...9efe8f2). Proveniência das evidências locais resumida sem caminhos pessoais em `docs/RELEASE-CHECKLIST.md`.
