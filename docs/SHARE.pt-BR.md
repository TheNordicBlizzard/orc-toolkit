# Posts de divulgação (prontos para copiar e colar)

Textos prontos para compartilhar o toolkit. É só copiar e postar.

**Repo:** https://github.com/TheNordicBlizzard/orc-toolkit
**Release:** https://github.com/TheNordicBlizzard/orc-toolkit/releases/tag/v1.0

---

## 📌 Post para fórum (RE Modding Boards BR / grupos de modding)

**Título:**
```
[Ferramenta] RE: Operation Raccoon City — extração de modelos em 1 clique (menu, Blender 3.x-5.x)
```

**Corpo:**

```markdown
Olá, pessoal!

Fiz um toolkit para extrair os modelos do **RE: Operation Raccoon City**
(Hexane Engine / Slant Six) e levá-los para o Blender do jeito mais fácil possível.
Ele embrulha todo o processo num **menu interativo simples** — sem precisar digitar
comandos.

## O que ele faz

- Desempacota **todos** os `.ssg` (v5/v6, zlib) → ~113 mil arquivos, 0 falhas
- Importa os `.edgemodel` (malha + esqueleto + materiais) no Blender
- Exporta tudo para **FBX**, separado por categoria
- Monta uma **Asset Library `.blend`** única com pastas (Characters / Enemies /
  Weapons / VFX / Props), miniaturas e previews
- Inclui um addon para os assets virem **editáveis** ao arrastar (dá pra mexer nos ossos!)

## Destaques

- 🖱️ **Menu interativo** (`python orc_menu.py`) — detecta o jogo e o Blender sozinho
- 🔄 **Funciona no Blender 3.x, 4.x e 5.x** (resolve as diferenças entre versões)
- 📦 Extrai 2.144 `.ssg` → 113.829 arquivos, **0 falhas**
- 🗂️ Organiza 2.337 modelos numa Asset Library navegável por pastas
- 🧩 Lida com os travamentos conhecidos (normais inválidas, alpha degenerado, memória)

## O que está incluído

Apenas **scripts e documentação** — nenhum asset do jogo. Você extrai da **sua própria
cópia** do jogo. (Assets são © CAPCOM / Slant Six.)

## Requisitos

- Windows, Python 3.10+, Blender 3.x/4.x/5.x, e o jogo instalado

## Como pegar

```
https://github.com/TheNordicBlizzard/orc-toolkit
```

Rode `python orc_menu.py` e siga o menu. Passo a passo completo no `INSTALL.pt-BR.md`.

## Créditos

Baseado no **ORCToolKit do PiMoNFeeD** e no script de importação original dele (MIT),
além do trabalho original do Szkaradek123. Muito obrigado a eles.

Feedback e pull requests são bem-vindos!
```

---

## 📌 Post curto para Discord

```markdown
**RE: Operation Raccoon City — toolkit de extração** 🧟

Fiz um toolkit pra extrair os modelos do ORC e levar pro Blender sem dor de cabeça —
tudo num **menu simples**, sem linha de comando.

✅ Desempacota todos os `.ssg` → 113 mil arquivos, 0 falhas
✅ Exporta tudo pra FBX
✅ Monta uma Asset Library `.blend` navegável (Characters/Enemies/Weapons/VFX/Props)
✅ Funciona no **Blender 3.x, 4.x e 5.x**
✅ Sem assets do jogo — você usa a sua própria cópia

🔗 https://github.com/TheNordicBlizzard/orc-toolkit
▶️ É só rodar `python orc_menu.py`

Baseado no ORCToolKit do PiMoNFeeD (MIT). Feedback bem-vindo!
```

---

## 📌 Resposta (quando perguntarem "cadê os modelos?")

```markdown
O repositório propositalmente **não inclui assets do jogo** — só o código de extração.
Você roda contra a sua própria cópia instalada do jogo e ele tira os modelos pra você.
Isso mantém tudo limpo legalmente (os assets são da CAPCOM) e é a mesma abordagem que
o PiMoNFeeD usou com o ORCToolKit. 👍
```

---

## 📌 Anúncio do Release (v1.0)

```markdown
**v1.0 — primeiro lançamento público** 🎉

Extraia os modelos do RE: Operation Raccoon City para o Blender com um menu interativo.

- 🖱️ Fluxo por menu (`python orc_menu.py`) — detecta jogo e Blender sozinho
- 🔄 Compatível com Blender 3.x / 4.x / 5.x
- 📦 2.144 `.ssg` → 113.829 arquivos, 0 falhas
- 🗂️ 2.337 modelos organizados numa Asset Library navegável
  (Characters / Enemies / Weapons / VFX / Props)
- 🧩 Robusto contra os travamentos conhecidos (normais, alpha, memória)

Baixe o zip abaixo (só código — sem assets do jogo).
```

---

## 📌 Dica para comunidades BR

- **Grupos de modding no WhatsApp/Telegram/Discord BR**: use o post curto.
- **Fóruns e Reddit (r/REBrasil, etc.)**: use o post completo.
- Sempre cite os **créditos ao PiMoNFeeD** — a comunidade valoriza e evita mal-entendidos.
- Deixe claro que **não há assets**: evita perguntas e problemas legais.
