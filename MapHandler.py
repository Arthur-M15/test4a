import threading
import multiprocessing
import time

from Settings import *

class MapManager(threading.Thread):
    def __init__(self, app_handler):
        super().__init__()
        self.app_handler = app_handler
        self.manager = multiprocessing.Manager()
        self.external_command_list = self.manager.list()
        self.__command_set = [self.manager.list() for _ in range(CHUNK_THREAD_NUMBER)]
        self.__result_set = [self.manager.list() for _ in range(CHUNK_THREAD_NUMBER)]
        self.process_list = [ChunkGenerator(self.__command_set[i], self.__result_set[i]) for i in range(CHUNK_THREAD_NUMBER)]

    def check_new_commands(self):
        while len(self.external_command_list) > 0:
            command = self.external_command_list.pop(0)
            coordinates, command_type = command
            self.__add_command(coordinates, command_type)

    def __add_command(self, coordinates, command_type):
        modulo = (coordinates[0] + coordinates[1]) % CHUNK_THREAD_NUMBER

        if not self.app_handler.map.get(coordinates):
            self.app_handler.map.load_chunk(coordinates)

        copied_object = self.app_handler.map.get(coordinates).export()
        command = copied_object, command_type
        self.__command_set[modulo].append(command)

    def collect(self):
        need_pause = True
        for result_list in self.__result_set:
            while len(result_list) > 0:
                result = result_list.pop(0)
                coordinates = result[0].coordinates
                self.app_handler.map.get(coordinates).unload_from_screen()
                if result[1] == "generate":
                    result.load_on_screen()
                    self.app_handler.map.replace_chunk(result)
                need_pause = False
        if need_pause:
            time.sleep(0.01)

    def run(self):
        if self.process_list:
            for process in self.process_list:
                process.start()

        while True:
            self.check_new_commands()
            self.collect()



class ChunkGenerator(multiprocessing.Process):
    def __init__(self, command_list, result_list):
        super().__init__()
        self.command_list = command_list
        self.result_list = result_list
        self.running = False

    def run(self):
        self.running = True
        while self.running:
            self.execute_task()

    def execute_task(self):
        if self.command_list:
            while len(self.command_list) > 0:
                command = self.command_list.pop(0)
                if command[1] == "generate":
                    command[0].__generate_matrix()
                self.result_list.append(command)
        else:
            time.sleep(0.01)

            # todo: pour la suite : Le MapHandler est normalement fini. Il reste plus qu'à l'intéger à la place de chunk.load_image.
            # todo: il faut s'occuper de la gestion des sprites. Idée : créer une fonction pour ajouter les sprites avec un lock.


def get_process_index(coordinates):
    return (coordinates[0] + coordinates[1]) % CHUNK_THREAD_NUMBER