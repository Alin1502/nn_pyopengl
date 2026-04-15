from __future__ import annotations
import numpy as np


class Vec3:

    def __init__(self, x: float = 0.0, y: float = 0.0, z: float = 0.0):
        self.data = np.array((x, y, z), dtype=np.float32)

    def dot(self, other: "Vec3") -> float:
        result = 0.0
        for i in range(3):
            result += self.data[i] * other.data[i]
        return result

    def magnitude(self) -> float:
        return np.sqrt(self.dot(self))

    def normalize(self) -> "Vec3":
        magnitude = self.magnitude()
        for i in range(3):
            self.data[i] = self.data[i] / magnitude
        return self

    def cross(self, other: "Vec3") -> "Vec3":
        u = self.data
        v = other.data
        x = u[1] * v[2] - u[2] * v[1]
        y = u[2] * v[0] - u[0] * v[2]
        z = u[0] * v[1] - u[1] * v[0]
        return Vec3(x, y, z)

    def __mul__(self, coefficient: float) -> "Vec3":
        return Vec3(coefficient * self.data[0], coefficient * self.data[1], coefficient * self.data[2])

    def __add__(self, other: "Vec3") -> "Vec3":
        return Vec3(other.data[0] + self.data[0], other.data[1] + self.data[1], other.data[2] + self.data[2])


class Vec4:

    def __init__(self, x: float = 0.0, y: float = 0.0, z: float = 0.0, w: float = 0.0):
        self.data = np.array((x, y, z, w), dtype=np.float32)

    def dot(self, other: "Vec4") -> float:
        result = 0.0
        for i in range(4):
            result += self.data[i] * other.data[i]
        return result

    def magnitude(self) -> float:
        return np.sqrt(self.dot(self))

    def normalize(self) -> "Vec4":
        magnitude = self.magnitude()
        for i in range(3):
            self.data[i] = self.data[i] / magnitude
        return self

    def __mul__(self, coefficient: float) -> "Vec4":
        return Vec4(coefficient * self.data[0], coefficient * self.data[1], coefficient * self.data[2], coefficient * self.data[3])

    def __add__(self, other: "Vec4") -> "Vec4":
        return Vec4(other.data[0] + self.data[0], other.data[1] + self.data[1], other.data[2] + self.data[2], other.data[3] + self.data[3])


class Mat4:

    def __init__(self):
        self.data = np.zeros((4, 4), dtype=np.float32)
        for i in range(4):
            self.data[i, i] = 1.0

    def from_scale(self, factor: float) -> "Mat4":
        for i in range(3):
            self.data[i, i] = factor
        return self

    def from_translation(self, pos: Vec3) -> "Mat4":
        self.data[3, 0:3] = pos.data[:]
        return self

    def from_x_rotation(self, theta: float) -> "Mat4":
        theta = np.radians(theta)
        c = np.cos(theta)
        s = np.sin(theta)
        self.data[1, 1] = c
        self.data[1, 2] = s
        self.data[2, 1] = -s
        self.data[2, 2] = c
        return self

    def from_y_rotation(self, theta: float) -> "Mat4":
        theta = np.radians(theta)
        c = np.cos(theta)
        s = np.sin(theta)
        self.data[0, 0] = c
        self.data[0, 2] = -s
        self.data[2, 0] = s
        self.data[2, 2] = c
        return self

    def from_z_rotation(self, theta: float) -> "Mat4":
        theta = np.radians(theta)
        c = np.cos(theta)
        s = np.sin(theta)
        self.data[0, 0] = c
        self.data[0, 1] = -s
        self.data[1, 0] = s
        self.data[1, 1] = c
        return self

    def from_perspective_projection(self, fovy: float, aspect: float, near: float, far: float) -> "Mat4":
        dy = near * np.tan(np.radians(0.5 * fovy))
        dx = aspect * dy

        self.data[0, 0] = near / dx
        self.data[1, 1] = near / dy
        self.data[2, 2] = (near + far) / (far - near)
        self.data[2, 3] = 1.0
        self.data[3, 2] = 2.0 * near * far / (near - far)
        self.data[3, 3] = 0.0

        return self

    def from_camera(self, pos: Vec3, right: Vec3, up: Vec3, forward: Vec3) -> "Mat4":
        self.data[0, 0:3] = right.data[:]
        self.data[1, 0:3] = up.data[:]
        self.data[2, 0:3] = forward.data[:]

        self.data = self.data.transpose()

        self.data[3, 0] = -pos.dot(right)
        self.data[3, 1] = -pos.dot(up)
        self.data[3, 2] = -pos.dot(forward)

        return self

    def __mul__(self, other: "Mat4" | Vec4) -> "Mat4" | Vec4:
        if hasattr(other, 'data') and other.data.shape == (4, 4):
            result = Mat4()
        else:
            result = Vec4()
        result.data = other.data.dot(self.data)
        return result
