bl_info = {
    "name": "ORC Mod Tools",
    "author": "Hermes Agent",
    "version": (1, 1, 2),
    "blender": (5, 0, 0),
    "location": "View3D > Sidebar > ORC",
    "description": "Import native ORC models; unbound placeholder skin; native export blocked",
    "category": "Import-Export",
    "doc_url": "https://github.com/nousresearch/orc-mod-tools",
}

import bpy
import json
import os
import sys
import struct
import math
import numpy as np
import mathutils
from array import array
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator, Panel, AddonPreferences
from bpy_extras.io_utils import ImportHelper, ExportHelper
from mathutils import Vector, Matrix, Quaternion

# ─── Constants ────────────────────────────────────────────────────────────
DEFAULT_MOD_PATH = r"C:/ORC-Modding"
DEFAULT_GAME_PATH = r"D:\Resident Evil Operation Raccoon City"
CHUNK_SIZE = 65536
SKIN_ENTRY_SIZE = 8  # 4x uint8 weights + 4x uint8 bone_indices

# ─── Language / Translation ───────────────────────────────────────────────
UI_STRINGS = {
    "files": {"en": "Files", "pt_br": "Arquivos"},
    "import": {"en": "Import", "pt_br": "Importação"},
    "export": {"en": "Export", "pt_br": "Exportação"},
    "validation": {"en": "Validation", "pt_br": "Validação"},
    "configuration": {"en": "Configuration", "pt_br": "Configuração"},
    "materials_preview": {"en": "Basic MATB diffuse preview (DDS); not original shaders", "pt_br": "Prévia básica diffuse MATB (DDS); não são shaders originais"},
    "native_blocked": {"en": "Native SSG/edgemodel export BLOCKED: legacy writer fails native tables/skin. Use Blender FBX or Save As .blend; no in-game validation.", "pt_br": "Exportação nativa SSG/edgemodel BLOQUEADA: writer legado falha nas tabelas/skin nativas. Use FBX do Blender ou Salvar Como .blend; sem validação no jogo."},
    "rig_unvalidated": {"en": "Placeholder rig: bone palette / bind matrices are NOT validated; decoding a skeleton alone is insufficient. Numeric skin preserved; no automatic binding.", "pt_br": "Rig placeholder: paleta de ossos / matrizes de bind NÃO validadas; decodificar skeleton não basta. Skin numérica preservada; sem vínculo automático."},
    "panel_title":      {"en": "ORC Mod Tools", "pt_br": "Ferramentas ORC"},
    "import_label":     {"en": "Import SSG (.ssg → Blender)", "pt_br": "Importar SSG (.ssg → Blender)"},
    "export_label":     {"en": "Export Blender → .ssg", "pt_br": "Exportar Blender → .ssg"},
    "convert_label":    {"en": "Convert Mesh → .edgemodel", "pt_br": "Converter Malha → .edgemodel"},
    "mod_path_label":   {"en": "ORC-Modding Path", "pt_br": "Caminho ORC-Modding"},
    "game_path_label":  {"en": "Game Directory", "pt_br": "Diretório do Jogo"},
    "lang_label":       {"en": "Language", "pt_br": "Idioma"},
    "original_ssg":     {"en": "Original .ssg (template)", "pt_br": ".ssg original (modelo)"},
    "output_ssg":       {"en": "Output .ssg", "pt_br": ".ssg de saída"},
    "output_edm":       {"en": "Output .edgemodel", "pt_br": ".edgemodel de saída"},
    "edgemodel_path":   {"en": "Edgemodel path in SSG", "pt_br": "Caminho do .edgemodel no SSG"},
    "import_bones":     {"en": "Import Bones", "pt_br": "Importar Ossos"},
    "import_materials": {"en": "Import Materials", "pt_br": "Importar Materiais"},
    "create_collection": {"en": "Create Collection", "pt_br": "Criar Coleção"},
    "file_filter":      {"en": "SSG Files", "pt_br": "Arquivos SSG"},
    "convert_tooltip":  {"en": "Convert Blender mesh to .edgemodel (FM6S)", "pt_br": "Converter malha do Blender para .edgemodel (FM6S)"},
    "import_tooltip":   {"en": "Import .ssg archive into Blender", "pt_br": "Importar arquivo .ssg para o Blender"},
    "export_tooltip":   {"en": "Export Blender mesh to .ssg archive", "pt_br": "Exportar malha do Blender para arquivo .ssg"},
}

def _ui(key):
    """Return UI string in the active language."""
    try:
        prefs = bpy.context.preferences.addons["orc_mod_tools"].preferences
        lang = prefs.language
    except (KeyError, AttributeError):
        lang = 'en'
    return UI_STRINGS.get(key, {}).get(lang, UI_STRINGS.get(key, {}).get('en', key))

def _set_lang():
    """Ensure language preference is accessible."""
    pass

