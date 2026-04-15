from __future__ import annotations
from math_utils import Vec3, Mat4
import numpy as np
import pygame as pg

class TransformComponent:
    def __init__(self, x: float, y: float, z: float, yaw: float, pitch:float, roll:float):
        self.pos = Vec3(x, y, z)
        self.yaw = yaw
        self.pitch = pitch
        self.roll = roll

    def get_transformation(self) -> Mat4:
        return (Mat4().from_translation(self.pos) * Mat4().from_y_rotation(self.yaw) 
                * Mat4().from_x_rotation(self.pitch) * Mat4().from_z_rotation(self.roll) )


class CameraComponent:

    UP = Vec3(0, 1.0, 0)

    def __init__(self, pos: Vec3):
        self.pos = pos
        self.right = Vec3()
        self.up = Vec3()
        self.forward = Vec3()
        self.yaw = 0.0
        self.pitch = 0.0

    def recalculate_vectors(self) -> None:
        c = np.cos(np.radians(self.yaw))
        s = np.sin(np.radians(self.yaw))
        c2 = np.cos(np.radians(self.pitch))
        s2 = np.sin(np.radians(self.pitch))
        self.forward.data[0] = c * c2
        self.forward.data[1] = s2
        self.forward.data[2] = s * c2

        self.right = self.forward.cross(CameraComponent.UP).normalize()
        self.up = self.right.cross(self.forward).normalize()

    def get_view_transform(self) -> Mat4:
        return Mat4().from_camera(self.pos, self.right, self.up, self.forward)

    def spin(self, dx: float, dy: float) -> None:
        self.yaw += dx
        if self.yaw < 0:
            self.yaw += 360
        if self.yaw > 360:
            self.yaw -= 360
        self.pitch = min(89, max(-89, self.pitch - dy))

    def move(self, amount: Vec3) -> None:
        movement = self.right * amount.data[0] + self.up * amount.data[1] + self.forward * amount.data[2]
        movement.data[1] = 0.0
        self.pos = self.pos + movement


class BasicObject:
    def __init__(self, object_id: int, x: float, y: float, z: float, pitch:float, yaw:float, roll:float, material=None):
        self.transform_component = TransformComponent(x, y, z, pitch, yaw, roll)
        self.object_id = object_id
        self.material = material


class Player:

    TURN_SPEED = (1.0, 1.0)
    WALK_SPEED = 0.1
    HEIGHT = 1.0

    def __init__(self):
        self.transform_component = TransformComponent(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        camera_pos = self.transform_component.pos + Vec3(0, Player.HEIGHT, 0)
        self.camera_component = CameraComponent(camera_pos)

    def update(self) -> None:
        self.camera_component.recalculate_vectors()
        foot_pos = self.camera_component.pos + Vec3(0, -Player.HEIGHT, 0)
        self.transform_component.pos = foot_pos

    def spin(self, dx: float, dy: float) -> None:
        self.camera_component.spin(Player.TURN_SPEED[0] * dx, Player.TURN_SPEED[1] * dy)

    def move(self, amount: Vec3) -> None:
        self.camera_component.move(amount * Player.WALK_SPEED)