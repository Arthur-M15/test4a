import math

from MapHandler import *
from typing import Any, Dict, Optional
from common.biomes.BiomeManager import *
from common.entities.Entity_c import EntityManager2
from common.biomes.Chunk_c import Chunk


class Map:
    def __init__(self, app_handler, seed=0, height=100):
        self.app_handler = app_handler
        self.chunks = {}
        self.entity_manager = EntityManager2(self.app_handler)
        self.seed = seed

        #normalized offset is on height=100
        self.total_height = height
        self.biome_manager = BiomeManager(self, SEED) # assets, frontiers_shape_list, app_handler
        self.manager = MapManager(self)

    def get_neighbor_chunks(self, coordinates) -> Optional[Dict[str, Optional[Dict[str, Any]]]]:
        neighbor_chunk = {}
        if self.chunks.get(coordinates) is None:
            x = coordinates[0]
            y = coordinates[1]
            # Gathering neighbor chunks information
            if self.chunks.get((x, y - 1)):
                neighbor_chunk["top"] = self.chunks.get((x, y - 1)).get_information()
            else:
                neighbor_chunk["top"] = None

            if self.chunks.get((x, y + 1)):
                neighbor_chunk["bottom"] = self.chunks.get((x, y + 1)).get_information()
            else:
                neighbor_chunk["bottom"] = None

            if self.chunks.get((x - 1, y)):
                neighbor_chunk["left"] = self.chunks.get((x - 1, y)).get_information()
            else:
                neighbor_chunk["left"] = None

            if self.chunks.get((x + 1, y)):
                neighbor_chunk["right"] = self.chunks.get((x + 1, y)).get_information()
            else:
                neighbor_chunk["right"] = None
        return neighbor_chunk

    def get_chunk(self, coordinates):
        self.set_chunk(coordinates)
        return self.chunks.get(coordinates)

    def set_chunk(self, coordinates):
        if self.chunks.get(coordinates) is None:
            x, y = coordinates
            biome = self.biome_manager.get_biome(x, y)
            neighbor_chunks = self.get_neighbor_chunks(coordinates)
            self.chunks[coordinates] = Chunk(self.app_handler, coordinates, biome, neighbor_chunks)

    def __len__(self):
        return len(self.chunks)


