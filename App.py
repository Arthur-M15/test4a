import pygame.mouse
from Map import *
from test_tools import *


class BaseSprite:
    def __init__(self, app_handler, group_name, size):
        self.app_handler = app_handler
        self.image = None
        self.rect = None
        self.entity_x, self.entity_y = 0.0, 0.0
        self.x, self.y = 0, 0
        self.intern_zoom_index = None
        self.width, self.height = size
        self.in_sprite_list = False
        if group_name is None:
            group_name = "default"
            print("group not found")
        self.group_name = group_name
        # todo later:
        # self.is_moving = True

    def update(self):
        """ Update the image on the screen, not the object. """
        if self.in_sprite_list:
            self.update_position()

    def get_zoom_offset(self):
        off_x = (WIN_W - self.app_handler.width) // 2
        off_y = (WIN_H - self.app_handler.height) // 2
        return off_x, off_y

    def update_position(self):
        screen_x, screen_y =  self.app_handler.screen_x_start, self.app_handler.screen_y_start
        self.x, self.y = int(self.entity_x) - screen_x, int(self.entity_y) - screen_y
        self.rect.center = self.x, self.y

    def load_on_screen(self):
        if self.image is not None and self.rect is not None:
            if self.entity_x is not None and self.entity_y is not None:
                self.app_handler.group_list.get(self.group_name).add_internal(self)
                self.in_sprite_list = True
        else:
            raise Exception("Can't load sprite on screen")

    def unload_from_screen(self):
        if self.in_sprite_list:
            self.in_sprite_list = False
            self.app_handler.group_list.get(self.group_name).spritedict.pop(self, None)
            self.image = None


class ChunkGroup(BaseSprite):
    def __init__(self, app_handler, size):
        group_name = "chunk" # app_handler.group_list.get("chunk")
        super().__init__(app_handler, group_name, size)


class EntityGroup(BaseSprite):
    def __init__(self, app_handler, size):
        group = "entity" # app_handler.group_list.get("entity")
        super().__init__(app_handler, group, size)


