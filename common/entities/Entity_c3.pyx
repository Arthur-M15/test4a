# cython: language_level=3
import random
from libc.stdlib cimport malloc, free
from argparse import ArgumentError
from libc.math cimport sqrt
from .utils.sprite_helper import *

from common.biomes.properties import pil_to_sdl2

import Settings as S


cdef public struct DoublePair:
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


cdef class IntPairList2:
    cdef int size
    cdef IntPair* lst
    def __cinit__(self, int size):
        self.size = size
        self.lst = <IntPair*>malloc(size*sizeof(IntPair))
    cdef set(self, int key, int x, int y):
        if key < 0 or key >= self.size:
            raise IndexError(f"Index out of bounds: key={key}; size={self.size}")
        cdef IntPair ip
        ip.x, ip.y = x, y
        self.lst[key] = ip

    cdef IntPair get_item(self, int i):
        if i >= self.size or i < 0:
            IndexError(f"Index out of bounds: i={i}; size={self.size}")
        cdef IntPair v
        v = self.lst[i]
        return v

    def __dealloc__(self):
        """
        Liberate the memory used by self.grid when this object dies.
        """
        if self.lst != NULL:
            free(self.lst)
            self.lst = NULL


class PyBaseSprite(BaseSprite):
    """
    BaseSprite interface for python calls
    """
    def __init__(self, app_handler, group_name, x, y, w, h):
        cdef DoublePair coord
        cdef IntPair size
        coord.x = <double>x
        coord.y = <double>y
        size.x = <int>w
        size.y = <int>h
        super().__init__(app_handler, group_name, x, y, w, h)

    def set_coordinates(self, x, y):
        self.coordinates_x = <double>x
        self.coordinates_y = <double>y
        self.update()


