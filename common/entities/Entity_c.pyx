from __future__ import annotations
import math

import Settings as S
import random
from common.biomes.properties.biome_generator_helper import pil_to_sdl2

cdef int max_local_counter  = S.MAX_LOCAL_COUNTER
cdef int sprite_margin      = S.SPRITE_MARGIN
cdef int grid_size          = S.GRID_SIZE

cdef struct FloatPair:
    float x
    float y

cdef struct IntPair:
    int x
    int y


cdef class Coordinates:
    cdef public float x
    cdef public float y
    def __init__(self, x, y):
        self.x = x
        self.y = y

    cdef void set_coord(self, float x, float y):
        self.x = x
        self.y = y

    cdef FloatPair get_coord(self):
        return self.x, self.y

    cdef FloatPair get_distance(self, Coordinates other_coord):
        return math.hypot(self.x - other_coord.x, self.y - other_coord.y)


cdef class BaseSprite:
    cdef object app_handler
    cdef object image
    cdef object rect
    cdef Coordinates entity_coord
    cdef int x
    cdef int y
    cdef int width
    cdef int height
    cdef bool in_sprite_list
    cdef str group_name

    def __init__(self, object app_handler, str group_name, tuple size, Coordinates coordinates = Coordinates(0.0, 0.0)):
        self.app_handler = app_handler
        self.image = None
        self.rect = None
        self.entity_coord = coordinates
        self.x: int = 0
        self.y: int = 0
        w, h = size
        self.width = w
        self.height = h
        self.in_sprite_list: bool = False
        if group_name not in app_handler.group_list.keys():
            group_name = "default"
            print("group not found")
        self.group_name = group_name

    def update(self) -> None:
        if self.in_sprite_list:
            self.update_position()

    cdef void update_position(self):
        cdef int screen_x = self.app_handler.screen_x_start
        cdef int screen_y = self.app_handler.screen_y_start

        self.x = <int>self.entity_coord.x - screen_x
        self.y = <int>self.entity_coord.y - screen_y

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
        image = pil_to_sdl2(self.app_handler.app.renderer, pil_image)
        self.load_sdl_image(image)

    def load_sdl_image(self, sdl_image) -> None:
        self.image = sdl_image
        self.rect = self.image.get_rect()
        self.load_on_screen()

    def change_image(self, new_image) -> None:
        self.image = pil_to_sdl2(self.app_handler.app.renderer, new_image)
        self.rect = self.image.get_rect()


cdef class Entity(BaseSprite):
    cdef EntityManager manager
    cdef int id
    cdef int timer_group
    cdef bool is_alive
    cdef float collide_radius
    cdef int local_counter
    cdef IntPair coord_grid
    cdef bool has_coord_grid
    def __init__(self, object app_handler, tuple size, float collide_radius=10,
                 int timer_group=1, str group, Coordinates coordinates=Coordinates(0.0, 0.0)) -> None:
        super().__init__(app_handler, group, size, coordinates)
        self.manager = app_handler.map.entity_manager
        self.id = 0
        self.timer_group = timer_group
        self.is_alive = True
        self.collide_radius = collide_radius
        self.local_counter = random.randint(0, max_local_counter)
        self.coord_grid.x = 0
        self.coord_grid.y = 0
        self.has_coord_grid = False

    cdef EntityEvent process(self):
        # Must return something
        return EntityEvent("None", self.manager, self)



    cdef void refresh(self):
        self.local_counter += 1
        if self.local_counter % max_local_counter == 0:
            if self.in_sprite_list and not self.pos_is_on_screen():
                self.unload_from_screen(keep_image=True)
            elif not self.in_sprite_list and self.pos_is_on_screen():
                self.load_on_screen()

    cdef bool pos_is_on_screen(self):
        cdef int x_start
        cdef int y_start
        cdef int x_end
        cdef int y_end
        x_start = self.app_handler.screen_x_start
        y_start = self.app_handler.screen_y_start
        if self.entity_coord.x + self.width + sprite_margin >= x_start and self.entity_coord.y + self.height + sprite_margin >= y_start:
            x_end = self.app_handler.screen_x_end
            y_end = self.app_handler.screen_y_end
            if self.entity_coord.x - sprite_margin <= x_end and self.entity_coord.y - sprite_margin <= y_end:
                return True
        return False


cdef class MovingEntity(Entity):
    cdef float x_speed
    cdef float y_speed
    def __init__(self, object app_handler, tuple size, float collide_radius=10,
                 int timer_group=1, str group, Coordinates coordinates=Coordinates(0.0, 0.0)) -> None:
        super().__init__(app_handler, size, collide_radius, timer_group, group, coordinates)
        self.x_speed = 0.0
        self.y_speed = 0.0
        self.coord_grid.x = <int>coordinates.x // grid_size
        self.coord_grid.y = <int>coordinates.y // grid_size
        self.has_coord_grid = True

    cdef void set_speed(self, x_speed: float, y_speed: float):
        self.x_speed = x_speed
        self.y_speed = y_speed

    cdef void change_speed(self, x_speed: float, y_speed: float):
        self.x_speed += x_speed
        self.y_speed += y_speed

    cdef void refresh(self):
        super().refresh()
        self.entity_coord.x += self.x_speed
        self.entity_coord.y += self.y_speed
        self.manager.entities.update_coord_group2(self)

#todo : continuer cdef class EntityManager2: