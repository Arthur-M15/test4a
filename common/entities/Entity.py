from Settings import *
from common.biomes.properties.biome_generator_helper import pil_to_sdl2

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

    def load_image(self, pil_image):
        """
        Load an image from the given PIL image. Only for tests !
        :param pil_image:
        :return:
        """
        self.image = pil_to_sdl2(self.app_handler.app.renderer, pil_image)
        self.rect = self.image.get_rect()
        self.load_on_screen()


class Entity(BaseSprite):
    def __init__(self, app_handler, size, timer_group=1, group="default"):
        super().__init__(app_handler, group, size)
        self.timer_group = timer_group
        self.is_alive = True


class EntityManager:
    def __init__(self, max_modulo=60):
        self.entities = EntityList()
        self.max_modulo = max_modulo
        self.frame_counter = 0

    def update(self):
        if self.frame_counter >= self.max_modulo:
            self.frame_counter = 0

        for modulo, entity_list in self.entities.get_list():
            local_counter = 0
            local_modulo = self.frame_counter % modulo
            for entity in entity_list:
                entity_modulo = local_counter % modulo
                local_counter += 1
                if entity_modulo == local_modulo:
                    entity.process()
        self.frame_counter += 1

    def add(self, entity):
        self.entities.add_item(entity.timer_group, entity)


class EntityList:
    def __init__(self):
        self.entities = {}

    def add_item(self, key, item):
        if not self.entities.get(key):
            self.entities[key] = []
        self.entities[key].append(item)

    def get_list(self):
        return self.entities.items()



class MovingEntity(Entity):
    def __init__(self, app_handler, size, timer_group=1, group="entity"):
        super().__init__(app_handler, size, timer_group, group)
        self.x_speed = 0
        self.y_speed = 0

    def set_speed(self, x_speed, y_speed):
        self.x_speed = x_speed
        self.y_speed = y_speed

    def change_speed(self, x_speed, y_speed):
        self.x_speed += x_speed
        self.y_speed += y_speed

    def process(self):
        self.entity_x += self.x_speed
        self.entity_y += self.y_speed
