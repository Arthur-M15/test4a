
import pygame as pg
import pygame.freetype as ft
from pygame._sdl2.video import Window, Renderer, Texture, Image as Pyimage

from random import randrange, uniform

# Paths
BIOME_SPRITE_DIR_PATH: str = "common/biomes"
FONTS_DIR_PATH: str = "assets/fonts"

# Screen size
WIN_W: int
WIN_H: int
WIN_SIZE: tuple[int, int]

# Choose a resolution
WIN_SIZE = WIN_W, WIN_H = 1000, 1000
# WIN_SIZE = WIN_W, WIN_H = 1600, 900
# WIN_SIZE = WIN_W, WIN_H = 1920, 1080

# Font
FONT_SIZE: int = 14

# FPS
MAX_FPS: int = 0
FPS_LIST_SIZE: int = 30

# Map & Terrain
BASE_SPEED: float = 1.0
CHUNK_SIZE: int = 12
CHUNK_LOAD_DISTANCE: int = 20
TILE_PIXEL_SIZE: int = 56
CHUNK_VARIATIONS: float = 0.05
HARMONIC_NUMBER: int = 5
TOTAL_WIDTH: int = CHUNK_SIZE * TILE_PIXEL_SIZE * CHUNK_LOAD_DISTANCE
CHUNK_PIXEL_WIDTH: int = CHUNK_SIZE * TILE_PIXEL_SIZE

# Biome config
BIOME_OFFSET_VARIATION: int = 10
BIOME_OFFSET_WIDTH: int = 50
TILE_HEIGHT_SATURATION: int = 5

# Generation
SEED: int = 0
TOP_BIOME_Y: int = -10
BIOME_OFFSET_HEIGHT: int = 5
VARIANTS_NUMBER: int = 8

# Threads
CHUNK_THREAD_NUMBER: int = 1

# Grid / Entity
GRID_SIZE: int = 20
SPRITE_MARGIN: int = 50
MAX_LOCAL_COUNTER: int = 10

# Environment config
ENVIRONMENT: int = 0  # 0 = Default, 12 = TILESGEN, 10 = TEST_SERIAL, 11 = TEST, 20 = BETA, 30 = PROD

if ENVIRONMENT == 12:
    TILE_PIXEL_SIZE = 20
    CHUNK_SIZE = 6
    VARIANTS_NUMBER = 20
    CHUNK_LOAD_DISTANCE = 2
    TOTAL_WIDTH = CHUNK_SIZE * TILE_PIXEL_SIZE * CHUNK_LOAD_DISTANCE
    CHUNK_PIXEL_WIDTH = CHUNK_SIZE * TILE_PIXEL_SIZE