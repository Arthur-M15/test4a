import time

import pygame.mouse
import os

import common
from Settings import *
from Map import *
from pyximport import install ; install()
import threading
lock = threading.Lock()
from test_tools import *


class BaseSprite:
    def __init__(self, app_handler, entity, x=0, y=0):
        """
        :param app_handler: The handler of the game
        :param x: Relative x position of the object on the window
        :param y: Relative y position of the object on the window
        """
        start2 = time.time()
        self.app_handler = app_handler
        self.in_sprite_list = False
        #todo : add sprite_name conditions
        self.entity = entity
        self.image = self.entity.image
        self.image_size = entity.max_size
        self.rect = self.entity.image.get_rect()
        self.orig_rect = self.rect.copy()
        self.x, self.y = self.app_handler.cam_x - self.entity.x, self.app_handler.cam_y - self.entity.y

        self.offset_x = (WIN_W - TOTAL_WIDTH)/2
        self.offset_y = (WIN_H - TOTAL_WIDTH)/2
        print_time(time.time() - start2, "inside_base", 0.01)


    def update(self):
        self.x, self.y = self.entity.x - self.app_handler.cam_x + self.offset_x, self.entity.y - self.app_handler.cam_y + self.offset_y
        self.rect.center = self.x, self.y


    def check_visibility(self):
        visible = True
        self.update()
        if self.x < 0 - self.image_size or self.x >= WIN_W + self.image_size:
            visible = False
        elif self.y < 0 - self.image_size or self.y >= WIN_H + self.image_size:
            visible = False
        return visible

    def add_to_group(self):
        if not self.in_sprite_list:
            self.app_handler.in_group.add_internal(self)
            self.in_sprite_list = True

    def remove_from_group(self):
        if self.in_sprite_list:
            self.app_handler.in_group.remove_internal(self)
            self.in_sprite_list = False

