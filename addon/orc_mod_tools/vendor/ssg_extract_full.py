#!/usr/bin/env python3
"""
Full SSG unpacker for RE: Operation Raccoon City (Hexane Engine / Slant Six).

Extracts EVERY .ssg archive in the game into a mirror tree, recovering the
original internal paths (e.g. dlc/pack1/characters/leon/models/leon.edgemodel).

Features:
  - version 5 & 6 archives, little & big endian
  - zlib-compressed blocks (64 KB uncompressed each) and uncompressed sections
  - resumable (skips archives already marked done in _done.txt)
  - per-archive error log (_errors.txt); never aborts the whole run
  - prints a final summary (archives ok/fail, files, bytes)

Usage:
    python ssg_extract_full.py <game_dir> <output_dir> [--only substr,substr]
"""
import sys, os, struct, zlib, json, time

HEADER_SIZE = 32
SECTION_SIZE = 32

def u32(b, o, e): return struct.unpack_from(e + "I", b, o)[0]
def i32(b, o, e): return struct.unpack_from(e + "i", b, o)[0]
def u16(b, o, e): return struct.unpack_from(e + "H", b, o)[0]


def parse_ssg(raw):
    """Return list of (name, type, data). Raises on malformed input."""
    ver_le = struct.unpack_from("<I", raw, 0)[0]
    e = ">" if ver_le > 0xFFFF else "<"

    version   = u32(raw, 0, e)
    padding1  = u32(raw, 4, e)
    sec_infos = i32(raw, 8, e)
    sec_names = i32(raw, 12, e)
    comp_size = i32(raw, 24, e)
    alignment = u16(raw, 28, e)

    if version not in (5, 6):
        raise ValueError(f"version {version}")
    if version == 5:
        alignment = 16
        comp_size = 0
    if alignment == 0:
        alignment = 16

    # compressed block sizes
    block_sizes = []
    pos = HEADER_SIZE + sec_infos
    for _ in range(comp_size // 4):
        sz = i32(raw, pos, e); pos += 4
        if sz == 0: break
        block_sizes.append(sz)

    names_off = HEADER_SIZE + sec_infos + comp_size
    data_off  = names_off + sec_names
    count = sec_infos // SECTION_SIZE

    # First pass: read section descriptors.
    descs = []
    for i in range(count):
        b = HEADER_SIZE + SECTION_SIZE * i
        name_off   = i32(raw, b + 4, e)
        uncomp_sz  = i32(raw, b + 8, e)
        dataoffset = i32(raw, b + 16, e)
        ftype      = u32(raw, b + 20, e)
        comp_sz    = i32(raw, b + 28, e)
        if comp_size == 0:
            comp_sz = 0
        nstart = names_off + name_off
        nend = raw.find(b"\x00", nstart)
        if nend < 0: nend = nstart
        name = raw[nstart:nend].decode("utf-8", "replace")
        descs.append((name, ftype, uncomp_sz, dataoffset, comp_sz))

    # Uncompressed sections are stored first, then the compressed blocks.
    # The compressed block region therefore starts after all uncompressed data.
    uncomp_total = sum(((u + alignment - 1) // alignment) * alignment
                       for (_, _, u, _, cs) in descs if cs == 0)
    comp_start = data_off + uncomp_total

    out = []
    decompressed = None
    decomp_off = 0
    for (name, ftype, uncomp_sz, dataoffset, comp_sz) in descs:
        if comp_sz != 0:
            if decompressed is None:
                decompressed = bytearray()
                p = comp_start
                for bsz in block_sizes:
                    chunk = raw[p:p + bsz]
                    try:
                        decompressed += zlib.decompress(chunk)
                    except zlib.error:
                        # Some large archives have a small non-zlib padding gap
                        # between blocks (observed 128 bytes), which desyncs the
                        # fixed offset stepping. Detect and skip to the next
                        # valid zlib stream.
                        d = zlib.decompressobj()
                        try:
                            decompressed += d.decompress(chunk)
                        except zlib.error:
                            nxt = raw.find(b"\x78\x9c", p + 2, p + bsz + 64)
                            for magic in (b"\x78\x01", b"\x78\x5e", b"\x78\xda"):
                                alt = raw.find(magic, p + 2, p + bsz + 64)
                                if alt != -1 and (nxt == -1 or alt < nxt):
                                    nxt = alt
                            if nxt != -1:
                                d2 = zlib.decompressobj()
                                decompressed += d2.decompress(raw[nxt:])
                    p += bsz
            data = bytes(decompressed[decomp_off:decomp_off + uncomp_sz])
        else:
            start = data_off + dataoffset
            data = raw[start:start + uncomp_sz]
        out.append((name, ftype, data))
        decomp_off += (uncomp_sz + alignment - 1) // alignment * alignment
    return out


def safe_relpath(name, idx):
    s = name.replace("\\", "/").lstrip("/")
    parts = [p for p in s.split("/") if p not in ("", ".", "..")]
    if not parts:
        return f"_section_{idx:04d}"
    return "/".join(parts)


def main():
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    game, out = sys.argv[1], sys.argv[2]
    only = None
    if "--only" in sys.argv:
        only = [x.strip().lower() for x in sys.argv[sys.argv.index("--only") + 1].split(",")]

    os.makedirs(out, exist_ok=True)
    done_path = os.path.join(out, "_done.txt")
    err_path  = os.path.join(out, "_errors.txt")
    done = set()
    if os.path.exists(done_path):
        done = set(open(done_path, encoding="utf-8").read().split("\n"))

    archives = []
    for root, _, files in os.walk(game):
        for fn in files:
            if fn.lower().endswith(".ssg"):
                archives.append(os.path.join(root, fn))
    if only:
        archives = [a for a in archives if any(o in a.lower() for o in only)]
    archives.sort()

    print(f"Found {len(archives)} .ssg archives")
    fdone = open(done_path, "a", encoding="utf-8")
    ferr  = open(err_path, "a", encoding="utf-8")
    ok = fail = skipped = 0
    files_written = bytes_written = 0
    t0 = time.time()

    for i, ap in enumerate(archives, 1):
        rel = os.path.relpath(ap, game)
        if rel in done:
            skipped += 1
            continue
        try:
            raw = open(ap, "rb").read()
            sections = parse_ssg(raw)
            base = os.path.splitext(rel)[0]
            for idx, (name, ftype, data) in enumerate(sections):
                dest = os.path.join(out, base, safe_relpath(name, idx))
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                with open(dest, "wb") as f:
                    f.write(data)
                files_written += 1
                bytes_written += len(data)
            fdone.write(rel + "\n"); fdone.flush()
            ok += 1
            print(f"[{i}/{len(archives)}] OK {rel} ({len(sections)} files)")
        except Exception as ex:
            ferr.write(f"{rel}\t{ex}\n"); ferr.flush()
            fail += 1
            print(f"[{i}/{len(archives)}] FAIL {rel}: {ex}")

    fdone.close(); ferr.close()
    dt = time.time() - t0
    print(f"\n=== DONE in {dt:.0f}s ===")
    print(f"archives: ok={ok} fail={fail} skipped={skipped}")
    print(f"files written: {files_written}  ({bytes_written/1024/1024:.0f} MB)")


if __name__ == "__main__":
    main()
