# Screen.py file
import pathlib
import pygame as pg
import pygame.freetype as ft
import sys
from pygame._sdl2.video import Window, Renderer, Texture, Image
from random import randrange, uniform

#WIN_SIZE = WIN_W, WIN_H = 1600, 900
BIOME_SPRITE_DIR_PATH = 'entities/biomes'
FONTS_DIR_PATH = 'assets/fonts'
WIN_SIZE = WIN_W, WIN_H = 1200, 900
#WIN_SIZE = WIN_W, WIN_H = 1920, 1080
FONT_SIZE = 14

MAX_FPS = 0
FPS_LIST_SIZE = 60
"""
FONT_SIZE = 40
SPEED = 200
NUM_SPRITES_PER_CLICK = 1
NUM_ANGLES = 180
DEBUG = True
"""

SPEED = 60
CHUNK_SIZE = 10
CHUNK_LOAD_DISTANCE = 20
TILE_SIZE = 46
CHUNK_VARIATIONS = 0.1
HARMONIC_NUMBER = 5
TOTAL_WIDTH = CHUNK_SIZE * TILE_SIZE * CHUNK_LOAD_DISTANCE
CHUNK_WIDTH = CHUNK_SIZE * TILE_SIZE
