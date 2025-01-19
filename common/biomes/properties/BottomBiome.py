from ..Biome import Biome
from .biome_generator_helper import *


class BottomBiome(Biome):
    def __init__(self, i, manager, name):
        end_color = ((0, 0, 0), (0, 0, 0), (0, 0, 0))
        self.main_color = ((100, 100, 100), (200, 200, 200), (250, 250, 250))

        super().__init__(name)

        self.assets = assets_generator(self.main_color, end_color, self.variants_number)
        manager.biome_directory[i] = self
