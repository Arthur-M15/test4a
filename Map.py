from App import BaseSprite
from Settings import CHUNK_VARIATIONS, CHUNK_SIZE, HARMONIC_NUMBER, TILE_SIZE
from entities.biomes import *
import math
import random

class Map:
    def __init__(self, app_handler):
        self.app_handler = app_handler
        self.chunks = {}
        self.entities = []

    def load_chunk(self, chunk_coordinates):
        x, y = chunk_coordinates
        if self.chunks.get((x, y)) is None:

            # Gathering neighbor chunks information
            if self.chunks.get((x, y - 1)):
                top_chunk = self.chunks[(x, y - 1)].get_information()
            else:
                top_chunk = None

            if self.chunks.get((x, y + 1)):
                bottom_chunk = self.chunks[(x, y + 1)].get_information()
            else:
                bottom_chunk = None

            if self.chunks.get((x - 1, y)):
                left_chunk = self.chunks[(x - 1, y)].get_information()
            else:
                left_chunk = None

            if self.chunks.get((x + 1, y)):
                right_chunk = self.chunks[(x + 1, y)].get_information()
            else:
                right_chunk = None

            self.chunks[(x, y)] = Chunk(self.app_handler, x, y)
            self.chunks[(x, y)].create(top_chunk, bottom_chunk, left_chunk, right_chunk)


class Chunk:
    def __init__(self, app_handler, x, y, is_loaded=False):
        self.x = x
        self.y = y
        self.biome_name = "classic"
        self.variation = CHUNK_VARIATIONS
        self.app_handler = app_handler
        self.tiles = []
        self.top_signal = None
        self.bottom_signal = None
        self.left_signal = None
        self.right_signal = None
        self.is_loaded = is_loaded

    def get_information(self):
        """
        Get all signals of this chunk
        :return: Dictionary
        """
        info = {key: value for key, value in self.__dict__.items() if key != "tiles"}
        return info

    def create(self, top_chunk, bottom_chunk, left_chunk, right_chunk, biome_index=1):

        top_signal = []
        bottom_signal = []
        left_signal = []
        right_signal = []
        # Use neighbor information
        # Use neighbor information
        if top_chunk is not None:
            left_begin = top_chunk["left_signal"][-1]
            right_begin = top_chunk["right_signal"][-1]
            left_begin_derivative = top_chunk["left_signal"][-1] - top_chunk["left_signal"][-2]
            right_begin_derivative = top_chunk["right_signal"][-1] - top_chunk["right_signal"][-2]
            top_signal = top_chunk["bottom_signal"]
        else:
            left_begin = None
            right_begin = None
            left_begin_derivative = None
            right_begin_derivative = None

        if bottom_chunk is not None:
            left_end = bottom_chunk["left_signal"][0]
            right_end = bottom_chunk["right_signal"][0]
            left_end_derivative = bottom_chunk["left_signal"][1] - bottom_chunk["left_signal"][0]
            right_end_derivative = bottom_chunk["right_signal"][1] - bottom_chunk["right_signal"][0]
            bottom_signal = bottom_chunk["top_signal"]
        else:
            left_end = None
            right_end = None
            left_end_derivative = None
            right_end_derivative = None

        if left_chunk is not None:
            top_begin = left_chunk["top_signal"][-1]
            bottom_begin = left_chunk["bottom_signal"][-1]
            top_begin_derivative = left_chunk["top_signal"][-1] - left_chunk["top_signal"][-2]
            bottom_begin_derivative = left_chunk["bottom_signal"][-1] - left_chunk["bottom_signal"][-2]
            left_signal = left_chunk["right_signal"]
        else:
            top_begin = None
            bottom_begin = None
            top_begin_derivative = None
            bottom_begin_derivative = None

        if right_chunk is not None:
            top_end = right_chunk["top_signal"][0]
            bottom_end = right_chunk["bottom_signal"][0]
            top_end_derivative = right_chunk["top_signal"][1] - right_chunk["top_signal"][0]
            bottom_end_derivative = right_chunk["bottom_signal"][1] - right_chunk["bottom_signal"][0]
            right_signal = right_chunk["left_signal"]
        else:
            top_end = None
            bottom_end = None
            top_end_derivative = None
            bottom_end_derivative = None


        if not top_signal:
            top_signal = create_curve(top_begin, top_end, top_begin_derivative, top_end_derivative)
        if not bottom_signal:
            bottom_signal = create_curve(bottom_begin, bottom_end, bottom_begin_derivative, bottom_end_derivative)
        if not left_signal:
            left_signal = create_curve(left_begin, left_end, left_begin_derivative, left_end_derivative)
        if not right_signal:
            right_signal = create_curve(right_begin, right_end, right_begin_derivative, right_end_derivative)

        # TEST
        if len(top_signal)==0 or len(bottom_signal) ==0 or len(left_signal)==0 or len(right_signal)== 0:
            pass

        self.top_signal = top_signal
        self.bottom_signal = bottom_signal
        self.left_signal = left_signal
        self.right_signal = right_signal
        self.tiles = self.__generate_matrix()


    def __generate_matrix(self):

        x_matrix = [[0] * CHUNK_SIZE for _ in range(CHUNK_SIZE)]
        y_matrix = [[0] * CHUNK_SIZE for _ in range(CHUNK_SIZE)]
        matrix = [[[0.0, None] for _ in range(CHUNK_SIZE)] for _ in range(CHUNK_SIZE)]


        absolute_chunk_x = self.x * TILE_SIZE * CHUNK_SIZE
        absolute_chunk_y = self.y * TILE_SIZE * CHUNK_SIZE

        for i in range(CHUNK_SIZE):
            for j in range(CHUNK_SIZE):
                x_matrix[i][j] = (self.top_signal[i] - ((j / CHUNK_SIZE) * (self.top_signal[i] - self.bottom_signal[i])))
                y_matrix[i][j] = (self.left_signal[i] - ((j / CHUNK_SIZE) * (self.left_signal[i] - self.right_signal[i])))
        for i in range(CHUNK_SIZE):
            for j in range(CHUNK_SIZE):
                matrix[i][j][0] = (x_matrix[i][j] + y_matrix[j][i]) / 2
                x, y = absolute_chunk_x + i * TILE_SIZE, absolute_chunk_y + j * TILE_SIZE
                tile = Tile(self.app_handler,x, y, matrix[i][j][0])
                matrix[i][j][1] = BaseSprite(self.app_handler, tile)
        return matrix


