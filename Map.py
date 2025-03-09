import pygame.image

from App import BaseSprite
import math

from common.biomes.BiomeManager import *
from pygame import Surface
from pygame._sdl2 import Image, Texture


class Map:
    def __init__(self, app_handler, seed=0, height=100):
        self.app_handler = app_handler
        self.chunks = SuperChunk()
        self.entities = []
        self.seed = seed

        #normalized offset is on height=100
        self.total_height = height
        self.biome_manager = BiomeManager(self, SEED)


    def get_height(self, y):
        return (y * 100) / self.total_height


    def load_chunk(self, chunk_coordinates):
        x, y = chunk_coordinates
        if self.chunks.get((x, y)) is None:
            self.chunks.set((x, y), Chunk(self.app_handler, x, y, self.get_biome(x, y)))
        else:
            self.chunks.get((x, y)).reload()
        return True

    def get_biome(self, chunk_x, chunk_y):
        return self.biome_manager.get_biome(chunk_x, chunk_y)


class SuperChunk:
    def __init__(self):
        """
        super_chunks: This list of dictionary: Is used to avoid dictionary expansion process (heavy process)
        chunk_list_location
        """
        self.super_chunks = []
        self.super_chunk_location = {}

    def __len__(self):
        total = 0
        for super_chunk in self.super_chunks:
            total += len(super_chunk)
        return total


    def get(self, coordinates):
        """
        Function returning the chunk at this coordinate.
        :param coordinates: tuple(x, y)
        :return: Chunk
        """
        x = coordinates[0]
        y = coordinates[1]
        super_x = x // SUPER_CHUNK_SIZE
        super_y = y // SUPER_CHUNK_SIZE

        position_in_list = self.super_chunk_location.get((super_x, super_y))
        if position_in_list is not None:
            chunk = self.super_chunks[position_in_list].get(coordinates)
            """
            if chunk is not None and chunk.image is not None and not chunk.is_loaded:
                chunk.reload()"""
            return chunk
        return None


    def set(self, coordinates, new_chunk, force_update = False):
        """
        Function setting the chunk at this (chunk) coordinates.
        :param coordinates: tuple(x, y)
        :param new_chunk: Chunk
        :param force_update: boolean
        :raise Exception if the chunk already exists.
        """
        x = coordinates[0]
        y = coordinates[1]
        super_x = x // SUPER_CHUNK_SIZE
        super_y = y // SUPER_CHUNK_SIZE

        position_in_list = self.super_chunk_location.get((super_x, super_y))
        if position_in_list is None:
            position_in_list = len(self.super_chunks)
            self.super_chunk_location[(super_x, super_y)] = len(self.super_chunks)
            self.super_chunks.append({})
            #print(len(self.super_chunk_location))

        if not self.super_chunks[position_in_list].get(coordinates) or force_update:
            self.super_chunks[position_in_list][coordinates] = new_chunk
        else:
            raise Exception("Writing on an already existing chunk")


