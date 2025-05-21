from Settings import HARMONIC_NUMBER
import math
import random
from common.biomes.BiomeManager import Tile
from common.biomes import *


def generate_tiles(coordinates, app_handler, top_chunk, bottom_chunk, left_chunk, right_chunk, scale, variations):
    top_signal = []
    bottom_signal = []
    left_signal = []
    right_signal = []

    # Use neighbor information
    if top_chunk is not None:
        left_begin = top_chunk.left_signal[-1]
        right_begin = top_chunk.right_signal[-1]
        left_begin_derivative = top_chunk.left_signal[-1] - top_chunk.left_signal[-2]
        right_begin_derivative = top_chunk.right_signal[-1] - top_chunk.right_signal[-2]
        top_signal = top_chunk.bottom_sin
    else:
        left_begin = None
        right_begin = None
        left_begin_derivative = None
        right_begin_derivative = None

    if bottom_chunk is not None:
        left_end = bottom_chunk.left_signal[0]
        right_end = bottom_chunk.right_signal[0]
        left_end_derivative = bottom_chunk.left_signal[1] - bottom_chunk.left_signal[0]
        right_end_derivative = bottom_chunk.right_signal[1] - bottom_chunk.right_signal[0]
        bottom_signal = bottom_chunk.top_sin
    else:
        left_end = None
        right_end = None
        left_end_derivative = None
        right_end_derivative = None

    if left_chunk is not None:
        top_begin = left_chunk.top_signal[-1]
        bottom_begin = left_chunk.bottom_signal[-1]
        top_begin_derivative = left_chunk.top_signal[-1] - top_chunk.top_signal[-2]
        bottom_begin_derivative = left_chunk.bottom_signal[-1] - top_chunk.bottom_signal[-2]
        left_signal = left_chunk.right_sin
    else:
        top_begin = None
        bottom_begin = None
        top_begin_derivative = None
        bottom_begin_derivative = None

    if right_chunk is not None:
        top_end = right_chunk.top_sin[0]
        bottom_end = right_chunk.bottom_sin[0]
        top_end_derivative = left_chunk.top_signal[1] - top_chunk.top_signal[0]
        bottom_end_derivative = left_chunk.bottom_signal[1] - top_chunk.bottom_signal[0]
        right_signal = right_chunk.left_sin
    else:
        top_end = None
        bottom_end = None
        top_end_derivative = None
        bottom_end_derivative = None

    if not top_signal:
        top_signal = __create_curve(scale, variations, top_begin, top_end, top_begin_derivative, top_end_derivative)
    if not bottom_signal:
        bottom_signal = __create_curve(scale, variations, bottom_begin, bottom_end, bottom_begin_derivative, bottom_end_derivative)
    if not left_signal:
        left_signal = __create_curve(scale, variations, left_begin, left_end, left_begin_derivative, left_end_derivative)
    if not right_signal:
        right_signal = __create_curve(scale, variations, right_begin, right_end, right_begin_derivative, right_end_derivative)

    return __chunk_generation(app_handler, top_signal, bottom_signal, left_signal, right_signal, scale)

def __correct_curve(offset, derivative, starting, scale):
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
    c = scale
    if starting:
        first = 0
        last = scale
    else:
        first = scale - 1
        last = -1
    signal_correction = []
    for x in range(first, last):
        f_x = -a * math.exp(-x)
        g_x = (math.cos((2 * math.pi * x) / (2 * c)) + 1) / 2
        h_x = b * math.exp(-((5 * x) / c) ** 2)

        # r(x) = (f(x) + h(x)) * g(x)
        r_x = (f_x + h_x) * g_x

        signal_correction.append(r_x)

    return signal_correction

def __create_curve(scale, variation, start=None, stop=None, start_derivative=0, stop_derivative=0):

    base_signal = [0] * scale

    for i in range(1, HARMONIC_NUMBER):
        random_phase = random.uniform(-math.pi, math.pi)
        harmonic = [
            (1 / i) * math.sin(((variation * j * math.pi) / (scale - 1)) + random_phase)
            for j in range(scale)
        ]
        base_signal = [a + b for a, b in zip(base_signal, harmonic)]

    if start:
        offset = start - base_signal[0]
        derivative = start_derivative - (base_signal[1] - base_signal[0])
        base_signal += __correct_curve(offset, derivative, True, scale)
    if stop:
        offset = stop - base_signal[-1]
        derivative = stop_derivative - (base_signal[-2] - base_signal[-1])
        base_signal += __correct_curve(offset, derivative, False, scale)

    return base_signal

def __chunk_generation(app_handler, top_signal, bottom_signal, left_signal, right_signal, scale):

    x_matrix = [[0] * scale for _ in range(scale)]
    y_matrix = [[0] * scale for _ in range(scale)]
    matrix = [[[0, None]] * scale for _ in range(scale)]

    for i in range(scale):
        for j in range(scale):
            x_matrix[i][j] = (top_signal[i] - ((j / scale) * (top_signal[i] - bottom_signal[i])))
            y_matrix[i][j] = (left_signal[i] - ((j / scale) * (left_signal[i] - right_signal[i])))
    for i in range(scale):
        for j in range(scale):
            matrix[i][j][0] = (x_matrix[i][j] + y_matrix[j][i]) / 2
            matrix[i][j][1] = Tile(app_handler, i, j, matrix[i][j][0])

    return matrix