# ─── Module Path Setup ────────────────────────────────────────────────────
def ensure_mod_path():
    """Prefer this package's reviewed vendor modules, independent of external CLI.

    The legacy mod_path preference is retained for old preference files, but
    importing the addon never loads a mutable shared ORC-Modding writer.
    """
    mod_path = os.path.join(os.path.dirname(__file__), 'vendor')
    if not os.path.isdir(mod_path):
        raise RuntimeError('Bundled ORC parser folder missing')
    if mod_path in sys.path:
        sys.path.remove(mod_path)
    sys.path.insert(0, mod_path)
    return mod_path

# ─── Helper: Collections ──────────────────────────────────────────────────
def get_or_create_collection(name, parent):
    """Get existing collection or create a new one under parent."""
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        parent.children.link(col)
    return col

# ─── Edgemodel Vertex / Skin Reading (IMPORT) ─────────────────────────────
def read_vertex(data, base, stride):
    """Read a single vertex (pos, norm, uv) at *base* with the given *stride*.

    Layout by stride (all little-endian):
      52: pos(3f) norm(3f) uv(2e) pad(3f) pad(3f)
      56: pos(3f) norm(3f) pad(1f) uv(2e) pad(6f)
      44: pos(3f) norm(3f) pad(1f) uv(2e) pad(3f)
      40: pos(3f) norm(3f) uv(2e) pad(3f)
      32: pos(3f) norm(3f) pad(1f) uv(2e)
      28: pos(3f) norm(3f) uv(2e)
      24: pos(3f) norm(3f)
      12: pos(3f)
    """
    pos = struct.unpack_from('<3f', data, base)
    norm = (0.0, 0.0, 0.0)
    uv = (0.0, 0.0)
    if stride >= 24:
        norm = struct.unpack_from('<3f', data, base + 12)
    if stride == 52:
        uv = struct.unpack_from('<2e', data, base + 24)
    elif stride == 44:
        uv = struct.unpack_from('<2e', data, base + 28)  # 12+12+4=28
    elif stride in (56, 60):
        uv = struct.unpack_from('<2e', data, base + 28)  # 12+12+4=28
    elif stride == 40:
        uv = struct.unpack_from('<2e', data, base + 24)
    elif stride == 32:
        uv = struct.unpack_from('<2e', data, base + 28)
    elif stride == 28:
        uv = struct.unpack_from('<2e', data, base + 24)
    else:
        if stride >= 28:
            uv = struct.unpack_from('<2e', data, base + 24) if stride != 44 else struct.unpack_from('<2e', data, base + 28)
    return pos, norm, uv


def read_skin_raw(data, skin_off, count):
    """Read skin data: 4×uint8 weights + 4×uint8 bone indices per vertex (8 bytes/vert).

    Returns a list per vertex of [(bone_idx, weight), ...] with weight normalized
    to 0-1 and bone 255 treated as 'no bone'.
    """
    results = []
    for vi in range(count):
        off = skin_off + vi * SKIN_ENTRY_SIZE
        if off + SKIN_ENTRY_SIZE > len(data):
            results.append([])
            continue
        weights = struct.unpack_from('<4B', data, off)
        bone_indices = struct.unpack_from('<4B', data, off + 4)
        influences = []
        for j in range(4):
            if bone_indices[j] < 255 and weights[j] > 0:
                influences.append((bone_indices[j], weights[j] / 255.0))
        results.append(influences)
    return results


# ─── Skeleton Parsing (adapted from orc_import_blender.py) ────────────────
class _EdgeBone:
    __slots__ = ('position', 'angle', 'parent_id', 'name', 'bind_matrix')

    def __init__(self):
        self.position = Vector((0, 0, 0))
        self.angle = Quaternion((1, 0, 0, 0))
        self.parent_id = -1
        self.name = "root"
        self.bind_matrix = Matrix()


def _u32_le(data, off):
    return struct.unpack_from('<I', data, off)[0]


def _i32_le(data, off):
    return struct.unpack_from('<i', data, off)[0]


def _u16_le(data, off):
    return struct.unpack_from('<H', data, off)[0]


def _i16_le(data, off):
    return struct.unpack_from('<h', data, off)[0]


