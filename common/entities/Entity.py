import random
import time

from typing_extensions import override
from Settings import *
from common.biomes.properties.biome_generator_helper import pil_to_sdl2
import math


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

    def get_distance(self, other_coord):
        return math.sqrt((self.x - other_coord.x) ** 2 + (self.y - other_coord.y) ** 2)

    def squared_distance(self, other_coord):
        return max(abs(self.x - other_coord.x), abs(self.y - other_coord.y))

class BaseSprite:
    def __init__(self, app_handler, group_name, size, coordinates=Coordinates(0.0, 0.0)):
        self.app_handler = app_handler
        self.image = None
        self.rect = None
        self.entity_coord = Coordinates(0.0, 0.0)# coordinates
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

    def unload_from_screen(self, keep_image=False):
        if self.in_sprite_list:
            self.in_sprite_list = False
            self.app_handler.group_list.get(self.group_name).spritedict.pop(self, None)
            if not keep_image:
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

    def change_image(self, new_image):
        self.image = pil_to_sdl2(self.app_handler.app.renderer, new_image)
        self.rect = self.image.get_rect()


class Entity(BaseSprite):
    def __init__(self, app_handler, size, radius=10, timer_group=1, group="default", coordinates=Coordinates(0.0, 0.0)):
        super().__init__(app_handler, group, size, coordinates)
        self.id = 0
        self.timer_group = timer_group
        self.is_alive = True
        self.collide_radius = radius
        self.local_counter = random.randint(0, MAX_LOCAL_COUNTER)
        self.coord_grid = None

    def process(self):
        return

    def refresh(self):
        t = time.time()
        self.local_counter += 1
        if self.local_counter % MAX_LOCAL_COUNTER == 0:
            if self.in_sprite_list and not self.pos_is_on_screen():
                self.unload_from_screen(keep_image=True)
            elif not self.in_sprite_list and self.pos_is_on_screen():
                self.load_on_screen()

    def pos_is_on_screen(self):
        x_start, y_start = self.app_handler.screen_x_start, self.app_handler.screen_y_start
        if self.entity_coord.x + self.width + SPRITE_MARGIN >= x_start and self.entity_coord.y + self.height + SPRITE_MARGIN >= y_start:
            x_end, y_end = self.app_handler.screen_x_end, self.app_handler.screen_y_end
            if self.entity_coord.x - SPRITE_MARGIN <= x_end and self.entity_coord.y - SPRITE_MARGIN <= y_end:
                return True
        return False


class MovingEntity(Entity):
    def __init__(self, app_handler, size, radius=10, timer_group=1, group="entity", coordinates=Coordinates(0.0, 0.0)):
        super().__init__(app_handler, size, radius, timer_group, group, coordinates)
        self.x_speed = 0
        self.y_speed = 0
        self.coord_grid = int(coordinates.x // GRID_SIZE), int(coordinates.y // GRID_SIZE)

    def set_speed(self, x_speed, y_speed):
        self.x_speed = x_speed
        self.y_speed = y_speed

    def change_speed(self, x_speed, y_speed):
        self.x_speed += x_speed
        self.y_speed += y_speed

    @override
    def refresh(self):
        super().refresh()
        self.entity_coord.x += self.x_speed
        self.entity_coord.y += self.y_speed
        self.app_handler.map.entity_manager.entities.update_coord_group2(self)

    def update_grid_zone(self):
        if self.pos_is_on_screen():
            x, y = self.entity_coord.get()
            new_coord_grid = int(x // GRID_SIZE), int(y // GRID_SIZE)
            if new_coord_grid != self.coord_grid:
                self.app_handler.map.entity_manager.entities.update_coord_group(self, new_coord_grid)


class EntityManager2:
    def __init__(self, app_handler, max_modulo=240):
        self.app_handler = app_handler
        self.entities = EntityList2()
        self.max_modulo = max_modulo
        self.frame_counter = 0
        self.serial_id_counter = 0

    def update(self):
        if self.frame_counter >= self.max_modulo:
            self.frame_counter = 0
        event_list = []

        for modulo, entity_list in self.entities.get_timer_groups():
            local_counter = 0
            local_modulo = self.frame_counter % modulo
            for entity in entity_list:
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



class EntityList2:
    def __init__(self):
        self.__id_entity = {}
        self.__timer_entity = {}
        self.__coord_entity = {}

    def add_item(self, timer, serial_id, entity):
        self.__id_entity[serial_id] = entity
        if not self.__timer_entity.get(timer):
            self.__timer_entity[timer] = []
        self.__timer_entity[timer].append(entity)
        coordinates = entity.coord_grid
        if coordinates is not None:
            if not self.__coord_entity.get(coordinates):
                self.__coord_entity[coordinates] = []
            self.__coord_entity[coordinates].append(entity)

    def remove_item(self, serial_id):
        entity = self.__id_entity.pop(serial_id)
        timer_group = entity.timer_group
        for i, e in (self.__timer_entity[timer_group]):
            if e.id == serial_id:
                self.__timer_entity[timer_group].pop(i)
                break
        coordinates = entity.coord_grid
        if coordinates is not None:
            for i, e in (self.__coord_entity[coordinates]):
                if e.id == serial_id:
                    self.__coord_entity[coordinates].pop(i)
                    break

    def get_timer_groups(self):
        return self.__timer_entity.items()

    def update_coord_group2(self, entity):
        x, y = entity.entity_coord.get()
        if entity.coord_grid[0] != int(x // GRID_SIZE) or entity.coord_grid[1] != int(y // GRID_SIZE):
            index = next((i for i, obj in enumerate(self.__coord_entity[entity.coord_grid]) if obj.id == entity.id), None)
            if index is None:
                raise ValueError("The entity does not exists in the 'self.__coord_entity' list.")
            new_coord_grid = (int(x // GRID_SIZE), int(y // GRID_SIZE))
            self.__coord_entity[entity.coord_grid].pop(index)
            if len(self.__coord_entity[entity.coord_grid]) == 0:
                del self.__coord_entity[entity.coord_grid]
            entity.coord_grid = new_coord_grid
            if self.__coord_entity.get(entity.coord_grid) is None:
                self.__coord_entity[entity.coord_grid] = []
            self.__coord_entity[entity.coord_grid].append(entity)

    def update_coord_group(self, entity, new_coordinates):
        if entity.coord_grid is None:
            raise ValueError("This object does not have a coordinate grid")
        prev_coord = entity.coord_grid
        for i, e in enumerate(self.__coord_entity[prev_coord]):
            if e.id == entity.id:
                self.__coord_entity[prev_coord].pop(i)
                if not self.__coord_entity[prev_coord]:
                    del self.__coord_entity[prev_coord]
                break
        if self.__coord_entity.get(new_coordinates) is None:
            self.__coord_entity[new_coordinates] = []
        entity.coord_grid = new_coordinates
        self.__coord_entity[new_coordinates].append(entity)

    def get_nearby_entities(self, grid_coordinates, size=1):
        entity_list = []
        for i in range(-size, size+1):
            for j in range(-size, size + 1):
                coordinates = grid_coordinates[0]+i, grid_coordinates[1]+j
                if self.__coord_entity.get(coordinates) is None:
                    continue
                entity_list.extend(self.__coord_entity.get(coordinates))
        return entity_list

    def get_entities(self):
        return self.__id_entity.values()

    def fetch_entities(self):
        for e in self.__id_entity.values():
            yield e


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
