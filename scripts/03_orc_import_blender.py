import io
import random
import os
from collections import namedtuple
from struct import unpack, calcsize
from typing import List

import bpy
import numpy as np
import mathutils
import math
import ctypes
import numpy
from pathlib import Path
from bpy.props import StringProperty, CollectionProperty, BoolProperty
from bpy_extras.io_utils import ImportHelper
from bpy.types import Operator, OperatorFileListElement
from mathutils import *
from math import *
from ctypes import *

debug_print = False

os.system('cls')

def get_or_create_collection(name, parent: bpy.types.Collection) -> bpy.types.Collection:
    new_collection = (bpy.data.collections.get(name, None) or
                      bpy.data.collections.new(name))
    if new_collection.name not in parent.children:
        parent.children.link(new_collection)
    new_collection.name = name
    return new_collection


def get_new_unique_collection(model_name, parent_collection):
    copy_count = len([collection for collection in bpy.data.collections if model_name in collection.name])

    master_collection = get_or_create_collection(model_name + (f'_{copy_count}' if copy_count > 0 else ''),
                                                 parent_collection)
    return master_collection


def read_fmt(fmt, f):
    return unpack(fmt, f.read(calcsize(fmt)))


def read_string(f):
    c = f.read(1)

    buff = b''
    while c and c != b'\x00':
        buff += c
        c = f.read(1)
    return buff.decode('ascii')


def read_int32(file):
    return unpack('i', file.read(4))[0]


def read_int16(file):
    return unpack('h', file.read(2))[0]


def read_int8(file):
    return unpack('b', file.read(1))[0]


def read_uint32(file):
    return unpack('I', file.read(4))[0]


def read_uint16(file):
    return unpack('H', file.read(2))[0]


def read_uint8(file):
    return unpack('B', file.read(1))[0]


def read_float(file):
    return unpack('f', file.read(4))[0]


def read_float16(file):
    return unpack('e', file.read(4))[0]


def align_bytes(value, align_to):
    padding = (align_to - value % align_to) % align_to
    return value + padding


def decompress_animation_rotation(compressed):
    q64 = compressed[0] << 40 | compressed[1] << 32 | compressed[2] << 24 | compressed[3] << 16 | compressed[4] << 8 | compressed[5]
    
    sqrt_2 = 1.414213562
    quat_scale = ((1 << 15) - 1) / sqrt_2
    quat_offset = quat_scale / sqrt_2

    a = int((q64 >> 32) & ((1<<15)-1))
    b = int((q64 >> 17) & ((1<<15)-1))
    c = int((q64 >> 2) & ((1<<15)-1))
    idx = int(q64 & 3)

    fa = (float(a) - quat_offset) / quat_scale
    fb = (float(b) - quat_offset) / quat_scale
    fc = (float(c) - quat_offset) / quat_scale
    fd = math.sqrt(1 - fa*fa - fb*fb - fc*fc)
    
    if idx == 0:
        return mathutils.Quaternion((fc, fd, fa, fb))
    elif idx == 1:
        return mathutils.Quaternion((fc, fa, fd, fb))
    elif idx == 2:
        return mathutils.Quaternion((fc, fa, fb, fd))
    elif idx == 3:
        return mathutils.Quaternion((fd, fa, fb, fc))


class floatInt(ctypes.Union):
    _fields_ = [("i", c_uint32),
                ("f", c_float)]


def decompress_animation_vector(compressed):
    x = floatInt(0, 0)
    y = floatInt(0, 0)
    z = floatInt(0, 0)
    
    x.i = (compressed[0] << 0) | (compressed[1] << 8) | (compressed[2] << 16) | (compressed[3] << 24)
    y.i = (compressed[4] << 0) | (compressed[5] << 8) | (compressed[6] << 16) | (compressed[7] << 24)
    z.i = (compressed[8] << 0) | (compressed[9] << 8) | (compressed[10] << 16) | (compressed[11] << 24)
    
    return mathutils.Vector((x.f, y.f, z.f))


def align_seek(file, align_to):
    seek_bytes = file.tell() % align_to
    if seek_bytes != 0:
        file.seek(align_to - seek_bytes, 1)


def anim_get_frame_set_index(anim_header, frame_set_info, frame):
    left_index = 0
    right_index = anim_header.num_frame_sets - 1
    
    while left_index + 1 < right_index:
        mid_index = (left_index + right_index) >> 1
        if frame < frame_set_info[mid_index].base_frame:
            right_index = mid_index
        else:
            left_index = mid_index
        
    return left_index


def anim_generate_bit_mask(bit_pos):
    t = numpy.uint64(0xffffffffffffffff)
    
    if bit_pos >= 64:
        t0 = t
        t1 = numpy.left_shift(t, numpy.uint32(128 - bit_pos))
    else:
        t0 = numpy.left_shift(t, numpy.uint32(64 - bit_pos))
        t1 = 0;

    mask = [numpy.uint32(t0 >> numpy.uint32(32)),
            numpy.uint32(t0),
            numpy.uint32(t1 >> numpy.uint32(32)),
            numpy.uint32(t1)]
    
    return mask


def anim_count_bits_32(v):
    tmp = numpy.uint32(v - ((v >> 1) & 0x55555555))
    tmp = (tmp & 0x33333333) + ((tmp >> 2) & 0x33333333)
    r = numpy.right_shift(numpy.uint32(tmp + (tmp >> 4) & 0xF0F0F0F) * numpy.uint32(0x1010101), numpy.uint32(24))
    
    return r


def anim_count_bits_128(v):
    r = anim_count_bits_32(v[0])
    r += anim_count_bits_32(v[1])
    r += anim_count_bits_32(v[2])
    r += anim_count_bits_32(v[3])
    
    return r


def anim_get_first_set_bit_32(v):
    clztab = [0,1,2,2,3,3,3,3,4,4,4,4,4,4,4,4]
    
    r = 32
    
    if v & 0xffff0000:
        v >>= 16
        r -= 16
    if v & 0xff00:
        v >>= 8
        r -= 8
    if v & 0xf0:
        v >>= 4
        r -= 4
    
    r -= clztab[v]
    
    return r


def anim_get_last_set_bit_32(v):
    return anim_get_first_set_bit_32(v & -v)


def anim_get_last_set_bit_128(v):
    i = 3
    while (i>=0) and (v[i] == 0):
        i -= 1

    if i < 0:
        r = numpy.uint32(-1)
    else:
        r = anim_get_last_set_bit_32(v[i]) + i * 32
    
    return r


def anim_get_first_set_bit_128(v):
    i = 0
    while (i<4) and (v[i] == 0):
        i += 1
    
    if i == 4:
        r = 128
    else:
        r = anim_get_first_set_bit_32(v[i]) + i * 32
    
    return r


# offset_initial_r_data = initialRAdr
# offset_initial_t_data = initialTAdr
# offset_initial_s_data = initialSAdr
# offset_initial_user_data = initialUAdr
# offset_intra_r_data = intraRAdr
# offset_intra_t_data = intraTAdr
# offset_intra_s_data = intraSAdr
# offset_intra_user_data = intraUAdr
# offset_final_r_data = finalRAdr
# offset_final_t_data = finalTAdr
# offset_final_s_data = finalSAdr
# offset_final_user_data = finalUAdr
# offset_intra_r_bits = intraRBitsOfs
# offset_intra_t_bits = intraTBitsOfs
# offset_intra_s_bits = intraSBitsOfs
# offset_intra_user_bits = intraUBitsOfs
# bits_intra_adr = intraBitsAdr
# size_initial_r_data = sizeInitialRData
# size_initial_t_data = sizeInitialTData
# size_initial_s_data = sizeInitialSData
# size_initial_user_data = sizeInitialUData
# size_intra_r_data = sizeIntraRData
# size_intra_t_data = sizeIntraTData
# size_intra_s_data = sizeIntraSData
# size_intra_user_data = sizeIntraUData
# size_final_r_data = sizeFinalRData
# size_final_t_data = sizeFinalTData
# size_final_s_data = sizeFinalSData
# bit_mask = bitMask
def anim_get_bracketing_keyframes(animation_file, frame_number, frame_fraction, prev_bit_mask, stride, offset_intra_r_bits, offset_intra_r_data, offset_initial_r_data, offset_final_r_data, offset_frameset_start, bits_intra_adr, bit_mask):
    ofs = offset_intra_r_bits & 7
    animation_file.seek(offset_frameset_start + (bits_intra_adr + (offset_intra_r_bits >> 3)), 0)
    adr = read_fmt('17B', animation_file) # read_uint8 17 times
    b0 = adr[0] << (24 + ofs)
    b0 |= adr[1] << (ofs + 16)
    b0 |= adr[2] << (ofs + 8)
    b0 |= adr[3] << (ofs)
    b0 |= adr[4] >> (8 - ofs)
    
    b1 = adr[4] << (24 + ofs)
    b1 |= adr[5] << (ofs + 16)
    b1 |= adr[6] << (ofs + 8)
    b1 |= adr[7] << (ofs)
    b1 |= adr[8] >> (8 - ofs)
    
    b2 = adr[8] << (24 + ofs)
    b2 |= adr[9] << (ofs + 16)
    b2 |= adr[10] << (ofs + 8)
    b2 |= adr[11] << (ofs)
    b2 |= adr[12] >> (8 - ofs)
    
    b3 = adr[12] << (24 + ofs)
    b3 |= adr[13] << (ofs + 16)
    b3 |= adr[14] << (ofs + 8)
    b3 |= adr[15] << (ofs)
    b3 |= adr[16] >> (8 - ofs)
    
    intra_bits = [b0 & bit_mask[0], b1 & bit_mask[1], b2 & bit_mask[2], b3 & bit_mask[3]]
    prev_bits = [b0 & prev_bit_mask[0], b1 & prev_bit_mask[1], b2 & prev_bit_mask[2], b3 & prev_bit_mask[3]]
    
    num_bits = anim_count_bits_128(intra_bits)
    num_prev_bits = anim_count_bits_128(prev_bits)
    
    intra_bits_m = [(intra_bits[0] & (~prev_bit_mask[0])) | (~bit_mask[0]), (intra_bits[1] & (~prev_bit_mask[1])) | (~bit_mask[1]), (intra_bits[2] & (~prev_bit_mask[2])) | (~bit_mask[2]), (intra_bits[3] & (~prev_bit_mask[3])) | (~bit_mask[3])]
    
    b_bits = frame_number - anim_get_last_set_bit_128(prev_bits) - 1
    a_bits = anim_get_first_set_bit_128(intra_bits_m) - frame_number + 1
    
    if num_prev_bits == 0:
        key_a = offset_initial_r_data
    else:
        key_a = offset_intra_r_data + (num_prev_bits - 1) * stride
    
    if num_prev_bits == num_bits:
        key_b = offset_final_r_data
    else:
        key_b = offset_intra_r_data + num_prev_bits * stride
    
    alpha = (b_bits + frame_fraction) / (a_bits + b_bits)
    
    return key_a, key_b, num_bits, alpha


