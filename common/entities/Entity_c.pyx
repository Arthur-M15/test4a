# cython: language_level=3
from libc.math cimport hypot
from libc.time cimport time
from typing import Tuple, List, Dict, Optional
import Settings as S

cdef class Coordinates:
    cdef public double x
    cdef public double y

    def __init__(self, double x, double y):
        self.x = x
        self.y = y

    def get_coord(self) -> Tuple[float, float]:
        return self.x, self.y

    def set_coord(self, double x, double y) -> None:
        self.x = x
        self.y = y

    def is_nearby(self, Coordinates other_coord, double tolerance) -> bool:
        return (self.x - tolerance <= other_coord.x <= self.x + tolerance and
                self.y - tolerance <= other_coord.y <= self.y + tolerance)

    def get_distance(self, Coordinates other_coord) -> float:
        # Utilisation de la fonction C hypot pour la distance euclidienne
        return hypot(self.x - other_coord.x, self.y - other_coord.y)

cdef class BaseSprite:
    cdef public str group_name
    cdef Coordinates entity_coord
    cdef public int x, y, width, height
    cdef public bint in_sprite_list

    def __init__(self, app_handler, str group_name, Tuple[int, int] size, Coordinates coordinates = None):
        self.app_handler = app_handler
        self.image = None
        self.rect = None
        if coordinates is None:
            self.entity_coord = Coordinates(0.0, 0.0)
        else:
            self.entity_coord = coordinates
        self.x = 0
        self.y = 0
        self.width, self.height = size
        self.in_sprite_list = False
        if group_name not in app_handler.group_list:
            group_name = "default"
            print("group not found")
        self.group_name = group_name

    def update(self) -> None:
        if self.in_sprite_list:
            self.update_position()

    def get_zoom_offset(self) -> Tuple[int, int]:
        off_x = (S.WIN_W - self.app_handler.width) // 2
        off_y = (S.WIN_H - self.app_handler.height) // 2
        return off_x, off_y

    def update_position(self) -> None:
        screen_x = self.app_handler.screen_x_start
        screen_y = self.app_handler.screen_y_start
        self.x = <int> self.entity_coord.x - screen_x
        self.y = <int> self.entity_coord.y - screen_y
        if self.rect is not None:
            self.rect.center = self.x, self.y

    # Les autres méthodes restent similaires sans changement

