import os
import random
from Settings import *
from common.biomes.properties import *
from common.biomes.properties.biome_generator_helper import *


class BiomeManager:
    def __init__(self, map, seed):
        self.map = map
        self.seed = seed

        self.biome_offset = BiomeOffsetList(seed)
        self.biome_directory = {}
        self.tiles_assets = self.fetch_tiles_assets()

        biome_order = [
            "TopBiome",
            "ClassicBiome",
            "TestBiome",
            "BottomBiome"
        ]
        TopBiome(0, biome_order, self, biome_order[0])
        self.dominance_matrix_index = generate_dominance_matrix_dict(CHUNK_SIZE, VARIANTS_NUMBER)

    def get_biome(self, x, y):
        number_of_biomes = len(self.biome_directory)
        y_ref = y - TOP_BIOME_Y
        biome_index = int((self.biome_offset.get_offset(x) + y_ref)//BIOME_OFFSET_HEIGHT)

        if biome_index >= len(self.biome_directory):
            return  self.biome_directory.get(number_of_biomes-1)
        elif biome_index < 0:
            return self.biome_directory.get(0)

        return self.biome_directory.get(biome_index)

    def fetch_tiles_assets(self):
        assets_list = []
        for key, assets in self.biome_directory.items():
            assets_list[key] = assets
        return assets_list


class BiomeOffsetList:
    def __init__(self, seed=0):
        self.positive_zone = []
        self.negative_zone = []
        self.seed = seed
        self.seed_multiplier = 1


    def get_offset(self, x):
        while abs(x) >= len(self.__get_zone(x)):
            if len(self.__get_zone(x)) == 0:
                start_value = 0
            else:
                start_value = self.__get_zone(x)[-1]
            random.seed(len(self.__get_zone(x)) + ((self.seed + 1) * self.seed_multiplier))
            target_value = random.gauss(start_value, BIOME_OFFSET_VARIATION)
            new_zone = []
            for i in range(1, BIOME_OFFSET_WIDTH + 1):
                value = start_value + (((target_value - start_value) * i)/BIOME_OFFSET_WIDTH)
                new_zone.append(int(value))
            self.__get_zone(x).extend(new_zone)

        return self.__get_zone(x)[abs(x)]


    def __get_zone(self, x):
        if x >= 0:
            self.seed_multiplier = 1
            return self.positive_zone
        else:
            self.seed_multiplier = 2
            return self.negative_zone

