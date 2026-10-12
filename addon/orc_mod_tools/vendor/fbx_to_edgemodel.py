#!/usr/bin/env python3
"""
fbx_to_edgemodel.py — Conversor FBX/JSON → .edgemodel (Hexane Engine FM6S)

ACEITA DOIS MODOS DE JSON:
  A) RAW BYTES (byte-exact — recomendado para round-trip testing):
     { "meshes": [{ "subs": [{ "index_raw": HEX, "vertex_raw": HEX, "skin_raw": HEX,
       "vertex_size": N, "index_size": N, "skin_size": N, "skin_vertex_count": N,
       "vertex_count": N, "face_count": N, "stride": 52, "face_start": 0 }] }] }
  B) SEMANTIC FLOATS (do Blender — pos/norm/uv/tan/bitan como floats):
     { "meshes": [{ "subs": [{ "indices":[u16], "vertices":[float...], "skin":[[b0,w0,b1,w1]],
       "stride": 52, "face_start": 0, "vertex_count": N }] }] }

Layout FM6S (validado via round-trip em 12.425 arquivos):
  header_global(0xB4) | MeshInfo_table(N×0x84) | submesh_hdr(S×0x6C) | data
  Cada submesh: [idx][vtx][pad16][skin], onde skin_off = align(vertex_end, 16).
"""
import struct, json, sys, os, argparse, subprocess

FM6S_MAGIC = b"FM6S"
FM6S_VERSION = 0x12
HDR_GLOBAL_SIZE = 0xB4
MESHINFO_SIZE = 0x84
SUBMESH_HDR_SIZE = 0x6C
STRIDE_52, STRIDE_28, STRIDE_24, STRIDE_12 = 52, 28, 24, 12

def align(v, a=16):
    return (v + (a - 1)) & ~(a - 1)