def anim_dot(quat_0, quat_1):
    result = (quat_0[1] * quat_1[1])
    result = (result + (quat_0[2] * quat_1[2]))
    result = (result + (quat_0[3] * quat_1[3]))
    result = (result + (quat_0[0] * quat_1[0]))
    
    return result


def anim_slerp(t, unit_quat_0, unit_quat_1):
    cos_angle = anim_dot(unit_quat_0, unit_quat_1)
    
    if cos_angle < 0.0:
        cos_angle = -cos_angle
        start = (-unit_quat_0)
    else:
        start = unit_quat_0
    
    if cos_angle < 0.999:
        angle = math.acos(cos_angle)
        recip_sin_angle = (1.0 / math.sin( angle ))
        scale_0 = (math.sin( ( ( 1.0 - t ) * angle ) ) * recip_sin_angle)
        scale_1 = (math.sin( ( t * angle ) ) * recip_sin_angle)
    else:
        scale_0 = (1.0 - t)
        scale_1 = t
    
    return (( start * scale_0 ) + ( unit_quat_1 * scale_1 ))


def anim_lerp(t, pnt_0, pnt_1):
    return (pnt_0 + ( ( pnt_1 - pnt_0 ) * t ))


class EdgeAnimSkeleton:
    def __init(self):
        self.tag = None # 0x00: version tag (uint32_t)
        self.size_total = None # 0x04: total size - in bytes, aligned 16 (uint32_t)
        self.size_custom_data = None # 0x08: size of custom data, including table - in bytes, aligned 16 (uint32_t)
        self.size_name_hashes = None # 0x0C: size of joint and user channel name hashes - in bytes, aligned 16 (uint32_t)
        self.num_joints = None # 0x10: number of joints (uint16_t)
        self.num_user_channels = None # 0x12: number of user channels (uint16_t)
        self.num_simd_hierarchy_quads = None # 0x14: number of "quads" in simd hierarchy (uint16_t)
        # self.pad0 = None # 0x16: pad (uint8_t x2)
        self.offset_base_pose = None # 0x18: offset of the base pose (EdgeAnimJointTransform*) relative to num_joints values (uint32_t)
        self.offset_parent_indices_array = None # 0x1C: offset to parent indices array (int16_t*) relative to num_joints values (uint32_t)
        self.offset_joint_name_hash_array; # 0x20: offset to joint name hash array (unsigned int*) relative to num_joints values (uint32_t)
        self.offset_user_channel_name_hash_array; # 0x24: offset to user channel name hash array (unsigned int*) relative to num_user_channels values (uint32_t)
        self.offset_user_channel_node_name_hash_array; # 0x28: offset to user channel node name hash array (unsigned int*) relative to num_user_channels values (uint32_t)
        self.offset_user_channel_flags_array; # 0x2C: offset to user channel flag array (unsigned char*) relative to num_user_channels values (uint32_t)
        self.offset_custom_data; # 0x30: offset to EdgeAnimCustomDataTable (or raw data from Edge tool) (uint32_t)


class EdgeAnimAnimation:
    def __init__(self):
        self.tag = None # 0x00: version tag (uint32_t)
        self.duration = None # 0x04: duration of animation (float)
        self.framerate = None # 0x08: sampling frequency (float)
        self.size_header = None # 0x0C: size (in bytes, aligned to 16) of the header (uint16_t)
        self.num_bones = None # 0x0E: number of joints (uint16_t)
        self.num_frames = None # 0x10: total number of frames (uint16_t)
        self.num_frame_sets = None # 0x12: number of frame sets (uint16_t)
        self.buffer_size = None # 0x14: size of evaluation buffer required for this anim (uint16_t)
        self.num_const_r_channels = None # 0x16: number of constant rotation channels (uint16_t)
        self.num_const_t_channels = None # 0x18: number of constant translation channels (uint16_t)
        self.num_const_s_channels = None # 0x1A: number of constant scale channels (uint16_t)
        self.num_const_user_channels = None # 0x1C: number of constant user channels (uint16_t)
        self.num_anim_r_channels = None # 0x1E: number of animated rotation channels (uint16_t)
        self.num_anim_t_channels = None # 0x20: number of animated translation channels (uint16_t)
        self.num_anim_s_channels = None # 0x22: number of animated scale channels (uint16_t)
        self.num_anim_user_channels = None # 0x24: number of animated user channels (uint16_t)
        self.flags = None # 0x26: flags (uint16_t)
        self.size_joints_weight_array = None # 0x28: if size set to 0, it means no array (uint32_t)
        self.user_joints_weight_array = None # 0x2C: user override for joint weights array - set to NULL by tools (uint32_t)
        self.offset_joints_weight_array = None # 0x30: offset of joint weights array - only if userJointWeightArray is NULL (uint32_t)
        self.offset_frame_set_dma_array = None # 0x34: offset of the frameset dma array (non relocated EdgeDmaListElement*) relative to itself (uint32_t)
        self.offset_frame_set_info_array = None # 0x38: offset of the frameset info array (EdgeAnimFrameSetInfo*) relative to itself (uint32_t)
        self.offset_const_r_data = None # 0x3C: offset to constant rotation data relative to itself (uint32_t)
        self.offset_const_t_data = None # 0x40: offset to constant translation data relative to itself (uint32_t)
        self.offset_const_s_data = None # 0x44: offset to constant scale data relative to itself (uint32_t)
        self.offset_const_user_data = None # 0x48: offset to constant user channel data relative to itself (uint32_t)
        self.offset_packing_specs = None # 0x4c: offset to packing specs relative to itself (NULL if no bitpacking) (uint32_t)
        self.offset_custom_data = None #0x50: offset to EdgeAnimCustomDataTable (or raw data from Edge tool) (uint32_t)
        self.size_custom_data = None #0x54: size of custom data, including table - in bytes, aligned 16 (uint32_t)


class EdgeAnimFrameSetInfo:
    def __init__(self, base_frame, num_intra_frames):
        self.base_frame = base_frame # uint16_t
        self.num_intra_frames = num_intra_frames # uint16_t
        self.offset_frameset_start = 0
        self.offset_initial_r_data = 0
        self.offset_initial_t_data = 0
        self.offset_initial_s_data = 0
        self.offset_initial_user_data = 0
        self.offset_intra_r_data = 0
        self.offset_intra_t_data = 0
        self.offset_intra_s_data = 0
        self.offset_intra_user_data = 0
        self.offset_next_frame_set = 0
        self.offset_final_r_data = 0
        self.offset_final_t_data = 0
        self.offset_final_s_data = 0
        self.offset_final_user_data = 0
        self.offset_intra_r_bits = 0
        self.offset_intra_t_bits = 0
        self.offset_intra_s_bits = 0
        self.offset_intra_user_bits = 0
        self.bits_intra_adr = 0
        self.size_initial_r_data = 0
        self.size_initial_t_data = 0
        self.size_initial_s_data = 0
        self.size_initial_user_data = 0
        self.size_intra_r_data = 0
        self.size_intra_t_data = 0
        self.size_intra_s_data = 0
        self.size_intra_user_data = 0
        self.size_final_r_data = 0
        self.size_final_t_data = 0
        self.size_final_s_data = 0
        self.bit_mask = []


class EdgeBone:
    def __init__(self):
        self.position = None
        self.angle = None
        self.parent_id = None
        self.name = None
        self.bind_matrix = None


class MeshInfo:
    def __init__(self, submesh_count, submesh_offset, lod, mat_offset, unk_data):
        self.submesh_count = submesh_count
        self.submesh_offset = submesh_offset
        self.lod = lod
        self.mat_offset = mat_offset
        self.unk_data = unk_data

    def __repr__(self) -> str:
        return 'MeshInfo(submesh_count={}, submesh_offset={}, lod={}, mat_offset={}, unk_data={})'.format(
            self.submesh_count, self.submesh_offset, self.lod, self.mat_offset, self.unk_data)


vert_dtype = np.dtype(
    [
        ('pos', np.float32, 3),
        ('norm', np.float32, 3),
        ('uv', np.float32, 2),
    ]
)


def parse_bones(skeleton_file, bone_list, bone_count, bone_pos_offset, bone_parent_offset, bone_names_offset):
    skeleton_file.seek(bone_pos_offset + 24, 0)
    for i in range(bone_count):
        bone = EdgeBone()

        # bone angles
        x, y, z, w = unpack('4f', skeleton_file.read(16))
        bone.angle = mathutils.Quaternion((w, x, y, z))
        if debug_print == True:
            print('Bone', i, 'angle:', bone.angle)

        # bone position
        # position is stored as float4, but the last axis is not used!
        x, y, z = unpack('3f', skeleton_file.read(12))
        skeleton_file.seek(4, 1) # the 4th axis, always 1.0 and not used
        bone.position = mathutils.Vector((x, y, z))
        if debug_print == True:
            print('Bone', i, 'position:', bone.position)

        # bone scale (not used in RE:ORC)
        skeleton_file.seek(16, 1)

        bone_list.append(bone)

    # read parents
    skeleton_file.seek(bone_parent_offset + 0x1C, 0)
    for bone_id, bone in enumerate(bone_list):
        bone.parent_id = unpack('h', skeleton_file.read(2))[0]
        if debug_print == True:
            print('Bone: {} parent: {}'.format(bone_id, bone.parent_id))

    # read names
    skeleton_file.seek(bone_names_offset + (bone_count * 4) + 0x30, 0)
    for i in range(bone_count):
        bone_list[i].name = ''.join(iter(lambda: skeleton_file.read(1).decode('ascii'), '\x00'))
        if debug_print == True:
            print('Bone', i, 'name:', bone_list[i].name)

    return bone_list


