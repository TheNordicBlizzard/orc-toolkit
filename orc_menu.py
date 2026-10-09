#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RE: Operation Raccoon City — Extraction Assistant (interactive menu)

A simple menu that configures your game path, detects Blender, and runs each
pipeline step for you — no commands to type.

Usage:
    python orc_menu.py

Progress is saved to orc_config.json (next to this script), so your paths are
remembered next time. Bilingual: English (default) / Portuguese.
"""
import os
import sys
import json
import shutil
import subprocess
import time

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, "scripts")
CONFIG_PATH = os.path.join(HERE, "orc_config.json")

# ------------------------------------------------------------------ i18n

LANG = os.environ.get("ORC_LANG", "").lower()

T = {
    "en": {
        "subtitle": "Extraction Assistant — Resident Evil: Operation Raccoon City",
        "subtitle2": "(extract the models from YOUR game into Blender)",
        "game": "Game:   ", "blender": "Blender:", "folder": "Folder: ",
        "ok_cfg": "OK", "no_cfg": "not configured", "no_bl": "not found",
        "m1": "Configure game and Blender",
        "m2": "Extract the game            (.ssg -> files)",
        "m3": "Export models to FBX",
        "m4": "Build the Asset Library     (.blend + folders + thumbnails)",
        "m5": "Finish                       (register in Blender + addon)",
        "m6": "DO EVERYTHING automatically",
        "ms": "Show current status",
        "mq": "Quit",
        "choose": "Choose an option: ",
        "invalid": "invalid option.",
        "bye": "Bye!  Game assets are (c) CAPCOM/Slant Six — personal use only.",
        "press_enter": "Press ENTER to return to the menu...",
        "continue": "Continue? (y/N)",
        # config
        "t_cfg": "1. CONFIGURATION",
        "cfg_intro": "Let's locate the game and Blender.",
        "ask_game": "Game folder (ENTER to auto-detect)",
        "ask_game_man": "Paste the game folder path",
        "game_detected": "game detected: ",
        "game_notfound": "couldn't find the game automatically.",
        "game_ok": "game folder OK ({n} .ssg files found)",
        "game_no_ssg": "no .ssg files here — check if this is the right folder.",
        "game_invalid": "invalid game folder.",
        "ask_blender": "Path to blender.exe (ENTER to auto-detect)",
        "ask_blender_man": "Paste the blender.exe path",
        "blender_detected": "Blender detected: ",
        "blender_notfound": "couldn't find Blender automatically.",
        "blender_ok": "Blender OK",
        "blender_undef": "Blender not set (needed for steps 3+).",
        "ask_work": "Work folder (where everything is saved)",
        "work_ok": "work folder: ",
        "cfg_saved": "Configuration saved to orc_config.json",
        # extract
        "t_extract": "2. EXTRACT THE GAME  (.ssg -> files)",
        "extract_intro": "I'll unpack ALL .ssg files into:\n    {out}",
        "extract_time": "This extracts ~113,000 files and takes a few minutes.",
        "extract_done": "extraction complete!",
        "extract_idx": "building the asset index (speeds up Blender)...",
        "idx_ready": "index ready.",
        "extract_fail": "extraction exited with code {rc}. See _errors.txt in the output folder.",
        # fbx
        "t_fbx": "3. EXPORT MODELS TO FBX",
        "fbx_intro": "I'll import each model and export to FBX into:\n    {out}",
        "fbx_time": "This takes a while (can exceed 1 hour). Each model runs in a separate process.",
        "fbx_done": "FBX exported to: ",
        "fbx_fail": "export exited with code {rc}.",
        # library
        "t_lib": "4. BUILD THE ASSET LIBRARY (.blend file)",
        "lib_nofbx": "No FBX found. Run the export (option 3) first.",
        "lib_phases": "The library is built in 3 automatic phases:",
        "lib_p1": "  4a. build in chunks",
        "lib_p2": "  4b. merge into a single .blend",
        "lib_p3": "  4c. organize into folders (catalogs) + thumbnails",
        "lib_time": "Takes ~1 hour total. Continue? (y/N)",
        "lib_4a": "4a. building in chunks",
        "lib_4b": "4b. merging into a single .blend",
        "lib_4c": "4c. converting to collection assets + thumbnails + folders",
        "lib_done": "Library ready at: ",
        "lib_fail": "{phase} exited with code {rc}.",
        # finish
        "t_fin": "5. FINISH (register in Blender + install addon)",
        "fin_nolib": "The library hasn't been built yet. Use option 4.",
        "fin_reg": "registering the library in Blender...",
        "fin_reg_ok": "library registered as 'ORC Assets'",
        "fin_addon": "installing the helper addon (makes assets editable)...",
        "fin_addon_ok": "addon copied to: ",
        "fin_addon_enable": "Enable it in: Edit > Preferences > Add-ons > search 'ORC Asset Library Helper'",
        "fin_addon_manual": "couldn't find Blender's addons folder automatically.",
        "fin_addon_manual2": "copy manually: {src}\n  to: {dst}",
        "fin_allok": "All set! Open Blender and use the Asset Browser.",
        # status
        "t_status": "CURRENT STATUS",
        "st_game": "Game:     {v}  ({p})",
        "st_blender": "Blender:  {v}  ({p})",
        "st_work": "Work:     {p}",
        "st_yes": "yes ({n} items)", "st_yes2": "yes", "st_no": "not yet",
        "st_extracted": "Extracted (ssg_unpacked)", "st_index": "Asset index",
        "st_models": "Models list", "st_fbx": "FBX exported",
        "st_lib": "Library (.blend)", "st_thumbs": "Thumbnails",
        # quick
        "t_quick": "DO EVERYTHING  (extract -> FBX -> library -> finish)",
        "quick_intro": "This runs ALL steps. It can take several hours.",
        "quick_note": "Leave the computer on and avoid using Blender during the process.",
        "quick_confirm": "Are you sure you want to continue? (y/N)",
        # errors
        "err_cmd": "command not found: ", "err_user": "interrupted by user",
        "need_game": "Game folder not set or invalid. Use option 1.",
        "need_blender": "Blender not found. Use option 1.",
        "run_extract_first": "Run the extraction (option 2) first.",
        "models_found": "{n} models found",
        "gen_list": "generating the model list (reading .edgemodel headers)...",
    },
    "pt": {
        "subtitle": "Assistente de Extração — Resident Evil: Operation Raccoon City",
        "subtitle2": "(extraia os modelos do SEU jogo para o Blender)",
        "game": "Jogo:    ", "blender": "Blender:", "folder": "Pasta:   ",
        "ok_cfg": "OK", "no_cfg": "não configurado", "no_bl": "não encontrado",
        "m1": "Configurar jogo e Blender",
        "m2": "Extrair o jogo             (.ssg -> arquivos)",
        "m3": "Exportar modelos para FBX",
        "m4": "Montar a Asset Library     (arquivo .blend + pastas)",
        "m5": "Finalizar                  (registrar no Blender + addon)",
        "m6": "FAZER TUDO automaticamente",
        "ms": "Ver o estado atual",
        "mq": "Sair",
        "choose": "Escolha uma opção: ",
        "invalid": "opção inválida.",
        "bye": "Até logo!  Assets do jogo são (c) CAPCOM/Slant Six — uso pessoal apenas.",
        "press_enter": "Pressione ENTER para voltar ao menu...",
        "continue": "Continuar? (s/N)",
        "t_cfg": "1. CONFIGURAÇÃO",
        "cfg_intro": "Vamos localizar o jogo e o Blender.",
        "ask_game": "Pasta do jogo (ENTER para detectar automaticamente)",
        "ask_game_man": "Cole o caminho da pasta do jogo",
        "game_detected": "jogo detectado: ",
        "game_notfound": "não encontrei o jogo automaticamente.",
        "game_ok": "pasta do jogo OK ({n} arquivos .ssg encontrados)",
        "game_no_ssg": "não achei arquivos .ssg aqui — confira se é a pasta certa.",
        "game_invalid": "pasta do jogo inválida.",
        "ask_blender": "Caminho do blender.exe (ENTER para detectar)",
        "ask_blender_man": "Cole o caminho do blender.exe",
        "blender_detected": "Blender detectado: ",
        "blender_notfound": "não encontrei o Blender automaticamente.",
        "blender_ok": "Blender OK",
        "blender_undef": "Blender não definido (necessário para as etapas 3+).",
        "ask_work": "Pasta de trabalho (onde tudo será salvo)",
        "work_ok": "pasta de trabalho: ",
        "cfg_saved": "Configuração salva em orc_config.json",
        "t_extract": "2. EXTRAIR O JOGO  (.ssg -> arquivos)",
        "extract_intro": "Vou desempacotar TODOS os .ssg do jogo para:\n    {out}",
        "extract_time": "Isso extrai ~113.000 arquivos e leva alguns minutos.",
        "extract_done": "extração concluída!",
        "extract_idx": "construindo o índice de assets (acelera o Blender)...",
        "idx_ready": "índice pronto.",
        "extract_fail": "extração terminou com código {rc}. Veja _errors.txt na pasta de saída.",
        "t_fbx": "3. EXPORTAR MODELOS PARA FBX",
        "fbx_intro": "Vou importar cada modelo e exportar em FBX para:\n    {out}",
        "fbx_time": "Isso demora (pode passar de 1 hora). Cada modelo roda em processo separado.",
        "fbx_done": "FBX exportados em: ",
        "fbx_fail": "exportação terminou com código {rc}.",
        "t_lib": "4. MONTAR A ASSET LIBRARY (arquivo .blend)",
        "lib_nofbx": "Nenhum FBX encontrado. Rode a exportação (opção 3) primeiro.",
        "lib_phases": "A biblioteca é montada em 3 fases (todas automáticas):",
        "lib_p1": "  4a. construir em pedaços (chunks)",
        "lib_p2": "  4b. juntar tudo num .blend único",
        "lib_p3": "  4c. organizar em pastas (catálogos) + miniaturas",
        "lib_time": "Demora ~1 hora no total. Continuar? (s/N)",
        "lib_4a": "4a. construindo em pedaços (chunks)",
        "lib_4b": "4b. juntando num .blend único",
        "lib_4c": "4c. convertendo em collection assets + miniaturas + pastas",
        "lib_done": "Biblioteca pronta em: ",
        "lib_fail": "{phase} terminou com código {rc}.",
        "t_fin": "5. FINALIZAR (registrar no Blender + instalar addon)",
        "fin_nolib": "A biblioteca ainda não foi montada. Use a opção 4.",
        "fin_reg": "registrando a biblioteca no Blender...",
        "fin_reg_ok": "biblioteca registrada como 'ORC Assets'",
        "fin_addon": "instalando o addon auxiliar (deixa os assets editáveis)...",
        "fin_addon_ok": "addon copiado para: ",
        "fin_addon_enable": "Ative em: Edit > Preferences > Add-ons > procure 'ORC Asset Library Helper'",
        "fin_addon_manual": "não achei a pasta de addons do Blender automaticamente.",
        "fin_addon_manual2": "copie manualmente: {src}\n  para: {dst}",
        "fin_allok": "Tudo pronto! Abra o Blender e use o Asset Browser.",
        "t_status": "ESTADO ATUAL",
        "st_game": "Jogo:      {v}  ({p})",
        "st_blender": "Blender:   {v}  ({p})",
        "st_work": "Trabalho:  {p}",
        "st_yes": "sim ({n} itens)", "st_yes2": "sim", "st_no": "ainda não",
        "st_extracted": "Extraído (ssg_unpacked)", "st_index": "Índice de assets",
        "st_models": "Lista de modelos", "st_fbx": "FBX exportados",
        "st_lib": "Biblioteca (.blend)", "st_thumbs": "Miniaturas",
        "t_quick": "TUDO AUTOMÁTICO  (extração -> FBX -> biblioteca -> finalizar)",
        "quick_intro": "Isso roda TODAS as etapas. Pode levar várias horas.",
        "quick_note": "Deixe o computador ligado e evite usar o Blender durante o processo.",
        "quick_confirm": "Tem certeza que quer continuar? (s/N)",
        "err_cmd": "comando não encontrado: ", "err_user": "interrompido pelo usuário",
        "need_game": "Pasta do jogo não definida ou inválida. Use a opção 1.",
        "need_blender": "Blender não encontrado. Use a opção 1.",
        "run_extract_first": "Rode a extração (opção 2) primeiro.",
        "models_found": "{n} modelos encontrados",
        "gen_list": "gerando lista de modelos (isso lê os cabeçalhos dos .edgemodel)...",
    },
}


def _pick_lang():
    if LANG in ("pt", "pt-br", "pt_br", "portugues", "português"):
        return "pt"
    if LANG in ("en", "english", "eng"):
        return "en"
    # auto: tenta pela locale do sistema
    try:
        import locale
        loc = (locale.getdefaultlocale()[0] or "").lower()
        if loc.startswith("pt"):
            return "pt"
    except Exception:
        pass
    return "en"


LANG = _pick_lang()


def t(key, **kw):
    s = T[LANG].get(key, T["en"].get(key, key))
    return s.format(**kw) if kw else s


# ------------------------------------------------------------------ utils

def c(text, code):
    """Simple ANSI color (disabled if not a terminal)."""
    if not sys.stdout.isatty():
        return text
    return f"\033[{code}m{text}\033[0m"

def title(x):
    print()
    print(c("=" * 66, "36"))
    print(c("  " + x, "1;36"))
    print(c("=" * 66, "36"))

def ok(x):   print(c("  [OK] " + x, "32"))
def warn(x): print(c("  [!] " + x, "33"))
def err(x):  print(c("  [X] " + x, "31"))
def info(x): print("  " + x)

def ask(prompt, default=""):
    d = f" [{default}]" if default else ""
    try:
        v = input(f"  {prompt}{d}: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return default
    return v or default

def pause():
    try:
        input(c("\n  " + t("press_enter"), "90"))
    except (EOFError, KeyboardInterrupt):
        print()

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def yes(v):
    return v.strip().lower() in ("y", "yes", "s", "sim", "1")


# ------------------------------------------------------------------ config

DEFAULTS = {
    "game_dir": r"C:\Program Files (x86)\DODI-Repacks\Resident Evil Operation Raccoon City",
    "work_dir": r"C:\ORC-COMPLETO",
    "blender":  r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe",
}

def load_config():
    cfg = dict(DEFAULTS)
    if os.path.isfile(CONFIG_PATH):
        try:
            cfg.update(json.load(open(CONFIG_PATH, encoding="utf-8")))
        except Exception:
            pass
    return cfg

def save_config(cfg):
    try:
        json.dump(cfg, open(CONFIG_PATH, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    except Exception as e:
        warn(f"could not save config: {e}")


# ------------------------------------------------------------------ detection

def find_blender():
    """Look for blender.exe in common locations."""
    import glob
    cands = [r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe"]
    cands += sorted(glob.glob(r"C:\Program Files\Blender Foundation\Blender*\blender.exe"), reverse=True)
    cands += sorted(glob.glob(r"C:\Program Files\Blender Foundation\*\blender.exe"), reverse=True)
    for p in cands:
        if os.path.isfile(p):
            return p
    w = shutil.which("blender")
    if w:
        return w
    return ""

def find_game():
    """Look for the game in common locations."""
    import glob
    cands = [
        r"C:\Program Files (x86)\DODI-Repacks\Resident Evil Operation Raccoon City",
        r"C:\Program Files\DODI-Repacks\Resident Evil Operation Raccoon City",
        r"C:\Program Files (x86)\Steam\steamapps\common\Resident Evil Operation Raccoon City",
        r"C:\Program Files\Steam\steamapps\common\Resident Evil Operation Raccoon City",
        r"D:\SteamLibrary\steamapps\common\Resident Evil Operation Raccoon City",
        r"E:\SteamLibrary\steamapps\common\Resident Evil Operation Raccoon City",
        r"C:\Games\Resident Evil Operation Raccoon City",
        r"D:\Games\Resident Evil Operation Raccoon City",
    ]
    cands += glob.glob(r"*:\*\*\Resident Evil Operation Raccoon City")
    for p in cands:
        if os.path.isdir(p):
            return p
    return ""

def is_game_dir(p):
    """Check whether the folder looks like the game (has .ssg)."""
    if not p or not os.path.isdir(p):
        return False
    for r, _, fs in os.walk(p):
        for f in fs:
            if f.lower().endswith(".ssg"):
                return True
        if r.count(os.sep) - p.count(os.sep) > 2:
            break
    return False

def count_ssg(p):
    n = 0
    for r, _, fs in os.walk(p):
        n += sum(1 for f in fs if f.lower().endswith(".ssg"))
    return n


# ------------------------------------------------------------------ execution

def run(cmd, cwd=None, env=None):
    """Run a command showing output in real time. Returns the exit code."""
    e = dict(os.environ)
    if env:
        e.update(env)
    try:
        p = subprocess.Popen(cmd, cwd=cwd, env=e)
        p.wait()
        return p.returncode
    except FileNotFoundError:
        err(t("err_cmd") + str(cmd[0]))
        return 127
    except KeyboardInterrupt:
        warn(t("err_user"))
        return 130

def py():
    return sys.executable

def blender_cmd(cfg, script, args):
    cmd = [cfg["blender"], "--background", "--factory-startup", "--python",
           os.path.join(SCRIPTS, script), "--"] + args
    env = {"ORC_BLENDER": cfg["blender"],
           "ORC_LIBDIR": os.path.join(cfg["work_dir"], "ORC-Asset-Library"),
           "ORC_IMPORTER": os.path.join(SCRIPTS, "03_orc_import_blender.py"),
           "ORC_ASSET_INDEX_FILE": os.path.join(cfg["work_dir"], "_asset_index.json"),
           "ORC_ASSET_ROOT": os.path.join(cfg["work_dir"], "ssg_unpacked")}
    return cmd, env

def check_ready(cfg, need_blender=False):
    if not cfg["game_dir"] or not os.path.isdir(cfg["game_dir"]):
        err(t("need_game"))
        return False
    if need_blender and (not cfg["blender"] or not os.path.isfile(cfg["blender"])):
        err(t("need_blender"))
        return False
    return True


# ------------------------------------------------------------------ steps

def step_config(cfg):
    clear()
    title(t("t_cfg"))
    print()
    info(t("cfg_intro"))
    print()
    # game
    g = ask(t("ask_game"), cfg["game_dir"] if os.path.isdir(cfg.get("game_dir", "")) else "")
    if not g or not os.path.isdir(g):
        d = find_game()
        if d:
            g = d
            ok(t("game_detected") + g)
        else:
            warn(t("game_notfound"))
            g = ask(t("ask_game_man"))
    if g and os.path.isdir(g):
        cfg["game_dir"] = g
        n = count_ssg(g)
        if n:
            ok(t("game_ok", n=n))
        else:
            warn(t("game_no_ssg"))
    else:
        err(t("game_invalid"))
    print()
    # blender
    b = ask(t("ask_blender"), cfg["blender"] if os.path.isfile(cfg.get("blender", "")) else "")
    if not b or not os.path.isfile(b):
        d = find_blender()
        if d:
            b = d
            ok(t("blender_detected") + b)
        else:
            warn(t("blender_notfound"))
            b = ask(t("ask_blender_man"))
    if b and os.path.isfile(b):
        cfg["blender"] = b
        ok(t("blender_ok"))
    else:
        warn(t("blender_undef"))
    print()
    w = ask(t("ask_work"), cfg["work_dir"])
    cfg["work_dir"] = w
    os.makedirs(w, exist_ok=True)
    ok(t("work_ok") + w)
    save_config(cfg)
    print()
    ok(t("cfg_saved"))
    pause()


def step_extract(cfg):
    clear()
    title(t("t_extract"))
    if not check_ready(cfg):
        pause(); return
    out = os.path.join(cfg["work_dir"], "ssg_unpacked")
    info(t("extract_intro", out=out))
    info(t("extract_time"))
    print()
    if not yes(ask(t("continue"), "n")):
        return
    print()
    rc = run([py(), os.path.join(SCRIPTS, "01_ssg_extract.py"), cfg["game_dir"], out])
    print()
    if rc == 0:
        ok(t("extract_done"))
        idx = os.path.join(cfg["work_dir"], "_asset_index.json")
        info(t("extract_idx"))
        run([py(), os.path.join(SCRIPTS, "02_build_index.py"), out, idx])
        ok(t("idx_ready"))
    else:
        err(t("extract_fail", rc=rc))
    pause()


def build_fbx_manifest(cfg):
    """Build the FBX manifest (for the library) from fbx_models/."""
    root = os.path.join(cfg["work_dir"], "fbx_models")
    man = os.path.join(cfg["work_dir"], "_all_manifest.json")
    if not os.path.isdir(root):
        return None
    items = []
    for cat in ("characters", "weapons", "vfx", "worlds"):
        d = os.path.join(root, cat)
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if f.lower().endswith(".fbx"):
                items.append([os.path.join(d, f), f"{cat}/{f[:-4]}"])
    if not items:
        return None
    json.dump(items, open(man, "w", encoding="utf-8"), ensure_ascii=False)
    ok(f"{len(items)} FBX -> _all_manifest.json")
    return man


def step_fbx(cfg):
    clear()
    title(t("t_fbx"))
    if not check_ready(cfg, need_blender=True):
        pause(); return
    out = os.path.join(cfg["work_dir"], "fbx_models")
    info(t("fbx_intro", out=out))
    info(t("fbx_time"))
    print()
    if not yes(ask(t("continue"), "n")):
        return
    print()
    # 04_export_all_models.py reads the extracted folder directly
    cmd, env = blender_cmd(cfg, "04_export_all_models.py", [os.path.join(cfg["work_dir"], "ssg_unpacked"), out])
    rc = run(cmd, env=env)
    print()
    if rc == 0:
        ok(t("fbx_done") + out)
    else:
        err(t("fbx_fail", rc=rc))
    pause()


def step_library(cfg):
    clear()
    title(t("t_lib"))
    if not check_ready(cfg, need_blender=True):
        pause(); return
    man = build_fbx_manifest(cfg)
    if not man:
        err(t("lib_nofbx"))
        pause(); return
    libdir = os.path.join(cfg["work_dir"], "ORC-Asset-Library")
    os.makedirs(libdir, exist_ok=True)
    blend = os.path.join(libdir, "ORC_AssetLibrary.blend")
    thumbs = os.path.join(libdir, "thumbnails")
    info(t("lib_phases"))
    info(t("lib_p1")); info(t("lib_p2")); info(t("lib_p3"))
    print()
    info(t("lib_time"))
    if not yes(ask("", "n")):
        return

    print(); title(t("lib_4a"))
    cmd, env = blender_cmd(cfg, "05_build_chunks.py", [cfg["work_dir"], man, blend, "300"])
    rc = run(cmd, env=env)
    if rc != 0:
        err(t("lib_fail", phase="chunks", rc=rc)); pause(); return

    print(); title(t("lib_4b"))
    cmd, env = blender_cmd(cfg, "07_merge_library.py", [os.path.join(cfg["work_dir"], "_chunks"), blend])
    rc = run(cmd, env=env)
    if rc != 0:
        err(t("lib_fail", phase="merge", rc=rc)); pause(); return

    print(); title(t("lib_4c"))
    for script, args in (
        ("08_convert_to_collections.py", [blend, thumbs]),
        ("09_gen_thumbnails.py", [man, thumbs]),
        ("10_apply_previews.py", [blend, thumbs]),
        ("11_organize_catalogs.py", [libdir]),
        ("13_fix_center_bones.py", [blend]),
    ):
        cmd, env = blender_cmd(cfg, script, args)
        run(cmd, env=env)
    print()
    ok(t("lib_done") + libdir)
    pause()


def blender_version(cfg):
    """Return (major, minor) of the configured Blender, or None."""
    b = cfg.get("blender", "")
    if not b or not os.path.isfile(b):
        return None
    try:
        r = subprocess.run([b, "--version"], capture_output=True, text=True, timeout=30)
        import re
        m = re.search(r"Blender\s+(\d+)\.(\d+)", r.stdout or "")
        if m:
            return (int(m.group(1)), int(m.group(2)))
    except Exception:
        pass
    return None


def addon_dir_for(cfg):
    """Blender's addons folder for the configured version."""
    v = blender_version(cfg)
    if not v:
        base = os.path.join(os.environ.get("APPDATA", ""), "Blender Foundation", "Blender")
        if os.path.isdir(base):
            vers = sorted(os.listdir(base))
            if vers:
                v = tuple(int(x) for x in vers[-1].split(".")[:2])
    if not v:
        v = (4, 2)
    return os.path.join(os.environ.get("APPDATA", ""), "Blender Foundation",
                        "Blender", f"{v[0]}.{v[1]}", "scripts", "addons")


