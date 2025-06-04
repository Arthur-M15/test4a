import random
from PIL import Image as PILImage
from pygame.transform import threshold
from typing_extensions import override

from common.biomes import pil_to_sdl2
from common.entities.Entity import MovingEntity, EntityEvent, Coordinates
import time


class TestBaseEntity(MovingEntity):
    def __init__(self, app_handler, x, y):
        self.size = (30, 30)
        super().__init__(app_handler, self.size, timer_group=1, coordinates=Coordinates(x, y))
        self.counter = 0
        self.entity_coord.set(x, y)
        self.time_to_live = random.expovariate(0.001)
        self.collide_radius = 30

    def process(self):
        multiplier = 0.5
        x_rand = random.uniform(-10, 10) * multiplier
        y_rand = random.uniform(-10, 10) * multiplier
        self.change_speed(x_rand, y_rand)

class TestEntity1(TestBaseEntity):
    def __init__(self, app_handler, x, y):
        super().__init__(app_handler, x, y)
        pil_image = PILImage.new("RGBA", self.size, randomize_color())
        self.load_image(pil_image)

    def process(self):
        self.counter += 1
        if self.counter > 1:
            x_rand = random.uniform(-10, 10)
            y_rand = random.uniform(-10, 10)
            self.change_speed(x_rand, y_rand)
            self.counter = 0


class TestEntity2(TestBaseEntity):
    def __init__(self, app_handler, x, y):
        super().__init__(app_handler, x, y)
        pil_image = PILImage.new("RGBA", self.size, randomize_color())
        #self.load_image(pil_image)
        self.time_to_live = 99999#random.expovariate(0.001)

    def process(self):
        x_rand = random.uniform(-1, 1)
        y_rand = random.uniform(-1, 1)
        self.change_speed(x_rand, y_rand)
        self.time_to_live -= 1
        if self.time_to_live <= 0:
            entity_manager = self.app_handler.map.entity_manager
            return EntityEvent("kill_self", entity_manager, self)
        return None


class TestEntity3(TestBaseEntity):
    def __init__(self, app_handler, x, y):
        super().__init__(app_handler, x, y)
        green_a = PILImage.new("RGBA", self.size, green_color())
        self.red_image = pil_to_sdl2(app_handler.app.renderer, PILImage.new("RGBA", self.size, red_color()))
        self.green_image = pil_to_sdl2(app_handler.app.renderer, green_a)
        self.load_image(green_a)
        self.process()

    @override
    def process(self):
        x_rand = random.uniform(-1, 1)
        y_rand = random.uniform(-1, 1)
        self.change_speed(x_rand, y_rand)
        self.counter = 0

        if self.time_to_live <= 0:
            entity_manager = self.app_handler.map.entity_manager
            return EntityEvent("kill_self", entity_manager, self)

    @override
    def refresh(self):
        super().refresh()

        entity_manager = self.app_handler.map.entity_manager
        t = time.time()
        entity_list = entity_manager.entities.get_nearby_entity(self.entity_coord, 1000)
        #print(time.time() - t)
        for entity_info in entity_list:
            if entity_info[0] != self.id:
                if entity_info[1][2] + self.collide_radius >= entity_info[1][0].get_distance(self.entity_coord):
                    self.image = self.red_image
                    return
        self.image = self.green_image

class TestEntity4(TestBaseEntity):
    def __init__(self, app_handler, x, y):
        super().__init__(app_handler, x, y)
        green_a = PILImage.new("RGBA", self.size, green_color())
        self.red_image = pil_to_sdl2(app_handler.app.renderer, PILImage.new("RGBA", self.size, red_color()))
        self.green_image = pil_to_sdl2(app_handler.app.renderer, green_a)
        self.load_image(green_a)
        self.is_green = True
        self.process()

    def refresh(self):
        t = time.time()
        super().refresh()
        t2 = time.time()
        nearby_entities = self.app_handler.map.entity_manager.entities.get_nearby_entities(self.coord_grid)
        t3 = time.time()
        for entity in nearby_entities:
            if entity.id != self.id:
                t5 = time.time()
                if entity.collide_radius + self.collide_radius >= entity.entity_coord.get_distance(self.entity_coord):
                    self.image = self.red_image
                    self.is_green = False
                    z = time.time() - t
                    return
                e = time.time() - t5
                if e > 0.0:
                    pass
        t4 = time.time()
        self.image = self.green_image
        self.is_green = True
        a = self.app_handler.logger.function_delay = time.time() - t
        b = time.time() - t2
        c = time.time() - t3
        d = time.time() - t4
        pass


def randomize_color():
    return tuple(random.randint(0, 255) for _ in range(3)) + (255,)

def red_color():
    return 255, 0, 0, 255

def green_color():
    return 0, 255, 0, 255