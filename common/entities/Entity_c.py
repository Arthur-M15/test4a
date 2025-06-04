from __future__ import annotations
from typing import Iterator, Callable

import Settings as S
from common.biomes.properties.biome_generator_helper import pil_to_sdl2
import pygame as pg

import math
import random
from typing import Optional, Tuple, List, Dict

class Coordinates:
    x: float
    y: float
    def __init__(self, x: float, y: float):
        self.x: float = float(x)
        self.y: float = float(y)

    def get(self) -> Tuple[float, float]:
        return self.x, self.y

    def set(self, x: float, y: float) -> None:
        self.x = float(x)
        self.y = float(y)

    def is_nearby(self, other_coord: Coordinates, tolerance: float) -> bool:
        return (self.x - tolerance <= other_coord.x <= self.x + tolerance and
                self.y - tolerance <= other_coord.y <= self.y + tolerance)

    def get_distance(self, other_coord: Coordinates) -> float:
        return math.hypot(self.x - other_coord.x, self.y - other_coord.y)


class BaseSprite:
    group_name: str
    entity_coord: Coordinates
    x: int
    y: int
    width: int
    height: int
    in_sprite_list: bool
    def __init__(self, app_handler, group_name: str, size: Tuple[int, int], coordinates: Coordinates = Coordinates(0.0, 0.0)) -> None:
        self.app_handler = app_handler
        self.image: Optional[pg._sdl2.video.Texture] = None
        self.rect: Optional[pg.Rect] = None
        self.entity_coord: Coordinates = coordinates
        self.x: int = 0
        self.y: int = 0
        self.intern_zoom_index = None
        self.width, self.height = size
        self.in_sprite_list: bool = False
        if group_name not in app_handler.group_list.keys():
            group_name = "default"
            print("group not found")
        self.group_name = group_name

    def update(self) -> None:
        if self.in_sprite_list:
            self.update_position()

    def get_zoom_offset(self) -> Tuple[int, int]:
        off_x: int
        off_y: int
        off_x = (S.WIN_W - self.app_handler.width) // 2
        off_y = (S.WIN_H - self.app_handler.height) // 2
        return off_x, off_y

    def update_position(self) -> None:
        screen_x: int
        screen_y: int
        screen_x, screen_y = self.app_handler.screen_x_start, self.app_handler.screen_y_start
        self.x = int(self.entity_coord.x) - screen_x
        self.y = int(self.entity_coord.y) - screen_y
        assert self.rect is not None
        self.rect.center = self.x, self.y

    def load_on_screen(self) -> None:
        if self.image is not None and self.rect is not None:
            self.app_handler.group_list.get(self.group_name).add_internal(self)
            self.in_sprite_list = True
        else:
            raise Exception("Can't load sprite on screen")

    def unload_from_screen(self, keep_image: bool = False) -> None:
        if self.in_sprite_list:
            self.in_sprite_list = False
            self.app_handler.group_list.get(self.group_name).spritedict.pop(self, None)
            if not keep_image:
                self.image = None
                self.rect = None

    def load_image(self, pil_image) -> None:
        self.image = pil_to_sdl2(self.app_handler.app.renderer, pil_image)
        self.rect = self.image.get_rect()
        self.load_on_screen()

    def change_image(self, new_image) -> None:
        self.image = pil_to_sdl2(self.app_handler.app.renderer, new_image)
        self.rect = self.image.get_rect()


class Entity(BaseSprite):
    size: Tuple[int, int]
    radius: int
    timer_group: int

    def __init__(self, app_handler, size: Tuple[int, int], radius: int = 10, timer_group: int = 1,
                 group: str = "default", coordinates: Coordinates = Coordinates(0.0, 0.0)) -> None:
        super().__init__(app_handler, group, size, coordinates)
        self.id: int = 0
        self.timer_group: int = timer_group
        self.is_alive: bool = True
        self.collide_radius: int = radius
        self.local_counter: int = random.randint(0, S.MAX_LOCAL_COUNTER)
        self.coord_grid: Tuple[int, int] = 0, 0
        self.has_coord_grid: bool = False

    def process(self):
        return EntityEvent("None", self.app_handler.map.entity_manager, self)

    def refresh(self) -> None:
        self.local_counter += 1
        if self.local_counter % S.MAX_LOCAL_COUNTER == 0:
            if self.in_sprite_list and not self.pos_is_on_screen():
                self.unload_from_screen(keep_image=True)
            elif not self.in_sprite_list and self.pos_is_on_screen():
                self.load_on_screen()

    def pos_is_on_screen(self) -> bool:
        x_start: int
        y_start: int
        x_end: int
        y_end: int
        x_start, y_start = self.app_handler.screen_x_start, self.app_handler.screen_y_start
        if self.entity_coord.x + self.width + S.SPRITE_MARGIN >= x_start and self.entity_coord.y + self.height + S.SPRITE_MARGIN >= y_start:
            x_end, y_end = self.app_handler.screen_x_end, self.app_handler.screen_y_end
            if self.entity_coord.x - S.SPRITE_MARGIN <= x_end and self.entity_coord.y - S.SPRITE_MARGIN <= y_end:
                return True
        return False


