from Settings import *
from common.biomes.properties import *

class Biome:
    def __init__(self, name):
        self.name = name
        self.main_color = ((180, 190, 200), (200, 210, 220), (220, 230, 240)) # Default
        self.variants_number = VARIANTS_NUMBER