def parse_skeleton_bytes(raw):
    """Parse a .edgeskel blob (magic 20SE / ES02) into a list of _EdgeBone.

    Returns (bone_list, num_joints).  Uses the same offset layout as
    orc_import_blender.py::parse_skel / parse_bones.
    """
    header = raw[:4]
    if header not in (b'20SE', b'ES02'):
        raise ValueError(f"bad skeleton magic: {header!r}")
    if len(raw) < 0x34:
        raise ValueError('Truncated skeleton header')
    num_joints = _u16_le(raw, 0x10)
    # Verified 20SE: 0x08 is custom-data size, NOT joint count.
    if not 0 < num_joints <= 4096:
        raise ValueError('Invalid skeleton joint count')
    # Read header fields (offsets relative to file start)
    offset_base_pose = _u32_le(raw, 0x18)
    offset_parent_indices = _u32_le(raw, 0x1C)
    offset_custom_data = _u32_le(raw, 0x30)

    bones = []
    # Bone transforms start at offset_base_pose + 24
    bp = offset_base_pose + 24
    pp = offset_parent_indices + 0x1C
    name_start = offset_custom_data + num_joints * 4 + 0x30
    if (bp < 0x34 or bp + num_joints * 48 > len(raw)
            or pp < 0x34 or pp + num_joints * 2 > len(raw)
            or not 0x34 <= name_start < len(raw)):
        raise ValueError('Skeleton buffer span outside file')
    for i in range(num_joints):
        b = _EdgeBone()
        # angle: quaternion (x, y, z, w)  →  Blender (w, x, y, z)
        x, y, z, w = struct.unpack_from('<4f', raw, bp)
        b.angle = Quaternion((w, x, y, z))
        bp += 16
        # position: vec3 + pad(1f)
        px, py, pz = struct.unpack_from('<3f', raw, bp)
        b.position = Vector((px, py, pz))
        bp += 16  # 12 + 4 pad
        bp += 16  # scale (unused)
        bones.append(b)

    # Parent indices at offset_parent_indices + 0x1C
    pp = offset_parent_indices + 0x1C
    for i in range(num_joints):
        parent = _i16_le(raw, pp + i * 2)
        if parent < -1 or parent >= num_joints or parent == i:
            raise ValueError('Invalid skeleton parent index')
        bones[i].parent_id = parent
    for i in range(num_joints):
        visited = set()
        while i != -1:
            if i in visited:
                raise ValueError('Cyclic skeleton hierarchy')
            visited.add(i)
            i = bones[i].parent_id

    # Bone names at offset_custom_data + (num_joints * 4) + 0x30
    name_base = offset_custom_data + num_joints * 4 + 0x30
    for i in range(num_joints):
        end = raw.find(b'\x00', name_base)
        if end < 0 or end == name_base:
            raise ValueError("Invalid skeleton name")
        try:
            bones[i].name = raw[name_base:end].decode('ascii', 'replace')
        except Exception:
            bones[i].name = f"bone_{i:03d}"
        name_base = end + 1

    return bones, num_joints


# ─── IMPORT: SSG → Blender ────────────────────────────────────────────────
def _import_fm6s_blocks(data):
    """Traverse native FM6S 17/18 tables; never infer layout from padding.

    Counts at subheader +8/+10 are u16 vertex/index counts. Buffer sizes
    include alignment padding and are not counts. The legacy scanner remains
    unchanged for writer validation, but is not an import geometry parser.
    Layout cross-checked with Explorer V2 and Albam's Hexane implementation.
    """
    if len(data) < 28 or data[:4] != b'FM6S':
        raise ValueError('Invalid FM6S header')
    version = _u32_le(data, 4)
    if version not in (17, 18):
        raise ValueError(f'Unsupported native FM6S version: {version}')
    mesh_count = _u32_le(data, 12)
    table = _u32_le(data, 24)
    if not 0 < mesh_count <= 10000 or table + mesh_count * 144 > len(data):
        raise ValueError('Invalid FM6S mesh table')
    blocks = []
    for mi in range(mesh_count):
        count, subtable = struct.unpack_from('<2I', data, table + mi * 144)
        if count > 10000 or subtable + count * 144 > len(data):
            raise ValueError('Invalid FM6S submesh table')
        material_path = ''
        material_info = _u32_le(data, table + mi * 144 + 12)
        if material_info and material_info + 4 <= len(data):
            from .materials import read_string
            try:
                material_path = read_string(data, _u32_le(data, material_info))
            except ValueError:
                material_path = ''
        for si in range(count):
            off = subtable + si * 144
            vc, ic = struct.unpack_from('<2H', data, off + 8)
            if not vc or not ic:
                continue
            io = _u32_le(data, off + 16)
            vo, vs = struct.unpack_from('<2I', data, off + 44)
            wo = _u32_le(data, off + 64)
            stride, remainder = divmod(vs, vc)
            if remainder or stride not in (12, 24, 28, 32, 40, 44, 52, 56, 60):
                raise ValueError(f'Unsupported FM6S vertex stride: {stride}')
            if vo + vs > len(data) or io + ic * 2 > len(data) or ic % 3:
                raise ValueError('Invalid FM6S geometry buffers')
            indices = struct.unpack_from(f'<{ic}H', data, io)
            if max(indices) >= vc:
                raise ValueError('FM6S index outside vertex buffer')
            # Position-only shadow geometry has no usable skin/UV semantics.
            skin_count = vc if stride > 12 and wo and wo + vc * 8 <= len(data) else 0
            blocks.append({'info_offset': off, 'vertex_offset': vo,
                           'vertex_count': vc, 'vertex_size': vs,
                           'inferred_stride': stride, 'index_offset': io,
                           'index_size': ic * 2, 'skin_offset_calc': wo,
                           'skin_vertex_count': skin_count, 'material_path': material_path})
    return {'version': version, 'mesh_count': mesh_count, 'blocks': blocks}


def _find_edgemodels(sections):
    """Return [(entry_name, edm_bytes)] for all .edgemodel sections."""
    result = []
    for name, ftype, data in sections:
        if isinstance(name, str) and name.endswith('.edgemodel'):
            if data[:4] == b'FM6S':
                result.append((name, data))
    return result


def _find_skeletons(sections):
    """Return [(entry_name, skel_bytes)] for skeleton sections (20SE/ES02)."""
    result = []
    for name, ftype, data in sections:
        if len(data) >= 4 and data[:4] in (b'20SE', b'ES02'):
            result.append((name, data))
    return result


