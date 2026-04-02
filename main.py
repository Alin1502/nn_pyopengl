#region imports
import pygame as pg
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import numpy as np
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

UNIFORM_TYPE_MODEL = 0
UNIFORM_TYPE_VIEW = 1
UNIFORM_TYPE_PROJECTION = 2
UNIFORM_NAMES = {
    UNIFORM_TYPE_MODEL:"model",
    UNIFORM_TYPE_VIEW:"view",
    UNIFORM_TYPE_PROJECTION:"projection"
}
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
    
def handle_mouse(center_x:int, center_y:int, camera: "Camera") -> None:

    mouse_pos = pg.mouse.get_pos()
    dx = mouse_pos[0] - center_x
    dy = mouse_pos[1] - center_y

    if abs(dx) + abs(dy) >0:
        camera.spin(dx, dy)
        pg.mouse.set_pos(center_x, center_y)

def handle_input(camera:"Camera"):

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

    camera.move(movement)
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



class Mat4:

    def __init__(self):
        self.data = np.zeros((4,4), dtype = np.float32)
        for i in range(4):
            self.data[i,i] = 1.0

    def from_translation(self, pos:Vec3)-> "Mat4":

        self.data[3,0:3]=pos.data[:]

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

    def __mul__(self, other: "Mat4") -> "Mat4":
        result = Mat4()
        result.data = other.data.dot(self.data)
        return result
    
class MovingQuad:
    def __init__(self):
        self.t =0.0
        self.pos = Vec3(4.0, 0.0, -1.0)
        self.z_angle = 0.0

    def update(self, dt:float) -> None:
        self.t += 0.001 * dt
        if self.t > 360:
            self.t -=360

        self.pos.data[1] = np.sin(20 * np.radians(self.t))

        self.z_angle = 10 * self.t

    def get_transformation(self) -> Mat4:

        return (Mat4().from_translation(self.pos) * Mat4().from_z_rotation(self.z_angle))


class Camera:

    UP = Vec3(0,0,1.0)
    TURN_SPEED = (1.0, 1.0)
    WALK_SPEED = 0.1
    def __init__(self):
        
        self.pos = Vec3()
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

        self.right = self.forward.cross(Camera.UP).normalize()
        self.up = self.right.cross(self.forward).normalize()

    def get_view_transform(self) -> Mat4:

        return Mat4().from_camera(self.pos, self.right, self.up, self.forward)
    
    def spin(self, dx:float, dy:float) -> None:
        self.yaw -= Camera.TURN_SPEED[0]* dx
        if self.yaw < 0:
            self.yaw +=360
        if self.yaw > 360:
            self.yaw -=360

        self.pitch = min(89, max(-89, self.pitch - Camera.TURN_SPEED[1]* dy))

    def move(self, amount: Vec3) -> None:

        movement = self.right * amount.data[0]\
        + self.up * amount.data[1]\
        + self.forward * amount.data[2]

        movement.data[2]=0.0
        self.pos = self.pos + movement * Camera.WALK_SPEED

       


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
        indices=np.array((0,1,2,2,3,0), dtype = np.ubyte)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.EBO)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)


        return self



    def draw(self) -> None:
        glBindVertexArray(self.VAO)
        glDrawElements(GL_TRIANGLES, self.index_count, GL_UNSIGNED_BYTE, ctypes.c_void_p(0))

    def destroy(self) -> None:
        glDeleteVertexArrays(1, (self.VAO,))
        glDeleteBuffers(2, (self.VBO,self.EBO,))


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

        self.mesh = Mesh().build_colored_quad()
        self.material = Material().load_from_file("textures/brickwall.jpg")

        self.shader = Shader("shaders/vertex.txt", "shaders/fragment.txt")
        self.shader.use()


        fovy = 60.0
        aspect = 4.0/3.0
        near = 0.1
        far = 10.0
        projection_matrix=Mat4().from_perspective_projection(fovy, aspect, near, far)  

        self.shader.upload_mat4(UNIFORM_TYPE_PROJECTION, projection_matrix)

    def draw(self,quad : MovingQuad, camera:Camera) -> None:

        glClear(GL_COLOR_BUFFER_BIT)

        self.shader.use()
        self.material.use()

        self.shader.upload_mat4(UNIFORM_TYPE_MODEL, quad.get_transformation())
        self.shader.upload_mat4(UNIFORM_TYPE_VIEW, camera.get_view_transform())
        self.mesh.draw()

    def destroy(self) -> None:

        self.mesh.destroy()
        self.material.destroy()
        self.shader.destroy()

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
camera = Camera()
quad = MovingQuad() 
#endregion

#region main loop
running = True
while running:
    for event in pg.event.get():
        if (event.type == pg.QUIT
        or(event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE)):
            running = False

    handle_mouse(400, 300, camera)
    camera.recalculate_vectors()
    handle_input(camera)

    quad.update(16.67)
    
    renderer.draw(quad, camera)
    pg.display.flip()
    clock.tick(FRAMERATE)
#endregion

#region cleanup
renderer.destroy()
pg.quit()
#endregion
