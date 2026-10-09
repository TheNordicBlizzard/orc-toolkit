#!/usr/bin/env python3
"""Build a JSON asset index for the unpacked ORC tree so the Blender importer
can resolve material/texture paths without re-walking 113k files each run.

Key = path tail starting at the FIRST "dlc/" occurrence (that is how RE:ORC
stores internal paths), value = absolute path. Also indexes by basename.

Usage: python build_index.py <ssg_unpacked_root> <index.json>
"""
import os, sys, json

def main():
    root, out = sys.argv[1], sys.argv[2]
    by_tail = {}
    by_name = {}
    n = 0
    for r, _, fs in os.walk(root):
        for f in fs:
            full = os.path.join(r, f)
            rel = os.path.relpath(full, root).replace("\\", "/").lower()
            k = rel.find("dlc/")
            tail = rel[k:] if k >= 0 else rel
            by_tail.setdefault(tail, full)
            by_name.setdefault(os.path.basename(rel), full)
            n += 1
    json.dump({"tail": by_tail, "name": by_name}, open(out, "w", encoding="utf-8"))
    print(f"indexed {n} files -> {out} ({len(by_tail)} tails, {len(by_name)} names)")

if __name__ == "__main__":
    main()