def _extract_skeleton_from_game(game_dir, char_name):
    """Read a matching skeleton SSG under dlc/**/Characters/skel.

    Files are only read; sections must be decompressed before 20SE parsing.
    Ambiguous matches are rejected rather than guessing a character's rig.
    """
    from pathlib import Path
    from ssg_extract_full import parse_ssg
    key = char_name.lower()
    root = Path(game_dir)
    candidates = sorted(p for p in root.glob('dlc/**/Characters/skel/*.ssg')
                        if p.stem.lower() == key)
    candidates += sorted(p for p in (root / 'skel').glob('*')
                         if p.is_file() and p.stem.lower() == key)
    blobs = []
    for path in candidates:
        raw = path.read_bytes()
        if raw[:4] in (b'20SE', b'ES02'):
            blobs.append(raw)
        else:
            blobs.extend(data for _, data in _find_skeletons(parse_ssg(raw)))
    unique = list(dict.fromkeys(blobs))
    if len(unique) > 1:
        raise ValueError(f'Ambiguous skeleton match: {char_name}')
    return unique[0] if unique else None


def import_ssg(filepath, mod_path, game_path=None, import_bones=True,
               import_uvs=True, import_materials=True, edgemodel_entry=''):
    """Import an .ssg file into the current Blender scene.

    Creates meshes from native FM6S 17/18 tables. When requested, numeric
    skin groups and an UNBOUND placeholder armature are retained. Decoded
    external skeleton counts do not prove mesh palette or bind association.
    No automatic Armature modifier is added before those are validated.
    """
    if mod_path and mod_path not in sys.path and os.path.isdir(mod_path):
        sys.path.insert(0, mod_path)

    from ssg_extract_full import parse_ssg

    raw = open(filepath, 'rb').read()
    sections = [(os.path.basename(filepath), 0, raw)] if raw[:4] == b'FM6S' else parse_ssg(raw)
    edm_list = _find_edgemodels(sections)
    if edgemodel_entry:
        edm_list = [(name, data) for name, data in edm_list if name == edgemodel_entry]
    if not edm_list:
        ssg_name = os.path.basename(filepath)
        raise ValueError(f"No .edgemodel sections found in {ssg_name}")

    # Determine character name for skeleton lookup
    char_name = os.path.basename(filepath).replace('.ssg', '')
    first_edm_name = edm_list[0][0]
    parts = first_edm_name.replace('\\', '/').split('/')
    if len(parts) >= 4:
        char_name = parts[3]

    # Try to find skeleton data
    skel_sections = _find_skeletons(sections)
    skel_data = None
    lookup_warning = None
    if skel_sections:
        skel_data = skel_sections[0][1]
    elif game_path:
        try:
            skel_data = _extract_skeleton_from_game(game_path, char_name)
        except (ValueError, OSError) as ex:
            lookup_warning = f'Skeleton unresolved: {ex}'

    # Parse skeleton if available
    bone_list = []
    bone_name_map = {}  # bone_idx -> name
    has_real_skeleton = False
    warnings = [lookup_warning] if lookup_warning else []
    decoded_joint_count = 0
    if skel_data:
        try:
            bone_list, num_joints = parse_skeleton_bytes(skel_data)
            decoded_joint_count = num_joints
            # Decoding names/parents does not prove mesh palette association.
            # Keep numeric groups and a clearly marked unbound placeholder.
            for i, b in enumerate(bone_list):
                bone_name_map[i] = b.name
        except Exception as ex:
            print(f"  [warn] skeleton parse failed: {ex}")

    if import_bones:
        warnings.append(_ui("rig_unvalidated"))
        print("[ORC WARNING]", warnings[-1])
    # Create collection
    ssg_stem = os.path.basename(filepath)
    model_collection = get_or_create_collection(ssg_stem, bpy.context.scene.collection)

    # Create armature
    arm_name = f"{ssg_stem}_Armature"
    arm_data = bpy.data.armatures.new(arm_name)
    arm_obj = bpy.data.objects.new(arm_name, arm_data)
    model_collection.objects.link(arm_obj)
    arm_obj.show_in_front = True
    arm_obj["orc_rig_status"] = "unvalidated_palette"
    arm_obj["orc_decoded_joint_count"] = decoded_joint_count
    arm_obj["orc_warning"] = _ui("rig_unvalidated")

    # First pass: collect all bone indices across all submeshes
    all_bone_idx = set()
    for edm_name, edm_data in edm_list:
        p = _import_fm6s_blocks(edm_data)
        if not p or not p['blocks']:
            continue
        for b in p['blocks']:
            skin_off = b['skin_offset_calc']
            svc = b['skin_vertex_count']
            for vi in range(svc):
                off = skin_off + vi * SKIN_ENTRY_SIZE
                if off + SKIN_ENTRY_SIZE > len(edm_data):
                    break
                idx = struct.unpack_from('<4B', edm_data, off + 4)
                for j in range(4):
                    if idx[j] < 255:
                        all_bone_idx.add(idx[j])

    # Ensure we have at least 1 bone
    if not all_bone_idx:
        all_bone_idx = {0}

    max_bone = max(all_bone_idx)
    num_bones = max_bone + 1

    # Build bone name list (from skeleton if available, else placeholder)
    if has_real_skeleton and bone_list:
        for i in range(num_bones):
            if i < len(bone_list):
                bone_name_map[i] = bone_list[i].name
            else:
                bone_name_map[i] = f"bone_{i:03d}"
    else:
        for i in range(num_bones):
            bone_name_map[i] = f"bone_{i:03d}"

    # Create bones in armature
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='EDIT')
    edit_bones = {}
    for i in range(num_bones):
        bname = bone_name_map[i]
        eb = arm_data.edit_bones.new(bname)
        eb.head = Vector((0, 0, 0))
        eb.tail = Vector((0, 0, 0.1))
        # Set bone position from skeleton data if available
        if has_real_skeleton and i < len(bone_list) and bone_list[i].position:
            eb.head = bone_list[i].position
            eb.tail = bone_list[i].position + Vector((0, 0, 1))
        # Set parent
        if has_real_skeleton and i < len(bone_list) and bone_list[i].parent_id != -1:
            pid = bone_list[i].parent_id
            if pid < len(edit_bones):
                eb.parent = edit_bones[pid]
        edit_bones[i] = eb
    bpy.ops.object.mode_set(mode='POSE')

    # Apply skeleton bone poses if available
    if has_real_skeleton:
        for i, bone in enumerate(bone_list):
            if i >= num_bones:
                break
            pb = arm_obj.pose.bones.get(bone.name)
            if pb:
                mat = Matrix.Translation(bone.position) @ bone.angle.to_matrix().to_4x4()
                pb.matrix_basis.identity()
                pb.matrix = mat

    bpy.ops.pose.armature_apply()
    bpy.ops.object.mode_set(mode='OBJECT')

    # Create mesh objects
    mesh_count = 0
    vert_count_total = 0
    for edm_name, edm_data in edm_list:
        p = _import_fm6s_blocks(edm_data)
        if not p or not p['blocks']:
            continue
        for blk_idx, block in enumerate(p['blocks']):
            stride = block['inferred_stride']
            if stride < 12:
                continue
            vtx_off = block['vertex_offset']
            vtx_cnt = block['vertex_count']
            idx_off = block['index_offset']
            idx_sz = block['index_size']

            # Read vertices
            positions = []
            normals = []
            uvs = []
            for vi in range(vtx_cnt):
                base = vtx_off + vi * stride
                pos, norm, uv = read_vertex(edm_data, base, stride)
                positions.append(pos)
                normals.append(norm)
                uvs.append(uv)

            # Read indices
            if idx_sz > 0:
                idx_count = idx_sz // 2
                indices = struct.unpack_from(f'<{idx_count}H', edm_data, idx_off)
                # Remove 0xFFFF terminator if present
                indices = [i for i in indices if i != 0xFFFF]
                faces = [(indices[i], indices[i + 1], indices[i + 2])
                         for i in range(0, len(indices) - len(indices) % 3, 3)]
            else:
                indices = []
                faces = []

            if not faces:
                continue

            # Read skin data
            skin_off = block['skin_offset_calc']
            svc = block['skin_vertex_count']
            skin_data = read_skin_raw(edm_data, skin_off, svc)

            # Create mesh
            mesh_name = f"{ssg_stem}_sub{blk_idx:02d}"
            mesh_data = bpy.data.meshes.new(mesh_name + "_MESH")
            obj = bpy.data.objects.new(mesh_name, mesh_data)
            model_collection.objects.link(obj)
            # No automatic bind to unvalidated placeholder rig.
            obj["orc_rig_status"] = "unvalidated_palette"

            # Set geometry
            mesh_data.from_pydata(list(positions), [], faces)
            mesh_data.update()
            mesh_data.calc_loop_triangles()

            # Custom split normals — convert per-vertex → per-loop to avoid
            # Blender 5.0 ACCESS_VIOLATION in normals_split_custom_set_from_vertices
            if stride >= 24 and len(normals) == len(mesh_data.vertices):
                norms_arr = np.ascontiguousarray(np.array(normals, dtype=np.float32))
                lens = np.linalg.norm(norms_arr.astype(np.float64), axis=1)
                if (np.isfinite(norms_arr).all() and (lens > 1e-8).all()
                        and norms_arr.ndim == 2 and norms_arr.shape[1] == 3):
                    vi_map = array('I', [0] * len(mesh_data.loops))
                    mesh_data.loops.foreach_get('vertex_index', vi_map)
                    norms_arr = norms_arr.astype(np.float64) / lens[:, None]
                    loop_normals = [tuple(float(c) for c in norms_arr[vi]) for vi in vi_map]
                    # Blender 5 expects one vector per corner, not flattened floats.
                    # Let API failures reach the operator's explicit error report.
                    mesh_data.normals_split_custom_set(loop_normals)

            # Set UVs
            if import_uvs and any(uv != (0.0, 0.0) for uv in uvs):
                uvm = mesh_data.uv_layers.new(name="UVMap")
                vert_idx = array('I', [0] * len(mesh_data.loops))
                mesh_data.loops.foreach_get('vertex_index', vert_idx)
                uv_flat = []
                for li in range(len(mesh_data.loops)):
                    vi = vert_idx[li]
                    u, v = uvs[vi] if vi < len(uvs) else (0.0, 0.0)
                    uv_flat.extend([u, 1.0 - v])  # flip V
                uvm.data.foreach_set('uv', uv_flat)

            # Set skin weights via vertex groups
            for i in range(num_bones):
                bname = bone_name_map.get(i, f"bone_{i:03d}")
                obj.vertex_groups.new(name=bname)

            for vi, influences in enumerate(skin_data):
                if vi >= len(mesh_data.vertices):
                    break
                for bidx, w in influences:
                    if bidx >= num_bones:
                        continue
                    bname = bone_name_map.get(bidx, f"bone_{bidx:03d}")
                    vg = obj.vertex_groups.get(bname)
                    if vg:
                        vg.add([vi], w, 'REPLACE')

            # Armature modifier
            if has_real_skeleton:
                mod = obj.modifiers.new(type='ARMATURE', name='Armature')
                mod.object = arm_obj

            # Basic material
            if import_materials:
                from .materials import create_basic_material
                mat = create_basic_material(mesh_name, block['material_path'], sections, warnings)
                mesh_data.materials.append(mat)

            mesh_count += 1
            vert_count_total += vtx_cnt

    # Select armature
    bpy.ops.object.select_all(action='DESELECT')
    arm_obj.select_set(True)
    bpy.context.view_layer.objects.active = arm_obj

    if not import_bones:
        # Preserve the parser/rig construction path, then remove all rig data
        # from the newly imported collection for a mesh-only result.
        for obj in list(model_collection.objects):
            if obj.type == 'MESH':
                obj.parent = None
                obj.vertex_groups.clear()
                for modifier in list(obj.modifiers):
                    if modifier.type == 'ARMATURE' and modifier.object == arm_obj:
                        obj.modifiers.remove(modifier)
                obj.select_set(True)
                bpy.context.view_layer.objects.active = obj
        bpy.data.objects.remove(arm_obj, do_unlink=True)
        bpy.data.armatures.remove(arm_data)

    return {
        "meshes": mesh_count,
        "vertices": vert_count_total,
        "bones": num_bones if import_bones else 0,
        "skeleton": "real" if has_real_skeleton else "placeholder_unbound",
        "decoded_joint_count": decoded_joint_count,
        "palette_validated": False,
        "warnings": warnings,
    }


