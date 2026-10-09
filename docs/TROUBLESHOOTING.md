# Solução de problemas

## Extração

**`.ssg` falha com `zlib.error`**
Arquivos grandes (level chunks) têm um pequeno bloco não-zlib entre blocos
comprimidos. O `01_ssg_extract.py` já trata: no erro, procura o próximo header
zlib válido (`78 01/5e/9c/da`) e retoma. Se ainda falhar, veja `_errors.txt`.

**Cutscenes saem corrompidas**
Cutscenes (NIS) misturam seções comprimidas e não-comprimidas. A versão atual
calcula o offset correto — atualize o script.

## Blender / Importação

**`EXCEPTION_ACCESS_VIOLATION` ao importar um modelo**
Crash nativo (não capturável por try/except). Causa: normais de comprimento
zero/NaN. O importador sanitiza — se persistir, o modelo é LOD shadow; pule-o.

**Blender crasha ao abrir o `.blend` da biblioteca**
**Pressão de RAM.** A library carrega ~28.000 imagens (~4 GB). Feche outros
Blenders/programas pesados. A abertura é intermitente: com a máquina livre, abre normal.

**"Cannot edit library linked or non-editable override object"**
O asset veio como **LINK** (read-only). Soluções:
- No Asset Browser: **Import Method = Append** (Preferences ▸ File Paths ▸ Asset Libraries)
- Ou: `Object ▸ Relations ▸ Make Local ▸ All`
- O addon `orc_asset_helper` faz isso automaticamente.

**Arrastar um asset traz só um Empty (sem malha/ossos)**
Você está arrastando um **object asset** ou uma **instância**. Use **collection
assets** (o build já converte). Ou desmarque **Instance** no cabeçalho do Asset
Browser antes de arrastar.

**Ossos não se movem / não dá para clicar neles**
1. Entre em **Pose Mode** (selecione a Armature → `Ctrl+Tab`).
2. Os ossos precisam estar **na frente** da malha: `armature.show_in_front = True`
   (o `13_fix_center_bones.py` faz isso).

**Modelo aparece longe do centro / flutuando**
A armadura vem deslocada pela engine. `13_fix_center_bones.py` centraliza
(X/Y no centro, base em Z=0).

**Corpo/cabelo transparente**
Textura DXT5 com alpha degenerado (todo 0 ou todo 255). `14_fix_degenerate_alpha.py`
força alpha a 255 mantendo a cor.

## Asset Library

**Os assets não aparecem no Asset Browser**
- Confirme a biblioteca em *Preferences ▸ File Paths ▸ Asset Libraries*.
- Clique no ícone **⟳** (atualizar) no cabeçalho do Asset Browser.
- Reinicie o Blender.

**Assets aparecem duplicados**
Você tem mais de um `.blend` na mesma pasta de biblioteca. Ponha cada versão em
sua **própria subpasta** com seu próprio `blender_assets.cats.txt`.

**As pastas (catálogos) aparecem vazias**
O `blender_assets.cats.txt` precisa estar **ao lado** do `.blend`, e os
`catalog_id` dos assets precisam existir nele. Veja `11_organize_catalogs.py`.

**As texturas somem ao mover o `.blend`**
Os caminhos são **relativos** (`//ORC_textures/...`). Mova o `.blend` **junto**
com a pasta `ORC_textures`. Ou `File ▸ External Data ▸ Find Missing Files`.

## Performance

**O build da library crasha por volta de 1000 modelos**
Não construa num processo único. Use chunks (`05_build_chunks.py`) com split-recursivo.

**Cada processo Blender demora muito para iniciar**
Falta o índice de assets. Rode `02_build_index.py` e defina `ORC_ASSET_INDEX_FILE`.
