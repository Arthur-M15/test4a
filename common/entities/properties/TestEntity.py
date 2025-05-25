import random
from PIL import Image as PILImage

from common.entities.Entity import MovingEntity


class TestEntity(MovingEntity):
    def __init__(self, app_handler, x, y):
        size = (30, 30)
        super().__init__(app_handler, size, timer_group=10)
        self.counter = 0
        self.entity_x = x
        self.entity_y = y
        pil_image = PILImage.new("RGBA", size, (250, 50, 50, 255))
        self.load_image(pil_image)

    def process(self):
        self.entity_x += self.x_speed
        self.entity_y += self.y_speed
        self.counter += 1
        if self.counter > 1:
            x_rand = random.uniform(-10, 10)
            y_rand = random.uniform(-10, 10)
            self.change_speed(x_rand, y_rand)
            self.counter = 0