def parse_skel(filepath):
    with filepath.open('rb') as skeleton_file:
        header = skeleton_file.read(4).decode('ascii')
        assert header == '20SE' or header == 'ES02'
        
        skeleton_header = EdgeAnimSkeleton()
        skeleton_header.tag = header
        skeleton_header.size_total = read_uint32(skeleton_file)
        skeleton_header.size_custom_data = read_uint32(skeleton_file)
        skeleton_header.size_name_hashes = read_uint32(skeleton_file)
        skeleton_header.num_joints = read_uint16(skeleton_file)
        skeleton_header.num_user_channels = read_uint16(skeleton_file)
        skeleton_header.num_simd_hierarchy_quads = read_uint16(skeleton_file)
        skeleton_file.seek(0x02, 1) # pad0 (uint8_t x2)
        skeleton_header.offset_base_pose = read_uint32(skeleton_file)
        skeleton_header.offset_parent_indices_array = read_uint32(skeleton_file)
        skeleton_header.offset_joint_name_hash_array = read_uint32(skeleton_file)
        skeleton_header.offset_user_channel_name_hash_array = read_uint32(skeleton_file)
        skeleton_header.offset_user_channel_node_name_hash_array = read_uint32(skeleton_file)
        skeleton_header.offset_user_channel_flags_array = read_uint32(skeleton_file)
        skeleton_header.offset_custom_data = read_uint32(skeleton_file)
        if debug_print == True:
            print('')
            print('EdgeAnimSkeleton header info')
            print('Tag:', skeleton_header.tag)
            print('Size total:', skeleton_header.size_total)
            print('Size of custom data:', skeleton_header.size_custom_data)
            print('Size of name hashes:', skeleton_header.size_name_hashes)
            print('Num joints:', skeleton_header.num_joints)
            print('Num user channels:', skeleton_header.num_user_channels)
            print('Num SIMD hierarchy quads:', skeleton_header.num_simd_hierarchy_quads)
            print('Offset to base pose:', skeleton_header.offset_base_pose)
            print('Offset to parent indices array:', skeleton_header.offset_parent_indices_array)
            print('Offset to joint name hash array:', skeleton_header.offset_joint_name_hash_array)
            print('Offset to user channel name hash array:', skeleton_header.offset_user_channel_name_hash_array)
            print('Offset to user channel node name hash array:', skeleton_header.offset_user_channel_node_name_hash_array)
            print('Offset to user channel flags array:', skeleton_header.offset_user_channel_flags_array)
            print('Offset to custom data:', skeleton_header.offset_custom_data)

        # parse bone data
        bone_list: List[EdgeBone] = []
        parse_bones(skeleton_file, bone_list, skeleton_header.num_joints, skeleton_header.offset_base_pose, skeleton_header.offset_parent_indices_array, skeleton_header.offset_custom_data)
        
        # create skeleton
        armature = bpy.data.armatures.new("Armature")
        rig = bpy.data.objects.new("Armature", armature)
        bpy.context.scene.collection.objects.link(rig)
        rig.select_set(True)
        bpy.context.view_layer.objects.active = rig
        bpy.ops.object.mode_set(mode='EDIT')
        
        blender_bones = []
        for i in range(skeleton_header.num_joints):
            bl_bone = armature.edit_bones.new(bone_list[i].name)
            blender_bones.append(bl_bone)
        
        for bl_bone, bone in zip(blender_bones, bone_list):
            bl_bone.head = [0, 0, 0]
            bl_bone.tail = [0, 0, 0.1]
            bl_bone.use_relative_parent = True
            bl_bone.use_local_location = False
            if bone.parent_id != -1:
                bl_bone.parent = blender_bones[bone.parent_id]
        
        bpy.ops.object.mode_set(mode='POSE')
        for bone in bone_list:
            bl_bone = rig.pose.bones.get(bone.name)
            mat = Matrix.Translation(bone.position) @ bone.angle.to_matrix().to_4x4()
            bl_bone.matrix_basis.identity()
        
            bl_bone.matrix = bl_bone.parent.matrix @ mat if bl_bone.parent else mat
        
        bpy.ops.pose.armature_apply()
        bpy.ops.object.mode_set(mode='OBJECT')
        
        skeleton_file.close()
        
        return rig, bone_list

def image_has_alpha(img):
    b = 32 if img.is_float else 8
    return (
        img.depth == 2*b or   # Grayscale+Alpha
        img.depth == 4*b      # RGB+Alpha
    )

def alpha_is_meaningful(image):
    """True only if the diffuse texture's alpha channel actually varies.
    Some ORC character body textures are DXT5 but store alpha == 0 everywhere
    (the real alpha/opacity comes from elsewhere). Wiring that alpha to the
    Principled BSDF with HASHED blending makes the whole body invisible, so we
    must detect a degenerate (all-zero / all-opaque) alpha and skip it."""
    if not image_has_alpha(image):
        return False
    try:
        px = np.empty(len(image.pixels), dtype=np.float32)
        image.pixels.foreach_get(px)
    except Exception:
        return True  # if we cannot read pixels, keep the old behaviour
    a = px[3::4]  # RGBA -> alpha channel
    if a.size == 0:
        return False
    # Meaningful only if the alpha actually VARIES. A constant alpha (all-zero
    # or all-opaque) carries no cut-out information and must not drive opacity.
    return bool(a.max() - a.min() > 0.01)

def make_standard_normalmap(image):
    """RE:ORC normal maps store X in both the R/B channels and the alpha channel
    and Y in G (Z is implicit). Blender's importer rebuilds this with
    Separate/Combine-Color nodes, but the FBX exporter cannot translate those
    custom nodes and drops the normal map entirely.

    This bakes a proper tangent-space RGB normal map (X=R, Y=G, Z=reconstructed)
    as a new image so the normal survives FBX export (and works in any engine)."""
    try:
        w, h = image.size
        if w == 0 or h == 0:
            return None
        n = w * h
        buf = np.empty(n * 4, dtype=np.float32)
        image.pixels.foreach_get(buf)
        buf = buf.reshape(n, 4)
        nx = buf[:, 3] * 2.0 - 1.0          # X is stored in the alpha channel
        ny = buf[:, 1] * 2.0 - 1.0          # Y is stored in green
        nz = np.sqrt(np.clip(1.0 - nx * nx - ny * ny, 0.0, 1.0))
        out = np.empty(n * 4, dtype=np.float32)
        out[0::4] = nx * 0.5 + 0.5
        out[1::4] = ny * 0.5 + 0.5
        out[2::4] = nz * 0.5 + 0.5
        out[3::4] = 1.0
        img = bpy.data.images.new(image.name + "_nm", width=w, height=h, alpha=False)
        img.colorspace_settings.name = 'Non-Color'
        img.pixels.foreach_set(out)
        img.pack()
        return img
    except Exception:
        return None


def _load_asset_index():
    """Load (once, cached) the asset index: a precomputed JSON (env
    ORC_ASSET_INDEX_FILE) or a walk of ORC_ASSET_ROOT. Returns a dict
    {"tail":{...},"name":{...}} or {}."""
    global _ASSET_INDEX
    try:
        return _ASSET_INDEX
    except NameError:
        pass
    idx = None
    jf = os.environ.get("ORC_ASSET_INDEX_FILE")
    if jf and os.path.exists(jf):
        try:
            import json
            idx = json.load(open(jf, encoding="utf-8"))
        except Exception:
            idx = None
    if idx is None:
        root = os.environ.get("ORC_ASSET_ROOT")
        if root and os.path.isdir(root):
            tails, names = {}, {}
            for r, _, fs in os.walk(root):
                for f in fs:
                    full = os.path.join(r, f)
                    rel = os.path.relpath(full, root).replace("\\", "/").lower()
                    k = rel.find("dlc/")
                    tails.setdefault(rel[k:] if k >= 0 else rel, full)
                    names.setdefault(os.path.basename(rel), full)
            idx = {"tail": tails, "name": names}
    _ASSET_INDEX = idx or {}
    return _ASSET_INDEX


def resolve_asset_path(relative_path):
    """Resolve a path stored inside a model/material (e.g. 'dlc/pack1/.../x.dds'
    or 'materials/null.matb') against the model's folder, its ancestors, the
    global asset index and finally a basename search."""
    # 1) ancestor walk
    if relative_path and relative_path.strip():
        try:
            cur = Path(asset_filename).parent
            for _ in range(12):
                cand = cur / relative_path
                if os.path.isfile(cand):
                    return str(cand)
                if cur.parent == cur:
                    break
                cur = cur.parent
        except Exception:
            pass
    # 2) global asset index
    idx = _load_asset_index()
    if idx:
        key = relative_path.replace("\\", "/").lower()
        if "tail" in idx:
            tails = idx["tail"]; names = idx.get("name", {})
            if key in tails:
                return tails[key]
            for k, v in tails.items():
                if k.endswith("/" + key) or k == key:
                    return v
            base = os.path.basename(key)
            if base in names:
                return names[base]
        else:
            if key in idx:
                return idx[key]
            for k, v in idx.items():
                if k.endswith("/" + key) or k == key:
                    return v
    # 3) basename search near the model
    base = os.path.basename(relative_path)
    try:
        for r, _, fs in os.walk(Path(asset_filename).parent):
            if base in fs:
                return os.path.join(r, base)
    except Exception:
        pass
    return relative_path


