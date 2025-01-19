
from ..Biome import Tile


# Classic biome
class Tile_deprecated():
    def __init__(self, app_handler, x, y, height):
        super().__init__(app_handler, x, y, height, "classic", self.color)
