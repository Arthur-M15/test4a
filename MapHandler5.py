from multiprocessing import Process, Queue, Pipe
import queue
import threading
import time

from Settings import *
from PIL import Image as PILImage
from common.biomes.properties.biome_generator_helper import get_height_index, pil_to_sdl2


class MapManager:
    def __init__(self, parent_map):
        super().__init__()
        self.map = parent_map

        self.command_counter = 0
        self.command_list = {}

        assets = self.__get_assets()
        frontier_biome = self.__get_dominance_matrix()
        self.process_manager = ProcessManager(assets, frontier_biome, self.command_list)

    def load_chunk(self, coordinates):
        self.__process_chunk(coordinates, "generate")

    def unload_chunk(self, coordinates):
        self.__process_chunk(coordinates, "unload")

    def update(self):
        key_list = []
        for c_id, processed_command in self.command_list.items():
            if processed_command.is_completed:
                key_list.append(c_id)
        for c_id in key_list:
            command = self.command_list.get(c_id)
            command.merge_wrap()
            if command.task == "generate":
                command.chunk.load_on_screen()
            else:
                command.chunk.unload_from_screen()
            #print(f"TOTAL: {[command.wrap.timestamp[i][1] - command.wrap.timestamp[0][1] for i in range(len(command.wrap.timestamp))]}")
            print([f"{command.wrap.timestamp[i][0]}: {command.wrap.timestamp[i][1] - command.wrap.timestamp[0][1]}" for i in range(len(command.wrap.timestamp))])
            self.command_list.pop(c_id)

    def __process_chunk(self, coordinates, task):
        t = time.time()
        chunk = self.map.get_chunk(coordinates)
        command_id = self.__get_id()
        command = Command(chunk, task, command_id)
        self.command_list[command_id] = command
        command.wrap.timestamp.append(("MapManager: __process_chunk", time.time()))
        self.process_manager.insert_command(command)
        #print(f"Time: {time.time() - t}")
        pass

    def __get_id(self):
        if len(self.command_list) == 0:
            self.command_counter = 0
        self.command_counter += 1
        return self.command_counter

    def __get_assets(self):
        return self.map.biome_manager.tiles_assets

    def __get_dominance_matrix(self):
        return self.map.biome_manager.dominance_matrix_index


class ProcessManager(threading.Thread):
    def __init__(self, assets, frontier_biome_list, command_list):
        super().__init__(daemon=True)
        self.wrap_list = Pipe()
        self.result_list = Pipe()
        self.command_list = command_list
        self.process_list = [Unit(i, self.wrap_list, self.result_list, assets, frontier_biome_list) for i in range(CHUNK_THREAD_NUMBER)]
        self.is_running = True
        self.start()

    def run(self):
        [process.start() for process in self.process_list]
        while self.is_running:
            self.collect_results()

    def insert_command(self, command):
        t = time.time()
        wrap = command.wrap
        self.wrap_list.put(wrap)
        wrap.timestamp.append(("ProcessManager: insert_command", time.time()))
        #print(f"Time: {time.time() - t}")
        return True

    def collect_results(self):
        """result = self.result_list.get()
        result.timestamp.append(("ProcessManager: collect_results2", time.time()))
        c_id = result.c_id
        command = self.command_list.get(c_id)
        command.wrap = result
        command.is_completed = True
        command.wrap.timestamp.append(("ProcessManager: collect_results3", time.time()))
"""
        try:
            result = self.result_list.get_nowait()
            result.timestamp.append(("ProcessManager: collect_results2", time.time()))
            c_id = result.c_id
            command = self.command_list.get(c_id)
            command.wrap = result
            command.is_completed = True
            command.wrap.timestamp.append(("ProcessManager: collect_results3", time.time()))
        except Pipe.Empty:
            time.sleep(0.1)


