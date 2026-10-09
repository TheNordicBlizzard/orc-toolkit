#!/usr/bin/env python3
"""
SSG Extractor for Resident Evil: Operation Raccoon City (Hexane Engine / Slant Six)
Based on reverse-engineering by PiMoNFeeD (ORCToolKit, MIT license).

Extracts the internal files (e.g. .edgemodel, .matb, .dds, .minfo) from an .ssg
archive. These .edgemodel files can then be imported into Blender with the
ORC Blender script (PiMoNFeeD's, posted on residentevilmodding.boards.net).

Usage:
    python ssg_extract.py <file_or_folder> [output_dir]
"""
import sys, os, struct, zlib

HEADER_SIZE = 32
SECTION_SIZE = 32

TYPE_NAMES = {
    0x00000001: "bin", 0x00000002: "txt", 0x00000003: "dds",
    0x00000004: "matb", 0x00000005: "edgemodel", 0x00000006: "minfo",
}


class SSG:
    def __init__(self, path):
        self.path = path
        self.sections = []  # (name, type, data)
        self.endian = "<"
        self._parse()

    def _u32(self, buf, off):
        return struct.unpack_from(self.endian + "I", buf, off)[0]

    def _i32(self, buf, off):
        return struct.unpack_from(self.endian + "i", buf, off)[0]

    def _parse(self):
        raw = open(self.path, "rb").read()
        # endianness detection (game style)
        ver_le = struct.unpack_from("<I", raw, 0)[0]
        self.endian = ">" if ver_le > 0xFFFF else "<"

        version   = self._u32(raw, 0)
        padding1  = self._u32(raw, 4)
        sec_infos = self._i32(raw, 8)
        sec_names = self._i32(raw, 12)
        sec_data  = self._i32(raw, 16)
        comp_blocks_size = self._i32(raw, 24)
        alignment = struct.unpack_from(self.endian + "H", raw, 28)[0]

        if version not in (5, 6):
            raise ValueError(f"Unsupported SSG version {version} (expected 5 or 6)")
        if version == 5:
            alignment = 16
            comp_blocks_size = 0
        if alignment == 0:
            alignment = 16

        # compressed block sizes (each block = 64KB uncompressed)
        block_sizes = []
        pos = HEADER_SIZE + sec_infos
        for _ in range(comp_blocks_size // 4):
            sz = self._i32(raw, pos)
            pos += 4
            if sz == 0:
                break
            block_sizes.append(sz)

        names_off = HEADER_SIZE + sec_infos + comp_blocks_size
        data_off  = names_off + sec_names

        section_count = sec_infos // SECTION_SIZE
        decompressed = None
        comp_data_off = 0

        for i in range(section_count):
            base = HEADER_SIZE + SECTION_SIZE * i
            name_crc   = self._i32(raw, base + 0)
            name_off   = self._i32(raw, base + 4)
            uncomp_sz  = self._i32(raw, base + 8)
            unknown    = self._i32(raw, base + 12)
            dataoffset = self._i32(raw, base + 16)
            ftype      = self._u32(raw, base + 20)
            uncomp_crc = self._i32(raw, base + 24)
            comp_sz    = self._i32(raw, base + 28)

            # name
            nstart = names_off + name_off
            nend = raw.index(b"\x00", nstart)
            name = raw[nstart:nend].decode("utf-8", "replace")

            if comp_blocks_size == 0:
                comp_sz = 0
            is_compressed = (comp_sz != 0)

            if is_compressed:
                if decompressed is None:
                    decompressed = bytearray()
                    p = data_off
                    for bsz in block_sizes:
                        chunk = raw[p:p + bsz]
                        d = zlib.decompressobj()
                        decompressed += d.decompress(chunk)
                        p += bsz
                data = bytes(decompressed[comp_data_off:comp_data_off + uncomp_sz])
            else:
                start = data_off + dataoffset
                data = raw[start:start + uncomp_sz]

            self.sections.append((name, ftype, data))
            comp_data_off += (uncomp_sz + alignment - 1) // alignment * alignment

    def extract(self, outdir, verbose=True):
        total = 0
        for name, ftype, data in self.sections:
            # section names are like "dlc/pack1/characters/leon/..." -> keep last part + dirs
            safe = name.replace("\\", "/").lstrip("/")
            if not safe or safe.endswith("/"):
                safe = f"section_{total}"
            # avoid path traversal
            safe = "/".join(p for p in safe.split("/") if p not in ("", ".", ".."))
            dest = os.path.join(outdir, safe)
            os.makedirs(os.path.dirname(dest) or outdir, exist_ok=True)
            with open(dest, "wb") as f:
                f.write(data)
            total += 1
            if verbose:
                print(f"  [{ftype:#010x}] {len(data):>10} B  {name}")
        return total


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    src = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else None

    files = []
    if os.path.isdir(src):
        for root, _, fnames in os.walk(src):
            for fn in fnames:
                if fn.lower().endswith(".ssg"):
                    files.append(os.path.join(root, fn))
    else:
        files = [src]

    for f in files:
        print(f"\n=== {f} ===")
        try:
            ssg = SSG(f)
        except Exception as e:
            print(f"  ERROR: {e}")
            continue
        odir = out or (os.path.splitext(f)[0] + "_extracted")
        n = ssg.extract(odir)
        print(f"  -> {n} files written to {odir}")


if __name__ == "__main__":
    main()
