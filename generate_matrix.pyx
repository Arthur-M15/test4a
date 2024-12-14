# cython : language_level=3

import numpy as np
from App import BaseSprite
from entities.biomes import *
cimport numpy as cnp

cdef class ChunkGenerator:
    cdef int CHUNK_SIZE, TILE_SIZE
    cdef double x, y
    cdef object app_handler
    cdef list top_signal, bottom_signal, left_signal, right_signal

    def __init__(self, int chunk_size, int tile_size, double x, double y, object app_handler,
                 list top_signal, list bottom_signal, list left_signal, list right_signal):
        self.CHUNK_SIZE = chunk_size
        self.TILE_SIZE = tile_size
        self.x = x
        self.y = y
        self.app_handler = app_handler
        self.top_signal = top_signal
        self.bottom_signal = bottom_signal
        self.left_signal = left_signal
        self.right_signal = right_signal

    def generate_matrix(self):
        cdef int i, j
        cdef double top_diff, left_diff, factor, avg_value
        cdef double absolute_chunk_x = self.x * self.TILE_SIZE * self.CHUNK_SIZE
        cdef double absolute_chunk_y = self.y * self.TILE_SIZE * self.CHUNK_SIZE
        cdef cnp.ndarray[cnp.float64_t, ndim=2] x_matrix = np.zeros((self.CHUNK_SIZE, self.CHUNK_SIZE))
        cdef cnp.ndarray[cnp.float64_t, ndim=2] y_matrix = np.zeros((self.CHUNK_SIZE, self.CHUNK_SIZE))
        cdef list matrix = [[[0.0, None] for _ in range(self.CHUNK_SIZE)] for _ in range(self.CHUNK_SIZE)]

        # Calcul des matrices x et y
        for i in range(self.CHUNK_SIZE):
            top_diff = self.top_signal[i] - self.bottom_signal[i]
            left_diff = self.left_signal[i] - self.right_signal[i]
            for j in range(self.CHUNK_SIZE):
                factor = j / self.CHUNK_SIZE
                x_matrix[i, j] = self.top_signal[i] - (factor * top_diff)
                y_matrix[i, j] = self.left_signal[i] - (factor * left_diff)

        # Génération des objets
        for i in range(self.CHUNK_SIZE):
            for j in range(self.CHUNK_SIZE):
                avg_value = (x_matrix[i, j] + y_matrix[j, i]) / 2
                x = absolute_chunk_x + i * self.TILE_SIZE
                y = absolute_chunk_y + j * self.TILE_SIZE
                tile = Tile(self.app_handler, x, y, avg_value)
                sprite = BaseSprite(self.app_handler, tile)
                matrix[i][j] = [avg_value, sprite]

        return matrix