def parse_material(filename, model_ob, import_materials):
    # find a material either within current subfolder (unpacked archive) or within the game folder
    # NOTE: original code assumed every material path starts with a known folder present
    # in the model path; some models reference paths like "materials/null.matb" which
    # broke it. resolve_asset_path() handles both cases robustly.
    # Empty / whitespace names (seen on some v15 weapon submeshes) -> unnamed material.
    if not filename or not str(filename).strip():
        mat = bpy.data.materials.new("unnamed")
        mat.diffuse_color = [random.uniform(.4, 1) for _ in range(3)] + [1.0]
        model_ob.data.materials.append(mat)
        return 0
    filepath = Path(resolve_asset_path(filename))
    
    if debug_print == True:
        print('Material:', filename)

    mat_name = filepath.stem
    md = model_ob.data
    mat = bpy.data.materials.get(mat_name, None)
    if mat:
        if md.materials.get(mat.name, None):
            for i, material in enumerate(md.materials):
                if material == mat:
                    return i
    else:
        mat = bpy.data.materials.new(mat_name)
        mat.diffuse_color = [random.uniform(.4, 1) for _ in range(3)] + [1.0]

        # read material file and parse textures, if possible
        if import_materials == True and os.path.exists(filepath):
            textures_applied = 0
            with filepath.open('rb') as f:
                # material file structure:
                # magic (MAT + 1 byte version) - char[4]
                # shader path offset - uint32_t
                # num textures - uint32_t
                # num something - uint32_t
                # texture information offset - uint32_t
                # something else offset (right after texture information) - uint32_t
                # then some unknown junk data

                # texture information structure:
                # magic (determines whether it is diffuse, normal or specular) - uint32_t
                # texture path offset - uint32_t

                f.seek(4, io.SEEK_CUR)
                shader_path_offset = read_uint32(f)
                texture_count = read_uint32(f)
                f.seek(4, io.SEEK_CUR)
                textures_info_offset = read_uint32(f)
                f.seek(shader_path_offset, io.SEEK_SET)
                shader_path_relative = read_string(f)

                f.seek(textures_info_offset, io.SEEK_SET)
                for i in range(texture_count):
                    magic = read_uint32(f)
                    offset = read_uint32(f)
                    tmp = f.tell()

                    f.seek(offset, io.SEEK_SET)
                    texture_path_relative = read_string(f)

                    # different shaders have different magic per texture type... so dumb!
                    # for future: magic 415201260 is cubemap on all shaders
                    #diffuse_textures_map = {
                    #    # shader name                           # magic
                    #    ("decal",                               3014450751),
                    #    ("decal_skinned",                       3014450751),
                    #    ("glow",                                439570611),
                    #    ("glow_tint",                           439570611),
                    #    ("hair_skinned_char_zombified",         3014450751),
                    #    ("lit_alphatest_d",                     3014450751),
                    #    ("lit_alphatest_decay_d",               3014450751),
                    #    ("lit_alphatest_dns",                   3014450751),
                    #    ("lit_bling_dns",                       3014450751),
                    #    ("lit_bling_env_anim_dns",              3014450751),
                    #    ("lit_bling_env_dns",                   3014450751),
                    #    ("lit_bling_env_dns_skinned",           3014450751),
                    #    ("lit_bling_env_ds",                    3014450751),
                    #    ("lit_bling_env_glass_dns",             3014450751),
                    #    ("lit_bling_env_glass_ds",              3014450751),
                    #    ("lit_bump",                            3014450751),
                    #    ("lit_bump_alpha",                      3014450751),
                    #    ("lit_bump_glow",                       3014450751),
                    #    ("lit_bump_glow_skinned",               3014450751),
                    #    ("lit_bump_glow_skinned_dismemberable", 3014450751),
                    #    ("lit_bump_skinned",                    3014450751),
                    #    ("lit_bump_skinned_char",               3014450751),
                    #    ("lit_bump_skinned_char_dismemberable", 3014450751),
                    #    ("lit_bump_skinned_char_zombified",     3014450751),
                    #    ("lit_d",                               3014450751),
                    #    ("lit_diffasspec_alphatest_dn",         3014450751),
                    #    ("lit_diffasspec_d",                    3014450751),
                    #    ("lit_diffasspec_dn",                   3014450751),
                    #    ("lit_dn",                              3014450751),
                    #    ("lit_ds",                              3014450751),
                    #    ("lit_env_dns",                         3014450751),
                    #    ("onelayer",                            3154041481),
                    #    ("onelayer_env",                        3154041481),
                    #    ("onelayer_wet",                        3154041481),
                    #    ("simplereflection_masked",             3014450751),
                    #    ("skin_skinned_char_zombified",         3014450751),
                    #    ("twolayer",                            2002049559),
                    #    ("twolayer_1uv_1ns",                    2002049559),
                    #    ("twolayer_1uv_1ns_wet",                2002049559),
                    #    ("twolayer",                            3154041481),
                    #    ("twolayer_1uv_1ns",                    3154041481),
                    #    ("twolayer_1uv_1ns_wet",                3154041481)
                    #}
                    #normal_textures_map = {
                    #    # shader name                           # magic
                    #    ("decal",                               3007457328),
                    #    ("decal_skinned",                       3007457328),
                    #    ("hair_skinned_char_zombified",         3007457328),
                    #    ("lit_alphatest_dns",                   3007457328),
                    #    ("lit_bling_dns",                       3007457328),
                    #    ("lit_bling_env_anim_dns",              3007457328),
                    #    ("lit_bling_env_dns",                   3007457328),
                    #    ("lit_bling_env_dns_skinned",           3007457328),
                    #    ("lit_bling_env_glass_dns",             3007457328),
                    #    ("lit_bump",                            3007457328),
                    #    ("lit_bump_alpha",                      3007457328),
                    #    ("lit_bump_glow",                       3007457328),
                    #    ("lit_bump_glow_skinned",               3007457328),
                    #    ("lit_bump_glow_skinned_dismemberable", 3007457328),
                    #    ("lit_bump_skinned",                    3007457328),
                    #    ("lit_bump_skinned_char",               3007457328),
                    #    ("lit_bump_skinned_char_dismemberable", 3007457328),
                    #    ("lit_bump_skinned_char_zombified",     3007457328),
                    #    ("lit_diffasspec_alphatest_dn",         3007457328),
                    #    ("lit_diffasspec_dn",                   3007457328),
                    #    ("lit_dn",                              3007457328),
                    #    ("lit_env_dns",                         3007457328),
                    #    ("onelayer",                            3078402388),
                    #    ("onelayer_env",                        3078402388),
                    #    ("onelayer_wet",                        3078402388),
                    #    ("simplereflection_masked",             3007457328),
                    #    ("skin_skinned_char_zombified",         3007457328),
                    #    ("twolayer",                            2077667786),
                    #    ("twolayer",                            3078402388),
                    #    ("twolayer_1uv_1ns",                    3078402388),
                    #    ("twolayer_1uv_1ns_wet",                3078402388)
                    #}
                    #specular_textures_map = {
                    #    # shader name                           # magic
                    #    ("decal",                               3784419238),
                    #    ("decal_skinned",                       3784419238),
                    #    ("hair_skinned_char_zombified",         3784419238),
                    #    ("lit_alphatest_dns",                   3784419238),
                    #    ("lit_bling_dns",                       3784419238),
                    #    ("lit_bling_env_anim_dns",              3784419238),
                    #    ("lit_bling_env_dns",                   3784419238),
                    #    ("lit_bling_env_dns_skinned",           3784419238),
                    #    ("lit_bling_env_ds",                    3784419238),
                    #    ("lit_bling_env_glass_dns",             3784419238),
                    #    ("lit_bling_env_glass_ds",              3784419238),
                    #    ("lit_bump",                            3784419238),
                    #    ("lit_bump_alpha",                      3784419238),
                    #    ("lit_bump_glow",                       3784419238),
                    #    ("lit_bump_glow_skinned",               3784419238),
                    #    ("lit_bump_glow_skinned_dismemberable", 3784419238),
                    #    ("lit_bump_skinned",                    3784419238),
                    #    ("lit_bump_skinned_char",               3784419238),
                    #    ("lit_bump_skinned_char_dismemberable", 3784419238),
                    #    ("lit_bump_skinned_char_zombified",     3784419238),
                    #    ("lit_ds",                              3784419238),
                    #    ("lit_env_dns",                         3784419238),
                    #    ("onelayer",                            3678436289),
                    #    ("onelayer_env",                        3678436289),
                    #    ("onelayer_wet",                        3678436289),
                    #    ("simplereflection_masked",             3784419238),
                    #    ("skin_skinned_char_zombified",         3784419238),
                    #    ("twolayer",                            270313572),
                    #    ("twolayer",                            3678436289),
                    #    ("twolayer_1uv_1ns",                    3678436289),
                    #    ("twolayer_1uv_1ns_wet",                3678436289)
                    #}
                    #glow_textures_map = {
                    #    # shader name                           # magic
                    #    ("decal",                               3014450751), # TODO: not sure about that?
                    #    ("lit_bump_glow",                       2480866802),
                    #    ("lit_bump_glow_skinned",               2480866802),
                    #    ("lit_bump_glow_skinned_dismemberable", 2480866802)
                    #}
                    #is_diffuse = (Path(shader_path_relative).stem, magic) in diffuse_textures_map and has_diffuse == False
                    #is_normal = (Path(shader_path_relative).stem, magic) in normal_textures_map and has_normal == False
                    #is_specular = (Path(shader_path_relative).stem, magic) in specular_textures_map and has_specular == False
                    #is_glow = (Path(shader_path_relative).stem, magic) in glow_textures_map and has_glow == False

                    is_diffuse = magic == 3014450751 or magic == 439570611 or magic == 3154041481 or magic == 2002049559
                    is_normal = magic == 3007457328 or magic == 3078402388 or magic == 2077667786
                    is_specular = magic == 3784419238 or magic == 3678436289 or magic == 270313572
                    is_glow = magic == 2480866802

                    if is_diffuse or is_normal or is_specular or is_glow:
                        # find the texture either within current subfolder (unpacked archive) or within the game folder
                        texture_path = resolve_asset_path(texture_path_relative)

                        if os.path.exists(texture_path):
                            mat.use_nodes = True
                            nodes = mat.node_tree.nodes
                            principled_bsdf = nodes.get("Principled BSDF")
                            if principled_bsdf is None:
                                principled_bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
                            material_output = nodes.get("Material Output")
                            if material_output is None:
                                material_output = nodes.new(type="ShaderNodeOutputMaterial")
                            links = mat.node_tree.links
                            links.new(principled_bsdf.outputs["BSDF"], material_output.inputs["Surface"])

                            image = bpy.data.images.load(texture_path, check_existing=True)
                            texture_node = None
                            for node in nodes:
                                # find an existing node with the same texture
                                if node.type == "TEX_IMAGE" and node.image == image:
                                    texture_node = node
                                    break
                            if texture_node == None:
                                texture_node = nodes.new(type="ShaderNodeTexImage")
                                texture_node.image = image
                            if is_diffuse:
                                textures_applied += 1
                                if debug_print == True:
                                    print('Diffuse:', texture_path)
                                links.new(texture_node.outputs["Color"], principled_bsdf.inputs["Base Color"])
                                if alpha_is_meaningful(image) == True:
                                    # compat: blend_method (<=4.1) / surface_render_method (4.2+)
                                    try:
                                        mat.blend_method = 'HASHED'
                                    except Exception:
                                        try: mat.surface_render_method = 'DITHERED'
                                        except Exception: pass
                                    links.new(texture_node.outputs["Alpha"], principled_bsdf.inputs["Alpha"])
                            elif is_normal:
                                textures_applied += 1
                                if debug_print == True:
                                    print('Normal:', texture_path)

                                # normal maps in RE:ORC have mixed channels:
                                # r -> compression loss data (perhaps for green channel?), not needed
                                # g -> g
                                # b -> same as r
                                # a -> r (for compression reasons)
                                #
                                # The Separate/Combine-Color node graph below works
                                # in Blender but the FBX exporter cannot translate it
                                # and silently drops the normal map. So we bake a
                                # standard tangent-space RGB normal map (X=R, Y=G,
                                # Z=reconstructed) and wire THAT directly, so the
                                # normal survives FBX export and works in any engine.
                                nm_image = make_standard_normalmap(image)
                                if nm_image is not None:
                                    nm_tex = nodes.new(type="ShaderNodeTexImage")
                                    nm_tex.image = nm_image
                                    normal_map_node = nodes.new(type="ShaderNodeNormalMap")
                                    links.new(nm_tex.outputs["Color"], normal_map_node.inputs["Color"])
                                    links.new(normal_map_node.outputs["Normal"], principled_bsdf.inputs["Normal"])
                                else:
                                    normal_map_node = nodes.new(type="ShaderNodeNormalMap")
                                    separate_color_node = nodes.new(type="ShaderNodeSeparateColor")
                                    combine_color_node = nodes.new(type="ShaderNodeCombineColor")
                                    links.new(texture_node.outputs["Color"], separate_color_node.inputs["Color"])
                                    links.new(texture_node.outputs["Alpha"], combine_color_node.inputs["Red"])
                                    links.new(separate_color_node.outputs["Green"], combine_color_node.inputs["Green"])
                                    combine_color_node.inputs["Blue"].default_value = 1.0 # set blue to 255, as we don't have data for it
                                    links.new(combine_color_node.outputs["Color"], normal_map_node.inputs["Color"])
                                    links.new(normal_map_node.outputs["Normal"], principled_bsdf.inputs["Normal"])
                            elif is_specular:
                                textures_applied += 1
                                if debug_print == True:
                                    print('Specular:', texture_path)
                                if bpy.app.version[0] >= 4:
                                    links.new(texture_node.outputs["Color"], principled_bsdf.inputs["Specular Tint"])
                                else:
                                    links.new(texture_node.outputs["Color"], principled_bsdf.inputs["Specular"])
                                if image_has_alpha(image) == True:
                                    links.new(texture_node.outputs["Alpha"], principled_bsdf.inputs["Metallic"])
                            elif is_glow:
                                textures_applied += 1
                                if debug_print == True:
                                    print('Glow:', texture_path)
                                if bpy.app.version[0] >= 4:
                                    links.new(texture_node.outputs["Color"], principled_bsdf.inputs["Emission Color"])
                                    principled_bsdf.inputs["Emission Strength"].default_value = 1.0 # why in the world did they swap this to 0.0 by default...
                                else:
                                    links.new(texture_node.outputs["Color"], principled_bsdf.inputs["Emission"])

                    # return back
                    f.seek(tmp, io.SEEK_SET)

                if texture_count > 0 and textures_applied == 0:
                    raise NotImplementedError("No textures applied for material {}, check texture magics!".format(filename))
                f.close()

    md.materials.append(mat)
    return len(md.materials) - 1

