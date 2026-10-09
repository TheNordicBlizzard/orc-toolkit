# Installation & Usage Guide — step by step

A complete guide for first-time users. From zero to models in Blender.

> **Before anything:** this toolkit includes **no game models**. You extract from
> **your own copy** of *RE: Operation Raccoon City*. Assets © CAPCOM/Slant Six.

**Languages:** English (this file) · [Português (BR)](INSTALL.pt-BR.md)

---

## 1. What you need

| Requirement | Where to get it |
|-------------|-----------------|
| **Python 3.10+** | [python.org](https://www.python.org/downloads/) — check *"Add to PATH"* |
| **Blender 3.x / 4.x / 5.x** | [blender.org](https://www.blender.org/download/) |
| **The game installed** | Steam or another store |

> You only need Python to **extract** the files. Everything else is Blender.

---

## 2. Download the toolkit

- **Option A (git):**
  ```bash
  git clone https://github.com/TheNordicBlizzard/orc-toolkit.git
  cd orc-toolkit
  ```
- **Option B (zip):** download `ORC-Toolkit.zip` and extract it to a folder, e.g. `C:\ORC-Toolkit`.

---

## 3. Run the assistant

Open a terminal (**Command Prompt** or **PowerShell**) in the toolkit folder and run:

```bash
python orc_menu.py
```

You'll see the menu:

![Assistant menu](docs/menu.png)

> On **Windows**, if you get "python is not recognized", use `py orc_menu.py`.

---

## 4. Step by step in the menu

### ➤ Option 1 — Configure

The assistant **auto-detects** the game and Blender. If it can't find them:

- **Game folder:** paste the full path (e.g. `C:\Program Files (x86)\Steam\steamapps\common\Resident Evil Operation Raccoon City`)
- **Blender:** paste the path to `blender.exe` (e.g. `C:\Program Files\Blender Foundation\Blender 5.0\blender.exe`)
- **Work folder:** where everything will be saved (default `C:\ORC-COMPLETO`)

The config is saved to `orc_config.json` — next time it's already filled in.

### ➤ Option 2 — Extract the game

Unpacks **all** `.ssg` files (~113,000 files). Takes ~5–10 minutes.
The assistant also builds an index that speeds up the following steps.

**Result:** an `ssg_unpacked/` folder with the entire game content.

### ➤ Option 3 — Export to FBX

Imports each model and exports it to FBX, sorted by category
(`characters/`, `weapons/`, `vfx/`, `worlds/`). **Takes ~1 hour.**

**Result:** an `fbx_models/` folder.

> 💡 If you only want the **characters**, you can stop here — the FBX files are
> already usable in any program (Blender, 3ds Max, Unity, Unreal...).

### ➤ Option 4 — Build the Asset Library

Creates **a single `.blend`** with all models organized into folders
(Characters, Enemies, Weapons, VFX, Props), with thumbnails and previews.
**Takes ~1 hour.**

**Result:** an `ORC-Asset-Library/` folder with `ORC_AssetLibrary.blend`.

### ➤ Option 5 — Finish

- **Registers** the library in Blender (shows up in the Asset Browser)
- **Installs** the helper addon (makes assets editable when dragged)

### ➤ Option 6 — DO EVERYTHING

Runs options 2→5 in sequence, without stopping. Leave the PC on and go do something else.

---

## 5. Using it in Blender

1. Open Blender.
2. Create a workspace with the **Asset Browser**:
   *File ▸ New ▸ RE Assets* (if the RE addon is installed) **or**
   Editor Type ▸ **Asset Browser**.
3. In the library selector (top), choose **"ORC Assets"**.
4. Browse the folders: **Characters**, **Enemies**, **Weapons**, **VFX**, **Props**.
5. **Drag** the model into the scene.

> ⚠️ **Drag the COLLECTION** (folder icon), not a loose object — that way the
> mesh + skeleton + materials come together.

### Moving the bones (pose/animation)

1. Select the model's **Armature**.
2. `Ctrl+Tab` → **Pose Mode**.
3. Click a bone and rotate it (`R`).

The helper addon makes sure the model comes in **editable** (not locked). If it
somehow comes in locked, use the **"Tornar Assets ORC Editáveis"** button in the
**ORC** tab of the sidebar (`N`).

---

## 6. Common issues

| Symptom | Fix |
|---------|-----|
| `python` not recognized | Use `py orc_menu.py` or reinstall Python with "Add to PATH" |
| Game not detected | Configure it manually (option 1) and paste the path |
| Blender not found | Configure it manually (option 1) |
| Assets don't show in Blender | Click the **⟳** in the Asset Browser or restart Blender |
| Model comes in locked (read-only) | Run option 5 (installs the addon) or `Object ▸ Relations ▸ Make Local` |
| Dragging brings an empty | Drag the **collection** (folder), not the object |
| Blender crashes opening the library | Close other programs (the library uses ~4 GB RAM) |

More details in **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)**.

---

## 7. Compatibility

Works on **Blender 3.x, 4.x and 5.x** — version differences are handled
automatically by the toolkit. Just point to your `blender.exe` in option 1.

---

## Legal notice

This toolkit is **code and documentation only**. The models, textures, and other
assets of *RE: Operation Raccoon City* are © **CAPCOM / Slant Six Games**.
Use with your own copy of the game, for **personal/educational** purposes.
**Do not redistribute** the extracted assets.
