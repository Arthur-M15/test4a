import threading
import multiprocessing
import common.biomes.properties.biome_generator_helper
import time
import queue
from pygame import Surface
from common.biomes.BiomeManager import *
from pygame._sdl2 import Image as ImageSDL2, Texture as TextureSDL2

from Settings import *


class MapManager(threading.Thread):
    def __init__(self, assets):
        super().__init__()
        self.PIL_assets = assets
        self.daemon = True

        # Lists shared with the application
        self.__instructions_queue = CommandList()
        self.__result_queue = queue.Queue() #

        # Lists shared with the process units:
        self.__manager = multiprocessing.Manager()
        self.__instruction_list = [self.__manager.list() for _ in range(CHUNK_THREAD_NUMBER)]
        self.__result_list = [self.__manager.list() for _ in range(CHUNK_THREAD_NUMBER)]
        self.process_list = [CommandProcess(self.__instruction_list[i], self.__result_list[i], self.PIL_assets) for i in range(CHUNK_THREAD_NUMBER)]

    def run(self):
        for process in self.process_list:
            process.start()
        while True:
            self.collect()

    def add_command(self, chunk, order):
        command = self.__instructions_queue.add(chunk, order)
        self.process_command(command)

    def process_command(self, command):
        elements = command.unwrap()
        process_index = command.get_process_index()
        self.__instruction_list[process_index].append(elements)

    def collect(self):
        for result_list in self.__result_list:
            while len(result_list) > 0:
                result = result_list.pop(0)
                r_number = result.get("number")
                r_surface = result.get("surface")
                r_tiles= result.get("tiles")
                result_object = self.__instructions_queue[r_number].wrap(r_surface, r_tiles)
                self.__result_queue.put(result_object)
                del self.__instructions_queue[r_number]
            else:
                time.sleep(0.01)

    def flush(self):
        chunk_list = []
        while not self.__result_queue.empty():
            chunk_list.append(self.__result_queue.get())
        return chunk_list


class CommandProcess(multiprocessing.Process):
    def __init__(self, instruction_list, result_list, PIL_assets):
        super().__init__()
        self.daemon = True
        self.PIL_assets = PIL_assets
        self.__instruction_list = instruction_list
        self.__result_list = result_list

    def run(self):
        self.pg_assets = convert_assets_to_surface(self.PIL_assets)
        while True:
            self.process_command()

    def process_command(self):
        while len(self.__instruction_list) > 0:
            ins = self.__instruction_list.pop(0)
            if ins["order"] == "generate":
                processed = generate_chunk_image(
                    ins["top_signal"], ins["bottom_signal"],
                    ins["left_signal"], ins["right_signal"],
                    ins["dominance_matrix"], self.pg_assets,
                    ins["biome_index"], ins["coordinates"])
                result = {"number": ins["number"], "surface": processed[0], "tiles": processed[1]}
            else:
                result = {"number": ins["number"], "surface": None, "tiles": None}
            self.__result_list.append(result)
        else:
            time.sleep(0.01)


def generate_chunk_image(top_signal, bottom_signal, left_signal, right_signal, dominance_matrix, assets, biome_index, coordinates):
    """x_matrix = [[0] * CHUNK_SIZE for _ in range(CHUNK_SIZE)]
    y_matrix = [[0] * CHUNK_SIZE for _ in range(CHUNK_SIZE)]
    matrix = [[0] * CHUNK_SIZE for _ in range(CHUNK_SIZE)]
    size = CHUNK_SIZE * TILE_SIZE + TILE_SIZE / 4
    surf = Surface((size, size), pg.SRCALPHA)

    for i in range(CHUNK_SIZE):
        for j in range(CHUNK_SIZE):
            x_matrix[i][j] = \
                (top_signal[i] - ((j / CHUNK_SIZE) * (top_signal[i] - bottom_signal[i])))
            y_matrix[i][j] = \
                (left_signal[j] - ((i / CHUNK_SIZE) * (left_signal[j] - right_signal[j])))
            height = (x_matrix[i][j] + y_matrix[i][j]) / 2
            height_index = get_height_index(height, VARIANTS_NUMBER, TILE_HEIGHT_SATURATION)
            variant = dominance_matrix[i][j]
            chosen_image = assets.get(biome_index)[variant][height_index]
            surf.blit(chosen_image, (i * TILE_SIZE, j * TILE_SIZE))
            matrix[i][j] = (x_matrix[i][j] + y_matrix[j][i]) / 2
    if coordinates == (0, 0):
        corner = pg.image.load("corner.png")
        surf.blit(corner, (0, 0))
    return surf, matrix"""
    pass


class Command:
    def __init__(self, number, c_object, order):
        self.number = number
        self.c_object = c_object
        self.order = order

    def unwrap(self):
        elements = {}
        frontier_shape = biome_generator_helper.get_dominance_matrix_name(self.c_object.frontier_biome)
        dominance_matrix = self.c_object.app_handler.map.biome_manager.dominance_matrix_index[frontier_shape]
        elements["number"]              = self.number
        elements["top_signal"]          = self.c_object.top_signal
        elements["bottom_signal"]       = self.c_object.bottom_signal
        elements["right_signal"]        = self.c_object.right_signal
        elements["left_signal"]         = self.c_object.left_signal
        elements["coordinates"]         = self.c_object.coordinates()
        elements["order"]               = self.order
        elements["dominance_matrix"]    = dominance_matrix
        elements["biome_index"]         = self.c_object.biome.index
        return elements

    def wrap(self, surface, tiles):
        self.c_object.tiles = tiles
        texture_chunk = TextureSDL2.from_surface(self.c_object.app_handler.app.renderer, surface)
        self.c_object.image = ImageSDL2(texture_chunk)
        self.c_object.rect = self.c_object.image.get_rect()
        return self

    def get_process_index(self):
        coordinates = self.c_object.coordinates()
        return (coordinates[0] + coordinates[1]) % CHUNK_THREAD_NUMBER


class CommandList:
    def __init__(self):
        self.commands = {}
        self.counter = 0

    def __getitem__(self, item):
        self.commands.get(item)

    def __delitem__(self, key):
        self.commands.pop(key)

    def add(self, chunk, order):
        if len(self.commands) == 0:
            self.counter = 0
        number = self.counter
        command = Command(number, chunk, order)
        self.commands[self.counter] = command
        self.counter += 1
        return command
