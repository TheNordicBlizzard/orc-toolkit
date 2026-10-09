"""Constroi a Asset Library em CHUNKS (cada chunk em seu proprio processo Blender),
evitando o crash de memoria apos ~1000 modelos. Split recursivo isola modelos ruins.

Uso:
    python 05_build_chunks.py <work_dir> <manifest.json> <out_blend> [chunk_size]

Variaveis de ambiente:
    ORC_BLENDER   caminho do blender.exe (default: instalacao padrao)
    ORC_TEXDIR    pasta das texturas PNG
"""
import os, sys, json, subprocess, time

BLENDER = os.environ.get("ORC_BLENDER") or r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe"
HERE = os.path.dirname(os.path.abspath(__file__))
BUILDER = os.path.join(HERE, "06_build_library.py")
COUNTER = [0]
BAD = []


def build(chunk, chunkdir, depth=0):
    if not chunk:
        return
    COUNTER[0] += 1
    idx = COUNTER[0]
    out = os.path.join(chunkdir, f"part_{idx:03d}.blend")
    man = os.path.join(chunkdir, f"_man_{idx:03d}.json")
    json.dump(chunk, open(man, "w", encoding="utf-8"))
    r = subprocess.run([BLENDER, "--background", "--factory-startup", "--python", BUILDER,
                        "--", man, out], capture_output=True, text=True)
    try:
        os.remove(man)
    except Exception:
        pass
    if os.path.exists(out) and os.path.getsize(out) > 200:
        print(f"  part_{idx:03d}: OK ({len(chunk)} models, {os.path.getsize(out)//1024//1024} MB)", flush=True)
        return
    if len(chunk) == 1:
        BAD.append(chunk[0][1])
        print(f"  SKIP bad: {chunk[0][1]}", flush=True)
        return
    mid = len(chunk) // 2
    print(f"  part_{idx:03d} FAILED ({len(chunk)}) -> split", flush=True)
    build(chunk[:mid], chunkdir, depth + 1)
    build(chunk[mid:], chunkdir, depth + 1)


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)
    work, manifest, out_blend = sys.argv[1], sys.argv[2], sys.argv[3]
    cs = int(sys.argv[4]) if len(sys.argv) > 4 else 300
    chunkdir = os.path.join(work, "_chunks")
    os.makedirs(chunkdir, exist_ok=True)
    items = json.load(open(manifest, encoding="utf-8"))
    chunks = [items[i:i + cs] for i in range(0, len(items), cs)]
    print(f"{len(items)} models -> {len(chunks)} chunks of {cs}", flush=True)
    t0 = time.time()
    for ci, ch in enumerate(chunks):
        print(f"[chunk {ci+1}/{len(chunks)}]", flush=True)
        build(ch, chunkdir)
    json.dump(BAD, open(os.path.join(work, "_bad_models.json"), "w"))
    print(f"DONE in {time.time()-t0:.0f}s; bad: {len(BAD)}", flush=True)
    print(f"partes em: {chunkdir}", flush=True)
    print("agora rode 07_merge_library.py apontando para essa pasta", flush=True)


if __name__ == "__main__":
    main()
