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
#endregion

#region classes:

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


class Renderer:
    SCREEN_COLOR = (0.5, 0.0, 0.25, 1.0)

    def __init__(self):
        glClearColor(*Renderer.SCREEN_COLOR)

        self.mesh = Mesh().build_colored_quad()
        self.material = Material().load_from_file("textures/brickwall.jpg")

        self.shader = make_shader("shaders/vertex.txt", "shaders/fragment.txt")

    def draw(self) -> None:

        glClear(GL_COLOR_BUFFER_BIT)

        glUseProgram(self.shader)
        self.material.use()
        self.mesh.draw()

    def destroy(self) -> None:

        self.mesh.destroy()
        self.material.destroy()
        glDeleteProgram(self.shader)

#endregion




#region program setup
pg.init()
pg.display.gl_set_attribute(pg.GL_CONTEXT_MAJOR_VERSION,3)
pg.display.gl_set_attribute(pg.GL_CONTEXT_MINOR_VERSION,3)
pg.display.gl_set_attribute(pg.GL_CONTEXT_PROFILE_MASK,pg.GL_CONTEXT_PROFILE_CORE)

screen = pg.display.set_mode(SCREEN_SIZE, WINDOW_CREATION_FLAGS)
clock = pg.time.Clock()
renderer = Renderer()
#endregion

#region main loop
running = True
while running:
    for event in pg.event.get():
        if (event.type == pg.QUIT
        or(event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE)):
            running = False

    renderer.draw()
    pg.display.flip()
    clock.tick(FRAMERATE)
#endregion

#region cleanup
renderer.destroy()
pg.quit()
#endregion