class MovingEntity(Entity):
    size: Tuple[int, int]
    radius: int
    timer_group: int
    group: str
    coordinates: Coordinates
    def __init__(self, app_handler, size: Tuple[int, int], radius: int = 10, timer_group: int = 1,
                 group: str = "entity", coordinates: Coordinates = Coordinates(0.0, 0.0)) -> None:
        super().__init__(app_handler, size, radius, timer_group, group, coordinates)
        self.x_speed: float = 0.0
        self.y_speed: float = 0.0
        self.coord_grid = int(coordinates.x // S.GRID_SIZE), int(coordinates.y // S.GRID_SIZE)
        self.has_coord_grid: bool = True

    def set_speed(self, x_speed: float, y_speed: float) -> None:
        self.x_speed = x_speed
        self.y_speed = y_speed

    def change_speed(self, x_speed: float, y_speed: float) -> None:
        self.x_speed += x_speed
        self.y_speed += y_speed

    def refresh(self) -> None:
        super().refresh()
        self.entity_coord.x += self.x_speed
        self.entity_coord.y += self.y_speed
        self.app_handler.map.entity_manager.entities.update_coord_group2(self)


class EntityManager2:
    max_modulo: int
    def __init__(self, app_handler, max_modulo: int = 240) -> None:
        self.app_handler = app_handler
        self.entities = EntityList2()
        self.max_modulo = max_modulo
        self.frame_counter: int = 0
        self.serial_id_counter: int = 0

    def update(self) -> None:
        if self.frame_counter >= self.max_modulo:
            self.frame_counter = 0
        event_list: List[EntityEvent] = []

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
            assert event is not None
            event.execute()
        self.frame_counter += 1

    def add(self, entity: Entity) -> None:
        entity.id = self.serial_id_counter
        self.entities.add_item(entity.timer_group, self.serial_id_counter, entity)
        self.serial_id_counter += 1

    def remove(self, s_id: int) -> None:
        self.entities.remove_item(s_id)


class EntityList2:
    def __init__(self) -> None:
        self.__id_entity: Dict[int, Entity] = {}
        self.__timer_entity: Dict[int, List[Entity]] = {}
        self.__coord_entity: Dict[Tuple[int, int], List[Entity]] = {}

    def add_item(self, timer: int, serial_id: int, entity: Entity) -> None:
        self.__id_entity[serial_id] = entity
        self.__timer_entity.setdefault(timer, []).append(entity)
        if entity.has_coord_grid:
            self.__coord_entity.setdefault(entity.coord_grid, []).append(entity)

    def remove_item(self, serial_id: int) -> None:
        entity = self.__id_entity.pop(serial_id)
        timer_group = entity.timer_group
        self.__timer_entity[timer_group] = [e for e in self.__timer_entity[timer_group] if e.id != serial_id]
        if not self.__timer_entity[timer_group]:
            del self.__timer_entity[timer_group]
        if entity.coord_grid:
            self.__coord_entity[entity.coord_grid] = [e for e in self.__coord_entity[entity.coord_grid] if e.id != serial_id]
            if not self.__coord_entity[entity.coord_grid]:
                del self.__coord_entity[entity.coord_grid]

    def get_timer_groups(self):
        return self.__timer_entity.items()

    def update_coord_group2(self, entity: Entity) -> None:
        x: float
        y: float
        x, y = entity.entity_coord.get()
        new_coord_grid: Tuple[int, int] = int(x // S.GRID_SIZE), int(y // S.GRID_SIZE)
        if entity.coord_grid != new_coord_grid:
            if entity.coord_grid and entity.coord_grid in self.__coord_entity:
                self.__coord_entity[entity.coord_grid] = [e for e in self.__coord_entity[entity.coord_grid] if e.id != entity.id]
                if not self.__coord_entity[entity.coord_grid]:
                    del self.__coord_entity[entity.coord_grid]
            entity.coord_grid = new_coord_grid
            self.__coord_entity.setdefault(entity.coord_grid, []).append(entity)

    def update_coord_group(self, entity: Entity, new_coordinates: Tuple[int, int]) -> None:
        if entity.coord_grid is None:
            raise ValueError("This object does not have a coordinate grid")
        self.__coord_entity[entity.coord_grid] = [e for e in self.__coord_entity[entity.coord_grid] if e.id != entity.id]
        if not self.__coord_entity[entity.coord_grid]:
            del self.__coord_entity[entity.coord_grid]
        self.__coord_entity.setdefault(new_coordinates, []).append(entity)
        entity.coord_grid = new_coordinates

    def get_nearby_entities(self, grid_coordinates: Tuple[int, int], size: int = 1) -> List[Entity]:
        entity_list: List[Entity] = []
        for i in range(-size, size + 1):
            for j in range(-size, size + 1):
                coordinates = (grid_coordinates[0] + i, grid_coordinates[1] + j)
                if coordinates in self.__coord_entity:
                    entity_list.extend(self.__coord_entity[coordinates])
        return entity_list

    def get_entities(self):
        return self.__id_entity.values()

    def fetch_entities(self) -> Iterator[Entity]:
        for e in self.__id_entity.values():
            yield e


class EntityEvent:
    def __init__(self, event_type: str, entity_manager, entity: Entity) -> None:
        self.event_type = event_type
        self.entity_manager = entity_manager
        self.entity = entity

    def execute(self) -> None:
        if self.event_type == "None":
            return
        elif self.event_type == "kill_self":
            self.kill()


    def kill(self) -> None:
        s_id = self.entity.id
        self.entity.unload_from_screen()
        self.entity_manager.remove(s_id)