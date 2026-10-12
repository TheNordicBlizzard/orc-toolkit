import struct,zlib
HEADER_SIZE=32
SECTION_SIZE=32
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