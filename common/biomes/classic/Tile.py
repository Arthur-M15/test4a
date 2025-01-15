
from ..Super import SuperTile


# Classic biome
class Tile(SuperTile):
    def __init__(self, app_handler, x, y, height):
        super().__init__(app_handler, x, y, height, "classic")