def find_skeleton_for_model(filepath):
    """Return the skeleton path for a model, or None.
    The skeleton is a file WITHOUT extension, with the same name as the model.
    It may sit next to the model (characters) or in a separate 'skel' folder
    (weapons, props) — so we also consult the global asset index."""
    cand = filepath.with_suffix('')
    if cand.exists() and cand.is_file():
        return cand
    # global index lookup: search a 'skel' entry matching the model name
    idx = _load_asset_index()
    if idx and "tail" in idx:
        name = filepath.stem.lower()
        tails = idx["tail"]
        for k, v in tails.items():
            kb = os.path.basename(k)
            if kb == name and "/skel/" in k:
                return Path(v)
    return None


def parse_model(filepath, import_bones, import_materials):
    skel_path = find_skeleton_for_model(filepath) if import_bones else None
    if skel_path is not None:
        model_collection = get_or_create_collection(filepath.stem, bpy.context.scene.collection)
        if debug_print == True:
            print('Skeleton file:', skel_path)
        rig, bone_list = parse_skel(skel_path)
    else:
        rig = None
        bone_list = []
        model_collection = bpy.context.scene.collection

    with filepath.open('rb') as f:
        file_size = f.seek(0,2)
        f.seek(0,0)
        magic = f.read(4).decode('ascii')
        assert magic == 'FM6S'
        version = read_int32(f)
        unk, mesh_count = read_int32(f), read_int32(f)
        if debug_print == True:
            print('Reading edge model "{}" of version {}'.format(magic, version))

        if version == 0x12 or version == 0x11:
            f.seek(8, io.SEEK_CUR)
            mesh_table_offset = read_int32(f)
        elif version == 0x0f:
            # version 15: only shadow / LOD1 meshes use it (weapon real models are
            # v18). Its submesh layout differs and we only export LOD0 anyway, so
            # skip cleanly rather than emit an empty mesh.
            raise NotImplementedError('Edge model of version {} is not supported (shadow/LOD mesh)'.format(version))
        else:
            raise NotImplementedError('Edge model of version {} is not supported'.format(version))
        f.seek(mesh_table_offset)
        mesh_infos: List[MeshInfo] = []
        for _ in range(mesh_count):
            sub_count, sub_offset, have_skeleton, mat_offset = read_fmt('4i', f)
            f.seek(0x40 + 0x20, io.SEEK_CUR)
            unk_data = read_fmt('8i', f)
            mesh_info = MeshInfo(sub_count, sub_offset, have_skeleton, mat_offset, unk_data)
            mesh_infos.append(mesh_info)
            if debug_print == True:
                print(mesh_info)

        for mesh_id, mesh_info in enumerate(mesh_infos):
            f.seek(mesh_info.submesh_offset)
            tmp = f.tell()
            if debug_print == True:
                print('Mesh id:', mesh_id)

            lod_collection = get_or_create_collection(f'LOD{mesh_info.lod}', model_collection)

            for sub_id in range(mesh_info.submesh_count):
                f.seek(tmp + 8)
                if debug_print == True:
                    print('Sub start:', f.tell())
                vert_count, face_count, vert_color, face_start, face_size = read_fmt('2H2iH', f)
                f.seek(0x16, io.SEEK_CUR)
                vert_start, vert_size = read_fmt('2i', f)
                f.seek(0xC, io.SEEK_CUR)
                weight_start, weight_size = read_fmt('2i', f)
                f.seek(0x24 + 4 + 12 + 4, io.SEEK_CUR)
                tmp = f.tell()
                # f.seek(24 * 4, io.SEEK_CUR)
                f.seek(mesh_info.mat_offset)
                mat_name_offset, unk_0_string_offset, unk_1_string_offset = read_fmt('3i', f)
                f.seek(mat_name_offset)
                mat_name = read_string(f)

                f.seek(face_start)
                # PiMoN: face_count * 2 was previously face_size, but it is inconsistent and might be more than face_count * 2, plus be not a multiple of 2 (FF, or 65535)
                faces = np.frombuffer(f.read(face_count * 2), np.uint16)
                faces = faces[:face_count]

                f.seek(vert_start)
                vertex_stride = vert_size // vert_count # PiMoN: vertex stride is number of bytes allocated for each vertex, noting that for myself
                vert_buffer = np.zeros(vert_count, vert_dtype)
                if debug_print == True:
                    print('Buffer start:', f.tell())
                    print('Vertex stride:', vertex_stride)
                if vertex_stride == 60:
                    for i in range(vert_count):
                        vert_buffer[i]['pos'][:] = read_fmt('3f', f)
                        vert_buffer[i]['norm'][:] = read_fmt('3f', f)
                        read_fmt('f', f)
                        vert_buffer[i]['uv'][:] = read_fmt('2e', f)
                        read_fmt('2e', f) # UV 2?
                        read_fmt('2e', f) # UV 3?
                        read_fmt('5f', f)
                elif vertex_stride == 56:
                    for i in range(vert_count):
                        vert_buffer[i]['pos'][:] = read_fmt('3f', f)
                        vert_buffer[i]['norm'][:] = read_fmt('3f', f)
                        read_fmt('f', f)
                        vert_buffer[i]['uv'][:] = read_fmt('2e', f)
                        read_fmt('6f', f)
                elif vertex_stride == 52:
                    for i in range(vert_count):
                        vert_buffer[i]['pos'][:] = read_fmt('3f', f)
                        vert_buffer[i]['norm'][:] = read_fmt('3f', f)
                        vert_buffer[i]['uv'][:] = read_fmt('2e', f)
                        read_fmt('3f', f)
                        read_fmt('3f', f)
                elif vertex_stride == 44:
                    for i in range(vert_count):
                        vert_buffer[i]['pos'][:] = read_fmt('3f', f)
                        vert_buffer[i]['norm'][:] = read_fmt('3f', f)
                        read_fmt('f', f)
                        vert_buffer[i]['uv'][:] = read_fmt('2e', f)
                        read_fmt('3f', f)
                elif vertex_stride == 40:
                    for i in range(vert_count):
                        vert_buffer[i]['pos'][:] = read_fmt('3f', f)
                        vert_buffer[i]['norm'][:] = read_fmt('3f', f)
                        vert_buffer[i]['uv'][:] = read_fmt('2e', f)
                        read_fmt('3f', f)
                elif vertex_stride == 32:
                    for i in range(vert_count):
                        vert_buffer[i]['pos'][:] = read_fmt('3f', f)
                        vert_buffer[i]['norm'][:] = read_fmt('3f', f)
                        read_fmt('f', f)
                        vert_buffer[i]['uv'][:] = read_fmt('2e', f)
                elif vertex_stride == 28:
                    for i in range(vert_count):
                        vert_buffer[i]['pos'][:] = read_fmt('3f', f)
                        vert_buffer[i]['norm'][:] = read_fmt('3f', f)
                        vert_buffer[i]['uv'][:] = read_fmt('2e', f)
                elif vertex_stride == 24:
                    for i in range(vert_count):
                        vert_buffer[i]['pos'][:] = read_fmt('3f', f)
                        vert_buffer[i]['norm'][:] = read_fmt('3f', f)
                elif vertex_stride == 12:
                    for i in range(vert_count):
                        vert_buffer[i]['pos'][:] = read_fmt('3f', f)
                else:
                    if debug_print == True:
                        print('Unknown vertex stride: {}, vertex size: {}, vertex count: {}'.format(vertex_stride, vert_size, vert_count))
                        break
                    else:
                        raise NotImplementedError('Unknown vertex stride: {}, vertex size: {}, vertex count: {}'.format(vertex_stride, vert_size, vert_count))
                if vertex_stride > 12:
                    f.seek(weight_start)
                    # PiMoN: 2 * 4 * vert_count was weight_size, but it sometimes could be out of bounds of the file and/or point to data completely unrelated to weights
                    weights = np.frombuffer(f.read(2 * 4 * vert_count), np.uint8).reshape((-1, 2, 4))[:vert_count]

                mesh_name = f'MESH{mesh_id:02d}_SUB{sub_id:02d}_LOD{mesh_info.lod}'
                mesh_data = bpy.data.meshes.new(f'{mesh_name}_MESH')
                mesh_obj = bpy.data.objects.new(mesh_name, mesh_data)

                mesh_data.from_pydata(vert_buffer['pos'].tolist(), [], faces.reshape((-1, 3)).tolist())
                mesh_data.update()

                parse_material(mat_name, mesh_obj, import_materials)

                vertex_indices = np.zeros((len(mesh_data.loops, )), dtype=np.uint32)
                mesh_data.loops.foreach_get('vertex_index', vertex_indices)

                mesh_data.polygons.foreach_set("use_smooth", np.ones(len(mesh_data.polygons), np.uint32))
                # guard: normals_split_custom_set_from_vertices crashes the
                # Blender 4.1+/5.x native code on meshes with any missing
                # (all-zero), zero-length or NaN normal. Only apply custom
                # normals when EVERY normal is valid; otherwise skip and let
                # Blender compute its own (visually fine, and no crash).
                norms = vert_buffer['norm']
                if norms.size:
                    lens = np.linalg.norm(norms, axis=1)
                    if np.isfinite(norms).all() and (lens > 1e-8).all():
                        mesh_data.normals_split_custom_set_from_vertices(norms)
                # mesh_data.use_auto_smooth = True -- PiMoN: Blender 4.1 removed this attribute, but we use custom normals anyway

                uv_data = mesh_data.uv_layers.new(name=f'UV')
                uv_layer_data = vert_buffer['uv'].copy()
                uv_layer_data[:, 1] = (1 - uv_layer_data[:, 1])
                uv_data.data.foreach_set('uv', uv_layer_data[vertex_indices].flatten())

                if bone_list:
                    weight_groups = {bone.name: mesh_obj.vertex_groups.new(name=bone.name) for bone in bone_list}
                    for n, vertex in enumerate(weights):
                        for (bone_index, weight) in zip(vertex[1], vertex[0]):
                            if weight > 0:
                                bone_name = bone_list[min(bone_index, len(bone_list) - 1)].name
                                weight_groups[bone_name].add([n], weight / 255, 'REPLACE')

                    modifier = mesh_obj.modifiers.new(type="ARMATURE", name="Armature")
                    modifier.object = rig
                    mesh_obj.parent = rig

                lod_collection.objects.link(mesh_obj)


