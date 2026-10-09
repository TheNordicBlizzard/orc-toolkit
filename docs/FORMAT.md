# Formato de arquivos — Hexane Engine (RE: Operation Raccoon City)

O jogo **não** usa Unreal Engine. Usa a **Hexane Engine** (Slant Six Games),
DirectX 9 + Havok 7.0.

## `.ssg` — container

Arquivo de arquivo (archive) que empacota quase todo o conteúdo do jogo.

**Header (32 bytes):**

| Offset | Campo | Descrição |
|--------|-------|-----------|
| 0 | `version` | u32 LE. Se `> 0xFFFF` → arquivo é **big-endian** |
| 4 | `pad1` | |
| 8 | `secInfosSize` | tamanho da tabela de seções |
| 12 | `secNamesSize` | tamanho dos nomes |
| 16 | `secDataSize` | tamanho dos dados |
| 20 | `pad2` | |
| 24 | `compBlocksSize` | tamanho da tabela de blocos comprimidos |
| 28 | `alignment` | u16 (alinhamento das seções) |
| 30 | `pad3` | u16 |

**Section info (32 bytes cada):**

```
nameCRC32, nameOffset, uncompSize, unk(=1), dataOffset, type, uncompCRC32, compSize
```

**Dados:**
- Comprimidos em **zlib, blocos de 64 KB** de saída.
- `compBlocksSize` = tamanho da tabela de tamanhos de bloco (u32 cada, terminada em 0).
- Seções com `compSize != 0` são comprimidas (valor **negativo** = compartilha o
  bloco com a anterior).
- **Layout:** `[seções não-comprimidas][blocos comprimidos]`. O início dos blocos
  comprimidos = `data_off + soma(align(uncompSize))` de **todas** as seções
  não-comprimidas (o `dataOffset` das comprimidas é lixo).
- **Cutscenes (NIS)** misturam seções comprimidas e não-comprimidas — o cálculo acima resolve.
- **Gap de padding:** arquivos grandes (level chunks) têm um pequeno bloco não-zlib
  (ex.: 128 bytes) entre blocos comprimidos, dessincronizando o passo fixo.
  Solução no `01_ssg_extract.py`: no `zlib.error`, procurar o próximo header zlib
  válido (`78 01/5e/9c/da`) e retomar dali.

## `.edgemodel` — malha

- Magic **`FM6S`** = malha real (versão `0x12`).
- Magic **`IM6S`** (versão 2) = **apenas metadados** de modelo — NÃO é malha. Filtre!
- Contém LODs 0..4 e submeshes. Versões de malha suportadas: `0x11` (17), `0x12` (18).
  `0x0f` (15) só aparece em meshes shadow/LOD1 — pule.

## Outros

| Extensão | Conteúdo |
|----------|----------|
| `.matb` | material (magic `MAT`), referencia texturas por caminho relativo |
| `.dds` | texturas (DXT1/DXT5) |
| `.hkx` | física Havok (pode ignorar para modelos) |
| *(sem ext.)* | esqueleto (magic `ES02`/`20SE`) ou animação (magic `40AE`/`EA04`) |

## Estrutura de pastas do jogo

```
dlc/packN/Characters/<nome>/models/<nome>.edgemodel
dlc/packN/Characters/<nome>/materials/*.matb
dlc/packN/Characters/<nome>/textures/*.dds
Characters/skel/<nome>          (esqueleto, sem extensão)
Animation/Projects/*.anims.ssg  (animações)
```

O importador precisa do **modelo + esqueleto com o mesmo nome** (sem extensão)
**ao lado**, e da árvore `dlc/...` preservada para resolver os materiais.

## Pitfalls de importação (crash)

- **`EXCEPTION_ACCESS_VIOLATION`** ao importar: causado por (a) malhas stride-12
  "shadow" sem normais, ou (b) vértices com normal de comprimento zero/NaN passados
  a `normals_split_custom_set_from_vertices` (Blender 4.1+/5.x). Corrija sanitizando
  as normais (zeros/NaN → `(0,0,1)`) e só chame a função se **todas** forem válidas.
  **Isso NÃO é capturável com try/except** — é crash nativo.
- **Import de FBX com textura empacotada** relê o DDS e crasha (OpenImageIO). Use
  `use_image_search=False` no import.
