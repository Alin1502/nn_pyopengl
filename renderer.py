from __future__ import annotations
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
from math_utils import Mat4
from models import Mesh, Material, Model
from constants import *


def make_shader(vertex_filename: str, fragment_filename: str) -> int:
    vertex_module = make_shader_module(vertex_filename, GL_VERTEX_SHADER)
    fragment_module = make_shader_module(fragment_filename, GL_FRAGMENT_SHADER)
    return compileProgram(vertex_module, fragment_module)


def make_shader_module(filename: str, module_type: int) -> int:
    with open(filename, "r") as file:
        source_code = file.readlines()
        return compileShader(source_code, module_type)


class Shader:

    def __init__(self, vertex_filename: str, fragment_filename: str):
        self.program = make_shader(vertex_filename, fragment_filename)
        self.locations: dict[int, int] = {}

    def use(self) -> None:
        glUseProgram(self.program)

    def upload_mat4(self, uniform_type: int, matrix: Mat4) -> None:
        if uniform_type not in self.locations:
            name = UNIFORM_NAMES[uniform_type]
            self.locations[uniform_type] = glGetUniformLocation(self.program, name)
        glUniformMatrix4fv(self.locations[uniform_type], 1, GL_FALSE, matrix.data)

    def destroy(self) -> None:
        glDeleteProgram(self.program)


class Renderer:
    SCREEN_COLOR = (0.1, 0.1, 1.0, 1.0)

    def __init__(self):
        glClearColor(*Renderer.SCREEN_COLOR)
        glEnable(GL_DEPTH_TEST)

        self.materials = {}
        self.meshes = {}
        self.load_assets()

        self.mesh = Mesh().build_colored_quad()
        self.material = Material().load_from_file("textures/brickwall.jpg")

        self.shaders: dict[int, Shader] = {}
        self.load_shaders()

        fovy = 60.0
        aspect = 4.0 / 3.0
        near = 0.1
        far = 10.0
        projection_matrix = Mat4().from_perspective_projection(fovy, aspect, near, far)
        for shader in self.shaders.values():
            shader.use()
            shader.upload_mat4(UNIFORM_TYPE_PROJECTION, projection_matrix)

    def load_assets(self) -> None:
        self.meshes[OBJECT_TYPE_QUAD] = Mesh().build_colored_quad()
        self.materials[OBJECT_TYPE_QUAD] = Material().load_from_file("textures/brickwall.jpg")

        self.meshes[OBJECT_TYPE_MODEL] = Model(
            filename="models/Bullet.obj",
            pre_transform=Mat4().from_x_rotation(90.0) * Mat4().from_scale(0.15)
        )

    def load_shaders(self) -> None:
        for pipeline_type, filenames in SHADER_FILENAMES.items():
            self.shaders[pipeline_type] = Shader(*filenames)

    def draw(self, objects: list, camera) -> None:
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        view_transform = camera.get_view_transform()
        for shader in self.shaders.values():
            shader.use()
            shader.upload_mat4(UNIFORM_TYPE_VIEW, view_transform)

        for obj in objects:
            object_id = obj.object_id

            if getattr(obj, "material", None) is not None:
                instance_mat = obj.material
                pipeline_type = PIPELINE_TYPE_TEXTURED
                shader = self.shaders[pipeline_type]
                shader.use()
                transform_component = obj.transform_component
                shader.upload_mat4(UNIFORM_TYPE_MODEL, transform_component.get_transformation())

                mesh_ref = self.meshes[object_id]
                if isinstance(mesh_ref, Model):
                    for mesh in mesh_ref.meshes:
                        instance_mat.use()
                        mesh.draw()
                else:
                    instance_mat.use()
                    mesh_ref.draw()

                continue

            pipeline_type = PIPELINE_TYPE_TEXTURED
            if object_id in self.materials:
                pipeline_type = PIPELINE_TYPE_COLORED
                self.materials[object_id].use()
            shader = self.shaders[pipeline_type]
            shader.use()
            transform_component = obj.transform_component
            shader.upload_mat4(UNIFORM_TYPE_MODEL, transform_component.get_transformation())
            self.meshes[object_id].draw()

    def destroy(self) -> None:
        for mesh in self.meshes.values():
            mesh.destroy()
        for material in self.materials.values():
            material.destroy()
        for shader in self.shaders.values():
            shader.destroy()
