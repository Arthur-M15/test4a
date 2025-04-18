from ..Biome import Biome
from .biome_generator_helper import *


class BottomBiome(Biome):
    def __init__(self, i, biome_order, manager, name):
        self.main_color = end_color = ((100, 100, 120), (80, 80, 70), (30, 10, 10))
        self.next_biome = self

        super().__init__(name, i)
        self.assets = assets_generator(self.main_color, end_color, self.variants_number)
        manager.biome_directory[i] = self