def parse_anim(filepath, bone_list):
    print('Filepath:', filepath)
    if filepath == None:
        return

    with filepath.open('rb') as animation_file:
        header = animation_file.read(4).decode('ascii')
        assert header == '40AE' or header == 'EA04'
        
        animation_header = EdgeAnimAnimation()
        animation_header.tag = header
        animation_header.duration = read_float(animation_file)
        animation_header.framerate = read_float(animation_file)
        animation_header.size_header = read_uint16(animation_file)
        animation_header.num_bones = read_uint16(animation_file)
        animation_header.num_frames = read_uint16(animation_file)
        animation_header.num_frame_sets = read_uint16(animation_file)
        animation_header.buffer_size = read_uint16(animation_file)
        animation_header.num_const_r_channels = read_uint16(animation_file)
        animation_header.num_const_t_channels = read_uint16(animation_file)
        animation_header.num_const_s_channels = read_uint16(animation_file)
        animation_header.num_const_user_channels = read_uint16(animation_file)
        animation_header.num_anim_r_channels = read_uint16(animation_file)
        animation_header.num_anim_t_channels = read_uint16(animation_file)
        animation_header.num_anim_s_channels = read_uint16(animation_file)
        animation_header.num_anim_user_channels = read_uint16(animation_file)
        animation_header.flags = read_uint16(animation_file)
        animation_header.size_joints_weight_array = read_uint32(animation_file)
        animation_header.user_joints_weight_array = read_uint32(animation_file)
        animation_header.offset_joints_weight_array = read_uint32(animation_file)
        animation_header.offset_frame_set_dma_array = read_uint32(animation_file)
        animation_header.offset_frame_set_info_array = read_uint32(animation_file)
        animation_header.offset_const_r_data = read_uint32(animation_file)
        animation_header.offset_const_t_data = read_uint32(animation_file)
        animation_header.offset_const_s_data = read_uint32(animation_file)
        animation_header.offset_const_user_data = read_uint32(animation_file)
        animation_header.offset_packing_specs = read_uint32(animation_file)
        animation_header.offset_custom_data = read_uint32(animation_file)
        animation_header.size_custom_data = read_uint32(animation_file)

        if debug_print == True:
            print('')
            print('EdgeAnimAnimation header info')
            print('Tag:', animation_header.tag)
            print('Duration:', round(animation_header.duration, 1))
            print('Framerate:', round(animation_header.framerate, 1))
            print('Size of header:', animation_header.size_header)
            print('Bones count:', animation_header.num_bones)
            print('Frames count:', animation_header.num_frames)
            print('Frame sets count:', animation_header.num_frame_sets)
            print('Buffer size:', animation_header.buffer_size)
            print('Num const rotation channels:', animation_header.num_const_r_channels)
            print('Num const translation channels:', animation_header.num_const_t_channels)
            print('Num const scale channels:', animation_header.num_const_s_channels)
            print('Num const user channels:', animation_header.num_const_user_channels)
            print('Num animated rotation channels:', animation_header.num_anim_r_channels)
            print('Num animated translation channels:', animation_header.num_anim_t_channels)
            print('Num animated scale channels:', animation_header.num_anim_s_channels)
            print('Num animated user channels:', animation_header.num_anim_user_channels)
            print('Flags:', animation_header.flags)
            print('Size of joints weight array:', animation_header.size_joints_weight_array)
            print('User joints weight array:', animation_header.user_joints_weight_array)
            print('Offset to joints weight array:', animation_header.offset_joints_weight_array)
            print('Offset to frameset dma array:', animation_header.offset_frame_set_dma_array)
            print('Offset to frameset info array:', animation_header.offset_frame_set_info_array)
            print('Offset to const rotation data:', animation_header.offset_const_r_data)
            print('Offset to const translation data:', animation_header.offset_const_t_data)
            print('Offset to const scale data:', animation_header.offset_const_s_data)
            print('Offset to const user channel data:', animation_header.offset_const_user_data)
            print('Offset to packing specs:', animation_header.offset_packing_specs)
            print('Offset to custom data:', animation_header.offset_custom_data)
            print('Size of custom data:', animation_header.size_custom_data)
        
        animation_file.seek(0x8, 1) # we didn't read 2 x unit32_t so seek forward
        const_r_channels = []
        const_t_channels = []
        const_s_channels = []
        const_user_channels = []
        anim_r_channels = []
        anim_t_channels = []
        anim_s_channels = []
        anim_user_channels = []
        for i in range(align_bytes(animation_header.num_const_r_channels, 8)):
            const_r_channels.append(read_uint16(animation_file))
        for i in range(align_bytes(animation_header.num_const_t_channels, 4)):
            const_t_channels.append(read_uint16(animation_file))
        for i in range(align_bytes(animation_header.num_const_s_channels, 4)):
            const_s_channels.append(read_uint16(animation_file))
        for i in range(align_bytes(animation_header.num_const_user_channels, 4)):
            const_user_channels.append(read_uint16(animation_file))
        for i in range(align_bytes(animation_header.num_anim_r_channels, 4)):
            anim_r_channels.append(read_uint16(animation_file))
        for i in range(align_bytes(animation_header.num_anim_t_channels, 4)):
            anim_t_channels.append(read_uint16(animation_file))
        for i in range(align_bytes(animation_header.num_anim_s_channels, 4)):
            anim_s_channels.append(read_uint16(animation_file))
        for i in range(align_bytes(animation_header.num_anim_user_channels, 4)):
            anim_user_channels.append(read_uint16(animation_file))
        
        if debug_print == True:
            print('')
            print('Const rotation channels:', const_r_channels)
            print('Const translation channels:', const_t_channels)
            print('Const scale channels:', const_s_channels)
            print('Const user channels:', const_user_channels)
            print('Animated rotation channels:', anim_r_channels)
            print('Animated translation channels:', anim_t_channels)
            print('Animated scale channels:', anim_s_channels)
            print('Animated user channels:', anim_user_channels)
        
        align_seek(animation_file, 16) # TODO it doesn't align in the compiler but I have to?
        
        bpy.ops.object.mode_set(mode='POSE')
        bpy.context.scene.render.fps = int(animation_header.framerate)
        
        # reset all bones to bind pose first
        for bone in bpy.data.objects['Armature'].pose.bones:
            bone.matrix_basis.identity()
            bone.id_data.animation_data_clear()
        
        for bone in bone_list:
            bone.angle = [bone.angle] * animation_header.num_frames
            bone.position = [bone.position] * animation_header.num_frames
            try:
                pose_bone = bpy.data.objects['Armature'].pose.bones[bone.name]
                if pose_bone != None:
                    bone.bind_matrix = mathutils.Matrix(pose_bone.bone.matrix_local)
                else:
                    bone.bind_matrix = mathutils.Matrix()
            except KeyError:
                bone.bind_matrix = mathutils.Matrix()
                if debug_print == True:
                    print('Bone {} not found;'.format(bone.name))

        bpy.context.scene.frame_current = 0
        bpy.context.scene.frame_start = 0
        bpy.context.scene.frame_end = animation_header.num_frames - 1
        
        # read const rotation data
        for i in range(animation_header.num_const_r_channels):
            bytes = read_fmt('6B',animation_file) # read_uint8 6 times
            animation_data = decompress_animation_rotation(bytes)
            
            # save it to apply later
            for j in range(animation_header.num_frames):
                bone_list[const_r_channels[i]].angle[j] = animation_data
        
        # read const translation
        align_seek(animation_file, 16)
        for i in range(animation_header.num_const_t_channels):
            bytes = read_fmt('12B',animation_file) # read_uint8 12 times
            animation_data = decompress_animation_vector(bytes)
            
            # save it to apply later
            for j in range(animation_header.num_frames):
                bone_list[const_t_channels[i]].position[j] = animation_data

        # const scale (not used in RE:ORC)
        align_seek(animation_file, 16)
        animation_file.seek(12 * animation_header.num_const_s_channels, 1)
        
        # const user data (not used for animation playback)
        align_seek(animation_file, 4)
        animation_file.seek(4 * animation_header.num_const_user_channels, 1)
        
        # packing specks (not used in RE:ORC)
        if animation_header.offset_packing_specs != 0:
            align_seek(animation_file, 4)
            assert animation_file.tell() == 0x4c + animation_header.offset_packing_specs
            # how to calculate size?
            # animation_file.seek(???, 1)
        
        # frame set dma
        align_seek(animation_file, 16)
        for i in range(animation_header.num_frame_sets):
            animation_file.seek(2, 1)
            animation_file.seek(2, 1)
            animation_file.seek(4, 1)

        # frame set info
        align_seek(animation_file, 4)
        frame_set_info = []
        for i in range(animation_header.num_frame_sets):
            base_frame = read_uint16(animation_file)
            num_intra_frames = read_uint16(animation_file)
            frame_set_info.append(EdgeAnimFrameSetInfo(base_frame, num_intra_frames))
        
        #for i in range(animation_header.num_frames):
        #    print('Frame',i,'animset:',anim_get_frame_set_index(animation_header,frame_set_info,i))
        
        # end header
        align_seek(animation_file, 16)
        
        # joint weights
        if animation_header.size_joints_weight_array != 0:
            align_seek(animation_file, 16)
            animation_file.seek(animation_header.size_joints_weight_array, 1)
        
        # frame set data
        for i in range(animation_header.num_frame_sets):
            align_seek(animation_file, 16)
            if i == 0:
                assert animation_file.tell() == animation_header.size_header

            if debug_print == True:
                print('')
                print('Frameset',i,)
                print('Base frames:',frame_set_info[i].base_frame)
                print('Num intra frames:',frame_set_info[i].num_intra_frames)
            
            frame_set_info[i].offset_frameset_start = animation_file.tell()
            if debug_print == True:
                print('Offset to frameset start:', frame_set_info[i].offset_frameset_start)

            # these offsets are relative to the start of the frame set!
            if animation_header.num_frame_sets > 1:
                frame_set_info[i].size_initial_r_data = read_uint16(animation_file)
                frame_set_info[i].size_initial_t_data = read_uint16(animation_file)
                frame_set_info[i].size_initial_s_data = read_uint16(animation_file)
                frame_set_info[i].size_initial_user_data = read_uint16(animation_file)
                frame_set_info[i].size_intra_r_data = read_uint16(animation_file)
                frame_set_info[i].size_intra_t_data = read_uint16(animation_file)
                frame_set_info[i].size_intra_s_data = read_uint16(animation_file)
                frame_set_info[i].size_intra_user_data = read_uint16(animation_file)
                if debug_print == True:
                    print('Size of initial rotation data:', frame_set_info[i].size_initial_r_data)
                    print('Size of initial translation data:', frame_set_info[i].size_initial_t_data)
                    print('Size of initial scale data:', frame_set_info[i].size_initial_s_data)
                    print('Size of initial user data:', frame_set_info[i].size_initial_user_data)
                    print('Size of intra rotation data:', frame_set_info[i].size_intra_r_data)
                    print('Size of intra translation data:', frame_set_info[i].size_intra_t_data)
                    print('Size of intra scale data:', frame_set_info[i].size_intra_s_data)
                    print('Size of intra user data:', frame_set_info[i].size_intra_user_data)
                
                frame_set_info[i].offset_initial_r_data = 0x10
                frame_set_info[i].offset_initial_t_data = frame_set_info[i].offset_initial_r_data + frame_set_info[i].size_initial_r_data
                frame_set_info[i].offset_initial_s_data = frame_set_info[i].offset_initial_t_data + frame_set_info[i].size_initial_t_data
                frame_set_info[i].offset_user_data_initial = frame_set_info[i].offset_initial_s_data + frame_set_info[i].size_initial_s_data
                frame_set_info[i].bits_intra_adr = frame_set_info[i].offset_user_data_initial + frame_set_info[i].size_initial_user_data
                frame_set_info[i].offset_intra_r_data = int(frame_set_info[i].bits_intra_adr + ((animation_header.num_anim_r_channels + animation_header.num_anim_t_channels + animation_header.num_anim_s_channels + animation_header.num_anim_user_channels) * frame_set_info[i].num_intra_frames + 7) / 8)
                frame_set_info[i].offset_intra_t_data = frame_set_info[i].offset_intra_r_data + frame_set_info[i].size_intra_r_data
                frame_set_info[i].offset_intra_s_data = frame_set_info[i].offset_intra_t_data + frame_set_info[i].size_intra_t_data
                frame_set_info[i].offset_intra_user_data = align_bytes(frame_set_info[i].offset_intra_s_data + frame_set_info[i].size_intra_s_data, 4)
                frame_set_info[i].offset_next_frame_set = align_bytes(frame_set_info[i].offset_intra_user_data + frame_set_info[i].size_intra_user_data, 16)
                animation_file.seek(frame_set_info[i].offset_frameset_start + frame_set_info[i].offset_next_frame_set, 0)
                frame_set_info[i].size_final_r_data = read_uint16(animation_file)
                frame_set_info[i].size_final_t_data = read_uint16(animation_file)
                frame_set_info[i].size_final_s_data = read_uint16(animation_file)
                animation_file.seek(0xA, 1)
                frame_set_info[i].offset_final_r_data = animation_file.tell() - frame_set_info[i].offset_frameset_start
                frame_set_info[i].offset_final_t_data = frame_set_info[i].offset_final_r_data + frame_set_info[i].size_final_r_data
                frame_set_info[i].offset_final_s_data = frame_set_info[i].offset_final_t_data + frame_set_info[i].size_final_t_data
                frame_set_info[i].offset_final_user_data = frame_set_info[i].offset_final_s_data + frame_set_info[i].size_final_s_data
                frame_set_info[i].offset_intra_r_bits = 0
                frame_set_info[i].offset_intra_t_bits = frame_set_info[i].offset_intra_r_bits + animation_header.num_anim_r_channels * frame_set_info[i].num_intra_frames
                frame_set_info[i].offset_intra_s_bits = frame_set_info[i].offset_intra_t_bits + animation_header.num_anim_t_channels * frame_set_info[i].num_intra_frames
                frame_set_info[i].offset_intra_user_bits = frame_set_info[i].offset_intra_s_bits + animation_header.num_anim_s_channels * frame_set_info[i].num_intra_frames
                frame_set_info[i].bit_mask = anim_generate_bit_mask(frame_set_info[i].num_intra_frames)
                if debug_print == True:
                    print('Offset to initial rotation data', frame_set_info[i].offset_initial_r_data)
                    print('Offset to initial translation data', frame_set_info[i].offset_initial_t_data)
                    print('Offset to initial scale data', frame_set_info[i].offset_initial_s_data)
                    print('Offset to initial user data', frame_set_info[i].offset_initial_user_data)
                    print('Bits intra adr', frame_set_info[i].bits_intra_adr)
                    print('Offset to intra rotation data', frame_set_info[i].offset_intra_r_data)
                    print('Offset to intra translation data', frame_set_info[i].offset_intra_t_data)
                    print('Offset to intra scale data', frame_set_info[i].offset_intra_s_data)
                    print('Offset to intra user data', frame_set_info[i].offset_intra_user_data)
                    print('Offset to next frame set', frame_set_info[i].offset_next_frame_set)
                    print('Size of final rotation data:', frame_set_info[i].size_final_r_data)
                    print('Size of final translation data:', frame_set_info[i].size_final_t_data)
                    print('Size of final scale data:', frame_set_info[i].size_final_s_data)
                    print('Offset to final rotation data', frame_set_info[i].offset_final_r_data)
                    print('Offset to final translation data', frame_set_info[i].offset_final_t_data)
                    print('Offset to final scale data', frame_set_info[i].offset_final_s_data)
                    print('Offset to final user data', frame_set_info[i].offset_final_user_data)
                    print('Offset to intra rotation bits', frame_set_info[i].offset_intra_r_bits)
                    print('Offset to intra translation bits', frame_set_info[i].offset_intra_t_bits)
                    print('Offset to intra scale bits', frame_set_info[i].offset_intra_s_bits)
                    print('Offset to intra user bits', frame_set_info[i].offset_intra_user_bits)
                    print('Bit mask (from intra frame count):', frame_set_info[i].bit_mask)

            # seek to the start of next frame set data
            animation_file.seek(frame_set_info[i].offset_frameset_start + frame_set_info[i].offset_next_frame_set, 0)

        for i in range(animation_header.num_frames):
            frame_set_id = anim_get_frame_set_index(animation_header, frame_set_info, i)
            frame_set = frame_set_info[frame_set_id]
            frame_number = i - frame_set.base_frame
            frame_fraction = 0
            
            if frame_number > frame_set.num_intra_frames:
                frame_number = frame_set.num_intra_frames
                frame_fraction = 1

            prev_bit_mask = anim_generate_bit_mask(frame_number)
            offset_intra_r_bits = frame_set.offset_intra_r_bits
            offset_intra_r_data = frame_set.offset_intra_r_data
            offset_initial_r_data = frame_set.offset_initial_r_data
            offset_final_r_data = frame_set.offset_final_r_data
            offset_intra_t_bits = frame_set.offset_intra_t_bits
            offset_intra_t_data = frame_set.offset_intra_t_data
            offset_initial_t_data = frame_set.offset_initial_t_data
            offset_final_t_data = frame_set.offset_final_t_data
            
            # read animated rotation
            animation_file.seek(frame_set.offset_frameset_start, 0)
            for j in range(animation_header.num_anim_r_channels):
                key_a, key_b, num_keys, alpha = anim_get_bracketing_keyframes(animation_file, numpy.uint32(frame_number), frame_fraction, prev_bit_mask, 6, offset_intra_r_bits, offset_intra_r_data, offset_initial_r_data, offset_final_r_data, frame_set.offset_frameset_start, frame_set.bits_intra_adr, frame_set.bit_mask)

                try:
                    animation_file.seek(frame_set.offset_frameset_start + key_a, 0)
                    rot_a = decompress_animation_rotation(read_fmt('6B',animation_file)) # read_uint8 6 times
                    animation_file.seek(frame_set.offset_frameset_start + key_b, 0)
                    rot_b = decompress_animation_rotation(read_fmt('6B',animation_file)) # read_uint8 6 times

                    result_data = anim_slerp(alpha, rot_a, rot_b)
                except ValueError:
                    # a fucking NaN by sony, what a joke
                    # use last frame's data for this bone
                    result_data = bone_list[anim_r_channels[j]].angle[i - 1]
            
                # save it to apply later
                bone_list[anim_r_channels[j]].angle[i] = result_data
                
                offset_intra_r_bits += frame_set.num_intra_frames
                offset_intra_r_data += num_keys * 6
                offset_initial_r_data += 6
                offset_final_r_data += 6

            # read animated translation
            animation_file.seek(frame_set.offset_frameset_start, 0)
            for j in range(animation_header.num_anim_t_channels):
                key_a, key_b, num_keys, alpha = anim_get_bracketing_keyframes(animation_file, numpy.uint32(frame_number), frame_fraction, prev_bit_mask, 12, offset_intra_t_bits, offset_intra_t_data, offset_initial_t_data, offset_final_t_data, frame_set.offset_frameset_start, frame_set.bits_intra_adr, frame_set.bit_mask)

                animation_file.seek(frame_set.offset_frameset_start + key_a, 0)
                trans_a = decompress_animation_vector(read_fmt('12B',animation_file)) # read_uint8 12 times
                animation_file.seek(frame_set.offset_frameset_start + key_b, 0)
                trans_b = decompress_animation_vector(read_fmt('12B',animation_file)) # read_uint8 12 times
                
                result_data = anim_lerp(alpha, trans_a, trans_b)

                # save it to apply later
                bone_list[anim_t_channels[j]].position[i] = result_data
                
                offset_intra_t_bits += frame_set.num_intra_frames
                offset_intra_t_data += num_keys * 12
                offset_initial_t_data += 12
                offset_final_t_data += 12

        if animation_header.offset_custom_data > 0:
            # custom data (skel_root motion)
            animation_file.seek(animation_header.offset_custom_data + 0x50 + 32, 0)

            # translation
            for i in range(animation_header.num_frames):
                x = read_float(animation_file)
                y = read_float(animation_file)
                z = read_float(animation_file)
                animation_file.seek(4, 1)
                result_data = mathutils.Vector((x, y, z))
                
                # save it to apply later
                bone_list[0].position[i] = result_data

            # angle
            for i in range(animation_header.num_frames):
                x = read_float(animation_file)
                y = read_float(animation_file)
                z = read_float(animation_file)
                w = read_float(animation_file)
                result_data = mathutils.Quaternion((w, x, y, z))
                
                # save it to apply later
                bone_list[0].angle[i] = result_data
        
        for bone in bone_list:
            try:
                pose_bone = bpy.data.objects['Armature'].pose.bones[bone.name]
                if pose_bone != None:
                    bind_matrix = bone.bind_matrix
                    if bone.parent_id != -1:
                        bind_matrix = bone_list[bone.parent_id].bind_matrix.inverted() @ bind_matrix
                    for i in range(animation_header.num_frames):
                        pose_bone.location = bone.position[i] - bind_matrix.to_translation()
                        pose_bone.keyframe_insert(data_path='location',frame=i)
                        pose_bone.rotation_quaternion = bind_matrix.to_quaternion().rotation_difference(bone.angle[i])
                        pose_bone.keyframe_insert(data_path='rotation_quaternion',frame=i)
            except KeyError:
                if debug_print == True:
                    print('Bone {} not found;'.format(bone.name))

        bpy.ops.object.mode_set(mode='OBJECT')

        animation_file.close()

