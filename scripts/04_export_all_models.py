#!/usr/bin/env python3
"""Driver: export all models to FBX in few Blender processes (batched), with a
precomputed asset index. Dedupes by model basename.

Usage:
    python export_all_models.py <ssg_unpacked_root> <out_dir> [--cat weapons,vfx,worlds]
                                [--batch 150]
"""
import os, sys, json, glob, subprocess, collections, time

BLENDER = r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe"
HERE = os.path.dirname(os.path.abspath(__file__))
BATCHER = os.path.join(HERE, "batch_export.py")
INDEX = os.path.join(HERE, "_asset_index.json")

def internal_key(rel):
    rel = rel.replace("\\", "/").lower()
    k = rel.find("dlc/")
    return rel[k:] if k >= 0 else rel

def cat_of(key):
    if "/characters/" in key: return "characters"
    if "/weapons/" in key:    return "weapons"
    if "/vfx/" in key:        return "vfx"
    if "/worlds/" in key:     return "worlds"
    return "other"

def main():
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    root, out = sys.argv[1], sys.argv[2]
    only = None
    if "--cat" in sys.argv:
        only = set(x.strip() for x in sys.argv[sys.argv.index("--cat")+1].split(","))
    batch = int(sys.argv[sys.argv.index("--batch")+1]) if "--batch" in sys.argv else 150

    # 1) build the asset index once (if missing)
    if not os.path.exists(INDEX):
        print("building asset index...")
        subprocess.run([sys.executable, os.path.join(HERE, "build_index.py"), root, INDEX], check=True)
    os.environ["ORC_ASSET_INDEX_FILE"] = INDEX

    # 2) collect unique models by basename — ONLY real meshes (magic FM6S);
    #    .edgemodel files with magic IM6S are model metadata, not meshes.
    uniq = {}
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
            key = internal_key(os.path.relpath(p, root))
            cat = cat_of(key)
            if only and cat not in only:
                continue
            uniq.setdefault((cat, os.path.splitext(f)[0].lower()), p)
    items = sorted(uniq.items())
    print(f"unique FM6S models: {len(items)}")

    os.makedirs(out, exist_ok=True)
    t0 = time.time()

    def run_batch(chunk, cat_out, cat_name, depth=0):
        """Run a batch; if the Blender process crashes, split it in half and
        retry, so a single bad model doesn't take down the whole chunk."""
        man = os.path.join(HERE, f"_manifest_{cat_name}_{depth}_{os.getpid()}_{len(chunk)}.json")
        json.dump(chunk, open(man, "w", encoding="utf-8"))
        r = subprocess.run([BLENDER, "--background", "--factory-startup", "--python", BATCHER,
                            "--", man, cat_out], capture_output=True, text=True)
        try:
            os.remove(man)
        except Exception:
            pass
        tail = ""
        for line in (r.stdout + r.stderr).splitlines():
            if line.startswith("BATCH_DONE"):
                tail = line
        if tail:
            return tail
        # crash: split and retry
        if len(chunk) <= 1:
            return f"CRASH single model ({chunk[0][1]})"
        mid = len(chunk) // 2
        return run_batch(chunk[:mid], cat_out, cat_name, depth+1) + " + " + run_batch(chunk[mid:], cat_out, cat_name, depth+1)

    # group by category so each batch writes into its own subfolder
    by_cat = collections.defaultdict(list)
    for (cat, name), path in items:
        by_cat[cat].append([path, name])
    for cat in sorted(by_cat):
        cat_out = os.path.join(out, cat)
        os.makedirs(cat_out, exist_ok=True)
        chunk_list = by_cat[cat]
        print(f"category {cat}: {len(chunk_list)} models -> {cat_out}")
        for i in range(0, len(chunk_list), batch):
            chunk = chunk_list[i:i+batch]
            tail = run_batch(chunk, cat_out, cat)
            print(f"  [{cat} {i+len(chunk)}/{len(chunk_list)}] {tail}  ({time.time()-t0:.0f}s)")

    total = sum(len(os.listdir(os.path.join(out,c))) for c in os.listdir(out) if os.path.isdir(os.path.join(out,c)))
    print(f"\nDONE models exported: {total} in {time.time()-t0:.0f}s")

if __name__ == "__main__":
    main()
