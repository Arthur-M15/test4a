import os
from Settings import *

# Classic biome
class Tile:
    def __init__(self, app_handler, x, y, height, biome_index=1):
        self.x, self.y = x, y
        self.image = load_tile_image(app_handler, height)
        self.type = "tile"


def load_tile_image(app_handler, height):
    """
    Loads the tile image based on the height value.
    :param app_handler: Application handler for accessing the renderer.
    :param height: Height of the tile (between -1 and 1).
    :return: An instance of the loaded image.
    """
    # Normaliser la hauteur entre 1 et 30
    height_index = max(1, min(30, int((height + 1) / 0.0666667) + 1))  # -1 à 1 -> 1 à 30
    return app_handler.loaded_sprites["classic"][f"tile_color_{height_index}.png"]

