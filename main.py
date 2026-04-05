#region imports
from __future__ import annotations
import pygame as pg
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import numpy as np
from typing import TextIO
#endregion

#region constant
SCREEN_SIZE = (800, 600)
WINDOW_CREATION_FLAGS = pg.OPENGL | pg.DOUBLEBUF
FRAMERATE = 60
DATA_TYPE_COLORED_VERTEX = np.dtype({
    'names': ['x', 'y', 'z', 'color', 'u', 'v'],
    'formats': [np.float32, np.float32, np.float32, np.uint32, np.float32, np.float32],
    'offsets': [0,4,8,12,16,20],
    'itemsize': 24
})
DATA_TYPE_VERTEX = np.dtype({
    'names': ['x', 'y', 'z', 'u', 'v'],
    'formats': [np.float32, np.float32,  np.uint32, np.float32, np.float32],
    'offsets': [0,4,8,12,16,20],
    'itemsize': 24
})

UNIFORM_TYPE_MODEL = 0
UNIFORM_TYPE_VIEW = 1
UNIFORM_TYPE_PROJECTION = 2
UNIFORM_NAMES = {
    UNIFORM_TYPE_MODEL:"model",
    UNIFORM_TYPE_VIEW:"view",
    UNIFORM_TYPE_PROJECTION:"projection"
}

PIPELINE_TYPE_COLORED = 0
PIPELINE_TYPE_TEXTURED = 1

SHADER_FILENAMES = {
    PIPELINE_TYPE_COLORED: ("shaders/colored_vertex.txt", "shaders/colored_fragment.txt"),
    PIPELINE_TYPE_TEXTURED: ("shaders/model_vertex.txt", "shaders/model_fragment.txt")
}

OBJECT_TYPE_MODEL = 0
OBJECT_TYPE_QUAD = 1
#endregion

#region functions

def make_shader(vertex_filename:str, fragment_filename:str) -> int:
    vertex_module = make_shader_module(vertex_filename, GL_VERTEX_SHADER)
    fragment_module = make_shader_module(fragment_filename, GL_FRAGMENT_SHADER)
    return compileProgram(vertex_module, fragment_module)

def make_shader_module(filename:str, module_type:int) -> int:

    with open(filename, "r") as file:
        source_code = file.readlines()
        return compileShader(source_code, module_type)
    
def handle_mouse(center_x:int, center_y:int, player: "Player") -> None:

    mouse_pos = pg.mouse.get_pos()
    dx = mouse_pos[0] - center_x
    dy = mouse_pos[1] - center_y

    if abs(dx) + abs(dy) >0:
        player.spin(dx, dy)
        pg.mouse.set_pos(center_x, center_y)

def handle_input(player:"Player"):



    keys = pg.key.get_pressed()
    movement = Vec3()
    if keys[pg.K_w]:
        movement.data[2] += 1.0
    if keys[pg.K_a]:
        movement.data[0] -= 1.0
    if keys[pg.K_d]:
        movement.data[0] += 1.0
    if keys[pg.K_s]:
        movement.data[2] -= 1.0

    player.move(movement)

def parse_materials(filename:str, materials:dict[int, "Material"]) -> dict[str, int]:
    mtl_filename = ""
    material_ids = {}

    with open(filename, "r") as file:
        while line :=file.readline():

            words = line.strip().split(" ")
            if words[0] == "mtllib":
                mtl_filename = "models/" + words[1]
                break

    if len(mtl_filename) == 0:
        return material_ids
    
    current_id = -1
    with open(mtl_filename, "r") as file:
        while line :=file.readline():
            words=line.strip().split(" ")
            if words[0] == "newmtl":
                current_id += 1
                material_ids[words[1]] = current_id
                materials[current_id] = Material()
            if words[0] == "map_Kd":
                materials[current_id].load_from_file(words[1])

    return material_ids    

def load_meshes(filename:str, material_ids:dict[str, int], pre_transform: "Mat4", meshes:list["Mesh"]) -> None:

    v = []
    vt = []
    history = {}

    with open(filename, "r") as file:
        while line := file.readline():
            words = line.strip().split(" ")

            if words[0] == "v":
                read_v(words, v, pre_transform )
            if words[0] == "vt":
                read_vt(words, vt)
            if words[0] == "usemtl":
                material_id = material_ids[words[1]]
                meshes.append(Mesh().build_from_file(file, material_id, pre_transform,
                        v, vt, history))