def step_finish(cfg):
    clear()
    title(t("t_fin"))
    if not check_ready(cfg, need_blender=True):
        pause(); return
    libdir = os.path.join(cfg["work_dir"], "ORC-Asset-Library")
    blend = os.path.join(libdir, "ORC_AssetLibrary.blend")
    if not os.path.isfile(blend):
        err(t("fin_nolib"))
        pause(); return
    info(t("fin_reg"))
    cmd, env = blender_cmd(cfg, "15_register_library.py", ["ORC Assets", libdir])
    run(cmd, env=env)
    ok(t("fin_reg_ok"))
    print()
    info(t("fin_addon"))
    addon_src = os.path.join(HERE, "addon", "orc_asset_helper.py")
    addon_dir = addon_dir_for(cfg)
    if os.path.isdir(os.path.dirname(addon_dir)) and os.path.isfile(addon_src):
        os.makedirs(addon_dir, exist_ok=True)
        shutil.copy(addon_src, os.path.join(addon_dir, "orc_asset_helper.py"))
        ok(t("fin_addon_ok") + addon_dir)
        info(t("fin_addon_enable"))
    else:
        warn(t("fin_addon_manual"))
        info(t("fin_addon_manual2", src=addon_src, dst=addon_dir))
    print()
    ok(t("fin_allok"))
    pause()


