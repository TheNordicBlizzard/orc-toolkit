#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RE: Operation Raccoon City — Assistente de Extracao (menu interativo)

Um menu simples que configura o caminho do jogo, detecta o Blender e roda
cada etapa do pipeline para voce, sem precisar digitar comandos.

Uso:
    python orc_menu.py

O progresso e salvo em orc_config.json (na mesma pasta do script), entao da
proxima vez seus caminhos ja estarão preenchidos.
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

# ------------------------------------------------------------------ utils

def c(text, code):
    """Cor ANSI simples (desativa se nao for terminal)."""
    if not sys.stdout.isatty():
        return text
    return f"\033[{code}m{text}\033[0m"

def title(t):
    print()
    print(c("=" * 66, "36"))
    print(c("  " + t, "1;36"))
    print(c("=" * 66, "36"))

def ok(t):   print(c("  [OK] " + t, "32"))
def warn(t): print(c("  [!] " + t, "33"))
def err(t):  print(c("  [X] " + t, "31"))
def info(t): print("  " + t)

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
        input(c("\n  Pressione ENTER para voltar ao menu...", "90"))
    except (EOFError, KeyboardInterrupt):
        print()

def clear():
    os.system("cls" if os.name == "nt" else "clear")


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
        warn(f"nao consegui salvar a config: {e}")


# ------------------------------------------------------------------ deteccao

