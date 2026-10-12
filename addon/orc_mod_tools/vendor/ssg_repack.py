#!/usr/bin/env python3
"""
ssg_repack.py - Repacker .ssg (Hexane Engine / RE: Operation Raccoon City)

Oferece o repack CIRURGICO (recomendado): mantem byte-identico a maioria dos
compressed-blocks de 64KB; recompensa SOMENTE o(s) chunk(s) que se interceptam
com o(s) entry(s) modificado(s). Perfeito para trocar UM .edgemodel.

Uso:
    python ssg_repack.py modify <orig.ssg> <out.ssg> --override <relpath> <newfile>
"""
import sys, os, struct, zlib
from ssg_extract_full import parse_ssg, HEADER_SIZE, SECTION_SIZE

CHUNK_SIZE = 65536


def u32(b, o, e): return struct.unpack_from(e + "I", b, o)[0]
def i32(b, o, e): return struct.unpack_from(e + "i", b, o)[0]
def u16(b, o, e): return struct.unpack_from(e + "H", b, o)[0]


def _align(v, a):
    return (v + (a - 1)) & ~(a - 1)


def parse_ssg_layout(raw):
    """Parseia header + descs (com offsets) + block_sizes. Sem decompress."""
    ver_le = struct.unpack_from("<I", raw, 0)[0]
    e = ">" if ver_le > 0xFFFF else "<"
    version = u32(raw, 0, e)
    sec_infos = i32(raw, 8, e)
    sec_names = i32(raw, 12, e)
    comp_size = i32(raw, 24, e)
    alignment = u16(raw, 28, e)
    if version not in (5, 6):
        raise ValueError(f"version {version}")
    if version == 5:
        alignment = 16; comp_size = 0
    if alignment == 0:
        alignment = 16
    block_sizes = []
    pos = HEADER_SIZE + sec_infos
    for _ in range(comp_size // 4):
        sz = i32(raw, pos, e); pos += 4
        if sz == 0: break
        block_sizes.append(sz)
    names_off = HEADER_SIZE + sec_infos + comp_size
    data_off = names_off + sec_names
    count = sec_infos // SECTION_SIZE
    descs = []
    for i in range(count):
        b = HEADER_SIZE + SECTION_SIZE * i
        d = {"name_off": i32(raw, b + 4, e), "uncomp_sz": i32(raw, b + 8, e),
             "dataoffset": i32(raw, b + 16, e), "ftype": u32(raw, b + 20, e),
             "comp_sz": i32(raw, b + 28, e), "_raw": bytes(raw[b:b + SECTION_SIZE])}
        nstart = names_off + d["name_off"]
        nend = raw.find(b"\x00", nstart)
        if nend < 0: nend = nstart
        d["name"] = raw[nstart:nend].decode("utf-8", "replace")
        descs.append(d)
    return {"raw": e, "version": version, "sec_infos": sec_infos,
            "sec_names": sec_names, "comp_size": comp_size, "alignment": alignment,
            "count": count, "descs": descs, "block_sizes": block_sizes,
            "names_off": names_off, "data_off": data_off}


def repack_modify(orig_path, out_path, entry_overrides=None):
    """REPACK CIRURGICO: recompensa so os chunks que contem entries modificados."""
    entry_overrides = entry_overrides or {}
    raw = open(orig_path, "rb").read()
    L = parse_ssg_layout(raw)
    e = L["raw"]; alignment = L["alignment"]
    names_off = L["names_off"]; data_off = L["data_off"]
    descs_l = L["descs"]
    chunk_orig_sizes = list(L["block_sizes"])  # todos positivos (uint)

    # 1) decompress full blob per chunk
    chunk_decomp = []
    pc = data_off
    for csz in chunk_orig_sizes:
        chunk = raw[pc:pc + csz]; pc += csz
        chunk_decomp.append(bytearray(zlib.decompress(chunk)))

    blob = bytearray()
    chunk_start = []
    for cd in chunk_decomp:
        chunk_start.append(len(blob))
        blob += cd

    def _ci(pos): return pos // CHUNK_SIZE

    # 2) overwrite + track touched chunks
    touched = set()
    decomp_off = 0
    for d in descs_l:
        usz = d["uncomp_sz"]; lo = decomp_off; hi = decomp_off + usz
        if d["name"] in entry_overrides:
            nd = entry_overrides[d["name"]]
            if len(nd) > usz: nd = nd[:usz]
            elif len(nd) < usz: nd = nd + b"\x00" * (usz - len(nd))
            blob[lo:hi] = nd
            for c in range(_ci(lo), _ci(hi - 1) + 1):
                touched.add(c)
        decomp_off += _align(usz, alignment)

    # 3) orig compressed chunk bytes (para untouched)
    p_orig = data_off
    orig_chunk_bytes = []
    for csz in chunk_orig_sizes:
        orig_chunk_bytes.append(raw[p_orig:p_orig + csz]); p_orig += csz

    # 4) assemble compressed blob + new block_sizes
    new_block_sizes = []
    comp_blob = bytearray()
    for c in range(len(chunk_decomp)):
        if c in touched:
            cc = zlib.compress(bytes(blob[chunk_start[c]:chunk_start[c] + len(chunk_decomp[c])]), 9)
            comp_blob += cc; new_block_sizes.append(len(cc))
        else:
            comp_blob += orig_chunk_bytes[c]; new_block_sizes.append(len(orig_chunk_bytes[c]))

    # 5) names verbatim
    names_blob = raw[names_off:names_off + L["sec_names"]]

    # 6) descs: copy originals, patch comp_sz
    descs_blob = bytearray()
    decomp_off = 0
    for d in descs_l:
        bb = bytearray(d["_raw"])
        usz = d["uncomp_sz"]
        if usz > 0:
            lo = decomp_off; hi = decomp_off + usz
            c0 = _ci(lo); c1 = _ci(hi - 1)
            new_cs = sum(new_block_sizes[c] for c in range(c0, c1 + 1))
        else:
            new_cs = 0
        if d["name"] in entry_overrides:
            struct.pack_into(e + "I", bb, 28, new_cs)
        descs_blob += bb
        decomp_off += _align(usz, alignment)

    # 7) header
    comp_size_new = len(new_block_sizes) * 4
    header = bytearray(raw[:HEADER_SIZE])
    struct.pack_into(e + "I", header, 8, L["sec_infos"])
    struct.pack_into(e + "I", header, 12, len(names_blob))
    struct.pack_into(e + "I", header, 24, comp_size_new)
    struct.pack_into(e + "H", header, 28, L["alignment"])

    out = bytearray()
    out += header
    out += descs_blob
    out += b"".join(struct.pack(e + "I", s) for s in new_block_sizes)
    out += names_blob
    out += comp_blob
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(bytes(out))
    return len(out), len(descs_l), touched


def main():
    if len(sys.argv) < 5:
        print(__doc__); sys.exit(1)
    if sys.argv[1] != "modify":
        print("Only 'modify' supported"); sys.exit(1)
    orig, outp = sys.argv[2], sys.argv[3]
    overrides = {}
    rest = sys.argv[5:]
    i = 0
    while i < len(rest):
        if rest[i] == "--override":
            overrides[rest[i + 1]] = open(rest[i + 2], "rb").read(); i += 3
        else: i += 1
    size, nsec, touched = repack_modify(orig, outp, overrides)
    print(f"[OK] {outp} ({size} bytes, {nsec} sections, {len(touched)} chunks recompressed)")
    raw = open(outp, "rb").read()
    try:
        secs = parse_ssg(raw); print(f"  Re-parse OK: {len(secs)} sections")
    except Exception as ex:
        print(f"  Re-parse FAIL: {ex}")


if __name__ == "__main__":
    main()



def repack_full(orig_path, out_path, entry_overrides=None):
    # FULL repack: allows a section to GROW (natural override size). Re-decompresses
    # all chunks, applies overrides at natural length, re-layouts sections (aligned),
    # rechunks to 64KB, recompresses, rewrites the block_sizes array + per-section
    # uncomp_sz (@8). comp_sz (@28) is patched ONLY for overridden entries (real
    # compressed size of their new chunks); all other descriptors keep their
    # original @28 (sentinels -2/-3 are preserved) and @16 is left untouched.
    # Read model (engine == parse_ssg): decompress chunks by block_sizes -> blob;
    # read each section by cumulative aligned decomp_off + uncomp_sz. So @28/@16
    # are flags/positions that must NOT be zeroed for untouched sections.
    entry_overrides = entry_overrides or {}
    raw = open(orig_path, "rb").read()
    L = parse_ssg_layout(raw)
    e = L["raw"]; align = L["alignment"]; descs = L["descs"]; bs = L["block_sizes"]
    # 1) decompress ALL chunks -> contiguous blob
    p = L["data_off"]; blob = bytearray()
    for csz in bs:
        blob += zlib.decompress(raw[p:p + csz]); p += csz
    # 2) original section decomp offsets (aligned)
    sec_off = []; o = 0
    for d in descs:
        sec_off.append(o); o += _align(d["uncomp_sz"], align)
    # 3) build new blob w/ overrides (natural size) + track new lo/usz
    nb = bytearray(); nlo = []; nus = []
    for i, d in enumerate(descs):
        nlo.append(len(nb))
        if d["name"] in entry_overrides:
            sd = entry_overrides[d["name"]]
        else:
            sd = bytes(blob[sec_off[i]:sec_off[i] + d["uncomp_sz"]])
        nus.append(len(sd)); nb += sd
        pad = (_align(len(sd), align) - len(sd)) % align
        if pad: nb += b"\x00" * pad
    # 4) rechunk 64KB + recompress
    new_chunks = []; pos = 0
    while pos < len(nb):
        ch = nb[pos:pos + CHUNK_SIZE]; pos += CHUNK_SIZE
        new_chunks.append(zlib.compress(bytes(ch), 9))
    new_bs = [len(c) for c in new_chunks]
    comp_data = b"".join(new_chunks)
    # 5) rebuild descriptors
    names_blob = raw[L["names_off"]:L["names_off"] + L["sec_names"]]
    dlb = bytearray()
    for i, d in enumerate(descs):
        bb = bytearray(d["_raw"])
        struct.pack_into(e + "I", bb, 8, nus[i])  # uncomp_sz (edgemodel grows)
        if d["name"] in entry_overrides:
            c0 = nlo[i] // CHUNK_SIZE
            if nus[i] > 0:
                c1 = (nlo[i] + nus[i] - 1) // CHUNK_SIZE
                nc = sum(new_bs[c] for c in range(c0, c1 + 1))
            else:
                nc = 0
            struct.pack_into(e + "I", bb, 28, nc)  # comp_sz (real, new)
            doff = sum(new_bs[:c0]) if c0 < len(new_bs) else 0
            struct.pack_into(e + "I", bb, 16, doff)  # dataoffset (compressed)
        # else: keep original @28 (sentinel) + @16 untouched
        dlb += bb
    # 6) header
    header = bytearray(raw[:HEADER_SIZE])
    struct.pack_into(e + "I", header, 8, len(descs) * SECTION_SIZE)
    struct.pack_into(e + "I", header, 12, len(names_blob))
    struct.pack_into(e + "I", header, 24, len(new_bs) * 4)
    struct.pack_into(e + "H", header, 28, align)
    out = bytearray()
    out += header; out += dlb
    out += b"".join(struct.pack(e + "I", s) for s in new_bs)
    out += names_blob; out += comp_data
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "wb") as f: f.write(bytes(out))
    return len(out), len(descs)