def read_v(words:list[str], v:list[list[float]], pre_transform: "Mat4") -> None:
    x = float(words[1])
    y = float(words[2])
    z = float(words[3])

    transformed = pre_transform * Vec4(x,y,z,1.0)
    v.append([transformed.data[0], transformed.data[1], transformed.data[2]])

def read_vt(words:list[str], vt:list[list[float]]) -> None:
    u = float(words[1])
    v = float(words[2])
 
    vt.append([u,v])
    

#endregion

#region classes:

class Vec3:

    def __init__(self, x:float = 0.0, y:float = 0.0, z:float = 0.0):
        self.data = np.array((x,y,z), dtype= np.float32)

    def dot(self, other:"Vec3") -> float:
        result = 0.0

        for i in range(3):
            result += self.data[i] * other.data[i]

        return result
    
    def magnitude(self) -> float:

        return np.sqrt(self.dot(self))
    
    def normalize(self) -> "Vec3":

        magnitude = self.magnitude()
        for i in range(3):
            self.data[i] = self.data[i]/magnitude

        return self
    
    def cross(self, other:"Vec3") -> "Vec3":
        u=self.data
        v=other.data

        x=u[1]*v[2] - u[2] * v[1]
        y=u[2]*v[0] - u[0] * v[2]
        z=u[0]*v[1] - u[1] * v[0]

        return Vec3(x,y,z)
    
    def __mul__(self, coefficient:float) -> "Vec3":
        return Vec3(coefficient*self.data[0],coefficient*self.data[1],coefficient*self.data[2])
    
    def __add__(self, other:"Vec3") -> "Vec3":
        return Vec3(other.data[0]+self.data[0],other.data[1]+self.data[1],other.data[2]+self.data[2])

class Vec4:

    def __init__(self, x:float = 0.0, y:float = 0.0, z:float = 0.0, w:float = 0.0):
        self.data = np.array((x,y,z,w), dtype= np.float32)

    def dot(self, other:"Vec4") -> float:
        result = 0.0

        for i in range(4):
            result += self.data[i] * other.data[i]

        return result
    
    def magnitude(self) -> float:

        return np.sqrt(self.dot(self))
    
    def normalize(self) -> "Vec4":

        magnitude = self.magnitude()
        for i in range(3):
            self.data[i] = self.data[i]/magnitude

        return self
    
 
    def __mul__(self, coefficient:float) -> "Vec4":
        return Vec4(coefficient*self.data[0],coefficient*self.data[1],coefficient*self.data[2],coefficient*self.data[3] )
    
    def __add__(self, other:"Vec4") -> "Vec4":
        return Vec4(other.data[0]+self.data[0],other.data[1]+self.data[1],other.data[2]+self.data[2], other.data[3]+self.data[3])