# ─── Blender Mesh → Edgemodel JSON (EXPORT / CONVERT) ──────────────────────
def extract_mesh_data(obj, armature=None):
    """Extract mesh data from a Blender object for .edgemodel export.

    Adapted from blender_extract.py::extract_mesh_data.
    Returns the JSON-compatible dict that write_edgemodel consumes
    (semantic-float mode).
    """
    mesh = obj.data
    mesh.calc_loop_triangles()

    # Compute tangents
    try:
        uvm_name = mesh.uv_layers.active.name if (mesh.uv_layers and mesh.uv_layers.active) else None
        if uvm_name:
            mesh.calc_tangents(uvmap=uvm_name)
    except Exception:
        uvm_name = None

    # Bone index map
    bone_idx_map = {}
    arm = armature
    if arm is None:
        for mod in obj.modifiers:
            if mod.type == 'ARMATURE' and mod.object:
                arm = mod.object
                break
    if arm and arm.data:
        for i, b in enumerate(arm.data.bones):
            bone_idx_map[b.name] = i

    # Per-vertex skin data (top-2 bones by weight)
    skin_data = {}
    for v in mesh.vertices:
        groups = [(vg.group, float(vg.weight)) for vg in v.groups if vg.weight > 0]
        resolved = []
        for gidx, w in groups:
            gname = obj.vertex_groups[gidx].name if gidx < len(obj.vertex_groups) else None
            bidx = bone_idx_map.get(gname, gidx) if gname else gidx
            resolved.append((bidx, w))
        resolved.sort(key=lambda x: -x[1])
        skin_data[v.index] = resolved[:2] if resolved else [(0, 0.0), (0, 0.0)]

    # Collect per-corner data
    vertices_out = []
    indices_out = []
    skin_out = []
    vertex_map = {}
    loops = mesh.loops
    uv_layer = mesh.uv_layers[0] if mesh.uv_layers else None

    for tri in mesh.loop_triangles:
        for loop_idx in tri.loops:
            if loop_idx in vertex_map:
                indices_out.append(vertex_map[loop_idx])
                continue
            idx = len(vertices_out) // 14  # FPU = 14 for stride 52
            vertex_map[loop_idx] = idx

            loop = loops[loop_idx]
            v = mesh.vertices[loop.vertex_index]

            co = [float(v.co[0]), float(v.co[1]), float(v.co[2])]
            if hasattr(loop, 'normal') and len(loop.normal) >= 3:
                nx, ny, nz = float(loop.normal[0]), float(loop.normal[1]), float(loop.normal[2])
            else:
                nx, ny, nz = float(v.normal[0]), float(v.normal[1]), float(v.normal[2])

            u, v_val = 0.0, 0.0
            if uv_layer and loop_idx < len(uv_layer.data):
                uv = uv_layer.data[loop_idx].uv
                u, v_val = float(uv.x), float(uv.y)

            tang = (0.0, 0.0, 0.0)
            bitan = (0.0, 0.0, 0.0)
            if hasattr(loop, 'tangent') and len(loop.tangent) >= 3:
                tang = (float(loop.tangent[0]), float(loop.tangent[1]), float(loop.tangent[2]))
            if hasattr(loop, 'bitangent') and len(loop.bitangent) >= 3:
                bitan = (float(loop.bitangent[0]), float(loop.bitangent[1]), float(loop.bitangent[2]))

            vert = co + [nx, ny, nz, u, v_val] + list(tang) + list(bitan)
            assert len(vert) == 14
            vertices_out.extend(vert)

            groups = skin_data.get(v.index, [(0, 0.0), (0, 0.0)])
            g0 = groups[0] if len(groups) > 0 else (0, 0.0)
            g1 = groups[1] if len(groups) > 1 else (0, 0.0)
            skin_out.append([g0[0], g0[1], g1[0], g1[1]])

            indices_out.append(idx)

    # skin_vertex_count = max bone index + 1
    max_bone = 0
    for s in skin_out:
        if s[0] > max_bone: max_bone = s[0]
        if s[2] > max_bone: max_bone = s[2]
    skin_vc = max_bone + 1 if skin_out else 0

    return {
        "indices": indices_out,
        "vertices": vertices_out,
        "skin": skin_out,
        "vertex_count": len(vertices_out) // 14,
        "face_count": len(indices_out) // 3,
        "skin_vertex_count": skin_vc,
        "face_start": 0,
        "stride": 52,
    }