def encode_vertex(verts, stride, vc):
    """Codifica floats → bytes no layout do stride (modo SEMÂNTICO).

    NOTA: half-floats (2e) contam como 1 valor Python mas ocupam 2 bytes.
    Entao fpu (floats-per-vertex no JSON) != stride//4 para layouts com UV.
    """
    # valores Python por vértice (depende do stride)
    FPU = {52: 14, 28: 8, 24: 6, 12: 3}
    fpu = FPU.get(stride, stride // 4)
    out = bytearray()
    for i in range(vc):
        base = i * fpu
        if stride == STRIDE_52:
            out += struct.pack("<6f", *verts[base:base+6])
            out += struct.pack("<2e", float(verts[base+6]), float(verts[base+7]))
            out += struct.pack("<6f", *verts[base+8:base+14])
        elif stride == STRIDE_28:
            out += struct.pack("<6f", *verts[base:base+6])
            out += struct.pack("<2e", float(verts[base+6]), float(verts[base+7]))
        elif stride == STRIDE_24:
            out += struct.pack("<6f", *verts[base:base+6])
        elif stride == STRIDE_12:
            out += struct.pack("<3f", *verts[base:base+3])
        else:
            out += struct.pack(f"<{stride//4}f", *verts[base:base + stride//4])
    return bytes(out)


def encode_skin(skin_list):
    """Codifica skin: 8 bytes/vertice (bone_idx uint16×2 + weight half×2)."""
    if not skin_list:
        return b"", 0
    out = bytearray()
    for sv in skin_list:
        if len(sv) >= 4:
            b0, w0, b1, w1 = int(sv[0]), float(sv[1]), int(sv[2]), float(sv[3])
        elif len(sv) == 2:
            b0, w0 = int(sv[0]), float(sv[1]); b1, w1 = 0, 0.0
        else:
            b0, w0, b1, w1 = 0, 0.0, 0, 0.0
        out += struct.pack("<HH", b0, b1)
        out += struct.pack("<ee", w0, w1)
    return bytes(out), len(skin_list)


def build_sub(sub):
    """Extrai (idx_bytes, vtx_bytes, skin_bytes, vc, svc) de um sub do JSON."""
    stride = sub.get("stride", STRIDE_52)

    if "index_raw" in sub:
        idx_bytes = bytes.fromhex(sub["index_raw"])
    else:
        idx_list = sub["indices"]
        idx_bytes = struct.pack(f"<{len(idx_list)}H", *idx_list)

    if "vertex_raw" in sub:
        vtx_bytes = bytes.fromhex(sub["vertex_raw"])
        vc = sub.get("vertex_count", len(vtx_bytes) // stride)
    else:
        FPU = {52: 14, 28: 8, 24: 6, 12: 3}
        fpu = FPU.get(stride, stride // 4)
        vc = sub.get("vertex_count", len(sub["vertices"]) // fpu)
        vtx_bytes = encode_vertex(sub["vertices"], stride, vc)

    if "skin_raw" in sub:
        skin_bytes = bytes.fromhex(sub["skin_raw"])
        svc = sub.get("skin_vertex_count", len(skin_bytes) // 8)
    else:
        skin_bytes, n_skin = encode_skin(sub.get("skin", []))
        svc = sub.get("skin_vertex_count", n_skin)

    return idx_bytes, vtx_bytes, skin_bytes, vc, svc


def write_edgemodel(data, out_path):
    mesh_count = len(data["meshes"])
    total_subs = sum(len(m["subs"]) for m in data["meshes"])
    sub_hdrs_start = HDR_GLOBAL_SIZE + mesh_count * MESHINFO_SIZE

    out = bytearray()
    # 1) Header global
    hdr = bytearray(HDR_GLOBAL_SIZE)
    hdr[0:4] = FM6S_MAGIC
    struct.pack_into("<i", hdr, 0x04, FM6S_VERSION)
    struct.pack_into("<i", hdr, 0x08, data.get("flags", 0))
    struct.pack_into("<i", hdr, 0x0C, mesh_count)
    struct.pack_into("<i", hdr, 0x10, data.get("unk_0x10", 160))
    struct.pack_into("<i", hdr, 0x14, data.get("unk_0x14", 0))
    struct.pack_into("<i", hdr, 0x20, HDR_GLOBAL_SIZE)
    out += hdr

    # 2,3) MeshInfo table + submesh headers (reservado)
    out += b"\x00" * (mesh_count * MESHINFO_SIZE)
    out += b"\x00" * (total_subs * SUBMESH_HDR_SIZE)

    # 4) Data sections
    cur = len(out)
    records = []
    fi = 0
    for mi, mesh in enumerate(data["meshes"]):
        for si, sub in enumerate(mesh["subs"]):
            idx_bytes, vtx_bytes, skin_bytes, vc, svc = build_sub(sub)
            idx_off = cur
            vtx_off = cur + len(idx_bytes)
            skin_off = align(vtx_off + len(vtx_bytes), 16)
            pad = b"\x00" * (skin_off - (vtx_off + len(vtx_bytes)))
            cur = skin_off + len(skin_bytes)

            records.append({
                "flat_idx": fi, "mi": mi,
                "index_offset": idx_off, "declared_index_size": len(idx_bytes),
                "vertex_offset": vtx_off, "vertex_size": len(vtx_bytes),
                "skin_offset": skin_off, "skin_size": len(skin_bytes),
                "skin_vertex_count": svc, "vertex_count": vc,
                "face_count": len(idx_bytes) // 6,
                "face_start": sub.get("face_start", 0),
                "idx_bytes": idx_bytes, "vtx_bytes": vtx_bytes,
                "skin_bytes": skin_bytes, "pad_bytes": pad,
            })
            fi += 1

    for rec in records:
        out += rec["idx_bytes"] + rec["vtx_bytes"] + rec["pad_bytes"] + rec["skin_bytes"]

    # 5) Fill MeshInfo
    shc = sub_hdrs_start
    for mi, mesh in enumerate(data["meshes"]):
        pos = HDR_GLOBAL_SIZE + mi * MESHINFO_SIZE
        struct.pack_into("<i", out, pos + 0x00, len(mesh["subs"]))
        struct.pack_into("<i", out, pos + 0x04, shc)
        struct.pack_into("<i", out, pos + 0x08, mesh.get("lod", 0))
        struct.pack_into("<i", out, pos + 0x0C, mesh.get("mat_offset", -1))
        shc += len(mesh["subs"]) * SUBMESH_HDR_SIZE

    # 6) Fill submesh headers
    for rec in records:
        pos = sub_hdrs_start + rec["flat_idx"] * SUBMESH_HDR_SIZE
        h = bytearray(SUBMESH_HDR_SIZE)
        struct.pack_into("<i", h, 0x0C, rec["face_count"])
        struct.pack_into("<i", h, 0x10, rec["index_offset"])
        struct.pack_into("<i", h, 0x14, rec["declared_index_size"])
        struct.pack_into("<i", h, 0x18, rec["face_start"])
        struct.pack_into("<i", h, 0x1C, rec["vertex_count"])
        struct.pack_into("<i", h, 0x2C, rec["vertex_offset"])
        struct.pack_into("<i", h, 0x30, rec["vertex_size"])
        struct.pack_into("<i", h, 0x3C, rec["skin_size"])
        struct.pack_into("<i", h, 0x44, rec["face_count"])
        struct.pack_into("<i", h, 0x48, rec["skin_vertex_count"])
        out[pos:pos + SUBMESH_HDR_SIZE] = h

    with open(out_path, "wb") as f:
        f.write(bytes(out))
    return len(out), records


def main():
    ap = argparse.ArgumentParser(description="FBX JSON -> .edgemodel converter")
    ap.add_argument("--json", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    with open(a.json) as f:
        data = json.load(f)
    size, recs = write_edgemodel(data, a.out)
    mode = "raw" if "vertex_raw" in (recs[0] if recs else {}) else "semantic"
    print(f"[OK] {a.out} ({size} bytes, {len(data['meshes'])} meshes, {len(recs)} subs, {mode})")
    rt = os.path.join(os.path.dirname(os.path.abspath(__file__)), "roundtrip_edgemodel.py")
    r = subprocess.run([sys.executable, rt, a.out], capture_output=True, text=True, timeout=60)
    print(r.stdout[:500])

if __name__ == "__main__":
    main()