def step_status(cfg):
    clear()
    title(t("t_status"))
    g = cfg.get("game_dir", "")
    info(t("st_game", v=("OK" if is_game_dir(g) else t("no_cfg")), p=g))
    b = cfg.get("blender", "")
    info(t("st_blender", v=("OK" if os.path.isfile(b) else t("no_bl")), p=b))
    w = cfg.get("work_dir", "")
    info(t("st_work", p=w))
    print()
    checks = [
        (t("st_extracted"), os.path.join(w, "ssg_unpacked")),
        (t("st_index"), os.path.join(w, "_asset_index.json")),
        (t("st_models"), os.path.join(w, "_all_manifest.json")),
        (t("st_fbx"), os.path.join(w, "fbx_models")),
        (t("st_lib"), os.path.join(w, "ORC-Asset-Library", "ORC_AssetLibrary.blend")),
        (t("st_thumbs"), os.path.join(w, "ORC-Asset-Library", "thumbnails")),
    ]
    for label, p in checks:
        if os.path.isdir(p):
            n = sum(len(fs) for _, _, fs in os.walk(p))
            ok(f"{label}: {t('st_yes', n=n)}")
        elif os.path.isfile(p):
            ok(f"{label}: {t('st_yes2')}")
        else:
            warn(f"{label}: {t('st_no')}")
    pause()


