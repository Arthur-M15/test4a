CYTHON_TRACE = 1

# cython: language_level=3
import random
from argparse import ArgumentError
from libc.math cimport sqrt

from PIL import Image as PILImage
from common.biomes.properties import pil_to_sdl2

import Settings as S

cdef struct DoublePair:
    double x
    double y

cdef struct IntPair:
    int x
    int y

cdef struct IntQuatuor:
    int x_start
    int y_start
    int x_end
    int y_end

cdef class Coordinates:
    cdef public double x
    cdef public double y
    cdef public int width
    cdef public int height

    def __cinit__(self, double x_val=0.0, double y_val=0.0, int width_v=0, int height_v=0):
        self.x = x_val
        self.y = y_val
        self.width = width_v
        self.height = height_v


    cdef double get_distance(self, double x, double y):
        cdef double dx = self.x - x
        cdef double dy = self.y - y
        return sqrt(dx * dx + dy * dy)

    cdef DoublePair get_coordinates(self):
        cdef DoublePair c
        c.x, c.y = self.x, self.y
        return c

    cdef IntPair get_size(self):
        cdef IntPair s
        s.x, s.y = self.width, self.height
        return s


class PyBaseSprite(BaseSprite):
    """
    BaseSprite interface for python calls
    """
    def __init__(self, app_handler, group_name, x, y, w, h):
        xc = <double>x
        yc = <double>y
        wc = <int>w
        hc = <int>h
        c = Coordinates(xc, yc, wc, hc)
        super().__init__(app_handler, group_name, c)

    def set_coordinates(self, x, y):
        self.coordinates.x = <double>x
        self.coordinates.y = <double>y

    def set_size(self, w, h):
        self.coordinates.w = <double>w
        self.coordinates.h = <double>h


