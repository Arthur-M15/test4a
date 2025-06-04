# test/TestEntity4.py
from __future__ import annotations
import random
import time
from typing import Tuple, TYPE_CHECKING

from PIL import Image as PILImage

from common.biomes import pil_to_sdl2
from common.entities.Entity_mypyc import MovingEntity, Coordinates

if TYPE_CHECKING:
    from App import AppHandler

def rand_c() -> int:
    return random.randint(0, 255)

def randomize_color() -> Tuple[int, int, int, int]:
    return rand_c(), rand_c(), rand_c(), 255

def red_color() -> Tuple[int, int, int, int]:
    return 255, 0, 0, 255

def green_color() -> Tuple[int, int, int, int]:
    return 0, 255, 0, 255

class TestBaseEntity(MovingEntity):
    def __init__(self, app_handler: AppHandler, x: float, y: float):
        self.size: Tuple[int, int] = (30, 30)
        super().__init__(app_handler, self.size, timer_group=1, coordinates=Coordinates(x, y))
        self.counter: int = 0
        self.entity_coord.set(x, y)
        self.time_to_live: int = int(random.expovariate(0.001))
        self.collide_radius: int = 30

    def process(self) -> None:
        multiplier: float = 0.5
        x_rand: float = random.uniform(-10, 10) * multiplier
        y_rand: float = random.uniform(-10, 10) * multiplier
        self.change_speed(x_rand, y_rand)
        super().process()


class TestEntity4(TestBaseEntity):
    def __init__(self, app_handler: AppHandler, x: float, y: float):
        super().__init__(app_handler, x, y)
        green_a = PILImage.new("RGBA", self.size, green_color())
        self.red_image = pil_to_sdl2(app_handler.app.renderer, PILImage.new("RGBA", self.size, red_color()))
        self.green_image = pil_to_sdl2(app_handler.app.renderer, green_a)
        self.load_image(green_a)
        self.is_green = True
        self.process()

    def refresh(self):
        super().refresh()
        nearby_entities = self.app_handler.map.entity_manager.entities.get_nearby_entities(self.coord_grid)
        for entity in nearby_entities:
            if entity.id != self.id:
                if entity.collide_radius + self.collide_radius >= entity.entity_coord.get_distance(self.entity_coord):
                    self.image = self.red_image
                    self.is_green = False
                    return
        self.image = self.green_image
        self.is_green = True

