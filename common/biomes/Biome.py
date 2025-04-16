from Settings import *
from common.biomes.properties import *

class Biome:
    def __init__(self, name, index):
        self.name = name
        self.variants_number = VARIANTS_NUMBER
        self.index = index