class Mat4:

    def __init__(self):
        self.data = np.zeros((4,4), dtype = np.float32)
        for i in range(4):
            self.data[i,i] = 1.0

    def from_scale(self, factor:float) -> "Mat4":
        for i in range(3):
            self.data[i,i] = factor
        return self

    def from_translation(self, pos:Vec3)-> "Mat4":

        self.data[3,0:3]=pos.data[:]

        return self
    
    def from_x_rotation(self, theta:float)-> "Mat4":

        theta = np.radians(theta)
        c = np.cos(theta)
        s = np.sin(theta)
        self.data[1,1]=c
        self.data[1,2]=s
        self.data[2,1]=-s
        self.data[2,2]=c

        return self
    
    def from_y_rotation(self, theta:float)-> "Mat4":

        theta = np.radians(theta)
        c = np.cos(theta)
        s = np.sin(theta)
        self.data[0,0]=c
        self.data[0,2]=-s
        self.data[2,0]=s
        self.data[2,2]=c

        return self
    
    def from_z_rotation(self, theta:float)-> "Mat4":

        theta = np.radians(theta)
        c = np.cos(theta)
        s = np.sin(theta)
        self.data[0,0]=c
        self.data[0,1]=-s
        self.data[1,0]=s
        self.data[1,1]=c

        return self
    
    def from_perspective_projection(self, fovy:float, aspect:float, near:float, far:float) -> "Mat4":
        
        dy = near * np.tan(np.radians(0.5*fovy))
        dx = aspect * dy

        self.data[0,0] = near/dx
        self.data[1,1] = near/dy
        self.data[2,2] = (near + far)/(far - near)
        self.data[2,3] = 1.0
        self.data[3,2] = 2.0 * near * far / (near - far)
        self.data[3,3] = 0.0


        return self


    def from_camera(self, pos:Vec3, right:Vec3, up:Vec3, forward:Vec3) -> "Mat4":

        self.data[0, 0:3] = right.data[:]
        self.data[1, 0:3] = up.data[:]
        self.data[2, 0:3] = forward.data[:]

        self.data = self.data.transpose()

        self.data[3,0] = -pos.dot(right)
        self.data[3,1] = -pos.dot(up)
        self.data[3,2] = -pos.dot(forward)


        return self

    def __mul__(self, other: "Mat4" | Vec4) -> "Mat4" | Vec4:

        if other.data.shape == (4,4):
            result = Mat4()         
        else:
            result = Vec4()
        result.data = other.data.dot(self.data)
        return result
    
class TransformComponent:
    def __init__(self, x:float, y:float, z:float, yaw:float):
        self.pos = Vec3(x,y,z)
        self.yaw=yaw

    def get_transformation(self) -> Mat4:

        return (Mat4().from_translation(self.pos) * Mat4().from_z_rotation(self.yaw))


class CameraComponent:

    UP = Vec3(0,0,1.0)
    def __init__(self, pos:Vec3):
        
        self.pos = pos
        self.right = Vec3()
        self.up = Vec3()
        self.forward = Vec3()
        self.yaw = 0.0
        self.pitch = 0.0

    def recalculate_vectors(self) -> None:

        c=np.cos(np.radians(self.yaw))
        s=np.sin(np.radians(self.yaw))
        c2=np.cos(np.radians(self.pitch))
        s2=np.sin(np.radians(self.pitch))
        self.forward.data[0] = c * c2
        self.forward.data[1] = s * c2
        self.forward.data[2] = s2

        self.right = self.forward.cross(CameraComponent.UP).normalize()
        self.up = self.right.cross(self.forward).normalize()

    def get_view_transform(self) -> Mat4:

        return Mat4().from_camera(self.pos, self.right, self.up, self.forward)
    
    def spin(self, dx:float, dy:float) -> None:
        self.yaw -= dx
        if self.yaw < 0:
            self.yaw +=360
        if self.yaw > 360:
            self.yaw -=360

        self.pitch = min(89, max(-89, self.pitch - dy))

    def move(self, amount: Vec3) -> None:

        movement = self.right * amount.data[0]\
        + self.up * amount.data[1]\
        + self.forward * amount.data[2]

        movement.data[2]=0.0
        self.pos = self.pos + movement    

class BasicObject:
    def __init__(self, object_id:int, x:float, y:float, z:float):
        self.transform_component =TransformComponent(x,y,z,0.0)
        self.object_id = object_id


class Player:

    TURN_SPEED = (1.0, 1.0)
    WALK_SPEED = 0.1
    HEIGHT = 1.0
    def __init__(self):
        
        self.transform_component = TransformComponent(0.0, 0.0, 0.0, 0.0)
        camera_pos = self.transform_component.pos + Vec3(0, 0, Player.HEIGHT)
        self.camera_component = CameraComponent(camera_pos)


    def update(self) -> None:
        self.camera_component.recalculate_vectors()
        foot_pos = self.camera_component.pos + Vec3(0, 0, -Player.HEIGHT)
        self.transform_component.pos = foot_pos
    
    def spin(self, dx:float, dy:float) -> None:
        
        self.camera_component.spin(Player.TURN_SPEED[0]*dx, Player.TURN_SPEED[1]* dy)


    def move(self, amount: Vec3) -> None:

        self.camera_component.move(amount * Player.WALK_SPEED)

       


