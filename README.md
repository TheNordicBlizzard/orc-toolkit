# RE: Operation Raccoon City — Toolkit de Extração de Modelos

Pipeline **testado e completo** para extrair os modelos do
*Resident Evil: Operation Raccoon City* (motor **Hexane Engine**, da Slant Six Games)
e montá-los no **Blender** — incluindo esqueletos, texturas e uma **Asset Library**
navegável por categorias.

> ⚠️ **Este repositório NÃO contém assets do jogo.** Apenas scripts e documentação.
> Você precisa ter o jogo instalado para extrair seus próprios arquivos.
> Modelos/texturas são © CAPCOM / Slant Six Games — **uso pessoal apenas**.

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
- **Blender 5.0+** (para importação e biblioteca)
- O **jogo** *RE: Operation Raccoon City* instalado

Opcional (recomendado): [ORCToolKit](https://github.com/PiMoNFeeD/ORCToolKit) (MIT),
a ferramenta GUI do PiMoNFeeD — útil para inspecionar `.ssg` manualmente.

---

## Instalação

```bash
git clone <este-repo> ORC-Toolkit
cd ORC-Toolkit
```

---

## Uso passo a passo

Defina o caminho do jogo e uma pasta de trabalho:

```bash
set GAME="C:\Program Files (x86)\DODI-Repacks\Resident Evil Operation Raccoon City"
set WORK=C:\ORC-COMPLETO
```

### 1. Extrair todos os `.ssg`

```bash
python scripts/01_ssg_extract.py "%GAME%" "%WORK%\ssg_unpacked"
```

Extrai **todos** os arquivos internos, preservando os caminhos originais
(ex.: `dlc/pack1/characters/leon/models/leon.edgemodel`). É **retomável** e
registra erros em `_errors.txt` sem abortar.

### 2. Índice de assets (acelera muito o Blender)

```bash
python scripts/02_build_index.py "%WORK%\ssg_unpacked" "%WORK%\_asset_index.json"
```

### 3. Importar/exportar com o Blender

O importador (`03_orc_import_blender.py`) é o script do PiMoNFeeD (MIT),
**corrigido para o Blender 5.0**. Para exportar tudo em FBX:

```bash
"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe" ^
  --background --factory-startup --python scripts/04_export_all_models.py -- ^
  "%WORK%\ssg_unpacked" "%WORK%\fbx_models"
```

### 4. Montar a Asset Library (opcional)

Os scripts `05`–`10` constroem um único `.blend` com coleções, catálogos,
thumbnails e previews. Veja `docs/PIPELINE.md` para a ordem exata.

### 5. Instalar o addon auxiliar (Blender)

O addon `addon/orc_asset_helper.py` garante que os assets arrastados da
biblioteca venham **editáveis** (converte instâncias e torna objetos linkados
locais, para poder mover os ossos). Copie para:

```
%APPDATA%\Blender Foundation\Blender\5.0\scripts\addons\
```

E ative em *Edit ▸ Preferences ▸ Add-ons*.

---

## Scripts

| Arquivo | Descrição |
|---------|-----------|
| `scripts/01_ssg_extract.py` | Desempacota **todos** os `.ssg` (v5/v6, zlib, retomável) |
| `scripts/01b_ssg_extract_single.py` | Desempacota **um** `.ssg` |
| `scripts/02_build_index.py` | Gera índice JSON de assets |
| `scripts/03_orc_import_blender.py` | Importa `.edgemodel` no Blender (PiMoNFeeD, MIT; corrigido p/ 5.0) |
| `scripts/04_export_all_models.py` | Exporta todos os modelos p/ FBX por categoria |
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

Configuração por variáveis de ambiente: `ORC_TEXDIR` (pasta de texturas),
`ORC_LIBDIR` (pasta da biblioteca), `ORC_ASSET_INDEX_FILE`, `ORC_ASSET_ROOT`.

---

## Documentação

- **[docs/PIPELINE.md](docs/PIPELINE.md)** — ordem completa do pipeline, com todos os comandos
- **[docs/FORMAT.md](docs/FORMAT.md)** — o formato `.ssg` e `.edgemodel` (Hexane Engine)
- **[docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** — erros comuns e soluções

---

## Créditos

- **[PiMoNFeeD](https://github.com/PiMoNFeeD/ORCToolKit)** — ORCToolKit + o script de
  importação original para Blender (MIT). Base de todo o importador.
- **Szkaradek123** — script original no fórum Xentax (do qual o de PiMoNFeeD derivou).
- Este toolkit — o pipeline de extração, biblioteca e automação.

## Licença

Os scripts deste repositório estão sob **MIT** (veja `LICENSE`).
O `03_orc_import_blender.py` deriva do trabalho de PiMoNFeeD (MIT) — créditos mantidos.

**Assets do jogo:** © CAPCOM / Slant Six Games. Não redistribua. Use apenas com
a sua própria cópia do jogo, para fins pessoais/educacionais.
