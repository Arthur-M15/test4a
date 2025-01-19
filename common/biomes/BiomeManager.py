import os
import random
from Settings import *
from common.biomes.properties import *
from properties.biome_generator_helper import *

class Tile:
    def __init__(self, app_handler, x, y, height, biome_name, color):
        self.app_handler = app_handler
        self.x, self.y = x, y
        self.image = None
        self.fetch_tile_image(height, biome_name)
        self.type = "tile"
        self.max_size = TILE_SIZE
        self.color = (color[0], color[1], color[2])


    def fetch_tile_image(self, height, biome_name):
        """
        Loads the tile image based on the height value.
        :param app_handler: Application handler for accessing the renderer.
        :param height: Height of the tile (between -1 and 1).
        :param biome_name: name of the biome. ex: "classic"
        :return: An instance of the loaded image.
        """
        # Normaliser la hauteur entre 1 et 30
        height_index = max(1, min(30, int((height + 1) / 0.0666667) + 1))  # -1 à 1 -> 1 à 30
        self.image = self.app_handler.get_sprite("biomes" ,biome_name, f"tile_color_{height_index}.png")


def load_tile_image(app):
    biome_dict = {}
    base_dir = os.path.dirname(os.path.abspath(__file__))

    for root, dirs, files in os.walk(base_dir):

        if os.path.basename(root) == "sprites":
            images = {
                file: Image(Texture.from_surface(app.renderer, pg.image.load(os.path.join(root, file))))
                for file in files if file.endswith(".png")}
            if images:
                common_type_name = os.path.basename(os.path.dirname(root))
                biome_dict[common_type_name] = images

    return biome_dict



class BiomeManager:
    def __init__(self, map, seed, min_y, max_y):
        self.map = map
        self.seed = seed
        self.max_y = max_y
        self.min_y = min_y

        self.biome_offset = BiomeOffsetList(seed)
        self.biome_directory = {}

        biome_order = [
            "TopBiome",
            "ClassicBiome",
            "TestBiome",
            "BottomBiome"
        ]
        TopBiome(0, biome_order, self, biome_order[0])

        self.dominance_matrix_set = generate_dominance_matrix_dict(CHUNK_SIZE)


    def get_biome(self, x, y):
        relative_y = self.biome_offset.get_offset(x) + y
        total = self.max_y - self.min_y
        relative_pos = relative_y - self.min_y
        biome_index = relative_pos / total

        if biome_index >= 1: return  list(self.biome_directory.items())[-1]
        elif biome_index < 0: return list(self.biome_directory.items())[0]

        biome_index = int(biome_index * len(self.biome_directory))
        return self.biome_directory.get(biome_index)


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
                value = start_value + (((target_value - start_value) * i)/BIOME_OFFSET_VARIATION)
                new_zone.append(value)
            self.__get_zone(x).extend(new_zone)

        return self.__get_zone(x)[abs(x)]


    def __get_zone(self, x):
        if x >= 0:
            self.seed_multiplier = 1
            return self.positive_zone
        else:
            self.seed_multiplier = 2
            return self.negative_zone