class AppHandler:
    def __init__(self, app):
        self.app = app

        # coordinates:
        self.coord_x, self.coord_y = 0, 0
        self.last_coord_x, self.last_coord_y = 0, 0
        self.width, self.height = WIN_W, WIN_H
        self.zoom_index = 0
        self.zoom_factor = 1
        self.screen_x_start, self.screen_y_start = 0, 0
        self.screen_x_end, self.screen_y_end = 0, 0
        self.margin = 100
        self.detection_range = 10000
        self.detection_x_start = self.coord_x - self.detection_range
        self.detection_y_start = self.coord_y - self.detection_range
        self.detection_x_end = self.coord_x + self.detection_range
        self.detection_y_end = self.coord_y + self.detection_range
        self.cam_speed = 5
        self.cam_x_retenue = 0.0
        self.cam_y_retenue = 0.0

        # Map:
        self.map = Map(self)
        # load this when in detection zone:
        self.detectable_chunks = []
        # create its sprite when in visible zone:
        self.visible_chunks = []


        # Graphics:
        self.group_list = {
            "chunk": pg.sprite.Group(),
            "default": pg.sprite.Group()
        }
        """ todo later:
        self.floor_group = pg.sprite.Group()
        self.object_group = pg.sprite.Group()
        self.atmosphere_group = pg.sprite.Group()
        """
        self.sprite_lock = threading.Lock()

        # Tests:
        self.logger = AppInformation(self)

        test_size = 20
        self.central_sprite = BaseSprite(self, "default", (test_size, test_size))
        pil_image = PILImage.new("RGBA", (test_size, test_size), (50, 50, 50, 50))
        self.central_sprite.image = pil_to_sdl2(self.app.renderer, pil_image)
        self.central_sprite.rect = self.central_sprite.image.get_rect()
        self.central_sprite.load_on_screen()

    def set_screen_size(self):
        self.zoom_factor = self.get_zoom()
        self.width, self.height = int(WIN_W // self.zoom_factor), int(WIN_H // self.zoom_factor)
        self.app.renderer.scale = (self.zoom_factor, self.zoom_factor)
        self.update_chunks(force=True)

    def zoom_in(self):
        a = self.group_list.get("chunk")
        if self.zoom_index > -4 or True:
            self.zoom_index -= 1
            self.set_screen_size()

    def zoom_out(self):
        if self.zoom_index < 4 or True:
            self.zoom_index += 1
            self.set_screen_size()

    def get_zoom(self):
        zoom_coefficient = 1.2
        return zoom_coefficient ** -self.zoom_index

    def update_zone(self):
        self.detection_x_start = self.coord_x - self.detection_range
        self.detection_y_start = self.coord_y - self.detection_range
        self.detection_x_end = self.coord_x + self.detection_range
        self.detection_y_end = self.coord_y + self.detection_range
        self.screen_x_start = self.coord_x - (self.width // 2)
        self.screen_y_start = self.coord_y - (self.height // 2)
        self.screen_x_end = self.coord_x + (self.width // 2)
        self.screen_y_end = self.coord_y + (self.height // 2)

    def get_cam_shift(self, axe, way):
        """
        :param axe: x or y
        :param way: equals -1 if up or left, and equals +1 if down or right
        :return: The shift of the camera as an integer.
        """
        if axe == "x":
            total = self.cam_x_retenue + (self.cam_speed * way)
            shift = int(total)
            self.cam_x_retenue = total - shift
        else:
            total = self.cam_y_retenue + (self.cam_speed * way)
            shift = int(total)
            self.cam_y_retenue = total - shift
        return shift

    def interact(self):
        # Camera movement:
        if 'up' in game_app.keybind:
            self.coord_y += self.get_cam_shift("y", -1)
        if 'down' in game_app.keybind:
            self.coord_y += self.get_cam_shift("y", 1)
        if 'left' in game_app.keybind:
            self.coord_x += self.get_cam_shift("x", -1)
        if 'right' in game_app.keybind:
            self.coord_x += self.get_cam_shift("x", 1)

        # Camera zoom:
        if 'mouse_up' in game_app.keybind:
            self.zoom_in()
        if 'mouse_down' in game_app.keybind:
            self.zoom_out()

    def sort_sprite_group(self):
        for key, group in self.group_list.items():
            if group.spritedict:
                sorted_in_group_x = {sprite: value for sprite, value in sorted(group.spritedict.items(),
                                                                               key=lambda item: item[0].x)}
                sorted_in_group = {sprite: value for sprite, value in sorted(sorted_in_group_x.items(),
                                                                             key=lambda item: item[0].y)}
                self.group_list.get(key).spritedict = sorted_in_group

    def update(self):
        self.update_zone()
        self.interact()
        self.update_chunks()
        self.map.manager.update()
        self.update_sprite_groups()
        self.draw()
        self.draw_information()
        self.sort_sprite_group()

    def update_sprite_groups(self):
        for group in self.group_list.values():
            group.update()

    def update_chunks(self, force=False):
        if      (len(self.visible_chunks) == 0 or
                (self.last_coord_x != self.coord_x or self.last_coord_y != self.coord_y) or
                force):
            self.set_detectable_chunks()
            previous_visible = self.visible_chunks
            self.set_visible_chunks()
            for chunk_coordinates in self.visible_chunks:
                if chunk_coordinates not in previous_visible:
                    self.map.manager.load_chunk(chunk_coordinates)
            for chunk_coordinates in previous_visible:
                if chunk_coordinates not in self.visible_chunks:
                    self.map.manager.unload_chunk(chunk_coordinates)

    def set_visible_chunks(self):
        top_left_chunk_coordinates = self.get_chunk_coordinates(self.screen_x_start - self.margin, self.screen_y_start - self.margin)
        bottom_right_chunk_coordinates = self.get_chunk_coordinates(self.screen_x_end + self.margin, self.screen_y_end + self.margin)
        visible_zone = self.select_zone(top_left_chunk_coordinates, bottom_right_chunk_coordinates)
        self.visible_chunks = [chunk for chunk in visible_zone if chunk in self.detectable_chunks]

    def set_detectable_chunks(self):
        top_left_chunk_coordinates = self.get_chunk_coordinates(self.detection_x_start, self.detection_y_start)
        bottom_right_chunk_coordinates = self.get_chunk_coordinates(self.detection_x_end, self.detection_y_end)
        self.detectable_chunks = self.select_zone(top_left_chunk_coordinates, bottom_right_chunk_coordinates)
        return self.detectable_chunks

    @staticmethod
    def get_chunk_coordinates(real_coord_x, real_coord_y):
        chunk_x = real_coord_x // CHUNK_PIXEL_WIDTH
        chunk_y = real_coord_y // CHUNK_PIXEL_WIDTH
        return chunk_x, chunk_y

    @staticmethod
    def select_zone(top_left, bottom_right):
        chunk_list = []
        for i in range(top_left[0], bottom_right[0] + 2):
            for j in range(top_left[1], bottom_right[1] + 2):
                chunk_list.append((i, j))
        return chunk_list

    def draw(self):
        # Draw only the visible group
        for group in self.group_list.values():
            group.draw(self.app.renderer)

    def get_coordinates(self):
        return self.coord_x, self.coord_y

    def draw_information(self):
        self.logger.print_info()

    def stop_all_threads(self):
        self.map.manager.stop()


class AppInformation:
    def __init__(self, app_handler):
        self.app_handler = app_handler
        self.sprite_count = 0
        self.fps = 0
        self.min_fps = 9999
        self.total_tiles = 0

    def update_fps(self):
        fps = self.app_handler.app.get_fps()
        if fps != 0:
            self.fps = fps
            if fps < self.min_fps:
                self.min_fps = fps

    def update_sprite_count(self):
        total = 0
        for group in self.app_handler.group_list.values():
            total += len(group)
        self.sprite_count = total

    def update_information(self):
        self.update_fps()
        self.update_sprite_count()

    def print_info(self, sprites = True, tiles = False, fps = True, minimum_fps = True, coordinates = True, corner_coordinates = True):
        self.update_information()
        info_list = []
        if sprites:
            info_list.append(f"Sprite count: {self.sprite_count}; ")
        if tiles:
            info_list.append(f"Tiles count: {normalize_text(self.total_tiles)}; ")
        if fps:
            info_list.append(f"FPS: {normalize_text(self.fps)}; ")
        if minimum_fps:
            info_list.append(f"Minimum FPS: {normalize_text(self.min_fps)}; ")
        if coordinates:
            info_list.append(f"Coord: {normalize_text(self.app_handler.get_coordinates(), 12)}; ")
        if corner_coordinates:
            info_list.append(f"Corner: {normalize_text(f"({self.app_handler.screen_x_start}, {self.app_handler.screen_y_start})", 16)}; ")
        infos = "".join(info_list)
        print(f"\r{infos}", end='')


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
        self.renderer.present()


    def inputs(self):
        self.keybind.clear()
        for event in pg.event.get():
            if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                self.app_handler.stop_all_threads()
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
        else:
            return 0
        return sum(self.fps) / len(self.fps)

    def run_application(self):
        while True:
            self.update_screen()
            self.inputs()


def get_thread_index(coordinates):
    modulo = CHUNK_THREAD_NUMBER
    coord_sum = sum(coordinates)
    return coord_sum % modulo


if __name__ == '__main__':
    game_app = App()
    game_app.run_application()