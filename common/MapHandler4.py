import multiprocessing
import queue
import threading
import time
from Settings import *
from collections import deque
from PIL import Image as PILImage
from common.biomes.properties.biome_generator_helper import get_height_index


class MapManager:
    def __init__(self, app_handler):
        super().__init__()
        self.__map = app_handler.map
        self.__renderer = app_handler.app.renderer
        self.__app_handler = app_handler

        self.__command_counter = 0
        self.__command_list = {}
        self.__command_waiting_list = []

        assets = self.__map.biome_manager.tiles_assets
        frontier_biome = self.__map.biome_manager.dominance_matrix_index
        self.__process_manager = ProcessManager(assets, frontier_biome)

    def load(self, coordinates):
        pass # todo: create or load the chunk. The pass the chunk to the __add_command()

    def unload(self, coordinates):
        pass # todo: create or load the chunk. The pass the chunk to the __add_command()

    def update(self):
        pass #todo

    def __add_command(self, chunk, task):
        c_id = self.__get_id()
        self.__command_list[c_id] = Command(chunk, task, c_id)
        self.__command_waiting_list.append(self.__command_list[c_id].wrap)

    def __get_id(self):
        if len(self.__command_list) == 0:
            self.__command_counter = 0
        return self.__command_counter

    def __get_assets(self):
        return self.__app_handler.biome_manager.tiles_assets

    def __get_dominance_matrix(self):
        return self.__app_handler.biome_manager.dominance_matrix_index



class ProcessManager(threading.Thread):
    def __init__(self, assets, frontier_biome_list):
        super().__init__()
        self.command_list = SharedList()
        self.result_list = SharedList()
        self.process_list = [Process(i, assets, frontier_biome_list, self.result_list) for i in range(CHUNK_THREAD_NUMBER)]
        self.daemon = True
        self.is_running = False

    def run(self):
        [process.start() for process in self.process_list]
        self.is_running = True
        while self.is_running:
            self.__send_to_process()

    def add(self, command):
        self.command_list.append(command)

    def get_results(self):
        return self.result_list.flush()

    def __get_process_id(self):
        for process in self.process_list:
            if process.notify_command():
                return process.id
        return 0


    def __send_to_process(self):
        while len(self.command_list) > 0:
            command_id = self.__get_process_id()
            if command_id != 0:
                command_id -= 1
                command = self.command_list.pop()
                self.process_list[command_id].inject_data(command)
                self.process_list[command_id].command = command
            else:
                time.sleep(0.1)


class Process(multiprocessing.Process):
    def __init__(self, p_id, assets, frontier_biome_list, result_list):
        super().__init__()
        self.id = p_id
        self.assets = assets
        self.frontier_biome_list = frontier_biome_list

        self.command = None
        self.result_list = result_list
        self.is_ready = False
        self.is_processing = False
        self.is_running = False
        self.lock = multiprocessing.Lock()

    def run(self):
        self.is_running = True
        self.is_ready = True
        while self.is_running:
            if not self.is_processing and self.command is not None:
                self.__execute_task()

    def notify_command(self):
        with self.lock:
            flag = self.is_ready
            self.is_ready = False
            return flag

    def inject_data(self, command):
        self.command = command
        self.is_processing = True

    def __execute_task(self):
        self.is_processing = True
        command = self.command
        result = self.__generate_image(command.signals, command.frontier_biome, command.biome_name)
        self.result_list.append(result)
        self.is_processing = False
        self.command = None
        self.is_ready = True


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


class SharedList:
    def __init__(self):
        self.lock = multiprocessing.Lock()
        self.shared_list = deque()

    def append(self, item):
        with self.lock:
            self.shared_list.append(item)

    def pop(self):
        with self.lock:
            return self.shared_list.popleft()

    def flush(self):
        result_list = []
        with self.lock:
            while len(self.shared_list) > 0:
                result_list.append(self.shared_list.popleft())
        return result_list

    def __len__(self):
        with self.lock:
            return len(self.shared_list)


class Command:
    def __init__(self, chunk, task, c_id):
        self.chunk = chunk
        self.task = task

        signals = self.chunk.get_information()
        frontier_biome = self.chunk.frontier_biome
        biome_name = self.chunk.biome.name
        self.wrap = Wrap(c_id, signals, task, frontier_biome, biome_name)


class Wrap:
    def __init__(self, c_id, signals, task, frontier_biome, biome_name):
        self.c_id = c_id
        self.signals = signals
        self.task = task
        self.frontier_biome = frontier_biome
        self.biome_name = biome_name

        self.pil_image = None
        self.tiles = None
        self.timestamp = time.time()