def step_quick(cfg):
    """Run everything in sequence, from scratch to the library."""
    clear()
    title(t("t_quick"))
    if not check_ready(cfg, need_blender=True):
        pause(); return
    info(t("quick_intro"))
    info(t("quick_note"))
    print()
    if not yes(ask(t("quick_confirm"), "n")):
        return
    step_extract(cfg)
    step_fbx(cfg)
    step_library(cfg)
    step_finish(cfg)


# ------------------------------------------------------------------ menu

def main_menu():
    cfg = load_config()
    if not is_game_dir(cfg.get("game_dir", "")):
        d = find_game()
        if d:
            cfg["game_dir"] = d
    if not os.path.isfile(cfg.get("blender", "")):
        d = find_blender()
        if d:
            cfg["blender"] = d
    save_config(cfg)

    while True:
        clear()
        # ASCII art: "ORC Toolkit"  +  assinatura no canto
        print(c(r"""
   ___   ____    ____     _____                _  _     _  _
  / _ \ |  _ \  / ___|   |_   _|  ___    ___  | || | __(_)| |_
 | | | || |_) || |         | |   / _ \  / _ \ | || |/ /| || __|
 | |_| ||  _ < | |___      | |  | (_) || (_) || ||   < | || |_
  \___/ |_| \_\\____|      |_|   \___/  \___/ |_||_|\_\|_| \__|""", "36"))
        print(c("                                          by TheNordicBlizzard", "1;33"))
        print(c("       " + t("subtitle"), "1;36"))
        print(c("       " + t("subtitle2"), "90"))
        print()
        g = cfg.get("game_dir", "")
        b = cfg.get("blender", "")
        print(f"   {t('game')}   {c('OK', '32') if is_game_dir(g) else c(t('no_cfg'), '33')}  {c(g, '90')}")
        print(f"   {t('blender')} {c('OK', '32') if os.path.isfile(b) else c(t('no_bl'), '33')}  {c(b, '90')}")
        print(f"   {t('folder')}   {c(cfg.get('work_dir',''), '90')}")
        print()
        print("   " + c("1", "1;33") + ") " + t("m1"))
        print("   " + c("2", "1;33") + ") " + t("m2"))
        print("   " + c("3", "1;33") + ") " + t("m3"))
        print("   " + c("4", "1;33") + ") " + t("m4"))
        print("   " + c("5", "1;33") + ") " + t("m5"))
        print("   " + c("6", "1;33") + ") " + t("m6"))
        print()
        print("   " + c("s", "36") + ") " + t("ms"))
        print("   " + c("q", "36") + ") " + t("mq"))
        print()
        try:
            op = input("   " + t("choose")).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print(); break

        if op == "1": step_config(cfg)
        elif op == "2": step_extract(cfg)
        elif op == "3": step_fbx(cfg)
        elif op == "4": step_library(cfg)
        elif op == "5": step_finish(cfg)
        elif op == "6": step_quick(cfg)
        elif op in ("s", "status"): step_status(cfg)
        elif op in ("q", "quit", "sair", "exit"): break
        else:
            warn(t("invalid"))
            time.sleep(0.6)

    print()
    print(c("  " + t("bye"), "90"))
    print()


if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print()
