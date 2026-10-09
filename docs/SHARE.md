# Promotion posts (ready to copy & paste)

Ready-to-use texts for sharing the toolkit. Just copy and post.

**Repo:** https://github.com/TheNordicBlizzard/orc-toolkit

---

## 📌 Forum post (RE Modding Boards / Xentax / Reddit)

**Title:**
```
[Tool] RE: Operation Raccoon City — one-click extraction toolkit (menu, Blender 3.x-5.x)
```

**Body:**

```markdown
Hey everyone,

I put together a toolkit to extract the models from **RE: Operation Raccoon City**
(Hexane Engine / Slant Six) and get them into Blender with as little hassle as
possible. It wraps the whole pipeline in a **simple interactive menu** — no need
to type commands.

## What it does

- Unpacks **all** `.ssg` archives (v5/v6, zlib) → ~113k files, 0 failures
- Imports `.edgemodel` (mesh + skeleton + materials) into Blender
- Exports everything to **FBX**, sorted by category
- Builds a single **Asset Library `.blend`** with folders (Characters / Enemies /
  Weapons / VFX / Props), thumbnails and previews
- Bundles an addon so dragged assets come in **editable** (move the bones!)

## Features

- 🖱️ **Interactive menu** (`python orc_menu.py`) — auto-detects your game and Blender
- 🔄 **Works on Blender 3.x, 4.x and 5.x** (handles the version differences for you)
- 📦 Extracts 2,144 `.ssg` → 113,829 files, **0 failures**
- 🗂️ Organizes 2,337 models into a browsable Asset Library
- 🧩 Handles the known crashes (bad normals, degenerate alpha, memory limits)

## What's included

Only **scripts and docs** — no game assets. You extract from **your own copy** of
the game. (Assets are © CAPCOM / Slant Six.)

## Requirements

- Windows, Python 3.10+, Blender 3.x/4.x/5.x, and the game installed

## Get it

```
https://github.com/TheNordicBlizzard/orc-toolkit
```

Run `python orc_menu.py` and follow the menu. Full walkthrough in `INSTALL.md`.

## Credits

Built on **PiMoNFeeD's** ORCToolKit and his original Blender import script (MIT),
plus Szkaradek123's original work. Huge thanks to them.

Feedback and pull requests welcome!
```

---

## 📌 Short post for Discord

```markdown
**RE: Operation Raccoon City — extraction toolkit** 🧟

Made a toolkit to rip the models from ORC and get them into Blender painlessly —
it's all wrapped in a **simple menu**, no command-line needed.

✅ Unpacks all `.ssg` → 113k files, 0 failures
✅ Exports everything to FBX
✅ Builds a browsable Asset Library `.blend` (Characters/Enemies/Weapons/VFX/Props)
✅ Works on **Blender 3.x, 4.x and 5.x**
✅ No game assets included — you use your own copy

🔗 https://github.com/TheNordicBlizzard/orc-toolkit
▶️ Just run `python orc_menu.py`

Built on PiMoNFeeD's ORCToolKit (MIT). Feedback welcome!
```

---

## 📌 Full post for Discord (mentions audio, video, data, etc.)

```markdown
**RE: Operation Raccoon City — complete extraction toolkit** 🧟🎬🎵

Hey all! I built a toolkit that rips **everything** out of ORC and gets the
models into Blender — all wrapped in a **simple interactive menu**, no
command-line needed.

## 🎮 What it unpacks

It extracts **all 2,144 `.ssg` archives** → **136,377 files (~13 GB)**, 0 failures.
Nothing is filtered — you get the whole game:

| Category | Files | Size | Contents |
|----------|------:|-----:|----------|
| 🧍 **Models** | 22,800 | 1.7 GB | `.edgemodel` (characters, weapons, props) |
| 🎨 **Textures** | 40,783 | 5.7 GB | `.dds` |
| 🧩 **Materials** | 22,014 | 7 MB | `.matb` |
| 🦴 **Skeletons/Anims** | 22,414 | 727 MB | rigs + animations |
| 🎵 **Audio** | 387 | **1.5 GB** | Wwise `.bnk` soundbanks |
| 🎬 **Video** | 104 | **1.6 GB** | 48 `.bik` cutscenes + `.fm` |
| 📊 **Data/Text** | 1,661 | 38 MB | `.csv`, `.lua` scripts, `.msb`, `.tbin` |
| 🖼️ **UI** | 247 | 56 MB | `.swb2`, `.vgoth`, `.mui` |

## 🎵 Audio — 6 dubbed languages

Full voice acting included: **English, French, German, Italian, Japanese, Spanish**
(character dialogue, music, ambience — e.g. `Heroes_Dialog.bnk`, `Nemesis.bnk`, `Music.bnk`).

## 🎬 Video

48 high-quality Bink cutscenes (`USS01_FMV01.bik`, `SPEC01_FMV01.bik`, ...).

## 🧍 Into Blender

- Imports `.edgemodel` (mesh + skeleton + materials)
- Exports everything to **FBX**, sorted by category
- Builds a browsable **Asset Library `.blend`**
  (Characters / Enemies / Weapons / VFX / Props) with thumbnails
- Helper addon so dragged assets come in **editable** (move the bones!)

## ✨ Features

- 🖱️ **Interactive menu** (`python orc_menu.py`) — auto-detects game + Blender
- 🔄 **Works on Blender 3.x, 4.x and 5.x**
- 🧩 Handles the known crashes (bad normals, degenerate alpha, memory limits)

## 📦 What's included

Only **scripts and docs** — **no game assets**. You extract from **your own copy**
of the game. (Assets are © CAPCOM / Slant Six.)

## 🔗 Get it

https://github.com/TheNordicBlizzard/orc-toolkit
▶️ Run `python orc_menu.py` and follow the menu.

Built on PiMoNFeeD's ORCToolKit (MIT). Feedback & PRs welcome!
```

---

## 📌 Reply (when someone asks "where are the models?")

```markdown
The repo intentionally ships **no game assets** — only the extraction code.
You run it against your own installed copy of the game and it pulls the models
out for you. That keeps it clean legally (assets are CAPCOM's) and it's the same
approach PiMoNFeeD took with ORCToolKit. 👍
```

---

## 📌 Repository description (GitHub "About")

```
One-click toolkit to extract RE: Operation Raccoon City models into Blender —
interactive menu, FBX export, browsable Asset Library. Blender 3.x-5.x. No game assets included.
```

**Topics/tags:** `resident-evil` `operation-raccoon-city` `blender` `modding` `asset-extraction` `hexane-engine` `fbx` `game-ripping`

---

## 📌 Release announcement (v1.0)

```markdown
**v1.0 — first public release** 🎉

Extract RE: Operation Raccoon City models into Blender with one interactive menu.

- 🖱️ Menu-based workflow (`python orc_menu.py`) — auto-detects game + Blender
- 🔄 Compatible with Blender 3.x / 4.x / 5.x
- 📦 2,144 `.ssg` → 113,829 files, 0 failures
- 🗂️ 2,337 models organized into a browsable Asset Library
  (Characters / Enemies / Weapons / VFX / Props)
- 🧩 Robust against the known crashes (normals, alpha, memory)

Download the zip below (code only — no game assets).
```
