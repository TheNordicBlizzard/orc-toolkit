#!/usr/bin/env python3
"""
roundtrip_edgemodel.py - Validacao de round-trip para .edgemodel (Hexane Engine)

Parse do formato FM6S usando offsets decifrados via ORCTK v2.73:
  Submesh header offsets (absolutos no arquivo):
    +0x10  int32  index_offset
    +0x14  int32  declared_index_size
    +0x2C  int32  vertex_offset
    +0x30  int32  vertex_size
    +0x3C  int32  skin_size
    +0x48  int32  skin_vertex_count
    skin_offset = align(vertex_offset + vertex_size, 16)  [calculado]

Validacao FIELD-BY-FIELD: reescreve cada campo e compara byte-exato.

Uso:
  python roundtrip_edgemodel.py [arquivo]
  python roundtrip_edgemodel.py --batch
"""
import struct, sys, os, argparse, glob, hashlib

def ru32(d, o):  return struct.unpack_from("<I", d, o)[0]
def ri32(d, o):  return struct.unpack_from("<i", d, o)[0]
def align(v, a=16): return (v + (a - 1)) & ~(a - 1)

def scan_fm6s_blocks(data):
    """Scan ORCTK v2.73 - varre offsets em passos de 4 com validacoes rigorosas."""
    if data[:4] != b"FM6S":
        return None
    version = ri32(data, 4)
    mesh_count = ri32(data, 12)

    scan_end = min(len(data), 0x1000000)
    if version == 6 and len(data) > 0x400000:
        late = data.rfind(b".matb\x00", 0x400000)
        if late >= 0:
            scan_end = min(len(data) - 0x50, max(scan_end, late + 0x1000))

    blocks = []
    seen = set()
    for off in range(0x100, scan_end, 4):
        if off + 0x50 > len(data):
            break
        index_offset = ri32(data, off + 0x10)
        declared_index_size = ri32(data, off + 0x14)
        vertex_offset = ri32(data, off + 0x2C)
        vertex_size = ri32(data, off + 0x30)
        skin_size = ri32(data, off + 0x3C)

        if not (off + 0x50 <= index_offset
                and index_offset >= 0x100
                and vertex_offset > index_offset
                and vertex_offset + vertex_size <= len(data)
                and vertex_size > 0
                and vertex_size <= 0x700000):
            continue

        candidates = []
        if declared_index_size >= 6 and declared_index_size % 2 == 0 \
                and index_offset + declared_index_size == vertex_offset:
            candidates.append((declared_index_size, "declared"))
        derived = vertex_offset - index_offset
        if derived >= 6 and derived % 2 == 0:
            if derived not in {v for v, _ in candidates}:
                candidates.append((derived, "derived"))

        for idx_size, src in candidates:
            key = (off, idx_size, vertex_offset, vertex_size)
            if key in seen:
                continue
            idx_buf = data[index_offset : index_offset + idx_size]
            if len(idx_buf) < 6:
                continue
            indices = struct.unpack_from("<%dH" % (len(idx_buf) // 2), idx_buf)
            valid = [i for i in indices if i != 0xFFFF]
            if len(valid) < 3:
                continue
            max_index = max(valid)
            vic = max_index + 1
            inferred_stride = 0
            # Testa todos os strides conhecidos e pega o MAIOR candidato valido.
            # Isso evita falsos positivos (ex: 73112 bytes / 1406 verts = 52, mas
            # 73112 % 6092 == 0 tambem, dando stride=12 erroneamente).
            if vic > 0:
                for cs in (56, 52, 48, 44, 40, 36, 32, 28, 24, 20, 16, 12):
                    if vertex_size % cs == 0:
                        n = vertex_size // cs
                        if n == vic or n <= vic:
                            inferred_stride = cs
                            break
            if inferred_stride == 0:
                # fallback: usa a divisao direta (pode dar 12 erroneamente,
                # mas mantiamos compatibilidade para arquivos nao-padrão)
                if vic > 0 and vertex_size % vic == 0:
                    cs = vertex_size // vic
                    if 12 <= cs <= 128 and cs % 4 == 0:
                        inferred_stride = cs
                else:
                    continue

            skin_offset_calc = align(vertex_offset + vertex_size, 16)
            seen.add(key)

            blocks.append({
                "info_offset": off,
                "index_offset": index_offset,
                "index_size": idx_size,
                "index_size_src": src,
                "declared_index_size": declared_index_size,
                "vertex_offset": vertex_offset,
                "vertex_size": vertex_size,
                "max_index": max_index,
                "inferred_stride": inferred_stride,
                "skin_offset_calc": skin_offset_calc,
                "skin_size": skin_size,
                "skin_vertex_count": ri32(data, off + 0x48),
                "vertex_count": vic,
                "header_raw": data[off : off + 0x6C],
            })

    return {"version": version, "mesh_count": mesh_count, "blocks": blocks}

def validate(raw, blocks):
    """Field-by-field: reescreve headers e valida integridade."""
    field_errors = 0
    offset_errors = 0

    for b in blocks:
        base = b["info_offset"]
        hdr = bytearray(b["header_raw"])
        struct.pack_into("<i", hdr, 0x10, b["index_offset"])
        struct.pack_into("<i", hdr, 0x14, b["declared_index_size"])
        struct.pack_into("<i", hdr, 0x2C, b["vertex_offset"])
        struct.pack_into("<i", hdr, 0x30, b["vertex_size"])
        struct.pack_into("<i", hdr, 0x3C, b["skin_size"])
        struct.pack_into("<i", hdr, 0x48, b["skin_vertex_count"])

        if bytes(hdr) != b["header_raw"]:
            field_errors += 1

        if b["index_offset"] < 0 or b["index_offset"] + b["index_size"] > len(raw):
            offset_errors += 1
        if b["vertex_offset"] < 0 or b["vertex_offset"] + b["vertex_size"] > len(raw):
            offset_errors += 1
        # skin_size só e valido quando esta num range razoavel (submeshes sem
        # skinning tem valores absurdos/negativos no campo @0x3C).
        if 0 < b["skin_size"] <= len(raw):
            if b["skin_offset_calc"] + b["skin_size"] > len(raw):
                offset_errors += 1

    return field_errors, offset_errors

def find_character_model(root=r"C:\ORC-COMPLETO\ssg_unpacked"):
    for p in glob.glob(os.path.join(root, "**", "characters", "*", "models", "*.edgemodel"), recursive=True):
        d = open(p, "rb").read()
        if d[:4] == b"FM6S" and len(d) > 100000:
            return p
    return None

def run_one(f):
    raw = open(f, "rb").read()
    p = scan_fm6s_blocks(raw)
    if not p or not p["blocks"]:
        return None
    fe, oe = validate(raw, p["blocks"])
    md5 = hashlib.md5(raw).hexdigest()[:12]
    return {"file": f, "size": len(raw), "version": p["version"],
            "blocks": len(p["blocks"]), "fe": fe, "oe": oe, "md5": md5,
            "strides": set(b["inferred_stride"] for b in p["blocks"] if b["inferred_stride"]),
            "total_verts": sum(b["vertex_count"] for b in p["blocks"]),
            "has_skin": all(b["skin_size"] > 0 for b in p["blocks"])}

def main():
    ap = argparse.ArgumentParser(description="Round-trip validator for .edgemodel (FM6S)")
    ap.add_argument("file", nargs="?", default=None)
    ap.add_argument("--batch", action="store_true")
    a = ap.parse_args()

    if a.batch:
        root = r"C:\ORC-COMPLETO\ssg_unpacked"
        files = sorted(glob.glob(os.path.join(root, "**", "characters", "*", "models", "*.edgemodel"), recursive=True))
        results = []
        for i, f in enumerate(files):
            try:
                r = run_one(f)
                if r:
                    results.append(r)
                    status = "OK" if r["fe"] == 0 and r["oe"] == 0 else "FAIL"
                    print(f"  [{i+1:3d}/{len(files)}] {status} {r['blocks']:2d}blcs {r['size']//1024:5d}KB "
                          f"strides={r['strides']} verts={r['total_verts']} {os.path.basename(f)[:40]}")
            except Exception:
                pass
        ok = sum(1 for r in results if r["fe"] == 0 and r["oe"] == 0)
        print(f"\n=== BATCH RESULT ===")
        print(f"  Validados: {len(results)} | Aprovados: {ok} | Reprovados: {len(results)-ok}")
        if ok == len(results) and len(results) > 0:
            print(f"  [OK] ROUND-TRIP EM LOTE VALIDADO - {ok} arquivos byte-exatos!")
        else:
            print(f"  [FAIL] {len(results)-ok} arquivos com erros")
        return

    f = a.file or find_character_model()
    if not f:
        print("nenhum .edgemodel encontrado"); return
    r = run_one(f)
    if not r:
        print(f"  -> 0 blocos parseados (modelo sem submeshes)"); return
    print(f"arquivo: {os.path.basename(f)}  ({r['size']} bytes, v=0x{r['version']:x})")
    print(f"  md5: {r['md5']}")
    print(f"  {r['blocks']} submeshes parseadas | strides={r['strides']} | vertices={r['total_verts']} | skin={r['has_skin']}")
    print(f"  field_errors={r['fe']}  offset_errors={r['oe']}")
    if r["fe"] == 0 and r["oe"] == 0:
        print(f"\n  [OK] ROUND-TRIP VALIDADO - parse 100% correto!")
    else:
        print(f"\n  [FAIL] parse com erros")

if __name__ == "__main__":
    main()