class Chunk(BaseSprite):
    def __init__(self, app_handler, chunk_x, chunk_y, biome):
        """
        Group of tiles.
        :param app_handler: app_handler
        :param chunk_x: Chunk x coordinate
        :param chunk_y: Chunk y coordinate
        :param biome: Biome
        :param is_loaded: True if self.image not None
        """
        super().__init__(app_handler, (chunk_x * CHUNK_WIDTH, chunk_y * CHUNK_WIDTH))
        self.chunk_x = chunk_x
        self.chunk_y = chunk_y
        self.variation = CHUNK_VARIATIONS

        self.top_signal = None
        self.bottom_signal = None
        self.left_signal = None
        self.right_signal = None
        self.tiles = []
        self.biome = biome
        self.frontier_biome = self.get_frontier_biome()
        self.create_borders()
        self.generate_chunk_image()
        self.is_loaded = True


    def get_frontier_biome(self):
        left = self.app_handler.map.get_biome(self.chunk_x - 1, self.chunk_y).name == self.biome.next_biome.name
        top_left = self.app_handler.map.get_biome(self.chunk_x - 1, self.chunk_y + 1).name == self.biome.next_biome.name
        top = self.app_handler.map.get_biome(self.chunk_x, self.chunk_y + 1).name == self.biome.next_biome.name
        top_right = self.app_handler.map.get_biome(self.chunk_x + 1, self.chunk_y + 1).name == self.biome.next_biome.name
        right = self.app_handler.map.get_biome(self.chunk_x + 1, self.chunk_y).name == self.biome.next_biome.name

        return left, top_left, top, top_right, right


    def get_information(self):
        """
        Get all signals of this chunk
        :return: Dictionary
        """
        info = {key: value for key, value in self.__dict__.items() if "signal" in key}
        return info

    def get_frontier_chunks(self, x, y):
        # Gathering neighbor chunks information
        if self.app_handler.map.chunks.get((x, y - 1)):
            top_chunk = self.app_handler.map.chunks.get((x, y - 1)).get_information()
        else:
            top_chunk = None

        if self.app_handler.map.chunks.get((x, y + 1)):
            bottom_chunk = self.app_handler.map.chunks.get((x, y + 1)).get_information()
        else:
            bottom_chunk = None

        if self.app_handler.map.chunks.get((x - 1, y)):
            left_chunk = self.app_handler.map.chunks.get((x - 1, y)).get_information()
        else:
            left_chunk = None

        if self.app_handler.map.chunks.get((x + 1, y)):
            right_chunk = self.app_handler.map.chunks.get((x + 1, y)).get_information()
        else:
            right_chunk = None
        return top_chunk, bottom_chunk, left_chunk, right_chunk

    def create_borders(self,):
        top_chunk, bottom_chunk, left_chunk, right_chunk = self.get_frontier_chunks(self.chunk_x, self.chunk_y)
        top_signal = []
        bottom_signal = []
        left_signal = []
        right_signal = []

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

    def generate_chunk_image(self):
        x_matrix = [[0] * CHUNK_SIZE for _ in range(CHUNK_SIZE)]
        y_matrix = [[0] * CHUNK_SIZE for _ in range(CHUNK_SIZE)]
        matrix = [[0] * CHUNK_SIZE for _ in range(CHUNK_SIZE)]
        size = CHUNK_SIZE * TILE_SIZE + TILE_SIZE/4
        surf = Surface((size, size), pg.SRCALPHA)

        frontier_shape = biome_generator_helper.get_dominance_matrix_name(self.frontier_biome)
        dominance_matrix = self.app_handler.map.biome_manager.dominance_matrix_index[frontier_shape]

        for i in range(CHUNK_SIZE):
            for j in range(CHUNK_SIZE):
                x_matrix[i][j] = \
                    (self.top_signal[i] - ((j / CHUNK_SIZE) * (self.top_signal[i] - self.bottom_signal[i])))
                y_matrix[i][j] = \
                    (self.left_signal[j] - ((i / CHUNK_SIZE) * (self.left_signal[j] - self.right_signal[j])))

                height = (x_matrix[i][j] + y_matrix[i][j]) / 2
                height_index = get_height_index(height, VARIANTS_NUMBER, TILE_HEIGHT_SATURATION)
                variant = dominance_matrix[i][j]
                chosen_image = self.biome.assets[variant][height_index]
                surf.blit(chosen_image, (i * TILE_SIZE, j * TILE_SIZE))
                matrix[i][j] = (x_matrix[i][j] + y_matrix[j][i]) / 2
        if self.chunk_y == 0 and self.chunk_x == 0:
            corner = pygame.image.load("corner.png")
            surf.blit(corner, (0, 0))

        self.tiles = matrix
        self.image = Image(Texture.from_surface(self.app_handler.app.renderer, surf))
        if self.image is None:
            print("alert!")
        self.rect = self.image.get_rect()
        self.is_loaded = True

    def unload(self):
        if self.is_loaded:
            self.image = None
            self.tiles = []
            self.is_loaded = False
            self.app_handler.number_of_loaded_sprites -= 1
        else:
            print("warning: sprites not loaded")
            self.image = None
            self.tiles = []
            self.is_loaded = False

    def reload(self):
        if not self.is_loaded:
            self.generate_chunk_image()
            self.app_handler.number_of_loaded_sprites += 1
            self.is_loaded = True
        else:
            print("Warning: reload() called twice!")
            self.generate_chunk_image()
            self.is_loaded = True


def create_curve(start=None, stop=None, start_derivative=0, stop_derivative=0, variations=1, size = None):
    if size is None: size = CHUNK_SIZE
    base_signal = [0] * size

    for i in range(1, HARMONIC_NUMBER+1):
        random_phase = random.uniform(-math.pi, math.pi)
        #random_amplitude = random.uniform(-1, 1)
        random_offset = random.uniform(-0.5, 0.5)
        random_amplitude = 1
        for j in range(size):
            base_signal[j] += random_offset + (random_amplitude / i) * math.sin(((2 * math.pi * j)/size) + random_phase)

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

def correct_curve(offset, derivative, starting, size = None):
    r"""
    f\left(x\right)=-ae^{-x}
    g\left(x\right)=\frac{\left(\cos\left(\frac{2\pi x}{2c}\right)+1\right)}{2}
    h\left(x\right)=be^{-\left(\frac{5x}{c}\right)^{2}}
    r\left(x\right)\ =\ \left(f\left(x\right)+h\left(x\right)\right)\cdot g\left(x\right)
    a=1
    b=1
    c=10
    """
    # Import in Desmos graph the formulas:

    # With
    # a derivative
    # b-a the offset
    # c the scale
    # r(x) the result

    if size is None: size = CHUNK_SIZE
    a = derivative
    b = offset + derivative
    c = size
    if starting:
        first = 0
        last = size
        increment = 1
    else:
        first = size - 1
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
