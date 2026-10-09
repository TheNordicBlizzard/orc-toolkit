# Guia de Instalação e Uso — passo a passo

Guia completo para quem nunca usou o toolkit. Do zero até os modelos no Blender.

> **Antes de tudo:** este toolkit **não inclui** nenhum modelo do jogo. Você extrai
> da **sua própria cópia** de *RE: Operation Raccoon City*. Assets © CAPCOM/Slant Six.

---

## 1. O que você precisa

| Requisito | Onde conseguir |
|-----------|----------------|
| **Python 3.10+** | [python.org](https://www.python.org/downloads/) — marque *"Add to PATH"* |
| **Blender 3.x / 4.x / 5.x** | [blender.org](https://www.blender.org/download/) |
| **O jogo instalado** | Steam ou outra loja |

> Só precisa de Python para **extrair** os arquivos. O resto é Blender.

---

## 2. Baixar o toolkit

- **Opção A (git):**
  ```bash
  git clone https://github.com/SEU_USUARIO/orc-toolkit.git
  cd orc-toolkit
  ```
- **Opção B (zip):** baixe o `ORC-Toolkit.zip` e extraia numa pasta, ex.: `C:\ORC-Toolkit`.

---

## 3. Rodar o assistente

Abra um terminal (**Prompt de Comando** ou **PowerShell**) na pasta do toolkit e rode:

```bash
python orc_menu.py
```

Você verá o menu:

![Menu do assistente](menu.png)

> No **Windows**, se der erro de "python não reconhecido", use `py orc_menu.py`.

---

## 4. Passo a passo no menu

### ➤ Opção 1 — Configurar

O assistente **detecta automaticamente** o jogo e o Blender. Se não achar:

- **Pasta do jogo:** cole o caminho completo (ex.: `C:\Program Files (x86)\Steam\steamapps\common\Resident Evil Operation Raccoon City`)
- **Blender:** cole o caminho do `blender.exe` (ex.: `C:\Program Files\Blender Foundation\Blender 5.0\blender.exe`)
- **Pasta de trabalho:** onde tudo será salvo (padrão `C:\ORC-COMPLETO`)

A configuração fica salva em `orc_config.json` — da próxima vez já vem preenchida.

### ➤ Opção 2 — Extrair o jogo

Desempacota **todos** os `.ssg` do jogo (~113.000 arquivos). Leva ~5–10 minutos.
O assistente também constrói um índice que acelera bastante as etapas seguintes.

**Resultado:** pasta `ssg_unpacked/` com todo o conteúdo do jogo.

### ➤ Opção 3 — Exportar para FBX

Importa cada modelo e exporta em FBX, separado por categoria
(`characters/`, `weapons/`, `vfx/`, `worlds/`). **Demora ~1 hora.**

**Resultado:** pasta `fbx_models/`.

> 💡 Se você só quer os **personagens**, pode parar aqui — os FBX já são usáveis
> em qualquer programa (Blender, 3ds Max, Unity, Unreal...).

### ➤ Opção 4 — Montar a Asset Library

Cria **um único arquivo `.blend`** com todos os modelos organizados em pastas
(Characters, Enemies, Weapons, VFX, Props), com miniaturas e previews.
**Demora ~1 hora.**

**Resultado:** pasta `ORC-Asset-Library/` com `ORC_AssetLibrary.blend`.

### ➤ Opção 5 — Finalizar

- **Registra** a biblioteca no Blender (aparece no Asset Browser)
- **Instala** o addon auxiliar (deixa os assets editáveis ao arrastar)

### ➤ Opção 6 — FAZER TUDO

Roda as opções 2→5 em sequência, sem parar. Deixe o PC ligado e vá fazer outra coisa.

---

## 5. Usar no Blender

1. Abra o Blender.
2. Crie um workspace com o **Asset Browser**:
   *File ▸ New ▸ RE Assets* (se o addon RE estiver instalado) **ou**
   Editor Type ▸ **Asset Browser**.
3. No seletor de biblioteca (topo), escolha **"ORC Assets"**.
4. Navegue pelas pastas: **Characters**, **Enemies**, **Weapons**, **VFX**, **Props**.
5. **Arraste** o modelo para a cena.

> ⚠️ **Arraste a COLEÇÃO** (ícone de pasta), não um objeto solto — assim vem
> malha + esqueleto + materiais juntos.

### Mexer nos ossos (pose/animação)

1. Selecione a **Armature** do modelo.
2. `Ctrl+Tab` → **Pose Mode**.
3. Clique num osso e gire (`R`).

O addon auxiliar garante que o modelo venha **editável** (não travado). Se por
algum motivo vier travado, use o botão **"Tornar Assets ORC Editáveis"** na aba
**ORC** da barra lateral (`N`).

---

## 6. Problemas comuns

| Sintoma | Solução |
|---------|---------|
| `python` não reconhecido | Use `py orc_menu.py` ou reinstale o Python marcando "Add to PATH" |
| Jogo não detectado | Configure manualmente (opção 1) e cole o caminho |
| Blender não encontrado | Configure manualmente (opção 1) |
| Assets não aparecem no Blender | Clique no **⟳** do Asset Browser ou reinicie o Blender |
| Modelo vem travado (read-only) | Rode a opção 5 (instala o addon) ou `Object ▸ Relations ▸ Make Local` |
| Arrastar traz só um vazio | Arraste a **coleção** (pasta), não o objeto |
| Blender trava ao abrir a library | Feche outros programas (a library usa ~4 GB de RAM) |

Mais detalhes em **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)**.

---

## 7. Compatibilidade

Funciona em **Blender 3.x, 4.x e 5.x** — as diferenças entre versões são tratadas
automaticamente pelo toolkit. Basta apontar o caminho do seu `blender.exe` na opção 1.

---

## Aviso legal

Este toolkit é **apenas código e documentação**. Os modelos, texturas e demais
assets de *RE: Operation Raccoon City* são © **CAPCOM / Slant Six Games**.
Use com a sua própria cópia do jogo, para fins **pessoais/educacionais**.
**Não redistribua** os assets extraídos.
