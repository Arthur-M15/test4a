import os
from Settings import *

class SuperTile:
    def __init__(self, app_handler, x, y, height, biome_name):
        self.app_handler = app_handler
        self.x, self.y = x, y
        self.fetch_tile_image(height, biome_name)
        self.type = "tile"
        self.max_size = TILE_SIZE


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