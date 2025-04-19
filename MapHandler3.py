import threading
import multiprocessing
import queue
import time

from common.biomes.BiomeManager import *
import pygame
from PIL import Image as PILImage
from pygame._sdl2 import Texture as TextureSDL2

from Settings import *


class MapManager(threading.Thread):
    def __init__(self, assets, frontiers_shape_list, app_handler):
        super().__init__()
        self.renderer = app_handler.app.renderer
        self.assets = assets
        self.frontiers_shape_list = frontiers_shape_list
        self.processes = []
        self.daemon = True
        self.is_running = False
        self.test_timer = 0.0

        #Input of the manager:
        self.queue = queue.Queue()
        self.input_command_list = CommandList3()

        #Interface with the processes:
        #self.__manager = multiprocessing.Manager()
        self.task_list = [multiprocessing.Queue() for _ in range(CHUNK_THREAD_NUMBER)]
        self.result_list = [multiprocessing.Queue() for _ in range(CHUNK_THREAD_NUMBER)]

    def run(self):
        self.is_running = True
        for i in range(CHUNK_THREAD_NUMBER):
            new_process = Process(self.task_list[i], self.result_list[i], self.assets, self.frontiers_shape_list)
            self.processes.append(new_process)

        while self.is_running:
            self.collect_commands()
            self.collect_results()

    def stop(self):
        [process.stop() for process in self.processes]
        self.is_running = False
        self.join()

    def add(self, chunk, task):
        self.queue.put((chunk, task))

    def collect_commands(self):
        while not self.queue.empty():
            raw_command = self.queue.get()
            command_id = self.input_command_list.add(raw_command[0], raw_command[1])
            command = self.input_command_list[command_id]
            process_id = command.process_id
            self.task_list[process_id].put(command.unwrap())

    def collect_results(self):
        for result_stack in self.result_list:
            try:
                while True:
                    unwrapped = result_stack.get_nowait()
                    print(f"process time: {unwrapped.process_time}")
                    command_id = unwrapped.command_id
                    command = self.input_command_list.pop(command_id)
                    if command.task == "generate":
                        t = time.time()
                        if unwrapped.pil_image and unwrapped.tiles is not None:
                            pil_image = unwrapped.pil_image
                            sdl_image = self.pil_to_sdl2(pil_image)
                            rect = sdl_image.get_rect()
                            tiles = unwrapped.tiles
                            command.chunk.image = sdl_image
                            command.chunk.tiles = tiles
                            command.chunk.rect = rect
                            command.chunk.load_on_screen()
                        else:
                            self.stop()
                            raise Exception("No image or tiles after generation")
                        self.test_timer = time.time() - t
                    else:
                        command.chunk.unload_from_screen()
                        command.chunk.image = None
                        command.chunk.tiles = None
                        command.chunk.rect = None
            except queue.Empty:
                continue

    def pil_to_sdl2(self, canvas):
        size = canvas.size
        data = canvas.tobytes()
        surface = pygame.image.fromstring(data, size, "RGBA")
        texture_chunk = TextureSDL2.from_surface(self.renderer, surface)
        return texture_chunk


class CommandList3:
    def __init__(self):
        self.input_command_list = {}
        self.command_id = 0

    def add(self, chunk, task):
        if len(self.input_command_list) == 0:
            #self.command_id = 0
            pass
        self.input_command_list[self.command_id] = Command(self.command_id, chunk, task)
        self.command_id += 1
        return self.command_id - 1

    def pop(self, command_id):
        return self.input_command_list.pop(command_id)

    def __getitem__(self, item):
        return self.input_command_list.get(item)


class Command:
    def __init__(self, command_id, chunk, task):
        self.command_id = command_id
        self.chunk = chunk
        self.task = task
        self.process_id = self.get_process_index()

        self.PIL_image = None
        self.tiles = None

    def unwrap(self):
        signals = self.chunk.get_information()
        frontier_shape = self.chunk.frontier_biome
        biome_name = self.chunk.biome.name
        unwrapped = UnwrappedCommand(self.command_id, signals, self.task, frontier_shape, biome_name)
        return unwrapped

    def get_process_index(self):
        coordinates = self.chunk.coordinates()
        return (coordinates[0] + coordinates[1]) % CHUNK_THREAD_NUMBER


class UnwrappedCommand:
    def __init__(self, command_id, signals, task, frontier_shape, biome_name):
        self.command_id = command_id
        self.signals = signals
        self.task = task
        self.frontier_shape = frontier_shape
        self.biome_name = biome_name
        self.pil_image = None
        self.tiles = None
        self.process_time = 0


class Process(multiprocessing.Process):
    def __init__(self, task_list, result_list, assets, frontiers_shape_list):
        super().__init__()
        self.is_running = False
        self.task_list = task_list
        self.result_list = result_list
        self.assets = assets
        self.daemon = True
        self.frontiers_shape_list = frontiers_shape_list
        self.start()

    def run(self):
        self.is_running = True
        while self.is_running:
            self.collect_tasks()

    def stop(self):
        self.is_running = False
        print("process stopped")

    def collect_tasks(self):
        try:
            unwrapped = self.task_list.get(timeout=0.01)
            t = time.time()
            if unwrapped.task == "generate":
                image, tiles = self.generate_image(unwrapped.signals, unwrapped.frontier_shape, unwrapped.biome_name)
                unwrapped.pil_image = image
                unwrapped.tiles = tiles
            unwrapped.process_time = time.time() - t
            self.result_list.put(unwrapped)
        except queue.Empty:
            time.sleep(0.01)

    def generate_image(self, signals, frontier_shape_name, biome_name):
        x_matrix = [[0] * CHUNK_SIZE for _ in range(CHUNK_SIZE)]
        y_matrix = [[0] * CHUNK_SIZE for _ in range(CHUNK_SIZE)]
        matrix = [[0] * CHUNK_SIZE for _ in range(CHUNK_SIZE)]

        size = int(CHUNK_SIZE * TILE_SIZE + TILE_SIZE / 4)
        canvas = PILImage.new("RGBA", (size, size), (0, 0, 0, 0))

        dominance_matrix = self.frontiers_shape_list[frontier_shape_name]

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