def find_blender():
    """Procura o blender.exe em locais comuns."""
    import glob
    cands = [r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe"]
    cands += sorted(glob.glob(r"C:\Program Files\Blender Foundation\Blender*\blender.exe"), reverse=True)
    cands += sorted(glob.glob(r"C:\Program Files\Blender Foundation\*\blender.exe"), reverse=True)
    for p in cands:
        if os.path.isfile(p):
            return p
    # PATH
    w = shutil.which("blender")
    if w:
        return w
    return ""

def find_game():
    """Procura o jogo em locais comuns."""
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
    """Confere se a pasta parece ser a do jogo (tem .ssg)."""
    if not p or not os.path.isdir(p):
        return False
    for r, _, fs in os.walk(p):
        for f in fs:
            if f.lower().endswith(".ssg"):
                return True
        # limita a profundidade
        if r.count(os.sep) - p.count(os.sep) > 2:
            break
    return False

def count_ssg(p):
    n = 0
    for r, _, fs in os.walk(p):
        n += sum(1 for f in fs if f.lower().endswith(".ssg"))
    return n


# ------------------------------------------------------------------ execucao

def run(cmd, cwd=None, env=None):
    """Roda um comando mostrando a saida em tempo real. Retorna o exit code."""
    e = dict(os.environ)
    if env:
        e.update(env)
    try:
        p = subprocess.Popen(cmd, cwd=cwd, env=e)
        p.wait()
        return p.returncode
    except FileNotFoundError:
        err(f"comando nao encontrado: {cmd[0]}")
        return 127
    except KeyboardInterrupt:
        warn("interrompido pelo usuario")
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
        err("Pasta do jogo nao definida ou invalida. Use a opcao 1.")
        return False
    if need_blender and (not cfg["blender"] or not os.path.isfile(cfg["blender"])):
        err("Blender nao encontrado. Use a opcao 2.")
        return False
    return True


# ------------------------------------------------------------------ etapas

def step_config(cfg):
    clear()
    title("1. CONFIGURACAO")
    print()
    info("Vamos localizar o jogo e o Blender.")
    print()
    # jogo
    g = ask("Pasta do jogo (ENTER para detectar automaticamente)", cfg["game_dir"] if os.path.isdir(cfg.get("game_dir","")) else "")
    if not g or not os.path.isdir(g):
        d = find_game()
        if d:
            g = d
            ok(f"jogo detectado: {g}")
        else:
            warn("nao encontrei o jogo automaticamente.")
            g = ask("Cole o caminho da pasta do jogo")
    if g and os.path.isdir(g):
        cfg["game_dir"] = g
        n = count_ssg(g)
        if n:
            ok(f"pasta do jogo OK ({n} arquivos .ssg encontrados)")
        else:
            warn("nao achei arquivos .ssg aqui — confira se e a pasta certa.")
    else:
        err("pasta do jogo invalida.")
    print()
    # blender
    b = ask("Caminho do blender.exe (ENTER para detectar)", cfg["blender"] if os.path.isfile(cfg.get("blender","")) else "")
    if not b or not os.path.isfile(b):
        d = find_blender()
        if d:
            b = d
            ok(f"Blender detectado: {b}")
        else:
            warn("nao encontrei o Blender automaticamente.")
            b = ask("Cole o caminho do blender.exe")
    if b and os.path.isfile(b):
        cfg["blender"] = b
        ok("Blender OK")
    else:
        warn("Blender nao definido (necessario para as etapas 3+).")
    print()
    w = ask("Pasta de trabalho (onde tudo sera salvo)", cfg["work_dir"])
    cfg["work_dir"] = w
    os.makedirs(w, exist_ok=True)
    ok(f"pasta de trabalho: {w}")
    save_config(cfg)
    print()
    ok("Configuracao salva em orc_config.json")
    pause()


def step_extract(cfg):
    clear()
    title("2. EXTRAIR O JOGO  (.ssg -> arquivos)")
    if not check_ready(cfg):
        pause(); return
    out = os.path.join(cfg["work_dir"], "ssg_unpacked")
    info(f"Vou desempacotar TODOS os .ssg do jogo para:\n    {out}")
    info("Isso extrai ~113.000 arquivos e leva alguns minutos.")
    print()
    if ask("Continuar? (s/N)", "s").lower() not in ("s", "sim", "y", "yes"):
        return
    print()
    rc = run([py(), os.path.join(SCRIPTS, "01_ssg_extract.py"), cfg["game_dir"], out])
    print()
    if rc == 0:
        ok("extracao concluida!")
        # indice
        idx = os.path.join(cfg["work_dir"], "_asset_index.json")
        info("construindo o indice de assets (acelera o Blender)...")
        run([py(), os.path.join(SCRIPTS, "02_build_index.py"), out, idx])
        ok("indice pronto.")
    else:
        err(f"extracao terminou com codigo {rc}. Veja _errors.txt na pasta de saida.")
    pause()


def build_fbx_manifest(cfg):
    """Gera o manifesto de FBX (para a biblioteca) a partir de fbx_models/."""
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


def step_manifest(cfg):
    """Lista os modelos (.edgemodel FM6S) — usado para referencia/contagem."""
    root = os.path.join(cfg["work_dir"], "ssg_unpacked")
    man = os.path.join(cfg["work_dir"], "_models_list.json")
    if not os.path.isdir(root):
        err("Rode a extracao (opcao 2) primeiro.")
        return None
    if os.path.isfile(man):
        return man
    info("gerando lista de modelos (isso le os cabecalhos dos .edgemodel)...")
    items = []
    seen = {}
    for r, _, fs in os.walk(root):
        for f in fs:
            if not f.lower().endswith(".edgemodel"):
                continue
            p = os.path.join(r, f)
            try:
                with open(p, "rb") as fh:
                    if fh.read(4) != b"FM6S":
                        continue
            except Exception:
                continue
            rel = os.path.relpath(p, root).replace("\\", "/").lower()
            k = rel.find("dlc/")
            key = rel[k:] if k >= 0 else rel
            if "/characters/" in key:   cat = "characters"
            elif "/weapons/" in key:    cat = "weapons"
            elif "/vfx/" in key:        cat = "vfx"
            elif "/worlds/" in key:     cat = "worlds"
            else:                       cat = "worlds"
            name = os.path.splitext(f)[0]
            if (cat, name.lower()) in seen:
                continue
            seen[(cat, name.lower())] = True
            items.append([p, f"{cat}/{name}"])
    json.dump(items, open(man, "w", encoding="utf-8"), ensure_ascii=False)
    ok(f"{len(items)} modelos encontrados")
    return man


def step_fbx(cfg):
    clear()
    title("3. EXPORTAR MODELOS PARA FBX")
    if not check_ready(cfg, need_blender=True):
        pause(); return
    out = os.path.join(cfg["work_dir"], "fbx_models")
    info(f"Vou importar cada modelo e exportar em FBX para:\n    {out}")
    info("Isso demora (pode passar de 1 hora). Cada modelo roda em processo separado.")
    print()
    if ask("Continuar? (s/N)", "n").lower() not in ("s", "sim", "y", "yes"):
        return
    print()
    # 04_export_all_models.py le direto da pasta extraida (monta o proprio manifesto)
    cmd, env = blender_cmd(cfg, "04_export_all_models.py", [os.path.join(cfg["work_dir"], "ssg_unpacked"), out])
    rc = run(cmd, env=env)
    print()
    if rc == 0:
        ok(f"FBX exportados em: {out}")
    else:
        err(f"exportacao terminou com codigo {rc}.")
    pause()


def step_library(cfg):
    clear()
    title("4. MONTAR A ASSET LIBRARY (arquivo .blend)")
    if not check_ready(cfg, need_blender=True):
        pause(); return
    man = build_fbx_manifest(cfg)
    if not man:
        err("Nenhum FBX encontrado. Rode a exportacao (opcao 3) primeiro.")
        pause(); return
    libdir = os.path.join(cfg["work_dir"], "ORC-Asset-Library")
    os.makedirs(libdir, exist_ok=True)
    blend = os.path.join(libdir, "ORC_AssetLibrary.blend")
    thumbs = os.path.join(libdir, "thumbnails")
    info("A biblioteca e montada em 3 fases (todas automaticas):")
    info("  4a. construir em pedacos (chunks)")
    info("  4b. juntar tudo num .blend unico")
    info("  4c. organizar em pastas (catalogos) + miniaturas")
    print()
    info("Demora ~1 hora no total. Continuar? (s/N)")
    if ask("", "n").lower() not in ("s", "sim", "y", "yes"):
        return

    # 4a chunks
    print()
    title("4a. construindo em pedacos (chunks)")
    cmd, env = blender_cmd(cfg, "05_build_chunks.py", [cfg["work_dir"], man, blend, "300"])
    rc = run(cmd, env=env)
    if rc != 0:
        err(f"chunks terminaram com codigo {rc}."); pause(); return

    # 4b merge
    print()
    title("4b. juntando num .blend unico")
    cmd, env = blender_cmd(cfg, "07_merge_library.py", [os.path.join(cfg["work_dir"], "_chunks"), blend])
    rc = run(cmd, env=env)
    if rc != 0:
        err(f"merge terminou com codigo {rc}."); pause(); return

    # 4c collections + thumbs + catalogs
    print()
    title("4c. convertendo em collection assets + miniaturas + pastas")
    cmd, env = blender_cmd(cfg, "08_convert_to_collections.py", [blend, thumbs])
    run(cmd, env=env)
    cmd, env = blender_cmd(cfg, "09_gen_thumbnails.py", [man, thumbs])
    run(cmd, env=env)
    cmd, env = blender_cmd(cfg, "10_apply_previews.py", [blend, thumbs])
    run(cmd, env=env)
    cmd, env = blender_cmd(cfg, "11_organize_catalogs.py", [libdir])
    run(cmd, env=env)
    cmd, env = blender_cmd(cfg, "13_fix_center_bones.py", [blend])
    run(cmd, env=env)
    print()
    ok(f"Biblioteca pronta em: {libdir}")
    pause()


def blender_version(cfg):
    """Retorna (major, minor) do Blender configurado, ou None."""
    b = cfg.get("blender", "")
    if not b or not os.path.isfile(b):
        return None
    try:
        r = subprocess.run([b, "--version"], capture_output=True, text=True, timeout=30)
        # primeira linha: "Blender 5.0.1"
        import re
        m = re.search(r"Blender\s+(\d+)\.(\d+)", r.stdout or "")
        if m:
            return (int(m.group(1)), int(m.group(2)))
    except Exception:
        pass
    return None


def addon_dir_for(cfg):
    """Pasta de addons do Blender configurado (varia por versao)."""
    v = blender_version(cfg)
    if not v:
        # tenta descobrir pelas pastas existentes
        base = os.path.join(os.environ.get("APPDATA", ""), "Blender Foundation", "Blender")
        if os.path.isdir(base):
            vers = sorted(os.listdir(base))
            if vers:
                v = tuple(int(x) for x in vers[-1].split(".")[:2])
    if not v:
        v = (4, 2)  # chute razoavel
    return os.path.join(os.environ.get("APPDATA", ""), "Blender Foundation",
                        "Blender", f"{v[0]}.{v[1]}", "scripts", "addons")


def step_finish(cfg):
    clear()
    title("5. FINALIZAR (registrar no Blender + instalar addon)")
    if not check_ready(cfg, need_blender=True):
        pause(); return
    libdir = os.path.join(cfg["work_dir"], "ORC-Asset-Library")
    blend = os.path.join(libdir, "ORC_AssetLibrary.blend")
    if not os.path.isfile(blend):
        err("A biblioteca ainda nao foi montada. Use a opcao 4.")
        pause(); return
    # registrar
    info("registrando a biblioteca no Blender...")
    cmd, env = blender_cmd(cfg, "15_register_library.py", ["ORC Assets", libdir])
    run(cmd, env=env)
    ok("biblioteca registrada como 'ORC Assets'")
    # addon
    print()
    info("instalando o addon auxiliar (deixa os assets editaveis)...")
    addon_src = os.path.join(HERE, "addon", "orc_asset_helper.py")
    addon_dir = addon_dir_for(cfg)
    if os.path.isdir(os.path.dirname(addon_dir)) and os.path.isfile(addon_src):
        os.makedirs(addon_dir, exist_ok=True)
        shutil.copy(addon_src, os.path.join(addon_dir, "orc_asset_helper.py"))
        ok(f"addon copiado para: {addon_dir}")
        info("Ative em: Edit > Preferences > Add-ons > procure 'ORC Asset Library Helper'")
    else:
        warn("nao achei a pasta de addons do Blender automaticamente.")
        info(f"copie manualmente: {addon_src}")
        info(f"para: {addon_dir}")
    print()
    ok("Tudo pronto! Abra o Blender e use o Asset Browser.")
    pause()


def step_status(cfg):
    clear()
    title("ESTADO ATUAL")
    g = cfg.get("game_dir", "")
    info(f"Jogo:      {'OK' if is_game_dir(g) else 'nao configurado'}  ({g})")
    b = cfg.get("blender", "")
    info(f"Blender:   {'OK' if os.path.isfile(b) else 'nao encontrado'}  ({b})")
    w = cfg.get("work_dir", "")
    info(f"Trabalho:  {w}")
    print()
    checks = [
        ("Extraido (ssg_unpacked)", os.path.join(w, "ssg_unpacked")),
        ("Indice de assets", os.path.join(w, "_asset_index.json")),
        ("Lista de modelos", os.path.join(w, "_all_manifest.json")),
        ("FBX exportados", os.path.join(w, "fbx_models")),
        ("Biblioteca (.blend)", os.path.join(w, "ORC-Asset-Library", "ORC_AssetLibrary.blend")),
        ("Miniaturas", os.path.join(w, "ORC-Asset-Library", "thumbnails")),
    ]
    for label, p in checks:
        if os.path.isdir(p):
            n = sum(len(fs) for _, _, fs in os.walk(p))
            ok(f"{label}: sim ({n} itens)")
        elif os.path.isfile(p):
            ok(f"{label}: sim")
        else:
            warn(f"{label}: ainda nao")
    pause()


def step_quick(cfg):
    """Roda tudo em sequencia, do zero ate a biblioteca."""
    clear()
    title("TUDO AUTOMATICO  (extracao -> FBX -> biblioteca -> finalizar)")
    if not check_ready(cfg, need_blender=True):
        pause(); return
    info("Isso roda TODAS as etapas. Pode levar varias horas.")
    info("Deixe o computador ligado e evite usar o Blender durante o processo.")
    print()
    if ask("Tem certeza que quer continuar? (s/N)", "n").lower() not in ("s", "sim", "y", "yes"):
        return
    step_extract(cfg)
    step_fbx(cfg)
    step_library(cfg)
    step_finish(cfg)


# ------------------------------------------------------------------ menu

def main_menu():
    cfg = load_config()
    # tenta preencher automaticamente na primeira vez
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
        print(c("""
   ____  ____   ____    _   _                 _    _
  |  _ \\|  _ \\ / ___|  | |_| |__   ___       | | _(_)_ __
  | |_) | |_) | |      | __| '_ \\ / _ \\ _____| |/ / | '_ \\
  |  _ <|  _ <| |___   | |_| | | |  __/_____|   <| | | | |
  |_| \\_\\_| \\_\\\\____|   \\__|_| |_|\\___|     |_|\\_\\_|_| |_|
""", "36"))
        print(c("       Assistente de Extracao — Resident Evil: Operation Raccoon City", "1;36"))
        print(c("       (extraia os modelos do SEU jogo para o Blender)", "90"))
        print()
        g = cfg.get("game_dir", "")
        b = cfg.get("blender", "")
        print(f"   Jogo:    {c('OK', '32') if is_game_dir(g) else c('nao configurado', '33')}  {c(g, '90')}")
        print(f"   Blender: {c('OK', '32') if os.path.isfile(b) else c('nao encontrado', '33')}  {c(b, '90')}")
        print(f"   Pasta:   {c(cfg.get('work_dir',''), '90')}")
        print()
        print("   " + c("1", "1;33") + ") Configurar jogo e Blender")
        print("   " + c("2", "1;33") + ") Extrair o jogo            (.ssg -> arquivos)")
        print("   " + c("3", "1;33") + ") Exportar modelos para FBX")
        print("   " + c("4", "1;33") + ") Montar a Asset Library    (arquivo .blend + pastas)")
        print("   " + c("5", "1;33") + ") Finalizar                  (registrar no Blender + addon)")
        print("   " + c("6", "1;33") + ") FAZER TUDO automaticamente")
        print()
        print("   " + c("s", "36") + ") Ver o estado atual")
        print("   " + c("q", "36") + ") Sair")
        print()
        try:
            op = input("   Escolha uma opcao: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print(); break

        if op == "1": step_config(cfg)
        elif op == "2": step_extract(cfg)
        elif op == "3": step_fbx(cfg)
        elif op == "4": step_library(cfg)
        elif op == "5": step_finish(cfg)
        elif op == "6": step_quick(cfg)
        elif op in ("s", "status"): step_status(cfg)
        elif op in ("q", "sair", "exit"): break
        else:
            warn("opcao invalida.")
            time.sleep(0.6)

    print()
    print(c("  Ate logo!  Assets do jogo sao (c) CAPCOM/Slant Six — uso pessoal apenas.", "90"))
    print()


if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print()
