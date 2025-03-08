import pygame.mouse
import common
import test
from Settings import *
from Map import *
import threading
lock = threading.Lock()
from test_tools import *
from pygame._sdl2.video import Texture, Image as Image


class BaseSprite:
    def __init__(self, app_handler, entity, x=0, y=0):
        """
        :param app_handler: The handler of the game
        :param x: Relative x position of the object on the window
        :param y: Relative y position of the object on the window
        """
        self.app_handler = app_handler
        self.in_sprite_list = False
        self.entity = entity
        self.image = self.entity.image
        self.original_image = self.entity.image
        self.rect = self.entity.image.get_rect()

        self.offset_x, self.offset_y = None, None
        self.set_position()
        self.x, self.y = self.app_handler.cam_x - self.entity.x, self.app_handler.cam_y - self.entity.y

    def update(self):
        self.set_position()
        self.action()
        self.x, self.y = self.entity.x - self.app_handler.cam_x + self.offset_x, self.entity.y - self.app_handler.cam_y + self.offset_y
        self.rect.center = self.x, self.y

    def action(self):
        if 'mouse_wheel' in self.app_handler.app.keybind:
            self.set_position()
            self.image.texture.renderer.scale = (self.app_handler.zoom_scale/5, self.app_handler.zoom_scale/5)

    def set_position(self):
        self.offset_x, self.offset_y = self.app_handler.get_offset()
        self.x, self.y = self.entity.x - self.app_handler.cam_x + self.offset_x, self.entity.y - self.app_handler.cam_y + self.offset_y

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
        self.cam_x, self.cam_y = 0, 0
        self.renderer_offset_x, self.renderer_offset_y = 0, 0
        self.chunk_position = self.get_chunk_position((self.cam_x, self.cam_y))
        self.visible_chunks = []
        self.map = Map(self)
        self.in_group = pg.sprite.Group()
        self.pause_group = {}
        self.param_hud = pg.Surface([400, 200])
        self.font = ft.SysFont('Verdana', FONT_SIZE)
        self.tick_divider = 0
        self.number_of_loaded_sprites = 0
        self.zoom_scale = 5
        self.cam_speed = BASE_SPEED


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
            self.add_entity()
        if 'mouse_up' in game_app.keybind and self.zoom_scale < 10:
            self.zoom_scale += 1
            self.load_chunks_thread()
        if 'mouse_down' in game_app.keybind and self.zoom_scale > 2:
            self.zoom_scale -= 1
            self.load_chunks_thread()


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
        self.sort_sprite_group()
        #self.timing_function(120, self.print_biome)

    def print_biome(self):
        x, y = self.get_chunk_position()
        biome = self.map.get_biome(x, y)
        print(biome.name)

    def sort_sprite_group(self):
        if self.in_group.spritedict:
            sorted_in_group_x = {sprite: value for sprite, value in sorted(self.in_group.spritedict.items(), key=lambda item: item[0].x)}
            sorted_in_group = {sprite: value for sprite, value in sorted(sorted_in_group_x.items(), key=lambda item: item[0].y)}
            self.in_group.spritedict = sorted_in_group

    def load_chunks(self):
        if self.chunk_position != self.get_chunk_position((self.cam_x, self.cam_y)) or self.map.chunks.super_chunk_location == {}:
            self.load_chunks_thread()
            if not lock.locked():
                pass
                """thread = threading.Thread(target=self.load_chunks_thread)
                thread.start()"""

    def load_chunks_thread(self):
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
            for i in range(self.chunk_position[0] - chunk_offset_x - 1 - scale, 1 + self.chunk_position[0] + max_chunks_width - chunk_offset_x + 1 + scale)
            for j in range(self.chunk_position[1] - chunk_offset_y - 1 - scale, 1 + self.chunk_position[1] + max_chunks_height - chunk_offset_y + 1 + scale)
        ]



    #todo : move this
    def add_entity(self):
        (x, y) = pygame.mouse.get_pos()
        pass


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

    def draw_hud(self):
        self.param_hud.set_colorkey((0, 0, 0))

        # Récupération des informations à afficher
        active_sprites = len(self.in_group)
        total_tiles = self.number_of_loaded_sprites
        fps = self.app.get_fps()
        cam_coord = f"x: {self.cam_x} | y: {self.cam_y}"

        # Liste des lignes de texte à afficher
        lines = [
            f"scale: {self.zoom_scale}",
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
        self.scale = 1

    def update_screen(self):
        self.dt = self.clock.tick(MAX_FPS) * 0.001  # Time for each frame
        self.renderer.clear()
        self.app_handler.update()
        self.app_handler.draw()
        self.app_handler.draw_hud()
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
    """if False:
        common.biomes.properties.biome_generator_helper.simple_dominance_matrix(10, "corner")
        test2 = test.main()
        test = BiomeOffsetList()
        a = test.get_offset(0)
        #biome_generator_helper.assets_generator(((100, 100, 100), (200, 200, 200), (0, 0, 0)), ((0, 100, 100), (0, 200, 200), (10, 0, 0)))
    else:"""
    game_app = App()
    game_app.run_application()