cdef class BaseSprite:
    cdef object app_handler
    cdef public Coordinates coordinates
    cdef public double x
    cdef public double y
    def __init__(self,
                 object app_handler,
                 group_name,
                 Coordinates coord):
        self.app_handler = app_handler
        self.image = None
        self.rect = None
        self.coordinates = coord
        self.x = 0.0
        self.y = 0.0
        self.in_sprite_list = False
        if group_name not in app_handler.group_list.keys():
            group_name = "default"
            print("group not found")
        self.group_name = group_name

    def update(self):
        """
        code executed on each tick if is on screen
        """
        cdef int screen_x_start
        cdef int screen_y_start
        cdef IntQuatuor screen_dim
        if self.in_sprite_list:
            screen_dim = self.app_handler.map.entity_manager.window_dimensions
            screen_x_start = screen_dim.x_start
            screen_y_start = screen_dim.y_start
            self.x = <int>(self.coordinates.x - screen_x_start)
            self.y = <int>(self.coordinates.y - screen_y_start)
            self.rect.center = self.x + (self.coordinates.width // 2), self.y + (self.coordinates.height // 2)

    def load_on_screen(self):
        if self.image is not None and self.rect is not None:
            self.app_handler.group_list.get(self.group_name).add_internal(self)
            self.in_sprite_list = True
        else:
            raise Exception(f"Can't load sprite on screen \n self.rect : {self.rect}\n self.image : {self.image}")

    def unload_from_screen(self, keep_image: bool = False):
        if self.in_sprite_list:
            self.in_sprite_list = False
            self.app_handler.group_list.get(self.group_name).spritedict.pop(self, None)
            if not keep_image:
                self.image = None
                self.rect = None

    def load_image(self, pil_image):
        pass
        #image = pil_to_sdl2(self.app_handler.app.renderer, pil_image)
        #self.load_sdl_image(image)

    def load_sdl_image(self, sdl_image):
        self.image = sdl_image
        self.rect = self.image.get_rect()
        self.load_on_screen()

    def change_image(self, new_image):
        pass
        #self.image = pil_to_sdl2(self.app_handler.app.renderer, new_image)
        #self.rect = self.image.get_rect()


cdef class StaticEntity(BaseSprite):
    cdef EntityManager entity_manager
    cdef int timer_group
    cdef int radius
    cdef list sub_process_list
    cdef int id
    cdef int counter
    cdef bint is_giant
    cdef list collide_list
    cdef list link_id_list
    cdef list[IntPair] grid

    #global env. variables:
    cdef int SPRITE_MARGIN
    def __init__(self,
                 object app_handler,
                 str group_name,
                 Coordinates coordinates,
                 EntityManager entity_manager,
                 int radius,
                 int timer_group = 1):
        super().__init__(app_handler, group_name, coordinates)
        self.entity_manager = entity_manager
        self.radius = radius
        self.timer_group = timer_group
        self.sub_process_list = []
        self.id = self.entity_manager.get_new_id()
        self.counter = 0
        if 2*self.radius >= self.entity_manager.GIANT_GRID:
            raise ArgumentError(f"Radius above limit size: {self.radius} >= {self.entity_manager.GIANT_GRID}.")
        self.is_giant = <bint>(2*self.radius >= S.GRID_SIZE)
        self.collide_list = []
        a  = self.entity_manager.get_grid_occupation(self.coordinates, self.radius)
        self.grid = <list[IntPair]>self.entity_manager.get_grid_occupation(self.coordinates, self.radius)

        #global env. variables:
        self.SPRITE_MARGIN = S.SPRITE_MARGIN

    cdef bint pos_is_on_screen(self):
        cdef int x_s = self.entity_manager.window_dimensions.x_start
        cdef int y_s = self.entity_manager.window_dimensions.y_start
        cdef int x_e
        cdef int y_e
        if (self.coordinates.x + self.coordinates.width + self.SPRITE_MARGIN >= x_s and
                self.coordinates.y + self.coordinates.height + self.SPRITE_MARGIN >= y_s):
            x_e = self.entity_manager.window_dimensions.x_end
            y_e = self.entity_manager.window_dimensions.y_end
            if (self.coordinates.x - self.SPRITE_MARGIN <= x_e and
                    self.coordinates.y - self.SPRITE_MARGIN <= y_e):
                return True
        return False

    cdef void refresh(self):
        """
        code executed on each tick
        """
        self.counter += 1
        if self.in_sprite_list and not self.pos_is_on_screen():
            self.unload_from_screen(keep_image=True)
        elif not self.in_sprite_list and self.pos_is_on_screen():
            self.load_on_screen()

    cdef void process(self):
        """
        code executed with timer group
        """
        pass


cdef class MovingEntity(StaticEntity):
    cdef double x_speed
    cdef double y_speed
    cdef IntPair dynamic_grid
    cdef IntPair giant_grid
    def __init__(self,
                 object app_handler,
                 str group_name,
                 Coordinates coordinates,
                 EntityManager entity_manager,
                 int radius,
                 int timer_group = 1):
        super().__init__(app_handler, group_name, coordinates, entity_manager, radius, timer_group)
        self.grid = []
        self.x_speed = 0.0
        self.y_speed = 0.0
        self.dynamic_grid = self.entity_manager.get_grid(self.coordinates)
        self.giant_grid = self.entity_manager.get_giant_grid(self.coordinates, self.is_giant)

    cdef void set_speed(self, double x_speed, double y_speed):
        self.x_speed = x_speed
        self.y_speed = y_speed

    cdef void add_speed(self, double x_speed, double y_speed):
        self.x_speed += x_speed
        self.y_speed += y_speed

    cdef void refresh(self):
        self.coordinates.x += self.x_speed
        self.coordinates.y += self.y_speed
        self.entity_manager.update_grid(self)
        super().refresh()


cdef class EntityManager:
    cdef object app_handler
    cdef public IntQuatuor window_dimensions
    cdef int frame_counter
    cdef int entity_id_counter
    cdef dict entity_with_id
    cdef dict entity_list_timed_at
    cdef dict[int, dict[int, list[StaticEntity]]] entity_at
    cdef dict[int, dict[int, list[MovingEntity]]] moving_entity_at
    cdef dict[int, dict[int, list[MovingEntity]]] giant_at

    #global env. variables:
    cdef int GRID_SIZE
    cdef int GIANT_GRID_SIZE_FACTOR
    cdef int GIANT_GRID
    def __init__(self, app_handler):
        self.app_handler = app_handler
        self.window_dimensions = self.get_window_dimensions()
        self.frame_counter = 0
        self.entity_id_counter = 0
        self.entity_with_id = {}
        self.entity_list_timed_at = {}
        self.entity_at = {}
        self.giant_at = {}
        self.moving_entity_at = {}

        #global env. variables:
        self.GRID_SIZE = S.GRID_SIZE
        self.GIANT_GRID_SIZE_FACTOR = S.GIANT_GRID_SIZE_FACTOR
        self.GIANT_GRID = self.GRID_SIZE * self.GIANT_GRID_SIZE_FACTOR


    cpdef void add(self, StaticEntity entity):
        cdef Coordinates e_c = entity.coordinates
        cdef IntPair zone
        cdef IntPair grid_coord
        if self.entity_with_id[entity.id] is None:
            self.entity_with_id[entity.id] = entity
            self.entity_list_timed_at.setdefault(entity.timer_group, []).append(entity)
            grid_coord = self.get_grid(e_c)

            if MovingEntity in type(entity).mro():
                if entity.is_giant:
                    self.giant_at.setdefault(self.get_giant_grid(e_c, <bint>1), []).append(entity)
                self.entity_at.setdefault(grid_coord.x, {}).setdefault(grid_coord.y, []).append(entity)
                self.moving_entity_at.setdefault(grid_coord.x, {}).setdefault(grid_coord.y, []).append(entity)
            else:
                for zone in <list[IntPair]>entity.grid:
                    self.entity_at.setdefault(zone.x, {}).setdefault(zone.y, []).append(entity)
        else:
            raise ArgumentError("this entity already exists")

    cpdef void remove(self, StaticEntity entity):
        cdef Coordinates e_c = entity.coordinates
        cdef IntPair zone
        cdef IntPair grid_coord
        cdef MovingEntity m_entity
        if self.entity_with_id[entity.id] is not None:
            grid_coord = self.get_grid(e_c)
            del self.entity_with_id[entity.id]
            self.entity_list_timed_at[entity.timer_group].remove(entity)

            if MovingEntity in type(entity).mro():
                m_entity = entity
                if m_entity.is_giant:
                    self.giant_at[m_entity.giant_grid.x][m_entity.giant_grid.y].remove(entity)
                self.entity_at[grid_coord.x][grid_coord.y].remove(entity)
                self.moving_entity_at[grid_coord.x][grid_coord.y].remove(entity)
            else:
                for zone in <list[IntPair]>entity.grid:
                    self.entity_at[zone.x][zone.y].remove(entity)
        else:
            raise ArgumentError("this entity already exists")

    cdef void update_grid(self, MovingEntity entity):
        cdef IntPair new_grid_coord = self.get_grid(entity.coordinates)
        cdef IntPair new_giant_grid
        if entity.dynamic_grid.x != new_grid_coord.x or entity.dynamic_grid.y != new_grid_coord.y:

            self.entity_at[entity.dynamic_grid].remove(entity)
            self.entity_at.setdefault(new_grid_coord, []).append(entity)

            self.moving_entity_at[entity.dynamic_grid].remove(entity)
            if not self.moving_entity_at[entity.dynamic_grid]:
                del self.moving_entity_at[entity.dynamic_grid]
            self.moving_entity_at.setdefault(new_grid_coord, []).append(entity)

            if entity.is_giant:
                new_giant_grid = self.get_giant_grid(entity.coordinates, <bint>1)
                if new_giant_grid.x != entity.giant_grid.x or new_giant_grid.y != entity.giant_grid.y:
                    self.giant_at[entity.giant_grid].remove(entity)
                    if not self.giant_at[entity.giant_grid]:
                        del self.giant_at[entity.giant_grid]
                    self.giant_at[new_giant_grid].append(entity)

    """  
    # - DEFINITION - #
    Process = Entity execute its code everytime his timer is reached
    Refresh = Entity execute a code only for the sprite display (position on screen, etc...)
    Execute = EntityManager execute some code for inter-sprite handling (collision, events, etc...)
    """

    cdef void process_entities(self):
        cdef int modulo
        cdef int phase = 0
        cdef bint need_process
        for modulo, entity_list in self.entity_list_timed_at.items():
            for entity in entity_list:
                entity.refresh()
                phase += 1
                if (self.frame_counter + phase) % modulo == 0:
                    #todo : add event management
                    entity.process()


    def execute(self):
        self.frame_counter += 1
        self.get_window_dimensions()
        self.process_entities()
        self.collide_elements()


    cdef int get_new_id(self):
        self.entity_id_counter += 1
        return self.entity_id_counter

    cdef list get_grid_occupation(self, Coordinates coordinates, int radius, int grid_size=-1):
        """
        Lists the grid coordinates the entity is on.
        :return: List[IntPair]
        """
        if grid_size == -1:
            grid_size = self.GRID_SIZE
        cdef int x_min = <int>((coordinates.x - radius)   // self.GRID_SIZE)
        cdef int x_max = <int>((coordinates.x + radius-1) // self.GRID_SIZE)
        cdef int y_min = <int>((coordinates.y - radius)   // self.GRID_SIZE)
        cdef int y_max = <int>((coordinates.y + radius-1) // self.GRID_SIZE)
        cdef list zones = []
        cdef IntPair zone
        cdef int i, j
        for i in range(x_min, x_max+1):
            for j in range(y_min, y_max+1):
                zone.x, zone.y = i, j
                zones.append(zone)
        return zones

    cdef IntQuatuor get_window_dimensions(self):
        """
        Cast "python<int>" into "cython<int>" of window coordinates
        :return: 
        """
        cdef IntQuatuor dim
        dim.x_start = self.app_handler.screen_x_start
        dim.y_start = self.app_handler.screen_y_start
        dim.x_end = self.app_handler.screen_x_end
        dim.y_end = self.app_handler.screen_y_end
        return dim

    cdef IntPair get_grid(self, Coordinates coordinates):
        """
        Calculates the coordinates for grid
        :param coordinates: coordinates of the entity
        :return: 
        """
        cdef IntPair grid_coordinates
        grid_coordinates.x = <int>(coordinates.x // self.GRID_SIZE)
        grid_coordinates.y = <int>(coordinates.y // self.GRID_SIZE)
        return grid_coordinates

    cdef IntPair get_giant_grid(self, Coordinates coordinates, bint is_giant):
        """
        Calculates the coordinates for the giant grid
        :param coordinates: coordinates of the entity
        :param is_giant: mandatory parameter when creating MovingEntity().
        :return: 
        """
        cdef IntPair giant_grid
        if not is_giant:
            giant_grid.x, giant_grid.y = 0, 0
            return giant_grid
        giant_grid.x = <int> (coordinates.x // self.GIANT_GRID)
        giant_grid.y = <int> (coordinates.y // self.GIANT_GRID)
        return giant_grid

    cdef void collide_elements(self):
        """
        Fetch all the moving entities of the map and append the collision between themselves.
        :return: 
        """
        cdef MovingEntity m_entity
        cdef StaticEntity s_entity
        cdef double x, y
        cdef int coord_x, coord_y
        cdef int counter
        for y_dict in self.moving_entity_at.values():
            for entity_list in y_dict.values():
                temp_entity_list = self.entity_at[x][y][:]

                for m_entity in entity_list:
                    if not m_entity.is_giant:
                        counter = 0
                        while counter < len(temp_entity_list):
                            s_entity = temp_entity_list[counter]
                            if m_entity.id != s_entity.id:
                                x, y = m_entity.coordinates.x, m_entity.coordinates.y
                                if s_entity.radius + m_entity.radius <= s_entity.coordinates.get_distance(x, y):
                                    s_entity.collide_list.append(m_entity)
                                    m_entity.collide_list.append(s_entity)
                                counter += 1
                            else:
                                temp_entity_list.pop(counter)
                    else: # Giant case...
                        self.collide_giant(m_entity, False)
                        self.collide_giant(m_entity, True)

    cdef void collide_giant(self, m_entity, with_giant):
        cdef int x, y, coord_x, coord_y, grid_size, add_grid_size
        cdef list type_entities_list

        if with_giant:
            type_entities_list = self.giant_at
            grid_size = self.GIANT_GRID
            add_grid_size = 0
        else:
            type_entities_list = self.entity_at
            grid_size = self.GRID_SIZE
            add_grid_size = self.GRID_SIZE // 2

        entity_list = []
        x, y = m_entity.coordinates.x, m_entity.coordinates.y
        for coord in <list>self.get_grid_occupation(m_entity.coordinates, m_entity.radius + add_grid_size, grid_size):
            coord_x, coord_y = coord.x, coord.y
            entity_list.extend(type_entities_list[coord_x][coord_y])
        for s_entity in entity_list:
            if s_entity.radius + m_entity.radius <= s_entity.coordinates.get_distance(x, y):
                if s_entity not in m_entity.collide_list:
                    m_entity.collide_list.append(s_entity)
                if m_entity not in s_entity.collide_list:
                    s_entity.collide_list.append(m_entity)


cdef class TestEntity(MovingEntity):

    cdef object app_handler
    cdef str group_name
    cdef Coordinates coordinates
    cdef EntityManager entity_manager
    cdef int radius
    cdef int timer_group
    cdef object red_image
    cdef object green_image
    cdef bint is_green
    def __init__(self,
                 object app_handler,
                 EntityManager entity_manager,
                 str group_name = "default",
                 Coordinates coordinates = Coordinates(0.0, 0.0, 40, 40),
                 int radius = 20,
                 int timer_group=120):
        super().__init__(app_handler, group_name, coordinates, entity_manager, radius, timer_group)
        self.timer_group = 120
        size = (self.coordinates.width, self.coordinates.height)
        red_a = PILImage.new("RGBA", size, red_color())
        green_a = PILImage.new("RGBA", size, green_color())
        self.red_image = pil_to_sdl2(app_handler.app.renderer, red_a)
        self.green_image = pil_to_sdl2(app_handler.app.renderer, green_a)

        self.load_image(self.green_image)
        self.is_green = <bint>1

    def process(self):
        super().process()
        self.x_speed += random.uniform(-10, 10)
        self.y_speed += random.uniform(-10, 10)

    def refresh(self):
        if self.collide_list:
            if self.is_green:
                self.is_green = False
                self.load_sdl_image(self.red_image)
        else:
            self.load_sdl_image(self.green_image)
            self.is_green = True
        super().refresh()
        self.collide_list = []

def red_color():
    return 255, 0, 0, 255

def green_color():
    return 0, 255, 0, 255