# ─── SSG Repack (sentinel-safe) ────────────────────────────────────────────
def validate_written_edgemodel(data, records):
    """Validate only headers emitted by our writer, not heuristic hits in buffers.

    Keep the existing parser unchanged: sequential u16 index data can resemble
    headers to its whole-file scanner. Writer records identify the real headers.
    """
    from fbx_to_edgemodel import HDR_GLOBAL_SIZE, MESHINFO_SIZE, SUBMESH_HDR_SIZE
    from roundtrip_edgemodel import scan_fm6s_blocks, validate
    mesh_count = struct.unpack_from('<i', data, 12)[0]
    start = HDR_GLOBAL_SIZE + mesh_count * MESHINFO_SIZE
    offsets = {start + record['flat_idx'] * SUBMESH_HDR_SIZE for record in records}
    parsed = scan_fm6s_blocks(data)
    blocks = [block for block in (parsed or {}).get('blocks', [])
              if block['info_offset'] in offsets and block['index_size_src'] == 'declared']
    if len(blocks) != len(records):
        raise ValueError(f'Writer: {len(records)} headers, releitura: {len(blocks)}')
    fe, oe = validate(data, blocks)
    return len(blocks), fe, oe


def edm_path_already_set(path):
    """Return True if the edgemodel path looks like a real SSG entry path."""
    return bool(path and path != "dlc/pack1/characters/adawong/models/adawong.edgemodel")