class Unit(Process):
    def __init__(self, p_id, wrap_list, result_list, assets, frontier_biome_list):
        super().__init__(daemon=True)
        self.id = p_id
        self.wrap_list = wrap_list
        self.result_list = result_list
        self.assets = assets
        self.frontier_biome_list = frontier_biome_list
        self.is_running = True

    def run(self):
        while self.is_running:
            try:
                wrap = self.wrap_list.get_nowait()
                wrap.timestamp.append(("Unit: run", time.time()))
                self.__execute_task(wrap)
            except Pipe.Empty:
                time.sleep(0.1)
            """wrap = self.wrap_list.get()
            wrap.timestamp.append(("Unit: run", time.time()))
            self.__execute_task(wrap)"""

    def __execute_task(self, wrap):
        t =time.time()
        if wrap.task == "generate":
            result = self.__generate_image(wrap.signals, wrap.frontier_biome, wrap.biome_name)
            wrap.pil_image = result[0]
            wrap.tiles = result[1]
        wrap.processed_by = self.id
        wrap.timestamp.append(("Unit: __execute_task", time.time()))
        self.result_list.put(wrap)
        #print(f"Time: {time.time() - t}")

    def __generate_image(self, signals, frontier_biome, biome_name):
        x_matrix = [[0] * CHUNK_SIZE for _ in range(CHUNK_SIZE)]
        y_matrix = [[0] * CHUNK_SIZE for _ in range(CHUNK_SIZE)]
        matrix = [[0] * CHUNK_SIZE for _ in range(CHUNK_SIZE)]

        size = int(CHUNK_SIZE * TILE_SIZE + TILE_SIZE / 4)
        canvas = PILImage.new("RGBA", (size, size), (0, 0, 0, 0))

        dominance_matrix = self.frontier_biome_list[frontier_biome]

        top_s = signals.get("top_signal")
        bottom_s = signals.get("bottom_signal")
        left_s = signals.get("left_signal")
        right_s = signals.get("right_signal")

        for i in range(CHUNK_SIZE):
            for j in range(CHUNK_SIZE):
                x_matrix[i][j] = top_s[i] - ((j / CHUNK_SIZE) * (top_s[i]) - bottom_s[i])
                y_matrix[i][j] = left_s[j] - ((i / CHUNK_SIZE) * (left_s[j]) - right_s[j])
                matrix[i][j] = (x_matrix[i][j] + y_matrix[j][i]) / 2 # noqa

                variant = dominance_matrix[i][j]
                height_index = get_height_index(matrix[i][j], VARIANTS_NUMBER, TILE_HEIGHT_SATURATION)
                pil_image = self.assets.get(biome_name)[variant][height_index]
                canvas.paste(pil_image, (i * TILE_SIZE, j * TILE_SIZE), mask=pil_image)

        return canvas, matrix


class Command:
    def __init__(self, chunk, task, c_id):
        self.chunk = chunk
        self.task = task
        self.is_completed = False

        signals = self.chunk.get_information()
        frontier_biome = self.chunk.frontier_biome
        biome_name = self.chunk.biome.name
        self.wrap = Wrap(c_id, signals, task, frontier_biome, biome_name)

    def merge_wrap(self):
        if self.wrap.task == "generate":
            if self.wrap.pil_image is not None and self.wrap.tiles is not None:
                renderer = self.chunk.app_handler.app.renderer
                sdl_image = pil_to_sdl2(renderer, self.wrap.pil_image)
                rect = sdl_image.get_rect()
                tiles = self.wrap.tiles
                self.chunk.tiles = tiles
                self.chunk.image = sdl_image
                self.chunk.rect = rect
            else:
                raise Exception("no image to merge")


class Wrap:
    def __init__(self, c_id, signals, task, frontier_biome, biome_name):
        self.c_id = c_id
        self.signals = signals
        self.task = task
        self.frontier_biome = frontier_biome
        self.biome_name = biome_name

        self.pil_image = None
        self.tiles = None
        self.timestamp = [("__init__", time.time())]
        self.processed_by = -1