class Material:
    
    def __init__(self): 
        self.texture = glGenTextures(1)

    def load_from_file(self, filename:str) -> "Material":

        image = pg.image.load(filename).convert_alpha()
        width,height = image.get_rect().size
        vertical_flip = True
        data = pg.image.tobytes(image, "RGBA", vertical_flip)

        glBindTexture(GL_TEXTURE_2D, self.texture)

        target_mip_level = 0
        internal_format = GL_RGBA
        border_color = 0
        incoming_format = GL_RGBA
        data_type = GL_UNSIGNED_BYTE
        glTexImage2D(GL_TEXTURE_2D,target_mip_level,internal_format,
                    width,height,border_color,incoming_format,
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

        vertices = np.zeros(4, dtype= DATA_TYPE_COLORED_VERTEX)
        
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
        size=3
        offset=0
        stride = DATA_TYPE_COLORED_VERTEX.itemsize 
        glVertexAttribPointer(attribute_index, size, GL_FLOAT, 
        GL_FALSE,stride,ctypes.c_void_p(offset))       
        glEnableVertexAttribArray(attribute_index)

        attribute_index +=1
        offset += 12
        size=1
        glVertexAttribIPointer(attribute_index, size, GL_UNSIGNED_INT, 
        stride,ctypes.c_void_p(offset))
        glEnableVertexAttribArray(attribute_index)


        attribute_index +=1
        offset += 4
        size=2
        glVertexAttribPointer(attribute_index, size, GL_FLOAT, 
        GL_FALSE,stride,ctypes.c_void_p(offset))       
        glEnableVertexAttribArray(attribute_index)

        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)


        self.index_count = 6
        indices=np.array((0,1,2,2,3,0), dtype = np.int32)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.EBO)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)


        return self

    def build_from_file(self, file: TextIO, material_id:int, pre_transform:Mat4,
                        v:list[list[float]], vt: list[list[float]], history:dict[str, int]) -> "Mesh":
        self.material_id = material_id
        self.vertices = np.zeros(0, dtype = DATA_TYPE_VERTEX)
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
                read_v(words, v, pre_transform )
            if words[0] == "vt":
                read_vt(words, vt)
            if words[0] == "f":
                self.read_face(words, v, vt, history)
            original_pos = file.tell()
            line = file.readline()
        self.finalize_model()
        return self
    def read_face(self, words:list[str], v:list[list[float]], vt:list[list[float]], history:dict[str, int]) -> None:

        triangle_count = len(words) - 3

        for i in range(triangle_count):
            self.read_vertex(words[1], v, vt, history)
            self.read_vertex(words[i+2], v, vt, history)
            self.read_vertex(words[i+3], v, vt, history)

    def read_vertex(self, words:str, v:list[list[float]], vt:list[list[float]], history:dict[str, int]) -> None:

        if words in history:
            self.indices.append(history[words])
            return
        
        history[words] = len(self.vertices)
        self.indices.append(history[words])

        v_vt_vn = [int(word) -1 for word in words.split("/")]
        new_vertex = np.zeros(1, dtype = DATA_TYPE_VERTEX)
        pos = v[v_vt_vn[0]]
        new_vertex[0]['x'] = pos[0]
        new_vertex[0]['y'] = pos[1]
        new_vertex[0]['z'] = pos[2]

        tex_coord = vt[v_vt_vn[1]]
        new_vertex[0]['u'] = tex_coord[0]
        new_vertex[0]['v'] = tex_coord[1]

        self.vertices = np.append(self.vertices, new_vertex[0])


    def finalize_model(self) -> "Mesh":

       

        glBindVertexArray(self.VAO)
        glBindBuffer(GL_ARRAY_BUFFER, self.VBO)

        attribute_index = 0
        size=3
        offset=0
        stride = DATA_TYPE_VERTEX.itemsize 
        glVertexAttribPointer(attribute_index, size, GL_FLOAT, 
        GL_FALSE,stride,ctypes.c_void_p(offset))       
        glEnableVertexAttribArray(attribute_index)

        attribute_index +=1
        offset += 12
        size=2
        glVertexAttribPointer(attribute_index, size, GL_FLOAT, 
        GL_FALSE,stride,ctypes.c_void_p(offset))       
        glEnableVertexAttribArray(attribute_index)

        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW)


        self.index_count = len(self.indices)
        indices=np.array(self.indices, dtype = np.uint32)
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
        glDeleteBuffers(2, (self.VBO,self.EBO,))

