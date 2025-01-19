from ..Biome import Biome
from .biome_generator_helper import *
from ..properties import *


class TestBiome(Biome):
    def __init__(self, i, biome_order, manager, name):
        self.main_color = ((100, 100, 100), (200, 200, 200), (250, 250, 250))

        super().__init__(name)
        next_biome_name = biome_order[i+1]
        if i + 1 >= len(biome_order):
            self.next_biome = None
        else:
            pre_instance = globals()[next_biome_name]
            self.next_biome = pre_instance(i + 1, biome_order, manager, next_biome_name)
        manager.biome_directory[i] = self

        self.assets = assets_generator(self.main_color, self.next_biome.main_color, self.variants_number)