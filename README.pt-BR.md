# RE: Operation Raccoon City — Toolkit

**v1.1.0-rc.1 — candidata de lançamento.** [Downloads](https://github.com/TheNordicBlizzard/orc-toolkit/releases/tag/v1.1.0-rc.1) · [Primeiro release v1.0](https://github.com/TheNordicBlizzard/orc-toolkit/releases/tag/v1.0). Fonte, addons Blender e candidata Windows com cobertura delimitada; não é uma versão estável ou universalmente validada. Instale o [pré-requisito Microsoft Visual C++ v14 x64 oficial](https://aka.ms/vc14/vc_redist.x64.exe). Leia a [auditoria do artefato e as lacunas de teste](docs/RELEASE-AUDIT.md). O importador Python pertence ao mantenedor e foi autorizado sob MIT existente; avisos aplicáveis de terceiros permanecem.

[English](README.md) · [Índice da documentação](docs/INDEX.pt-BR.md) · [Histórico](CHANGELOG.pt-BR.md)

Fluxos separados:
- **GUI Explorer Windows:** SSG/pasta/BNK/PCK somente leitura, prévia GPU de malha/textura, mídia via decoders opcionais, extração segura, inventário/lote da instalação; FBX/blend/GLB via Blender opcional. [Tutorial por função](docs/EXPLORER.pt-BR.md).
- **Menu/pipeline legado:** extração Python, FBX e Asset Library Blender. Já público; preservado abaixo. [Instalação](INSTALL.pt-BR.md) · [Pipeline](docs/PIPELINE.pt-BR.md).
- **ORC Mod Tools:** addon Blender separado, candidato isolado 1.1.2 não instalado; Explorer não depende dele. [Guia e limites CLI experimental](docs/ADDON.pt-BR.md).
- **NativeBridge / ORC Complemento 0.1.0:** addon Blender independente somente posições e CLI de projeto. Extrair Explorer → projeto nativo novo → editar posições Blender → novo edgemodel → reler Explorer. Contrato por arquivos, sem menu automático ou injeção no jogo. [Fluxo completo e limites](tools/native_bridge/README.pt-BR.md).

**Sem distribuição de assets do jogo.** Use sua própria cópia e mantenha extraídos privados. Rig nativo **SEM VÍNCULO**, zero pesos no Explorer; sem animação, paleta skin validada ou promessa de writer in-game. Explorer remove triângulos duplicados Ada inclusive no blend; não é topologia nativa exata.

Evidência local registra 94 testes de fonte e checks do candidato frozen, inventário seco de 2.144 SSG e dois lotes reduzidos de três itens—não uma nova extração completa do jogo. Consulte [cobertura](docs/COVERAGE.pt-BR.md). Totais históricos v1.0 abaixo são alegações das notas do release, não novas medições.

![Interface real de fonte sem assets](docs/screenshots/welcome_pt-BR.png)

**Requisitos:** Windows 11 x64 testado, GPU/driver OpenGL 3.3+ de hardware para prévias, saída gravável e disco/cache suficiente. EXE portable dispensa instalação separada de Python; Blender é opcional para exportar modelos, obrigatório para biblioteca legada/addon. Não se estabeleceu mínimo fixo RAM/VRAM/CPU nem garantia universal de fps. [Dependências](DEPENDENCIES.md) · [Build/portabilidade](docs/BUILD.pt-BR.md) · [Avisos](THIRD_PARTY_NOTICES.md).

---

## O que este toolkit faz

```
Jogo (.ssg)  →  [extração]  →  arquivos soltos  →  [import Blender]  →  FBX / Asset Library
```

| Etapa | Script | Resultado |
|-------|--------|-----------|
| 1. Desempacotar `.ssg` | `01_ssg_extract.py` | Árvore com todos os `.edgemodel`, `.matb`, `.dds` |
| 2. Índice de assets | `02_build_index.py` | JSON de resolução rápida de texturas |
| 3. Importar no Blender | `03_orc_import_blender.py` | Malha + esqueleto + materiais |
| 4. Exportar FBX | `04_export_all_models.py` | FBX por categoria (characters/weapons/vfx/worlds) |
| 5. Asset Library | `05`–`10` | `.blend` único, catálogos, thumbnails, previews |
| 6. Ajustes finais | `11`–`15` | Versões leve/pesada, centralização, correções |

**Resultado de referência:** 2.144 `.ssg` → 113.829 arquivos; 2.337 modelos em
biblioteca (Characters / Enemies / Weapons / VFX / Props), com 0 falhas.

---

## Requisitos

- **Windows** (os scripts assumem caminhos do Windows; adapte se necessário)
- **Python 3.10+** (para a extração)
- **Blender 3.x / 4.x / 5.x** (helpers de compatibilidade; nem toda versão retestada — veja a seção acima)
- O **jogo** *RE: Operation Raccoon City* instalado

Opcional (recomendado): [ORCToolKit](https://github.com/PiMoNFeeD/ORCToolKit) (MIT),
a ferramenta GUI do PiMoNFeeD — útil para inspecionar `.ssg` manualmente.

---

## Instalação

```bash
git clone https://github.com/TheNordicBlizzard/orc-toolkit.git ORC-Toolkit
cd ORC-Toolkit
```

---

## Uso rápido (assistente interativo)

A forma mais fácil: rode o **menu** e siga as opções.

```bash
python orc_menu.py
```

> 📖 **Novo no assunto?** Veja o **[INSTALL.md](INSTALL.md)** — guia completo
> do zero, com imagens.

![Menu do assistente](docs/menu.png)

```
   1) Configurar jogo e Blender      ← detecta automaticamente
   2) Extrair o jogo                 (.ssg -> arquivos)
   3) Exportar modelos para FBX
   4) Montar a Asset Library         (.blend + pastas + miniaturas)
   5) Finalizar                      (registrar no Blender + addon)
   6) FAZER TUDO automaticamente     ← roda 2→5 de uma vez
   s) Ver o estado atual
   q) Sair
```

O menu **detecta** o jogo e o Blender sozinho, salva a configuração em
`orc_config.json` e mostra o progresso de cada etapa. Ideal para quem não quer
mexer com linha de comando.

### Compatibilidade com versões do Blender

O toolkit legado inclui helpers para **Blender 3.x, 4.x e 5.x**; esta tarefa não retestou cada versão independentemente. As diferenças entre versões
são tratadas automaticamente (ver `scripts/_compat.py`):

| Mudança entre versões | Como é tratado |
|-----------------------|----------------|
| Engine EEVEE (`BLENDER_EEVEE` vs `BLENDER_EEVEE_NEXT`) | `_compat.eevee_engine()` testa os dois |
| Transparência (`blend_method` → `surface_render_method` em 4.2+) | `_compat.set_material_alpha()` |
| `orphans_purge` (assinatura mudou) | `_compat.purge_orphans()` |
| Pasta de addons (`.../Blender/<versao>/...`) | `orc_menu.addon_dir_for()` detecta a versão |
| Normais customizadas (crash 4.1+/5.x) | `_compat.set_custom_normals()` valida antes |

> O menu detecta a versão do Blender via `blender --version` e usa os caminhos certos.

---

## Uso manual (linha de comando)

Se preferir rodar cada etapa na mão, veja **[docs/PIPELINE.pt-BR.md](docs/PIPELINE.pt-BR.md)**.
Resumo:

```bash
set GAME=<pasta do jogo>
set WORK=<pasta de trabalho>

python scripts/01_ssg_extract.py "%GAME%" "%WORK%\ssg_unpacked"
python scripts/02_build_index.py "%WORK%\ssg_unpacked" "%WORK%\_asset_index.json"
```

E assim por diante (ordem completa na documentação).

---

## Scripts

| Arquivo | Descrição |
|---------|-----------|
| `orc_menu.py` | **Assistente interativo** (menu) — recomenda-se começar por aqui |
| `scripts/_compat.py` | Camada de compatibilidade entre versões do Blender |
| `scripts/01_ssg_extract.py` | Desempacota **todos** os `.ssg` (v5/v6, zlib, retomável) |
| `scripts/01b_ssg_extract_single.py` | Desempacota **um** `.ssg` |
| `scripts/02_build_index.py` | Gera índice JSON de assets |
| `scripts/03_orc_import_blender.py` | Importador Python do mantenedor, MIT; créditos históricos preservados; helpers 3.x–5.x |
| `scripts/04_export_all_models.py` | Exporta todos os modelos p/ FBX por categoria |
| `scripts/04b_export_characters_fbx.py` | Alternativa: 1 processo Blender por personagem |
| `scripts/04c_batch_export.py` | Processa um lote de modelos (usado pelo 04) |
| `scripts/04d_import_one.py` | Importa 1 modelo e exporta FBX (usado pelo 04b) |
| `scripts/05_build_chunks.py` | Constrói a library em chunks (evita crash de memória) |
| `scripts/06_build_library.py` | Importa FBX → `.blend` da biblioteca |
| `scripts/07_merge_library.py` | Funde as partes num `.blend` único |
| `scripts/08_convert_to_collections.py` | Objetos → **collection assets** (arrasto completo) |
| `scripts/09_gen_thumbnails.py` | Gera thumbnails 320×320 |
| `scripts/10_apply_previews.py` | Aplica thumbnails como previews dos assets |
| `scripts/11_organize_catalogs.py` | Organiza em catálogos (Characters/Enemies/Props...) |
| `scripts/12_make_versions.py` | Cria versões sem-props e só-props |
| `scripts/13_fix_center_bones.py` | Centraliza modelos + ossos visíveis |
| `scripts/14_fix_degenerate_alpha.py` | Corrige alpha degenerado (transparência) |
| `scripts/15_register_library.py` | Registra a biblioteca no Blender |
| `addon/orc_asset_helper.py` | Addon: deixa os assets editáveis ao arrastar |

Configuração por variáveis de ambiente: `ORC_TEXDIR` (pasta de texturas),
`ORC_LIBDIR` (pasta da biblioteca), `ORC_BLENDER` (caminho do Blender),
`ORC_IMPORTER` (importador), `ORC_ASSET_INDEX_FILE`, `ORC_ASSET_ROOT`.

---

## Documentação

- **[docs/PIPELINE.pt-BR.md](docs/PIPELINE.pt-BR.md)** — ordem completa do pipeline, com todos os comandos
- **[docs/FORMAT.pt-BR.md](docs/FORMAT.pt-BR.md)** — o formato `.ssg` e `.edgemodel` (Hexane Engine)
- **[docs/TROUBLESHOOTING.pt-BR.md](docs/TROUBLESHOOTING.pt-BR.md)** — erros comuns e soluções

---

## Créditos

- **TheNordicBlizzard** — importador Python criado com outra IA, pipeline e automação; publicação autorizada sob MIT existente.
- **[PiMoNFeeD](https://github.com/PiMoNFeeD/ORCToolKit)** — ORCToolKit e crédito histórico de referência preservado; MIT do C# não licencia automaticamente arquivo Python distribuído separadamente.
- **Szkaradek123** — script original no fórum Xentax (do qual o de PiMoNFeeD derivou).
- Este toolkit — o pipeline de extração, biblioteca e automação.

## Licença

Os scripts deste repositório estão sob **MIT** (veja `LICENSE`).
Autoria do importador esclarecida em [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Créditos históricos e avisos de trechos realmente reutilizados permanecem; coincidência não determina direção de derivação.

**Assets do jogo:** © CAPCOM / Slant Six Games. Não redistribua. Use apenas com
a sua própria cópia do jogo, para fins pessoais/educacionais.