def repack_modify_safe(orig_path, out_path, entry_overrides=None):
    """Repack an .ssg with sentinel-safe comp_sz patching.

    For no-op (empty overrides) the original file is copied verbatim,
    guaranteeing byte-identical output.  For actual overrides, delegates
    to ssg_repack.repack_modify which patches comp_sz (b+28) ONLY for
    overridden entries and preserves sentinel values (-2, -3) in all
    other descriptors.
    """
    entry_overrides = entry_overrides or {}
    if not entry_overrides:
        # No-op: copy byte-for-byte (preserves all block sizes, sentinels, etc.)
        with open(orig_path, 'rb') as f:
            data = f.read()
        os.makedirs(os.path.dirname(out_path) or '.', exist_ok=True)
        with open(out_path, 'wb') as f:
            f.write(data)
        return len(data), 0, set()
    # Actual repack with overrides
    from ssg_repack import repack_modify
    return repack_modify(orig_path, out_path, entry_overrides)


# ─── Operators ─────────────────────────────────────────────────────────────

class IMPORT_OT_ssg(Operator, ImportHelper):
    """Import an RE:ORC .ssg archive into Blender."""
    bl_idname = "orc.import_ssg"
    bl_label = "Import SSG"
    bl_label_plural = "Import SSG"
    bl_description = "Import .ssg archive (.ssg → Blender)"
    bl_options = {'REGISTER', 'UNDO'}

    filter_glob: StringProperty(default="*.ssg", options={'HIDDEN'})

    import_bones: BoolProperty(
        name="Import Bones", default=True,
        description="Create armature from skeleton / skin data")

    import_materials: BoolProperty(
        name="Basic MATB/DDS / Materiais básicos", default=True,
        description="Archive-local diffuse preview only; not original Hexane shaders")

    import_uvs: BoolProperty(name="Importar UVs", default=True)
    edgemodel_entry: StringProperty(name="Entrada edgemodel", options={'HIDDEN'})

    @classmethod
    def poll(cls, context):
        return context.scene is not None and context.mode == 'OBJECT'

    def execute(self, context):
        mod_path = ensure_mod_path()
        game_path = DEFAULT_GAME_PATH
        try:
            prefs = context.preferences.addons["orc_mod_tools"].preferences
            game_path = prefs.game_path or DEFAULT_GAME_PATH
        except (KeyError, AttributeError):
            pass

        try:
            info = import_ssg(self.filepath, mod_path, game_path if self.import_bones else None,
                              self.import_bones, self.import_uvs, self.import_materials,
                              self.edgemodel_entry)
            for warning in info["warnings"]:
                self.report({'WARNING'}, warning)
            self.report({'INFO'}, f"Imported {info['meshes']} meshes, "
                         f"{info['vertices']} verts, {info['bones']} bones "
                         f"({info['skeleton']})")
            return {'FINISHED'}
        except Exception as ex:
            import traceback
            traceback.print_exc()
            self.report({'ERROR'}, f"Import failed: {ex}")
            return {'CANCELLED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class EXPORT_OT_ssg(Operator, ExportHelper):
    """Export selected mesh objects to an .ssg archive."""
    bl_idname = "orc.export_ssg"
    bl_label = "Export SSG"
    bl_description = "Export Blender mesh → .ssg archive"
    bl_options = {'REGISTER', 'UNDO'}

    filename_filter = {"*.ssg"}
    filter_glob: StringProperty(default="*.ssg", options={'HIDDEN'})

    # Template / output paths
    original_ssg: StringProperty(
        name="Original .ssg", subtype='FILE_PATH',
        description="Original .ssg to use as repack template")

    edgemodel_path: StringProperty(
        name="Edgemodel path",
        default="dlc/pack1/characters/adawong/models/adawong.edgemodel",
        description="Path of the .edgemodel entry inside the .ssg")

    validate_output: BoolProperty(
        name="Validate output", default=True,
        description="Re-parse the output .ssg to verify integrity")

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and any(o.type == 'MESH' for o in context.selected_objects)

    def execute(self, context):
        self.report({'WARNING'}, _ui('native_blocked'))
        return {'CANCELLED'}

    def invoke(self, context, event):
        return self.execute(context)


class CONVERT_OT_edgemodel(Operator, ExportHelper):
    """Convert the active mesh object to a .edgemodel file."""
    bl_idname = "orc.convert_edgemodel"
    bl_label = "Convert to Edgemodel"
    bl_description = "Convert Blender mesh to .edgemodel (FM6S)"
    bl_options = {'REGISTER'}

    filename_filter = {"*.edgemodel"}
    filter_glob: StringProperty(default="*.edgemodel", options={'HIDDEN'})

    validate_output: BoolProperty(
        name="Validate output", default=True,
        description="Re-parse the .edgemodel to verify integrity")

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and context.active_object is not None and context.active_object.type == 'MESH'

    def execute(self, context):
        self.report({'WARNING'}, _ui('native_blocked'))
        return {'CANCELLED'}

    def invoke(self, context, event):
        return self.execute(context)


# ─── UI Panel ─────────────────────────────────────────────────────────────

class ORC_PT_panel(Panel):
    bl_label = "ORC Mod Tools"
    bl_idname = "ORC_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "ORC Tools"

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.operator(IMPORT_OT_ssg.bl_idname)
        col.operator(EXPORT_OT_ssg.bl_idname)
        col.operator(CONVERT_OT_edgemodel.bl_idname)
        col.separator()
        col.operator("orc.open_documentation")


class ORC_OT_open_docs(Operator):
    bl_idname = "orc.open_documentation"
    bl_label = "Documentation"
    def execute(self, context):
        import webbrowser
        doc = os.path.join(os.path.dirname(__file__), "README.md")
        webbrowser.open(doc if os.path.isfile(doc) else "https://github.com/nousresearch/orc-mod-tools")
        return {'FINISHED'}


# ─── Addon Preferences ────────────────────────────────────────────────────

class ORCAddonPreferences(AddonPreferences):
    bl_idname = __package__

    mod_path: StringProperty(
        name="ORC-Modding Path",
        default=DEFAULT_MOD_PATH, subtype='DIR_PATH',
        description="Path to ORC-Modding directory with parser scripts")

    game_path: StringProperty(
        name="Game Directory",
        default=DEFAULT_GAME_PATH, subtype='DIR_PATH',
        description="Path to Resident Evil: Operation Raccoon City installation")

    language: EnumProperty(
        name="Language",
        items=[
            ('en', "English", "English"),
            ('pt_br', "Português (Brasil)", "Português (Brasil)"),
        ],
        default='en')

    @property
    def language_code(self):
        return self.language

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "mod_path")
        layout.prop(self, "game_path")
        layout.prop(self, "language")


classes = [
    IMPORT_OT_ssg,
    EXPORT_OT_ssg,
    CONVERT_OT_edgemodel,
    ORC_OT_open_docs,
    ORCAddonPreferences,
]

from . import ui

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    ui.register()

def unregister():
    ui.unregister()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
