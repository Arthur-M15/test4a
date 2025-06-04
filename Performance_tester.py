import time
import random

import App
from Settings import GRID_SIZE
from common.entities.Entity import Entity, EntityManager2, Coordinates, MovingEntity


class Tester:
    def __init__(self):
        self.app = App.App()
        self.app_handler = App.AppHandler(self.app)
        self.entity_manager = EntityManager2(self.app_handler)
        self.app_handler.update_zone()
        self.size = (30, 30)
        self.entity = Entity(self.app_handler, self.size)

    def __clean(self):
        es = self.entity_manager.entities.get_entities()
        for e in es:
            self.entity_manager.entities.remove_item(e.id)

    def pos_is_on_screen_tester(self):
        t = time.time()
        for i in range(1000):
            self.entity.entity_coord.set(random.randint(-1000, 1000), random.randint(-1000, 1000))
            self.entity.pos_is_on_screen()
        result = time.time() - t
        print(f"pos_is_on_screen: {result} seconds")

    def update_coord_group_tester(self):
        for i in range(100):
            for j in range(100):
                self.app_handler.map.entity_manager.add(MovingEntity(self.app_handler, self.size, Coordinates(i*GRID_SIZE, j*GRID_SIZE)))
        t = time.time()
        for i, e in enumerate(self.entity_manager.entities.fetch_entities()):
            e.update_grid_zone()
            print(i)
        result = time.time() - t
        print(f"update_coord_group_tester: {result} seconds")

    def distance_tester(self):
        entity = self.entity
        b = Entity(self.app_handler, self.size)
        t = time.time()
        for i in range(10000):
            a = entity.collide_radius + b.collide_radius >= entity.entity_coord.get_distance(b.entity_coord)
        result = time.time() - t
        print(result)

    def get_nearby_entities_tester(self):
        self.__clean()
        [self.entity_manager.entities.add_item(0, i, MovingEntity(self.app_handler, self.size, coordinates=Coordinates(0, 0))) for i in range(1000)]
        t = time.time()
        a = []
        for _ in range(1000):
            a = self.entity_manager.entities.get_nearby_entities((0, 0))
        print(f"{(time.time() - t)*1000} ms")
        print(len(a))

    def pos_is_on_screen_tester(self):
        t = time.time()
        e = MovingEntity(self.app_handler, self.size, Coordinates(0, 0))
        for i in range(1000):
            b = e.pos_is_on_screen()
        print(f"{(time.time() - t)*1000} ms")

tester = Tester()
#tester.pos_is_on_screen_tester()
#tester.update_coord_group_tester()
#tester.distance_tester()
#tester.get_nearby_entities_tester()
tester.pos_is_on_screen_tester()


