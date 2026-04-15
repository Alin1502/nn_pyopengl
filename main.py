from __future__ import annotations
import pygame as pg
from math_utils import Vec3
from components import Player, BasicObject
from models import Material
from constants import OBJECT_TYPE_MODEL, OBJECT_TYPE_QUAD
from renderer import Renderer
import numpy as np

# local constants
SCREEN_SIZE = (800, 600)
WINDOW_CREATION_FLAGS = pg.OPENGL | pg.DOUBLEBUF
FRAMERATE = 60


def handle_mouse(center_x: int, center_y: int, player: "Player") -> None:
    mouse_pos = pg.mouse.get_pos()
    dx = mouse_pos[0] - center_x
    dy = mouse_pos[1] - center_y
    if abs(dx) + abs(dy) > 0:
        player.spin(dx, dy)
        pg.mouse.set_pos(center_x, center_y)


def handle_input(player: "Player"):
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


# program setup
pg.init()
pg.display.gl_set_attribute(pg.GL_CONTEXT_MAJOR_VERSION, 3)
pg.display.gl_set_attribute(pg.GL_CONTEXT_MINOR_VERSION, 3)
pg.display.gl_set_attribute(pg.GL_CONTEXT_PROFILE_MASK, pg.GL_CONTEXT_PROFILE_CORE)

screen = pg.display.set_mode(SCREEN_SIZE, WINDOW_CREATION_FLAGS)
pg.mouse.set_visible(False)
clock = pg.time.Clock()
renderer = Renderer()
player = Player()



# main loop
running = True
while running:
    for event in pg.event.get():
        if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
            running = False

    handle_mouse(400, 300, player)
    handle_input(player)
    objects = [
        BasicObject(object_id=OBJECT_TYPE_QUAD, x=3.0, y=0.0, z=0.2),
        BasicObject(object_id=OBJECT_TYPE_MODEL, x=2.0 + pg.time.get_ticks() * 0.001, y=0.0, z=0.0,
                    material=Material().load_from_file("textures/brickwall.jpg")),
        BasicObject(object_id=OBJECT_TYPE_MODEL, x=4.0, y=0.0, z=0.0,
                    material=Material().load_from_file("textures/brickwall.jpg")),
        BasicObject(object_id=OBJECT_TYPE_QUAD, x=5.0, y=2.0, z=0.2),

    ]
    print(objects[1].transform_component.pos.data[0])
    player.update()

    renderer.draw(objects, player.camera_component)
    pg.display.flip()
    clock.tick(FRAMERATE)


# cleanup
renderer.destroy()
pg.quit()
