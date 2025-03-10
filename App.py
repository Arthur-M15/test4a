import time

import pygame.mouse
import common
from Settings import *
from ThreadHandler import *
from Map import *
import threading
lock = threading.Lock()
from test_tools import *
from pygame._sdl2.video import Texture, Image as Image


class BaseSprite:
    def __init__(self, app_handler):
        """
        :param app_handler: The handler of the game
        :param x: Relative x position of the object on the window
        :param y: Relative y position of the object on the window
        """
        self.app_handler = app_handler
        self.image = None
        self.rect = None
        self.entity_x, self.entity_y = 0, 0
        self.x, self.y = 0, 0
        self.offset_x, self.offset_y = 0, 0

        self.in_sprite_list = False

    def update(self):
        """
        Update the image on the screen, not the object.
        """
        if self.in_sprite_list:
            self.set_position_on_screen()
            self.rect.center = self.x, self.y

    def set_position_on_screen(self):
        self.offset_x, self.offset_y = self.app_handler.get_offset()
        self.x, self.y = (self.entity_x - self.app_handler.cam_x + self.offset_x,
                          self.entity_y - self.app_handler.cam_y + self.offset_y)

    def load_on_screen(self):
        if self.image is not None and self.rect is not None:
            if self.entity_x is not None and self.entity_y is not None:
                self.app_handler.in_group.add_internal(self)
                self.in_sprite_list = True
        else:
            raise Exception("Can't load sprite on screen")

    def unload_from_screen(self):
        if self.in_sprite_list:
            self.app_handler.in_group.remove_internal(self)
            self.image = None
            self.in_sprite_list = False


class AppHandler:
    def __init__(self, app):
        self.app = app
        self.cam_x, self.cam_y = 0, 0
        self.renderer_offset_x, self.renderer_offset_y = 0, 0
        self.chunk_position = self.get_chunk_position((self.cam_x, self.cam_y))
        self.map = Map(self)
        self.in_group = pg.sprite.Group()
        self.pause_group = {}
        self.param_hud = pg.Surface([400, 200])
        self.font = ft.SysFont('Verdana', FONT_SIZE)
        self.tick_divider = 0
        self.number_of_loaded_sprites = 0
        self.zoom_scale = 5
        self.cam_speed = BASE_SPEED

        self.map_lock = threading.Lock()
        self.chunk_command_lock = threading.Lock()
        self.position_of_chunk_to_load = []
        self.visible_chunks = []
        self.thread_handler = ThreadHandler()
        self.thread_handler.create(self.load_chunk_worker)


    def move(self):
        if 'up' in game_app.keybind:
            self.cam_y -= self.cam_speed
        if 'down' in game_app.keybind:
            self.cam_y += self.cam_speed
        if 'left' in game_app.keybind:
            self.cam_x -= self.cam_speed
        if 'right' in game_app.keybind:
            self.cam_x += self.cam_speed

    def interact(self):
        if 'left_click' in game_app.keybind:
            pass
        if 'mouse_up' in game_app.keybind and self.zoom_scale < 10:
            self.zoom_scale += 1
            self.app.renderer.scale = (self.zoom_scale / 5, self.zoom_scale / 5)
            self.load_chunks()
        if 'mouse_down' in game_app.keybind and self.zoom_scale > 2:
            self.zoom_scale -= 1
            self.app.renderer.scale = (self.zoom_scale / 5, self.zoom_scale / 5)
            self.load_chunks()

    def timing_function(self, frequency, function, *args, **kwargs):
        if self.tick_divider % frequency == 0:
            self.tick_divider += 1
            function(*args, **kwargs)
        else:
            self.tick_divider += 1

    def update(self):
        self.update_chunk_zone()
        self.move()
        self.interact()
        self.in_group.update()
        self.sort_sprite_group()

    def get_biome_name(self):
        x, y = self.get_chunk_position()
        biome = self.map.biome_manager.get_biome(x, y)
        return biome.name

    def sort_sprite_group(self):
        if self.in_group.spritedict:
            sorted_in_group_x = {sprite: value for sprite, value in sorted(self.in_group.spritedict.items(),
                                                                           key=lambda item: item[0].x)}
            sorted_in_group = {sprite: value for sprite, value in sorted(sorted_in_group_x.items(),
                                                                         key=lambda item: item[0].y)}
            self.in_group.spritedict = sorted_in_group

    def update_chunk_zone(self):
        """
        load all the chunks if needed
        uses load_chunks() function.
        """
        if (self.chunk_position != self.get_chunk_position((self.cam_x, self.cam_y)) or
            self.map.chunks == {}):

            self.load_chunks()

    def load_chunks(self):
        """
        This appends a list of chunks to load or unload.
        The following work is processed by the load_chunk_worker() which is a thread.
        """
        previous_chunks = self.visible_chunks
        self.visible_chunks = self.get_visible_chunks()
        self.chunk_position = self.get_chunk_position((self.cam_x, self.cam_y))

        for chunk_coordinates in self.visible_chunks:
            if chunk_coordinates not in previous_chunks:
                command = ("load", chunk_coordinates)
                self.position_of_chunk_to_load.append(command)
        for chunk_coordinates in previous_chunks:
            if chunk_coordinates not in self.visible_chunks:
                command = ("unload", chunk_coordinates)
                self.position_of_chunk_to_load.append(command)

    def load_chunk_worker(self):
        work = None
        with self.chunk_command_lock:
            if len(self.position_of_chunk_to_load) > 0:
                work = self.position_of_chunk_to_load.pop(0)
        if work is not None:
            coordinates = work[1]
            with self.map_lock:
                if self.map.chunks.get(coordinates) is None:
                    self.map.load_chunk(coordinates)
            if work[0] == "load":
                with self.map_lock:
                    chunk = self.map.chunks.get(coordinates)
                independent_chunk = chunk
                independent_chunk.load_image()
                with self.map_lock:
                    self.map.chunks[coordinates] = independent_chunk
            if work[0] == "unload":
                with self.map_lock:
                    self.map.chunks.get(coordinates).unload_image()

    def get_visible_chunks(self):
        """
        This load according to the windows size and the zoom_scale
        :return: matrix of chunk coordinates
        """
        if self.zoom_scale < 5:
            scale = 5 - self.zoom_scale
        else:
            scale = 0

        max_chunks_width = WIN_W // (CHUNK_SIZE * TILE_SIZE)
        max_chunks_height = WIN_H // (CHUNK_SIZE * TILE_SIZE)

        chunk_offset_x = (WIN_W - TOTAL_WIDTH + CHUNK_WIDTH)//(CHUNK_WIDTH * 2)
        chunk_offset_y = (WIN_H - TOTAL_WIDTH + CHUNK_WIDTH)//(CHUNK_WIDTH * 2)

        return [
            (i, j)
            for i in range(self.chunk_position[0] - chunk_offset_x - 1 - scale,
                           1 + self.chunk_position[0] + max_chunks_width - chunk_offset_x + 1 + scale)
            for j in range(self.chunk_position[1] - chunk_offset_y - 1 - scale,
                           1 + self.chunk_position[1] + max_chunks_height - chunk_offset_y + 1 + scale)
        ]

    def get_chunk_position(self, position=None):
        """
        transforms coordinates into chunk position
        :param position: (x_cam, y_cam) -> position on the map
        :return:
        """
        if not position:
            chunk_x = self.cam_x // (TILE_SIZE * CHUNK_SIZE)
            chunk_y = self.cam_y // (TILE_SIZE * CHUNK_SIZE)
        else:
            chunk_x = position[0] // (TILE_SIZE * CHUNK_SIZE)
            chunk_y = position[1] // (TILE_SIZE * CHUNK_SIZE)
        return chunk_x, chunk_y

    def get_offset(self):
        x = ((WIN_W - TOTAL_WIDTH) / 2) - (WIN_W - ((5 / self.zoom_scale) * WIN_W)) / 2
        y = ((WIN_H - TOTAL_WIDTH) / 2) - (WIN_H - ((5 / self.zoom_scale) * WIN_H)) / 2
        return x, y

    def draw(self):
        # Draw only the visible group
        self.in_group.draw(self.app.renderer)

    def draw_information(self):
        self_time = time.time()

        active_sprites = normalize_text(str(len(self.in_group)))
        total_tiles = normalize_text(str(self.number_of_loaded_sprites))
        fps = normalize_text(str(self.app.get_fps()))
        cam_coord = normalize_text(f"x: {self.cam_x} | y: {self.cam_y}", 16)
        print(f"\ractive_sprites: {active_sprites}; total_tiles: {total_tiles}; fps: {fps}; cam_coord: {cam_coord}",
              end='')