cdef class BaseSprite:
    cdef public object app_handler
    cdef public double coordinates_x
    cdef public double coordinates_y
    cdef public int size_x
    cdef public int size_y
    cdef public int x, y
    cdef public object image
    cdef public object rect
    cdef public bint in_sprite_list, keep_image
    cdef public str group_name
    def __init__(self,
                 object app_handler,
                 group_name,
                 double coordinates_x,
                 double coordinates_y,
                 int size_x,
                 int size_y):
        self.app_handler = app_handler
        self.image = None
        self.rect = None
        self.coordinates_x = coordinates_x
        self.coordinates_y = coordinates_y
        self.size_x = size_x
        self.size_y = size_y
        self.x = 0
        self.y = 0
        self.in_sprite_list = False
        self.keep_image = False
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
            self.x = <int>(self.coordinates_x - screen_x_start - (self.size_x//2))
            self.y = <int>(self.coordinates_y - screen_y_start - (self.size_y//2))
            self.rect.center = self.x + (self.size_x // 2), self.y + (self.size_y // 2)


    def load_on_screen(self):
        if self.image is not None and self.rect is not None:
            self.app_handler.group_list.get(self.group_name).add_internal(self)
            self.in_sprite_list = True
        else:
            raise Exception(f"Can't load sprite on screen \n self.rect : {self.rect}\n self.image : {self.image}")

    def unload_from_screen(self):
        if self.in_sprite_list:
            self.in_sprite_list = False
            self.app_handler.group_list.get(self.group_name).spritedict.pop(self, None)
            if not self.keep_image:
                self.image = None
                self.rect = None

    def load_image(self, pil_image):
        self.image = pil_to_sdl2(self.app_handler.app.renderer, pil_image)
        self.rect = self.image.get_rect()
        self.load_on_screen()

    def change_image(self, new_image):
        pass
        #self.image = pil_to_sdl2(self.app_handler.app.renderer, new_image)
        #self.rect = self.image.get_rect()


cdef class StaticEntity(BaseSprite):
    cdef public EntityManager entity_manager
    cdef public int timer_group
    cdef public int radius
    cdef public list sub_process_list
    cdef public int id
    cdef public int counter
    cdef public bint is_giant
    cdef public list collide_list
    cdef public list link_id_list
    cdef public int bank_image_id
    cdef public int image_id

    #need to free:
    cdef IntPairList2 grid

    #global env. variables:
    cdef int SPRITE_MARGIN
    def __init__(self,
                 object app_handler,
                 str group_name,
                 double coordinates_x,
                 double coordinates_y,
                 int size_x,
                 int size_y,
                 EntityManager entity_manager,
                 int radius,
                 int timer_group = 1):
        super().__init__(app_handler, group_name, coordinates_x, coordinates_y, size_x, size_y)
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
        self.grid = self.entity_manager.get_grid_occupation(self.coordinates_x, self.coordinates_y, self.radius)

        #default value; must be reset after super()
        self.image_id = 0
        self.bank_image_id = 0

        #global env. variables:
        self.SPRITE_MARGIN = S.SPRITE_MARGIN

    cdef bint pos_is_on_screen(self):
        cdef int x_s = self.entity_manager.window_dimensions.x_start
        cdef int y_s = self.entity_manager.window_dimensions.y_start
        cdef int x_e
        cdef int y_e
        if (self.coordinates_x + self.size_x + self.SPRITE_MARGIN >= x_s and
                self.coordinates_y + self.size_y + self.SPRITE_MARGIN >= y_s):
            x_e = self.entity_manager.window_dimensions.x_end
            y_e = self.entity_manager.window_dimensions.y_end
            if (self.coordinates_x - self.SPRITE_MARGIN <= x_e and
                    self.coordinates_y - self.SPRITE_MARGIN <= y_e):
                return True
        return False

    cdef void refresh(self):
        """
        code executed on each tick
        """
        self.counter += 1
        if self.in_sprite_list and not self.pos_is_on_screen():
            self.unload_from_screen()
        elif not self.in_sprite_list and self.pos_is_on_screen():
            if self.image is None or self.rect is None:
                image_list = self.entity_manager.image_bank[self.bank_image_id]
                self.load_image(image_list[self.image_id])
            self.load_on_screen()

    cdef void process(self):
        """
        code executed with timer group
        """
        pass


cdef class MovingEntity(StaticEntity):
    cdef public double x_speed
    cdef public double y_speed
    cdef public int dynamic_grid_x
    cdef public int dynamic_grid_y
    cdef public int giant_grid_x
    cdef public int giant_grid_y
    def __init__(self,
                 object app_handler,
                 str group_name,
                 double coordinates_x,
                 double coordinates_y,
                 int size_x,
                 int size_y,
                 EntityManager entity_manager,
                 int radius,
                 int timer_group = 1):
        super().__init__(app_handler, group_name, coordinates_x, coordinates_y, size_x, size_y, entity_manager, radius, timer_group)
        self.x_speed = 0.0
        self.y_speed = 0.0
        cdef IntPair dynamic_grid = self.entity_manager.get_grid(self.coordinates_x, self.coordinates_y)
        self.dynamic_grid_x = dynamic_grid.x
        self.dynamic_grid_y = dynamic_grid.y
        cdef IntPair giant_grid = self.entity_manager.get_giant_grid(self.coordinates_x, self.coordinates_y)
        self.giant_grid_x = giant_grid.x
        self.giant_grid_y = giant_grid.y

    cdef void set_speed(self, double x_speed, double y_speed):
        self.x_speed = x_speed
        self.y_speed = y_speed

    cdef void add_speed(self, double x_speed, double y_speed):
        self.x_speed += x_speed
        self.y_speed += y_speed

    cdef void refresh(self):
        self.coordinates_x += self.x_speed
        self.coordinates_y += self.y_speed
        self.entity_manager.update_grid(self)
        StaticEntity.refresh(self)


cdef class EntityManager:
    cdef public object app_handler
    cdef public IntQuatuor window_dimensions
    cdef public int frame_counter
    cdef public int entity_id_counter
    cdef public dict entity_with_id
    cdef public dict entity_list_timed_at
    cdef public dict[int, dict[int, list[StaticEntity]]] entity_at
    cdef public dict[int, dict[int, list[MovingEntity]]] moving_entity_at
    cdef public dict[int, dict[int, list[MovingEntity]]] giant_at
    cdef public dict[int, list[object]] image_bank

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
        self.image_bank = create_sprite_bank()

        #global env. variables:
        self.GRID_SIZE = S.GRID_SIZE
        self.GIANT_GRID_SIZE_FACTOR = S.GIANT_GRID_SIZE_FACTOR
        self.GIANT_GRID = self.GRID_SIZE * self.GIANT_GRID_SIZE_FACTOR


    cpdef void add(self, StaticEntity entity):
        cdef MovingEntity m_entity
        cdef IntPair zone, grid_coord, giant_coord
        if self.entity_with_id.get(entity.id) is None:
            self.entity_with_id[entity.id] = entity
            self.entity_list_timed_at.setdefault(entity.timer_group, []).append(entity)
            if MovingEntity in type(entity).mro():
                m_entity = <MovingEntity>entity
                grid_coord.x = m_entity.dynamic_grid_x
                grid_coord.y = m_entity.dynamic_grid_y
                if m_entity.is_giant:
                    self.giant_at.setdefault(m_entity.giant_grid_x, {}).setdefault(m_entity.giant_grid_y, []).append(m_entity)
                self.entity_at.setdefault(grid_coord.x, {}).setdefault(grid_coord.y, []).append(entity)
                self.moving_entity_at.setdefault(grid_coord.x, {}).setdefault(grid_coord.y, []).append(entity)
            else:
                for i in range(entity.grid.size):
                    zone = entity.grid.get_item(i)
                    self.entity_at.setdefault(zone.x, {}).setdefault(zone.y, []).append(entity)
        else:
            raise ArgumentError("this entity already exists")

    cpdef void remove(self, StaticEntity entity):
        cdef IntPair zone
        cdef IntPair grid_coord
        cdef MovingEntity m_entity
        if self.entity_with_id.get(entity.id) is not None:
            del self.entity_with_id[entity.id]
            self.entity_list_timed_at[entity.timer_group].remove(entity)

            if MovingEntity in type(entity).mro():
                m_entity = <MovingEntity>entity
                if m_entity.is_giant:
                    self.giant_at[m_entity.giant_grid_x][m_entity.giant_grid_y].remove(entity)
                self.entity_at[m_entity.dynamic_grid_x][m_entity.dynamic_grid_y].remove(entity)
                self.moving_entity_at[grid_coord.x][grid_coord.y].remove(entity)
            else:
                for i in range(entity.grid.size):
                    zone = entity.grid.get_item(i)
                    self.entity_at[zone.x][zone.y].remove(entity)
        else:
            raise ArgumentError("this entity already exists")

    cpdef void update_grid(self, MovingEntity entity):
        cdef IntPair new_grid_coord = self.get_grid(entity.coordinates_x, entity.coordinates_y)
        cdef IntPair new_giant_grid
        if entity.dynamic_grid_x != new_grid_coord.x or entity.dynamic_grid_y != new_grid_coord.y:
            self.entity_at[entity.dynamic_grid_x][entity.dynamic_grid_y].remove(entity)
            self.entity_at.setdefault(new_grid_coord.x, {}).setdefault(new_grid_coord.y, []).append(entity)

            self.moving_entity_at[entity.dynamic_grid_x][entity.dynamic_grid_y].remove(entity)
            if not self.moving_entity_at[entity.dynamic_grid_x]:
                del self.moving_entity_at[entity.dynamic_grid_x]
            elif not self.moving_entity_at[entity.dynamic_grid_x][entity.dynamic_grid_y]:
                del self.moving_entity_at[entity.dynamic_grid_x][entity.dynamic_grid_y]

            if not self.entity_at[entity.dynamic_grid_x]:
                del self.entity_at[entity.dynamic_grid_x]
            elif not self.entity_at[entity.dynamic_grid_x][entity.dynamic_grid_y]:
                del self.entity_at[entity.dynamic_grid_x][entity.dynamic_grid_y]

            self.moving_entity_at.setdefault(new_grid_coord.x, {}).setdefault(new_grid_coord.y, []).append(entity)
            entity.dynamic_grid_x = new_grid_coord.x
            entity.dynamic_grid_y = new_grid_coord.y

            if entity.is_giant:
                new_giant_grid = self.get_giant_grid(entity.coordinates_x, entity.coordinates_y)
                if new_giant_grid.x != entity.giant_grid_x or new_giant_grid.y != entity.giant_grid_y:
                    self.giant_at[entity.giant_grid_x][entity.giant_grid_y].remove(entity)
                    self.giant_at.setdefault(new_giant_grid.x, {}).setdefault(new_giant_grid.y, []).append(entity)

                    if not self.giant_at[entity.giant_grid_x]:
                        del self.giant_at[entity.giant_grid_x]
                    elif not self.giant_at[entity.giant_grid_x][entity.giant_grid_y]:
                        del self.giant_at[entity.giant_grid_x][entity.giant_grid_y]
                    entity.giant_grid_x = new_giant_grid.x
                    entity.giant_grid_y = new_giant_grid.y


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
        self.window_dimensions = self.get_window_dimensions()
        self.process_entities()
        self.collide_elements()

    cdef int get_new_id(self):
        self.entity_id_counter += 1
        return self.entity_id_counter

    cdef IntPairList2 get_grid_occupation(self, double coordinates_x, double coordinates_y, int radius, int grid_size=-1):
        """
        Lists the grid coordinates the entity is on.
        :return: List[IntPair]
        """
        if grid_size == -1:
            grid_size = self.GRID_SIZE
        cdef int x_min = <int>((coordinates_x - radius)   // self.GRID_SIZE)
        cdef int x_max = <int>((coordinates_x + radius-1) // self.GRID_SIZE)
        cdef int y_min = <int>((coordinates_y - radius)   // self.GRID_SIZE)
        cdef int y_max = <int>((coordinates_y + radius-1) // self.GRID_SIZE)

        cdef IntPairList2 zones
        cdef int size = (x_max+1 - x_min) * (y_max+1 - y_min)
        zones = IntPairList2(size)

        cdef int i, j
        cdef int counter = 0
        for i in range(x_min, x_max+1):
            for j in range(y_min, y_max+1):
                zones.set(counter, i, j)
                counter += 1
        if zones.lst == NULL:
            raise MemoryError()
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

    cdef IntPair get_grid(self, double coordinates_x, double coordinates_y):
        """
        Calculates the coordinates for grid
        :param coordinates_x: coordinates of the entity on x
        :param coordinates_y: coordinates of the entity on y
        :return: IntPair
        """
        cdef IntPair grid_coordinates
        grid_coordinates.x = <int>(coordinates_x // self.GRID_SIZE)
        grid_coordinates.y = <int>(coordinates_y // self.GRID_SIZE)
        return grid_coordinates

    cdef IntPair get_giant_grid(self, double coordinates_x, double coordinates_y):
        """
        Calculates the coordinates for the giant grid
        :return: 
        """
        cdef IntPair giant_grid
        giant_grid.x = <int>(coordinates_x // self.GIANT_GRID)
        giant_grid.y = <int>(coordinates_y // self.GIANT_GRID)
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
        cdef int counter, i
        cdef IntPair zone
        cdef IntPairList2 zone_list
        cdef list e_list
        cdef list neighbor_static_zones
        for y_dict in self.moving_entity_at.values():
            for entity_list in y_dict.values():
                temp_entity_list = entity_list[:]
                neighbor_static_zones = [[] for _ in range(9)]

                while len(temp_entity_list) > 0:
                    m_entity = temp_entity_list.pop(0)
                    if not m_entity.is_giant:
                        ## This code collect the neighbor entities
                        zone_list = self.get_grid_occupation(m_entity.coordinates_x, m_entity.coordinates_y, m_entity.radius)
                        for i in range(zone_list.size):
                            zone = zone_list.get_item(i)
                            zone_hash = quick_cord_hash(zone.x, zone.y)
                            if len(neighbor_static_zones[zone_hash]) > 0:
                                if zone.x != m_entity.dynamic_grid_x and zone.y != m_entity.dynamic_grid_y:
                                    neighbor_entity_list_x = self.entity_at.get(zone.x)
                                    if neighbor_entity_list_x:
                                        neighbor_entity_list = neighbor_entity_list_x.get(zone.y)
                                        if neighbor_entity_list:
                                            neighbor_static_zones[zone_hash] = neighbor_entity_list
                        ##
                        for s_entity in temp_entity_list:
                            if s_entity.id == m_entity.id:
                                continue
                            x_m, y_m = m_entity.coordinates_x, m_entity.coordinates_y
                            x_s, y_s = s_entity.coordinates_x, s_entity.coordinates_y
                            if s_entity.radius + m_entity.radius >= get_distance(x_m, x_s, y_m, y_s):
                                s_entity.collide_list.append(m_entity)
                                m_entity.collide_list.append(s_entity)

                        for e_list in <list>neighbor_static_zones:
                            for s_entity in <list>e_list:
                                add_collision(s_entity, m_entity)
                    else:
                        self.collide_giant(m_entity, False)
                        self.collide_giant(m_entity, True)

    cdef void collide_giant(self, m_entity, with_giant):
        cdef int x, y, coord_x, coord_y, grid_size, add_grid_size
        cdef dict type_entities_dict, t_e_d_x
        cdef double xa, xb, ya, yb
        cdef IntPairList2 grid_occupation
        cdef IntPair coord

        if with_giant:
            type_entities_dict = self.giant_at
            grid_size = self.GIANT_GRID
            add_grid_size = 0
        else:
            type_entities_dict = self.entity_at
            grid_size = self.GRID_SIZE
            add_grid_size = self.GRID_SIZE // 2

        entity_list = []
        xb, yb = m_entity.coordinates_x, m_entity.coordinates_y
        grid_occupation = self.get_grid_occupation(xb, yb, m_entity.radius + add_grid_size, grid_size)
        for i in range(grid_occupation.size):
            coord = grid_occupation.get_item(i)
            t_e_d_x = type_entities_dict.get(coord.x)
            if t_e_d_x:
                t_e_d_y = t_e_d_x.get(coord.y)
                if t_e_d_y:
                    entity_list.extend(t_e_d_y)

        for s_entity in entity_list:
            add_collision(s_entity, m_entity)


cdef void add_collision(StaticEntity s_entity, MovingEntity m_entity):
    if s_entity.id == m_entity.id: return
    x_m, y_m = m_entity.coordinates_x, m_entity.coordinates_y
    x_s, y_s = s_entity.coordinates_x, s_entity.coordinates_y
    s_entity.app_handler.logger.default_message = str([x_m, x_s, y_m, y_s])
    if s_entity.radius + m_entity.radius >= get_distance(x_m, x_s, y_m, y_s):
        if s_entity not in m_entity.collide_list:
            m_entity.collide_list.append(s_entity)
        if m_entity not in s_entity.collide_list:
            s_entity.collide_list.append(m_entity)



cdef inline int get_distance(double xa, double xb, double ya, double yb):
    """
    Calculates the distance between two 2D points.
        :param xa: Re(a)
        :param xb: Re(b)
        :param ya: Im(a)
        :param yb: Im(b)
        :return: integer of the distance
    """
    cdef double delta_x = xb - xa
    cdef double delta_y = yb - ya
    return <int>sqrt((delta_x * delta_x) + (delta_y * delta_y))


cdef inline int quick_cord_hash(int x, int y, int size=3):
    """
    Function that returns a hash according to its coordinates and hash size.
    :param x: coordinates of the object on x
    :param y: coordinates of the object on y
    :param size: Must be odd and >= 3
    :return: quick hash based on size^2 number of possibilities
    """
    x_a, y_a = x % size, y % size
    return (size * x_a) + y_a


cdef class TestEntity(MovingEntity):
    cdef public bint is_moving
    def __init__(self,
                 object app_handler,
                 EntityManager entity_manager,
                 coord_x, coord_y,
                 str group_name = "default",
                 int radius = 10,
                 int timer_group=1200,
                 is_moving=False):
        distance = 10000
        super().__init__(app_handler, group_name, coord_x, coord_y, 20, 20, entity_manager, radius, timer_group)
        self.timer_group = timer_group
        self.is_moving = <bint>is_moving
        self.process()

    def process(self):
        if not self.is_moving:
            return
        self.x_speed += random.uniform(-1, 1)
        self.y_speed += random.uniform(-1, 1)#"""

    def refresh(self):
        if len(self.collide_list) > 0:
            if self.image_id == 0:
                self.image_id = 1
                image = self.entity_manager.image_bank[self.bank_image_id][self.image_id]
                self.load_image(image)
        else:
            if self.image_id == 1:
                self.image_id = 0
                image = self.entity_manager.image_bank[self.bank_image_id][self.image_id]
                self.load_image(image)

        MovingEntity.refresh(self)
        self.collide_list.clear()


cdef class TestEntity2(TestEntity):
    def __init__(self, object app_handler,
                 EntityManager entity_manager,
                 coord_x, coord_y,
                 str group_name = "default",
                 int radius = 400,
                 int timer_group=1200,
                 is_moving=False):
        super().__init__( app_handler,
                  entity_manager,
                 coord_x, coord_y,
                  group_name,
                  radius,
                  timer_group,
                 is_moving)
        self.size_x, self.size_y = 2 * radius, 2 * radius
        self.bank_image_id = 1


cdef class TestEntity3(TestEntity2):
    def __init__(self, object app_handler,
                 EntityManager entity_manager,
                 coord_x, coord_y,
                 str group_name = "default",
                 int radius = 400,
                 int timer_group=1200,
                 is_moving=False):
        super().__init__( app_handler,
                  entity_manager,
                 coord_x, coord_y,
                  group_name,
                  radius,
                  timer_group,
                 is_moving)
        print(f"{self.is_giant} - m")

    def refresh(self):
        self.coordinates_x = self.app_handler.mouse_x
        self.coordinates_y = self.app_handler.mouse_y
        TestEntity.refresh(self)