class Model:
    def __init__(self, filename:str, pre_transform:Mat4):

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

class Shader:

    def __init__(self, vertex_filename:str, fragment_filename:str):

        self.program = make_shader(vertex_filename, fragment_filename)
        self.locations: dict[int, int] = {}

    def use(self) -> None:
        glUseProgram(self.program)

    def upload_mat4(self, uniform_type:int, matrix:Mat4) -> None:
        if uniform_type not in self.locations:
            name = UNIFORM_NAMES[uniform_type]
            self.locations[uniform_type]=glGetUniformLocation(self.program, name)

        glUniformMatrix4fv(self.locations[uniform_type], 1, GL_FALSE, matrix.data)

    def destroy(self) -> None:
        glDeleteProgram(self.program)


class Renderer:
    SCREEN_COLOR = (0.5, 0.0, 0.25, 1.0)

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
        aspect = 4.0/3.0
        near = 0.1
        far = 10.0
        projection_matrix=Mat4().from_perspective_projection(fovy, aspect, near, far)  
        for shader in self.shaders.values():
            shader.use()
            shader.upload_mat4(UNIFORM_TYPE_PROJECTION, projection_matrix)

    def load_assets(self) -> None:
        self.meshes[OBJECT_TYPE_QUAD] = Mesh().build_colored_quad()
        self.materials[OBJECT_TYPE_QUAD] = Material().load_from_file("textures/brickwall.jpg")

        self.meshes[OBJECT_TYPE_MODEL] = Model(
            filename="models/Bullet.obj",
            pre_transform=Mat4().from_x_rotation(90.0) * Mat4().from_scale(0.01)

        )

    def load_shaders(self) -> None:
        for pipeline_type, filenames in SHADER_FILENAMES.items():
            self.shaders[pipeline_type] = Shader(*filenames)

    def draw(self, quad : list[BasicObject], camera:CameraComponent) -> None:

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        view_transform = camera.get_view_transform()
        for shader in self.shaders.values():
            shader.use()
            shader.upload_mat4(UNIFORM_TYPE_VIEW, view_transform)

        for object in objects:
            object_id = object.object_id
            pipeline_type = PIPELINE_TYPE_TEXTURED
            if object_id in self.materials:
                pipeline_type=PIPELINE_TYPE_COLORED
                self.materials[object_id].use()
            shader = self.shaders[pipeline_type]
            shader.use()
            transform_component = object.transform_component
            shader.upload_mat4(UNIFORM_TYPE_MODEL, transform_component.get_transformation())
            self.meshes[object_id].draw()    

    def destroy(self) -> None:
        
        for mesh in self.meshes.values():
            mesh.destroy()
        for material in self.materials.values():
            material.destroy()
        for shader in self.shaders.values():
            shader.destroy()

#endregion




#region program setup
pg.init()
pg.display.gl_set_attribute(pg.GL_CONTEXT_MAJOR_VERSION,3)
pg.display.gl_set_attribute(pg.GL_CONTEXT_MINOR_VERSION,3)
pg.display.gl_set_attribute(pg.GL_CONTEXT_PROFILE_MASK,pg.GL_CONTEXT_PROFILE_CORE)

screen = pg.display.set_mode(SCREEN_SIZE, WINDOW_CREATION_FLAGS)
pg.mouse.set_visible(False)
clock = pg.time.Clock()
renderer = Renderer()
player = Player()
objects = [
    BasicObject(object_id = OBJECT_TYPE_QUAD, x=3.0, y=0.0, z=0.2),
    BasicObject(object_id = OBJECT_TYPE_MODEL, x=2.0, y=0.0, z=0.0)
]

#endregion

#region main loop
running = True
while running:
    for event in pg.event.get():
        if (event.type == pg.QUIT
        or(event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE)):
            running = False

    handle_mouse(400, 300, player)
    handle_input(player)

    player.update()
    
    renderer.draw(objects, player.camera_component)
    pg.display.flip()
    clock.tick(FRAMERATE)
#endregion

#region cleanup
renderer.destroy()
pg.quit()
#endregion
