from Settings import *
from common.biomes.properties.biome_generator_helper import pil_to_sdl2


class Coordinates:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)

    def get(self):
        return self.x, self.y

    def set(self, x, y):
        self.x = float(x)
        self.y = float(y)

    def is_nearby(self, other_coord, tolerance):
        if other_coord.x <= self.x + tolerance and other_coord.y <= self.y + tolerance:
            if other_coord.x >= self.x - tolerance and other_coord.y >= self.y - tolerance:
                return True
        return False


class BaseSprite:
    def __init__(self, app_handler, group_name, size):
        self.app_handler = app_handler
        self.image = None
        self.rect = None
        self.entity_coord = Coordinates(0.0, 0.0)
        self.x, self.y = 0, 0
        self.intern_zoom_index = None
        self.width, self.height = size
        self.in_sprite_list = False
        if group_name is None:
            group_name = "default"
            print("group not found")
        self.group_name = group_name

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
        self.x, self.y = int(self.entity_coord.x) - screen_x, int(self.entity_coord.y) - screen_y
        self.rect.center = self.x, self.y

    def load_on_screen(self):
        if self.image is not None and self.rect is not None:
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
    def __init__(self, app_handler, size, radius=10, timer_group=1, group="default"):
        super().__init__(app_handler, group, size)
        self.id = 0
        self.timer_group = timer_group
        self.is_alive = True
        self.collide_radius = radius

    def process(self):
        return

    def refresh(self):
        return


class MovingEntity(Entity):
    def __init__(self, app_handler, size, radius=10, timer_group=1, group="entity"):
        super().__init__(app_handler, size, radius, timer_group, group)
        self.x_speed = 0
        self.y_speed = 0

    def set_speed(self, x_speed, y_speed):
        self.x_speed = x_speed
        self.y_speed = y_speed

    def change_speed(self, x_speed, y_speed):
        self.x_speed += x_speed
        self.y_speed += y_speed

    def refresh(self):
        self.entity_coord.x += self.x_speed
        self.entity_coord.y += self.y_speed


class EntityManager:
    def __init__(self, max_modulo=240):
        self.entities = EntityList()
        self.max_modulo = max_modulo
        self.frame_counter = 0
        self.serial_id_counter = 0

    def update(self):
        if self.frame_counter >= self.max_modulo:
            self.frame_counter = 0
        event_list = []
        for modulo, entity_list in self.entities.get_all():
            local_counter = 0
            local_modulo = self.frame_counter % modulo
            for entity in entity_list.values():
                entity_modulo = local_counter % modulo
                local_counter += 1
                entity.refresh()
                if entity_modulo == local_modulo:
                    event = entity.process()
                    if event is not None:
                        event_list.append(event)
        for event in event_list:
            event.execute()
        self.frame_counter += 1

    def add(self, entity):
        entity.id = self.serial_id_counter
        self.entities.add_item(entity.timer_group, self.serial_id_counter, entity)
        self.serial_id_counter += 1

    def remove(self, s_id):
        self.entities.remove_item(s_id)


class EntityList:
    def __init__(self):
        # Contains: {timer_group_key: {serial_id: Entity()}}
        self.__entities = {}
        # Contains: {serial_id: (Coordinates(), timer_group_key, radius)}
        self.__entity_by_id = {}

    def add_item(self, key, serial_id, item):
        if not self.__entities.get(key):
            self.__entities[key] = {}
        self.__entities[key][serial_id] = item
        self.__entity_by_id[serial_id] = (item.entity_coord, item.timer_group, item.collide_radius)

    def remove_item(self, serial_id):
        timer_group = self.__entity_by_id.pop(serial_id)[1]
        del self.__entities[timer_group][serial_id]

    def get_all(self):
        return self.__entities.items()

    def get_nearby_entity(self, center_coord, tolerance):
        return [(s_id, info) for s_id, info in self.__entity_by_id.items() if info[1].is_nearby(center_coord, tolerance)]


class EntityEvent:
    def __init__(self, event_type, entity_manager, entity, function=None):
        self.event_type = event_type
        self.entity_manager = entity_manager
        self.entity = entity
        self.function = function

    def execute(self):
        if self.function is None:
            match self.event_type:
                case "kill_self":
                    self.kill()
        else:
            self.function()

    def kill(self):
        s_id = self.entity.id
        self.entity.unload_from_screen()
        self.entity_manager.remove(s_id)
