"""Minimal archive-local MATB diffuse preview, not original Hexane shaders.
Layouts cross-checked against native Ada/Tweed archives and orc_import_blender.
No material-name or texture-basename guessing; unresolved resources stay basic.
"""
import os, struct, tempfile, hashlib
import bpy


def read_string(data, offset):
    if not 0 <= offset < len(data):
        raise ValueError('Material string offset outside buffer')
    end = data.find(b'\0', offset)
    if end < 0:
        raise ValueError('Unterminated material string')
    return data[offset:end].decode('utf-8')


def diffuse_reference(data):
    if len(data) < 24 or data[:3] != b'MAT':
        raise ValueError('Unsupported MATB header')
    count, table = struct.unpack_from('<I', data, 8)[0], struct.unpack_from('<I', data, 16)[0]
    if count > 4096 or table + count * 8 > len(data):
        raise ValueError('Invalid MATB texture table')
    matches = []
    for i in range(count):
        semantic, offset = struct.unpack_from('<2I', data, table + i * 8)
        path = read_string(data, offset)
        if semantic == 3014450751:
            matches.append(path)
    if len(matches) > 1:
        raise ValueError('Ambiguous MATB diffuse semantic')
    return matches[0] if matches else None


def create_basic_material(mesh_name, material_path, sections, warnings):
    mat = bpy.data.materials.new('ORC Basic ' + mesh_name)
    mat.use_nodes = True
    mat['orc_shader_fidelity'] = 'basic_diffuse_preview_only'
    mat['orc_matb'] = material_path
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (.3, .3, .3, 1.)
    resources = {n.replace('\\', '/').lower(): d for n, _, d in sections}
    raw = resources.get(material_path.replace('\\', '/').lower())
    if raw is None:
        warnings.append('MATB unresolved (basic material only): ' + material_path)
        return mat
    try:
        path = diffuse_reference(raw)
        if not path:
            return mat
        tex = resources.get(path.replace('\\', '/').lower())
        if tex is None or tex[:4] != b'DDS ':
            raise ValueError('Diffuse DDS unresolved: ' + path)
        # The archive path is metadata only, never used as a filesystem path.
        # Pack real DDS bytes so a saved .blend needs no source/game resources.
        cache = os.environ.get('ORC_TEXTURE_CACHE') or os.environ.get('TMPDIR') or bpy.app.tempdir
        os.makedirs(cache, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='orc-dds-', dir=cache) as directory:
            filename = os.path.join(directory, hashlib.sha256(tex).hexdigest() + '.dds')
            with open(filename, 'wb') as handle:
                handle.write(tex)
            image = bpy.data.images.load(filename, check_existing=False)
            if not image.size[0] or not image.size[1]:
                raise ValueError('Blender could not decode DDS: ' + path)
            image.pack()
            image['orc_archive_path'] = path
            image.name = path.rsplit('/', 1)[-1]
            image.filepath = '//' + image.name
        node = mat.node_tree.nodes.new('ShaderNodeTexImage')
        node.image = image
        mat.node_tree.links.new(node.outputs['Color'], bsdf.inputs['Base Color'])
        # Alpha, normal/specular and Hexane-specific shader behavior intentionally
        # remain unconnected: interpreting these would be a different feature.
    except (ValueError, RuntimeError, OSError, struct.error, UnicodeError) as exc:
        warnings.append('Basic diffuse preview failed: ' + str(exc))
    return mat
