#!/usr/bin/env python3
"""
Repair ORC DDS textures whose DXT5 alpha channel is degenerate (constant:
all-zero or all-opaque). Such alpha carries no cut-out information but makes
viewers/engines render the surface fully transparent. We force the alpha to
255 (fully opaque) in-place, keeping the DXT5 format and the colour data
untouched (lossless).

Usage: python fix_degenerate_alpha.py <dir> [<dir> ...]
"""
import sys, os

def alpha_bounds(data):
    mn, mx = 255, 0
    for i in range(0, len(data) - 15, 16):
        a0, a1 = data[i], data[i+1]
        mn = min(mn, a0, a1); mx = max(mx, a0, a1)
    return mn, mx

def make_opaque(path):
    d = bytearray(open(path, 'rb').read())
    if d[:4] != b'DDS ' or bytes(d[84:88]) != b'DXT5':
        return None
    data = d[128:]
    mn, mx = alpha_bounds(data)
    if mn != mx:               # real (varying) alpha -> keep it
        return "kept"
    if mx == 255:              # already fully opaque
        return "opaque"
    # force opaque: each 16-byte block -> a0=255, a1=255, indices=0
    for i in range(0, len(data) - 15, 16):
        d[128 + i] = 255
        d[128 + i + 1] = 255
        for j in range(2, 8):
            d[128 + i + j] = 0
    open(path, 'wb').write(bytes(d))
    return "FIXED"

def main():
    dirs = sys.argv[1:]
    n_fixed = n_kept = n_opaque = 0
    for root_dir in dirs:
        for root, _, files in os.walk(root_dir):
            for fn in files:
                if not fn.lower().endswith('.dds'):
                    continue
                r = make_opaque(os.path.join(root, fn))
                if r == "FIXED":
                    n_fixed += 1
                    print("FIXED", os.path.relpath(os.path.join(root, fn), root_dir))
                elif r == "kept":
                    n_kept += 1
                elif r == "opaque":
                    n_opaque += 1
    print(f"\nfixed={n_fixed}  real-alpha-kept={n_kept}  already-opaque={n_opaque}")

if __name__ == "__main__":
    main()
