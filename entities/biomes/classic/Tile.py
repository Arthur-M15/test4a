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
    :param height: Height of the tile (between -2 and 2).
    :return: An instance of the loaded image.
    """
    # Normaliser la hauteur entre 1 et 10
    height_index = max(1, min(10, int((height + 2) / 0.4) + 1))  # -2 à 2 -> 1 à 10
    base_path = os.path.dirname(__file__)  # Directory of the current file
    image_path = os.path.join(base_path, f"tile_color_{height_index}.png")

    return Image(Texture.from_surface(
        app_handler.app.renderer,
        pg.image.load(image_path)
    ))


#todo : modifier le code pour que l'insertion des tiles soient directement insérés au moment de la génération de la matrice