class App:
    def __init__(self):
        pg.init()
        self.window_size = window_width, window_height = WIN_W, WIN_H
        self.window = Window(size=self.window_size)     # Create a window
        self.renderer = Renderer(self.window)           # Rendering the content in the window
        self.renderer.draw_color = (0, 0, 0, 255)       # Fill it with black
        self.clock = pg.time.Clock()
        self.app_handler = AppHandler(self)
        self.dt = 0.0
        self.keybind = {}
        self.fps = []
        self.scale = 1

    def update_screen(self):
        self.dt = self.clock.tick(MAX_FPS) * 0.001  # Time for each frame
        self.renderer.clear()
        self.app_handler.update()
        self.app_handler.draw()
        #self.app_handler.draw_hud()
        self.app_handler.draw_information()
        self.renderer.present()

    def inputs(self):
        self.keybind.clear()
        for event in pg.event.get():
            if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                pg.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:
                    self.keybind['mouse_up'] = True
                    self.keybind['mouse_wheel'] = True
                elif event.button == 5:
                    self.keybind['mouse_down'] = True
                    self.keybind['mouse_wheel'] = True


        keys = pg.key.get_pressed()
        if keys[pg.K_UP]:
            self.keybind['up'] = True
        if keys[pg.K_DOWN]:
            self.keybind['down'] = True
        if keys[pg.K_RIGHT]:
            self.keybind['right'] = True
        if keys[pg.K_LEFT]:
            self.keybind['left'] = True
        if keys[pg.K_1]:
            self.keybind['1'] = True
        if keys[pg.K_2]:
            self.keybind['2'] = True
        if pygame.mouse.get_pressed()[0]:
            self.keybind['left_click'] = True
        if pygame.mouse.get_pressed()[1]:
            self.keybind['middle_click'] = True
        if pygame.mouse.get_pressed()[2]:
            self.keybind['right_click'] = True

    def get_fps(self):
        self.fps.append(self.clock.get_fps())
        if len(self.fps) == FPS_LIST_SIZE:
            self.fps.pop(0)
        if not self.fps:
            return 0
        return sum(self.fps) / len(self.fps)

    def run_application(self):
        while True:
            self.update_screen()
            self.inputs()

    def convert_image(self, image):
        mode = image.mode
        size = image.size
        data = image.tobytes()
        if mode == "RGBA":
            a = pg.image.fromstring(data, size, "RGBA")
        elif mode == "RGB":
            a = pg.image.fromstring(data, size, "RGB")
        else:
            raise ValueError(f"Unsupported image: {mode}")

        image = Image(Texture.from_surface(self.renderer, a))
        return image

if __name__ == '__main__':
    game_app = App()
    game_app.run_application()