class AppHandler:
    def __init__(self, app):
        self.app = app
        self.cam_x = 0
        self.cam_y = 0
        self.chunk_position = self.get_chunk_position((self.cam_x, self.cam_y))
        self.loaded_sprites = {}
        self.visible_chunks = []
        self.load_assets()
        self.map = Map(self)
        self.in_group = pg.sprite.Group()
        self.pause_group = {}
        self.param_hud = pg.Surface([400, 200])
        self.font = ft.SysFont('Verdana', FONT_SIZE)
        self.tick_divider = 0
        self.number_of_loaded_sprites = 0

    def get_sprite(self, category, biome, name):
        return self.loaded_sprites[category][biome][name]

    def load_assets(self):
        self.loaded_sprites = {
            "biomes": common.biomes.load_tile_image(self.app)
            #,"entities": common.entities.load_entity_image(self.app)
        }


    def move(self):
        if 'up' in game_app.keybind:
            self.cam_y -= SPEED
        if 'down' in game_app.keybind:
            self.cam_y += SPEED
        if 'left' in game_app.keybind:
            self.cam_x -= SPEED
        if 'right' in game_app.keybind:
            self.cam_x += SPEED


    def interact(self):
        if 'left_click' in game_app.keybind:
            self.add_entity()

    def timing_function(self, frequency, function, *args, **kwargs):
        if self.tick_divider % frequency == 0:
            self.tick_divider += 1
            function(*args, **kwargs)
        else:
            self.tick_divider += 1


    def update(self):
        self.load_chunks()
        self.move()
        self.interact()
        self.in_group.update()

        if self.in_group.spritedict:
            sorted_in_group_x = {sprite: value for sprite, value in sorted(self.in_group.spritedict.items(), key=lambda item: item[0].x)}
            sorted_in_group = {sprite: value for sprite, value in sorted(sorted_in_group_x.items(), key=lambda item: item[0].y)}
            self.in_group.spritedict = sorted_in_group

    def sort_sprite_group(self):
        if self.in_group.spritedict:
            sorted_in_group_x = {sprite: value for sprite, value in sorted(self.in_group.spritedict.items(), key=lambda item: item[0].x)}
            sorted_in_group = {sprite: value for sprite, value in sorted(sorted_in_group_x.items(), key=lambda item: item[0].y)}
            self.in_group.spritedict = sorted_in_group

    def load_chunks(self):
        if self.chunk_position != self.get_chunk_position((self.cam_x, self.cam_y)) or self.map.chunks.super_chunk_location == {}:
            start = time.time()
            self.load_chunks_thread()
            if print_time(time.time()-start):
                a = 10

            if not lock.locked():
                """thread = threading.Thread(target=self.load_chunks_thread)
                thread.start()"""

    def load_chunks_thread(self):
        with lock:
            previous_chunks = self.visible_chunks
            self.chunk_position = self.get_chunk_position((self.cam_x, self.cam_y))
            loading_zones = self.get_loading_zone()
            self.visible_chunks = self.get_visible_chunks()

            for chunk_coordinates in self.visible_chunks:
                if chunk_coordinates in loading_zones:
                    if not self.map.chunks.get(chunk_coordinates):
                        self.map.load_chunk(chunk_coordinates)
                    for chunk_x in self.map.chunks.get(chunk_coordinates).tiles:
                        for tile in chunk_x:
                            tile[1].add_to_group()

            for chunk_coordinates in previous_chunks:
                if chunk_coordinates not in self.visible_chunks and self.map.chunks.get(chunk_coordinates):
                    for chunk_x in self.map.chunks.get(chunk_coordinates).tiles:
                        for tile in chunk_x:
                            tile[1].remove_from_group()
                    self.map.chunks.get(chunk_coordinates).unload()

    def get_loading_zone(self):
        return [
            (self.chunk_position[0] + i, self.chunk_position[1] + j)
            for i in range(0, int(CHUNK_LOAD_DISTANCE))
            for j in range(0, CHUNK_LOAD_DISTANCE)
        ]

    def get_visible_chunks(self):
        max_chunks_width = WIN_W // (CHUNK_SIZE * TILE_SIZE)
        max_chunks_height = WIN_H // (CHUNK_SIZE * TILE_SIZE)

        chunk_offset_x = int(((WIN_W - TOTAL_WIDTH + CHUNK_WIDTH)/2)//CHUNK_WIDTH)
        chunk_offset_y = int(((WIN_H - TOTAL_WIDTH + CHUNK_WIDTH)/2)//CHUNK_WIDTH)

        return [
            (i, j)
            for i in range(self.chunk_position[0] - chunk_offset_x - 1, 1 + self.chunk_position[0] + max_chunks_width - chunk_offset_x + 1)
            for j in range(self.chunk_position[1] - chunk_offset_y - 1, 1 + self.chunk_position[1] + max_chunks_height - chunk_offset_y + 1)
        ]



    #todo : move this
    def add_entity(self):
        (x, y) = pygame.mouse.get_pos()
        new_entity = BaseSprite(self, Tile(self, x + self.cam_x, y + self.cam_y, -1), x, y)
        self.map.entities.append(new_entity)


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

    def draw(self):
        # Draw only the visible group
        self.in_group.draw(self.app.renderer)

    def draw_hud(self):
        self.param_hud.set_colorkey((0, 0, 0))

        # Récupération des informations à afficher
        active_sprites = len(self.in_group)
        total_tiles = self.number_of_loaded_sprites
        fps = self.app.get_fps()
        cam_coord = f"x: {self.cam_x} | y: {self.cam_y}"

        # Liste des lignes de texte à afficher
        lines = [
            f"Active sprites: {active_sprites}",
            f"Passive sprites: {total_tiles}",
            f"{fps:.2f} fps",  # Limitez les FPS à deux décimales
            cam_coord
        ]

        # Variables pour le rendu ligne par ligne
        x, y = 10, 10  # Position initiale
        line_spacing = 20  # Espace vertical entre les lignes

        # Rendre chaque ligne de texte séparément
        for line in lines:
            self.font.render_to(self.param_hud, (x, y), text=line, fgcolor='green', bgcolor='black')
            y += line_spacing  # Ajustement pour la ligne suivante

        # Affichage du HUD final
        hud = Texture.from_surface(self.app.renderer, self.param_hud)
        hud.draw((0, 0, *[300, 200]), (0, 0, *[300, 200]))

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

    def update_screen(self):
        self.dt = self.clock.tick(MAX_FPS) * 0.001  # Time for each frame
        self.renderer.clear()
        self.app_handler.update()
        self.app_handler.draw()
        self.app_handler.draw_hud()
        self.renderer.present()

    def inputs(self):
        self.keybind.clear()
        for e in pg.event.get():
            if e.type == pg.QUIT or (e.type == pg.KEYDOWN and e.key == pg.K_ESCAPE):
                pg.quit()
                sys.exit()

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

if __name__ == '__main__':

    game_app = App()
    game_app.run_application()