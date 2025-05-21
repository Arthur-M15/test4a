# Screen.py file
import pathlib
import pygame as pg
import pygame.freetype as ft
import sys
from pygame._sdl2.video import Window, Renderer, Texture, Image as Pyimage
from random import randrange, uniform

#WIN_SIZE = WIN_W, WIN_H = 1600, 900
BIOME_SPRITE_DIR_PATH = 'common/biomes'
FONTS_DIR_PATH = 'assets/fonts'
WIN_SIZE = WIN_W, WIN_H = 1000, 1000
#WIN_SIZE = WIN_W, WIN_H = 1920, 1080
FONT_SIZE = 14

MAX_FPS = 1000
FPS_LIST_SIZE = 10
"""
FONT_SIZE = 40
SPEED = 200
NUM_SPRITES_PER_CLICK = 1
NUM_ANGLES = 180
DEBUG = True
"""

BASE_SPEED = 1
CHUNK_SIZE = 12
CHUNK_LOAD_DISTANCE = 20
TILE_PIXEL_SIZE = 56
CHUNK_VARIATIONS = 0.05
HARMONIC_NUMBER = 5
TOTAL_WIDTH = CHUNK_SIZE * TILE_PIXEL_SIZE * CHUNK_LOAD_DISTANCE
CHUNK_PIXEL_WIDTH = CHUNK_SIZE * TILE_PIXEL_SIZE

BIOME_OFFSET_VARIATION = 10
BIOME_OFFSET_WIDTH = 50
TILE_HEIGHT_SATURATION = 5

SEED = 0
TOP_BIOME_Y = -10
BIOME_OFFSET_HEIGHT = 5
VARIANTS_NUMBER = 8

CHUNK_THREAD_NUMBER = 1

# -------------- #
ENVIRONMENT = 0
# TEST tilesgen 12
# TEST_SERIAL   10    for TEST without threads working in parallel
# TEST          11
# BETA          20     for testing the app in real conditions
# PROD          30
# -------------- #

if ENVIRONMENT == 12:
    TILE_PIXEL_SIZE = 20
    CHUNK_SIZE = 6
    VARIANTS_NUMBER = 20
    TOTAL_WIDTH = CHUNK_SIZE * TILE_PIXEL_SIZE * CHUNK_LOAD_DISTANCE
    CHUNK_PIXEL_WIDTH = CHUNK_SIZE * TILE_PIXEL_SIZE
    CHUNK_LOAD_DISTANCE = 2