def parse_file(filename, import_bones, import_materials):
    global asset_filename
    asset_filename = filename
    filepath = Path(filename)
    print('File name:', filename)
    print('File extension:', filepath.suffix if filepath.suffix != '' else 'None (animation or skeleton)')

    global anim_filepath
    if filepath.suffix=='.edgemodel':
        parse_model(filepath, import_bones, import_materials)
    elif filepath.suffix=='.edgeanim':
        anim_filepath = filepath
        bpy.ops.reorc.open_skelforanim('INVOKE_DEFAULT')
    elif filepath.suffix=='.edgeskel':
        parse_skel(filepath)
    elif filepath.suffix=='':
        with filepath.open('rb') as file:
            header = file.read(4).decode('ascii')
            if header == '40AE' or header == 'EA04':
                anim_filepath = filepath
                bpy.ops.reorc.open_skelforanim('INVOKE_DEFAULT')
            elif header == '20SE' or header == 'ES02':
                parse_skel(filepath)
            
            file.close()

class OT_OpenSkelForAnim(Operator, ImportHelper):
    bl_idname = "reorc.open_skelforanim"
    bl_label = "Load skeleton"

    filter_glob: StringProperty(
        #default='*.edgeskel',
        default='*',
        options={'HIDDEN'}
    )

    def execute(self, context):
        with Path(self.filepath).open('rb') as file:
            header = file.read(4).decode('ascii')
            if header == '20SE' or header == 'ES02':
                skeleton_header = EdgeAnimSkeleton()
                skeleton_header.tag = header
                skeleton_header.size_total = read_uint32(file)
                skeleton_header.size_custom_data = read_uint32(file)
                skeleton_header.size_name_hashes = read_uint32(file)
                skeleton_header.num_joints = read_uint16(file)
                skeleton_header.num_user_channels = read_uint16(file)
                skeleton_header.num_simd_hierarchy_quads = read_uint16(file)
                file.seek(0x02, 1) # pad0 (uint8_t x2)
                skeleton_header.offset_base_pose = read_uint32(file)
                skeleton_header.offset_parent_indices_array = read_uint32(file)
                skeleton_header.offset_joint_name_hash_array = read_uint32(file)
                skeleton_header.offset_user_channel_name_hash_array = read_uint32(file)
                skeleton_header.offset_user_channel_node_name_hash_array = read_uint32(file)
                skeleton_header.offset_user_channel_flags_array = read_uint32(file)
                skeleton_header.offset_custom_data = read_uint32(file)
                if debug_print == True:
                    print('')
                    print('EdgeAnimSkeleton header info')
                    print('Tag:', skeleton_header.tag)
                    print('Size total:', skeleton_header.size_total)
                    print('Size of custom data:', skeleton_header.size_custom_data)
                    print('Size of name hashes:', skeleton_header.size_name_hashes)
                    print('Num joints:', skeleton_header.num_joints)
                    print('Num user channels:', skeleton_header.num_user_channels)
                    print('Num SIMD hierarchy quads:', skeleton_header.num_simd_hierarchy_quads)
                    print('Offset to base pose:', skeleton_header.offset_base_pose)
                    print('Offset to parent indices array:', skeleton_header.offset_parent_indices_array)
                    print('Offset to joint name hash array:', skeleton_header.offset_joint_name_hash_array)
                    print('Offset to user channel name hash array:', skeleton_header.offset_user_channel_name_hash_array)
                    print('Offset to user channel node name hash array:', skeleton_header.offset_user_channel_node_name_hash_array)
                    print('Offset to user channel flags array:', skeleton_header.offset_user_channel_flags_array)
                    print('Offset to custom data:', skeleton_header.offset_custom_data)
            
                # parse bone data
                bone_list: List[EdgeBone] = []
                parse_bones(file, bone_list, skeleton_header.num_joints, skeleton_header.offset_base_pose, skeleton_header.offset_parent_indices_array, skeleton_header.offset_custom_data)
                parse_anim(anim_filepath, bone_list)

            file.close()

        return {'FINISHED'}

class OT_OpenAsset(Operator, ImportHelper):
    bl_idname = "reorc.open_asset"
    bl_label = "Load"

    filter_glob: StringProperty(
        #default='*.edgeanim;*.edgemodel;*.edgeskel',
        default='*',
        options={'HIDDEN'}
    )
    import_bones: BoolProperty(
        name='Import bones (models only)',
        default=True,
    )
    import_materials: BoolProperty(
        name='Import materials (models only)',
        default=True,
    )
    files: CollectionProperty(
        name="File Path",
        type=OperatorFileListElement,
    )
    directory: StringProperty(
        subtype='DIR_PATH',
    )

    def execute(self, context):
        for file_elem in self.files:
            filepath = os.path.join(self.directory, file_elem.name)
            if os.path.isfile(filepath) == True:
                parse_file(filepath, self.import_bones, self.import_materials)

        return {'FINISHED'}


bpy.utils.register_class(OT_OpenSkelForAnim)
bpy.utils.register_class(OT_OpenAsset)
bpy.ops.reorc.open_asset('INVOKE_DEFAULT')
