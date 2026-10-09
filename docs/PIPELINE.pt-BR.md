# Pipeline completo (ordem exata)

Todos os comandos assumem:
```bash
set GAME=<pasta do jogo>
set WORK=<pasta de trabalho>
set BLENDER="C:\Program Files\Blender Foundation\Blender 5.0\blender.exe"
```

---

## Fase A — Extração (Python puro)

### A1. Desempacotar todos os `.ssg`
```bash
python scripts/01_ssg_extract.py "%GAME%" "%WORK%\ssg_unpacked"
```
→ 2.144 arquivos `.ssg` → ~113.829 arquivos (preserva caminhos internos).
Retomável: re-executar pula o que já foi feito (`_done.txt`).

### A2. Índice de assets (essencial p/ performance)
```bash
python scripts/02_build_index.py "%WORK%\ssg_unpacked" "%WORK%\_asset_index.json"
```
Gera um JSON `nome → caminho absoluto`. Sem ele, cada processo Blender re-varre
113k arquivos (~40 s cada).

### A3. (Opcional) coletar arquivos soltos por categoria
Organize `ssg_unpacked` em `loose/` (models, textures, materials, skeletons...) —
veja `build_final.py` no histórico do projeto se precisar.

---

## Fase B — Exportação em FBX

### B1. Manifesto de modelos
Liste todos os `.edgemodel` com magic `FM6S` (filtrando os `IM6S`):
```
formato: [[caminho_fbx, "categoria/nome"], ...]
categorias: characters / weapons / vfx / worlds
```

### B2. Exportar
```bash
"%BLENDER%" --background --factory-startup --python scripts/04_export_all_models.py -- ^
  "%WORK%\_all_manifest.json" "%WORK%\fbx_models"
```
Roda **um processo Blender por lote** com **split-retry** (isola modelos que travam).

Variáveis de ambiente úteis:
```
ORC_ASSET_INDEX_FILE=%WORK%\_asset_index.json
ORC_ASSET_ROOT=%WORK%\ssg_unpacked
```

---

## Fase C — Asset Library (Blender)

### C1. Construir em chunks (evita crash de memória)
```bash
"%BLENDER%" --background --factory-startup --python scripts/05_build_chunks.py -- ^
  "%WORK%\_all_manifest.json" "%WORK%\_chunks" 300
```
> Um único processo com 2.347 FBX crasha (~1000 modelos). Chunks de 300 resolvem.
> `05_build_chunks.py` tem **split recursivo**: um chunk que falha é dividido e
> re-tentado, isolando o modelo ruim.

### C2. Fundir num `.blend` único
```bash
"%BLENDER%" --background --factory-startup --python scripts/07_merge_library.py -- ^
  "%WORK%\_chunks" "%WORK%\ORC_AssetLibrary.blend"
```
Classifica cada objeto pela **cadeia de parentesco** (malha → armature → holder)
usando o mapa `nome → categoria` do manifesto.

### C3. Converter em *collection assets*
```bash
"%BLENDER%" --background --factory-startup --python scripts/08_convert_to_collections.py -- ^
  "%WORK%\ORC_AssetLibrary.blend" "%WORK%\thumbnails"
```
> **Crítico:** cada modelo vira uma **Collection** marcada como asset. Se usar
> *object assets* (o Empty holder), arrastar traz **só o Empty**, sem a malha.

### C4. Thumbnails + previews
```bash
"%BLENDER%" --background --factory-startup --python scripts/09_gen_thumbnails.py -- ^
  "%WORK%\_all_manifest.json" "%WORK%\thumbnails"

"%BLENDER%" --background --factory-startup --python scripts/10_apply_previews.py -- ^
  "%WORK%\ORC_AssetLibrary.blend" "%WORK%\thumbnails"
```

### C5. Catálogos (pastas)
```bash
"%BLENDER%" --background --factory-startup --python scripts/11_organize_catalogs.py -- ^
  "%WORK%\ORC-Asset-Library"
```
Classifica em Characters / Enemies / Weapons / VFX / Props (+ subpastas) e
escreve `blender_assets.cats.txt`.

---

## Fase D — Ajustes finais

### D1. Centralizar + ossos visíveis
```bash
"%BLENDER%" --background --factory-startup --python scripts/13_fix_center_bones.py -- ^
  "%WORK%\ORC-Asset-Library\ORC_AssetLibrary.blend"
```

### D2. Versões leve / só-props (opcional)
```bash
"%BLENDER%" --background --factory-startup --python scripts/12_make_versions.py -- ^
  "%WORK%\ORC-Asset-Library"
```

### D3. Registrar a biblioteca no Blender
```bash
"%BLENDER%" --background --python scripts/15_register_library.py -- ^
  "ORC Assets" "%WORK%\ORC-Asset-Library"
```

### D4. Addon auxiliar
Copie `addon/orc_asset_helper.py` para a pasta de addons do Blender e ative.

---

## Estrutura final esperada

```
%WORK%\
├── ssg_unpacked\              (113k arquivos)
├── _asset_index.json
├── fbx_models\                (FBX por categoria)
├── _chunks\                   (partes intermediárias)
├── thumbnails\                (2.337 JPG 320×320)
└── ORC-Asset-Library\
    ├── ORC_AssetLibrary.blend
    ├── ORC_textures\          (PNG externalizadas)
    ├── thumbnails\
    └── blender_assets.cats.txt
```

## Performance (referência, i5 + 16 GB RAM)

| Etapa | Tempo |
|-------|-------|
| Extração dos `.ssg` | ~6 min |
| Export FBX (todos os modelos) | ~1 h |
| Build da library (chunks) | ~35 min |
| Merge | ~17 min |
| Thumbnails | ~20 min |
| Previews | ~5 min |