def create_curve(start=None, stop=None, start_derivative=0, stop_derivative=0, variations=1):

    base_signal = [0] * CHUNK_SIZE

    for i in range(1, HARMONIC_NUMBER+1):
        random_phase = random.uniform(-math.pi, math.pi)
        random_amplitude = random.uniform(0, 1)
        random_amplitude = 1
        for j in range(CHUNK_SIZE):
            base_signal[j] += (random_amplitude / i) * math.sin(((2 * math.pi * j)/CHUNK_SIZE) + random_phase)

    if start:
        offset = start - base_signal[0]
        derivative = start_derivative - (base_signal[1] - base_signal[0])
        base_signal2 = [a + b for a, b in zip(base_signal, correct_curve(offset, derivative, True))]
        base_signal = base_signal2
    if stop:
        offset = stop - base_signal[-1]
        derivative = stop_derivative - (base_signal[-2] - base_signal[-1])
        corrective = correct_curve(offset, derivative, False)
        base_signal2 = [a + b for a, b in zip(base_signal, corrective)]
        base_signal = base_signal2
    return base_signal

def correct_curve(offset, derivative, starting):
    # Import in Desmos graph the formulas:
    """
    f\left(x\right)=-ae^{-x}
    g\left(x\right)=\frac{\left(\cos\left(\frac{2\pi x}{2c}\right)+1\right)}{2}
    h\left(x\right)=be^{-\left(\frac{5x}{c}\right)^{2}}
    r\left(x\right)\ =\ \left(f\left(x\right)+h\left(x\right)\right)\cdot g\left(x\right)
    a=1
    b=1
    c=10
    """
    # With
    # a derivative
    # b-a the offset
    # c the scale
    # r(x) the result

    a = derivative
    b = offset + derivative
    c = CHUNK_SIZE
    if starting:
        first = 0
        last = CHUNK_SIZE
        increment = 1
    else:
        first = CHUNK_SIZE - 1
        last = -1
        increment = -1
    signal_correction = []
    for x in range(first, last, increment):
        f_x = -a * math.exp(-x)
        g_x = (math.cos((2 * math.pi * x) / (2 * c)) + 1) / 2
        h_x = b * math.exp(-((5 * x) / (4 * c)) ** 2)

        # r(x) = (f(x) + h(x)) * g(x)
        r_x = (f_x + h_x) * g_x

        signal_correction.append(r_x)

    return signal_correction
