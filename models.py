from __future__ import annotations
import pygame as pg
from OpenGL.GL import *
import numpy as np
from typing import TextIO
import ctypes
from math_utils import Vec3, Vec4, Mat4


DATA_TYPE_COLORED_VERTEX = np.dtype({
    'names': ['x', 'y', 'z', 'color', 'u', 'v'],
    'formats': [np.float32, np.float32, np.float32, np.uint32, np.float32, np.float32],
    'offsets': [0, 4, 8, 12, 16, 20],
    'itemsize': 24
})

DATA_TYPE_VERTEX = np.dtype({
    'names': ['x', 'y', 'z', 'u', 'v', 'nx', 'ny', 'nz'],
    'formats': [np.float32, np.float32, np.float32, np.float32, np.float32, np.float32, np.float32, np.float32],
    'offsets': [0, 4, 8, 12, 16, 20, 24, 28],
    'itemsize': 32
})


class Material:

    def __init__(self):
        self.texture = glGenTextures(1)

    def load_from_file(self, filename: str) -> "Material":
        image = pg.image.load(filename).convert_alpha()
        width, height = image.get_rect().size
        vertical_flip = True
        data = pg.image.tobytes(image, "RGBA", vertical_flip)

        glBindTexture(GL_TEXTURE_2D, self.texture)

        target_mip_level = 0
        internal_format = GL_RGBA
        border_color = 0
        incoming_format = GL_RGBA
        data_type = GL_UNSIGNED_BYTE
        glTexImage2D(GL_TEXTURE_2D, target_mip_level, internal_format,
                     width, height, border_color, incoming_format,
                     data_type, data)

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

        return self

    def use(self) -> None:
        glBindTexture(GL_TEXTURE_2D, self.texture)

    def destroy(self) -> None:
        glDeleteTextures(1, (self.texture,))


class Mesh:
    def __init__(self):
        self.VAO = glGenVertexArrays(1)
        self.VBO, self.EBO = glGenBuffers(2)
        self.index_count = 0
        self.material_id = -1
        self.vertices = None
        self.indices = None

    def build_colored_quad(self) -> "Mesh":
        vertices = np.zeros(4, dtype=DATA_TYPE_COLORED_VERTEX)
        vertices[0]['x'] = -0.75
        vertices[0]['y'] = -0.75
        vertices[0]['z'] = 0.0
        vertices[0]['color'] = 0
        vertices[0]['u'] = 0.0
        vertices[0]['v'] = 0.0

        vertices[1]['x'] = 0.75
        vertices[1]['y'] = -0.75
        vertices[1]['z'] = 0.0
        vertices[1]['color'] = 1
        vertices[1]['u'] = 1.0
        vertices[1]['v'] = 0.0

        vertices[2]['x'] = 0.75
        vertices[2]['y'] = 0.75
        vertices[2]['z'] = 0.0
        vertices[2]['color'] = 2
        vertices[2]['u'] = 1.0
        vertices[2]['v'] = 1.0

        vertices[3]['x'] = -0.75
        vertices[3]['y'] = 0.75
        vertices[3]['z'] = 0.0
        vertices[3]['color'] = 2
        vertices[3]['u'] = 0.0
        vertices[3]['v'] = 1.0

        glBindVertexArray(self.VAO)
        glBindBuffer(GL_ARRAY_BUFFER, self.VBO)
        attribute_index = 0
        size = 3
        offset = 0
        stride = DATA_TYPE_COLORED_VERTEX.itemsize
        glVertexAttribPointer(attribute_index, size, GL_FLOAT,
                              GL_FALSE, stride, ctypes.c_void_p(offset))
        glEnableVertexAttribArray(attribute_index)

        attribute_index += 1
        offset += 12
        size = 1
        glVertexAttribIPointer(attribute_index, size, GL_UNSIGNED_INT,
                               stride, ctypes.c_void_p(offset))
        glEnableVertexAttribArray(attribute_index)

        attribute_index += 1
        offset += 4
        size = 2
        glVertexAttribPointer(attribute_index, size, GL_FLOAT,
                              GL_FALSE, stride, ctypes.c_void_p(offset))
        glEnableVertexAttribArray(attribute_index)

        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

        self.index_count = 6
        indices = np.array((0, 1, 2, 2, 3, 0), dtype=np.int32)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.EBO)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)

        return self

    def build_from_file(self, file: TextIO, material_id: int, pre_transform: Mat4,
                        v: list[list[float]], vt: list[list[float]], vn: list[list[float]], history: dict[str, int]) -> "Mesh":
        self.material_id = material_id
        self.vertices = np.zeros(0, dtype=DATA_TYPE_VERTEX)
        self.indices = []

        original_pos = file.tell()
        line = file.readline()
        while line:
            words = line.strip().split(" ")
            if words[0] == "usemtl":
                file.seek(original_pos)
                self.finalize_model()
                return self
            if words[0] == "v":
                read_v(words, v, pre_transform)
            if words[0] == "vt":
                read_vt(words, vt)
            if words[0] == "vn":
                read_vn(words, vn)
            if words[0] == "f":
                self.read_face(words, v, vt, vn, history)
            original_pos = file.tell()
            line = file.readline()
        self.finalize_model()
        return self

    def read_face(self, words: list[str], v: list[list[float]], vt: list[list[float]], vn: list[list[float]], history: dict[str, int]) -> None:
        triangle_count = len(words) - 3
        for i in range(triangle_count):
            self.read_vertex(words[1], v, vt, vn, history)
            self.read_vertex(words[i + 2], v, vt, vn, history)
            self.read_vertex(words[i + 3], v, vt, vn, history)

    def read_vertex(self, words: str, v: list[list[float]], vt: list[list[float]], vn: list[list[float]], history: dict[str, int]) -> None:
        if words in history:
            self.indices.append(history[words])
            return

        history[words] = len(self.vertices)
        self.indices.append(history[words])

        v_vt_vn_indices = [int(word) - 1 for word in words.split("/")]
        new_vertex = np.zeros(1, dtype=DATA_TYPE_VERTEX)
        pos = v[v_vt_vn_indices[0]]
        new_vertex[0]['x'] = pos[0]
        new_vertex[0]['y'] = pos[1]
        new_vertex[0]['z'] = pos[2]

        tex_coord = vt[v_vt_vn_indices[1]]
        new_vertex[0]['u'] = tex_coord[0]
        new_vertex[0]['v'] = tex_coord[1]

        normal = vn[v_vt_vn_indices[2]]
        new_vertex[0]['nx'] = normal[0]
        new_vertex[0]['ny'] = normal[1]
        new_vertex[0]['nz'] = normal[2]

        self.vertices = np.append(self.vertices, new_vertex[0])

    def finalize_model(self) -> "Mesh":
        glBindVertexArray(self.VAO)
        glBindBuffer(GL_ARRAY_BUFFER, self.VBO)

        attribute_index = 0
        size = 3
        offset = 0
        stride = DATA_TYPE_VERTEX.itemsize
        glVertexAttribPointer(attribute_index, size, GL_FLOAT,
                              GL_FALSE, stride, ctypes.c_void_p(offset))
        glEnableVertexAttribArray(attribute_index)

        attribute_index += 1
        offset += 12
        size = 2
        glVertexAttribPointer(attribute_index, size, GL_FLOAT,
                              GL_FALSE, stride, ctypes.c_void_p(offset))
        glEnableVertexAttribArray(attribute_index)

        attribute_index += 1
        offset += 8
        size = 3
        glVertexAttribPointer(attribute_index, size, GL_FLOAT,
                              GL_FALSE, stride, ctypes.c_void_p(offset))
        glEnableVertexAttribArray(attribute_index)

        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW)

        self.index_count = len(self.indices)
        indices = np.array(self.indices, dtype=np.uint32)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.EBO)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)

        self.vertices = None
        self.indices = None

        return self

    def draw(self) -> None:
        glBindVertexArray(self.VAO)
        glDrawElements(GL_TRIANGLES, self.index_count, GL_UNSIGNED_INT, ctypes.c_void_p(0))

    def destroy(self) -> None:
        glDeleteVertexArrays(1, (self.VAO,))
        glDeleteBuffers(2, (self.VBO, self.EBO,))


