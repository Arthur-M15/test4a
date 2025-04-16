import threading
import multiprocessing
from inspect import unwrap

import common.biomes.properties.biome_generator_helper
import time
import queue
from pygame import Surface
from common.biomes.BiomeManager import *
from pygame._sdl2 import Image as ImageSDL2, Texture as TextureSDL2

from Settings import *


class MapManager(threading.Thread):
    def __init__(self, assets, app_handler):
        super().__init__()
        self.renderer = app_handler.app.renderer
        self.assets = assets
        self.processes = []
        self.daemon = True

        #Input of the manager:
        self.queue = queue.Queue()
        self.input_command_list = CommandList3()

        #Interface with the processes:
        self.__manager = multiprocessing.Manager()
        self.task_list = [self.__manager.list() for _ in range(CHUNK_THREAD_NUMBER)]
        self.result_list = [self.__manager.list() for _ in range(CHUNK_THREAD_NUMBER)]

    def run(self):
        [self.processes.append(Process()) for _ in range(CHUNK_THREAD_NUMBER)]

    def collect_commands(self):
        while not self.queue.empty():
            command = self.queue.get()
            command_id = self.input_command_list.add(command[0], command[1])


class CommandList3:
    def __init__(self):
        self.input_command_list = {}
        self.command_id = 0

    def add(self, chunk, task):
        if len(self.input_command_list) == 0:
            self.command_id = 0
        self.input_command_list[self.command_id] = Command(self.command_id, chunk, task)
        self.command_id += 1
        return self.command_id - 1

    def __getitem__(self, item):
        return self.input_command_list.get(item)


class Command:
    def __init__(self, command_id, chunk, task):
        self.command_id = command_id
        self.chunk = chunk
        self.task = task

        self.PIL_image = None
        self.tiles = None

    def unwrap(self):
        signals = self.chunk.get_information()
        unwrapped = UnwrappedCommand(self.command_id, signals, self.task)
        return unwrapped


class UnwrappedCommand:
    def __init__(self, command_id, signals, task):
        self.command_id = command_id
        self.signals = signals
        self.task = task
        self.PIL_image = None

class Process(multiprocessing.Process):
    pass


