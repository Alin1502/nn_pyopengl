from __future__ import annotations
import numpy as np

UNIFORM_TYPE_MODEL = 0
UNIFORM_TYPE_VIEW = 1
UNIFORM_TYPE_PROJECTION = 2
UNIFORM_NAMES = {
    UNIFORM_TYPE_MODEL: "model",
    UNIFORM_TYPE_VIEW: "view",
    UNIFORM_TYPE_PROJECTION: "projection"
}

PIPELINE_TYPE_COLORED = 0
PIPELINE_TYPE_TEXTURED = 1

OBJECT_TYPE_MODEL = 0
OBJECT_TYPE_QUAD = 1
OBJECT_TYPE_MODEL2 = 2

SHADER_FILENAMES = {
    PIPELINE_TYPE_COLORED: ("shaders/colored_vertex.txt", "shaders/colored_fragment.txt"),
    PIPELINE_TYPE_TEXTURED: ("shaders/model_vertex.txt", "shaders/model_fragment.txt")
}