class Model:
    def __init__(self, filename: str, pre_transform: Mat4):
        self.meshes: list[Mesh] = []
        self.materials: dict[int, Material] = {}

        material_ids = parse_materials(filename, self.materials)
        load_meshes(filename, material_ids, pre_transform, self.meshes)

    def draw(self) -> None:
        for mesh in self.meshes:
            self.materials[mesh.material_id].use()
            mesh.draw()

    def destroy(self) -> None:
        for material in self.materials.values():
            material.destroy()
        for mesh in self.meshes:
            mesh.destroy()


def parse_materials(filename: str, materials: dict[int, Material]) -> dict[str, int]:
    mtl_filename = ""
    material_ids = {}

    with open(filename, "r") as file:
        while line := file.readline():
            words = line.strip().split(" ")
            if words[0] == "mtllib":
                mtl_filename = "models/" + words[1]
                break

    if len(mtl_filename) == 0:
        return material_ids

    current_id = -1
    with open(mtl_filename, "r") as file:
        while line := file.readline():
            words = line.strip().split(" ")
            if words[0] == "newmtl":
                current_id += 1
                material_ids[words[1]] = current_id
                materials[current_id] = Material()
            if words[0] == "map_Kd":
                materials[current_id].load_from_file(words[1])

    return material_ids


def load_meshes(filename: str, material_ids: dict[str, int], pre_transform: "Mat4", meshes: list["Mesh"]) -> None:
    v = []
    vt = []
    vn = []
    history = {}

    with open(filename, "r") as file:
        while line := file.readline():
            words = line.strip().split(" ")
            if words[0] == "v":
                read_v(words, v, pre_transform)
            if words[0] == "vt":
                read_vt(words, vt)
            if words[0] == "vn":
                read_vn(words, vn)
            if words[0] == "usemtl":
                material_id = material_ids[words[1]]
                meshes.append(Mesh().build_from_file(file, material_id, pre_transform,
                                                     v, vt, vn, history))


def read_v(words: list[str], v: list[list[float]], pre_transform: "Mat4") -> None:
    x = float(words[1])
    y = float(words[2])
    z = float(words[3])

    transformed = pre_transform * Vec4(x, y, z, 1.0)
    v.append([transformed.data[0], transformed.data[1], transformed.data[2]])


def read_vt(words: list[str], vt: list[list[float]]) -> None:
    u = float(words[1])
    v = float(words[2])
    vt.append([u, v])

def read_vn(words:list[str], vn: list[list[float]]) -> None:
    x = float(words[1])
    y = float(words[2])
    z = float(words[3])

    vn.append([x,y,z])
