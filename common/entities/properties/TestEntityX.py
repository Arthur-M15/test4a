import random
from PIL import Image as PILImage

from common.entities.Entity import MovingEntity, EntityEvent


class TestBaseEntity(MovingEntity):
    def __init__(self, app_handler, x, y):
        self.size = (30, 30)
        super().__init__(app_handler, self.size, timer_group=240)
        self.counter = 0
        self.entity_x = x
        self.entity_y = y

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
        pil_image = PILImage.new("RGBA", self.size, randomize_color())
        self.load_image(pil_image)
        

def randomize_color():
    return tuple(random.randint(0, 255) for _ in range(3)) + (255,)