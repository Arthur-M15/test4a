from PIL import Image as imagePIL
from pygame._sdl2 import Texture as TextureSDL2
import numpy as np
import pygame as pg
import Settings

def assets_generator(main_color, next_color, color_variants_number=5):
    """
    Create a double list of images.
    return asset[i][j] with i and j respectively variation index and height index.
    :param main_color: color of the current
    :param next_color: color of the next biome
    :param color_variants_number: amount of colors variations
    :return:
    """
    if color_variants_number < 3:
        raise Exception('color_variants_number must be greater than 3')
    if next_color is None:
        next_color = main_color
    rgb_matrix = {}
    main_color_result = [main_color[0]]
    next_color_result = [next_color[0]]
    mid_index = color_variants_number // 2

    for color_index in range(1, mid_index):
        nb_inter_values = len(range(1, mid_index))
        dominance = color_index/(nb_inter_values + 1)
        new_main_color = sum_colors(main_color[0], main_color[1], dominance)
        new_next_color = sum_colors(next_color[0], next_color[1], dominance)
        main_color_result.append(new_main_color)
        next_color_result.append(new_next_color)
    main_color_result.append(main_color[1])
    next_color_result.append(next_color[1])
    for color_index in range(mid_index+1, color_variants_number-1):
        dominance = (color_index-mid_index)/(len(range(mid_index, color_variants_number-1)))
        new_main_color = sum_colors(main_color[1], main_color[2], dominance)
        new_next_color = sum_colors(next_color[1], next_color[2], dominance)
        main_color_result.append(new_main_color)
        next_color_result.append(new_next_color)
    main_color_result.append(main_color[2])
    next_color_result.append(next_color[2])

    for i in range(color_variants_number):
        dominance = i/(color_variants_number-1)
        mix_color_list = []
        for j in range(color_variants_number):
            mix_color_list.append(sum_colors(main_color_result[j], next_color_result[j], dominance))
            rgb_matrix[i] = mix_color_list

    assets = []
    for i, rgb_list in enumerate(rgb_matrix.values()):
        # [0] -> PIL ; [1] -> pg.Image
        assets.append([tile_generator(rgb)[0] for rgb in rgb_list])
    return assets


def sum_colors(color1, color2, second_dominance):
    if type(color1) != tuple or type(color2) != tuple:
        raise TypeError("color1 and color2 must be tuples")
    red = int((color2[0] * second_dominance) + (color1[0] * (1 - second_dominance)))
    green = int((color2[1] * second_dominance) + (color1[1] * (1 - second_dominance)))
    blue = int((color2[2] * second_dominance) + (color1[2] * (1 - second_dominance)))
    if red > 255: red = 255
    if green > 255: green = 255
    if blue > 255: blue = 255
    new_color = (red, green, blue)
    return new_color


def tile_generator(rgb, scale_factor=20, additional_pixel=None):
    size = (4, 5)
    image = imagePIL.new("RGBA", size, rgb)
    alpha_color = (0, 0, 0, 0)
    pixels = image.load()
    pixels[0, 0] = alpha_color
    pixels[3, 0] = alpha_color


    if additional_pixel:
        image = add_pixel_list(image, additional_pixel)

    image = image.convert("RGBA")
    enlarged_size = (size[0] * scale_factor, size[1] * scale_factor)
    image = image.resize(enlarged_size, imagePIL.NEAREST)
    image = image.rotate(45, expand=True, resample=imagePIL.NEAREST)
    image = auto_crop_left(image)
    image = auto_crop_right(image)
    image.save("C:/Users/Arthur/PycharmProjects/test4a/name.png")

    if Settings.ENVIRONMENT == 12:
        image = imagePIL.new("RGBA", (Settings.TILE_PIXEL_SIZE, Settings.TILE_PIXEL_SIZE), rgb)

    return image, pil_to_surface(image)

def pil_to_surface(new_image):
    """
    converts a PIL image into a pygame surface.
    :param new_image:
    :return:
    """
    mode = new_image.mode
    size = new_image.size
    data = new_image.tobytes()

    if mode == "RGBA":
        return pg.image.fromstring(data, size, "RGBA")
    elif mode == "RGB":
        return pg.image.fromstring(data, size, "RGB")
    else:
        raise ValueError(f"Unsupported image mode: {mode}")

def pil_to_sdl2(renderer, canvas):
    size = canvas.size
    data = canvas.tobytes()
    surface = pg.image.fromstring(data, size, "RGBA")
    texture_chunk = TextureSDL2.from_surface(renderer, surface)
    return texture_chunk

def auto_crop_left(image):
    pixels = image.load()
    for x in range(image.width):
        for y in range(image.height):
            if pixels[x, y] != (0, 0, 0, 0):
                image = image.crop((x ,x, image.width, image.height))
                return image

def auto_crop_right(image, margin=0):
    pixels = image.load()
    is_valid = False
    for x in range(image.width):
        pattern = []
        for y in range(image.height):
            alpha_value = pixels[x, y][3]
            if len(pattern) == 0:
                if alpha_value < 255:
                    pattern.append((0, y))
                else:
                    pattern.append((1, y))
            elif pattern[-1][0] == 0 and alpha_value == 255:
                pattern.append((1, y))
            elif pattern[-1][0] == 1 and alpha_value < 255:
                pattern.append((0, y))

        pattern_values = [pattern[i][0] for i in range(len(pattern))]
        if pattern_values == [0, 1, 0] and is_valid:
            image = image.crop((0 ,0, pattern[-1][1]+margin, pattern[-1][1]+margin))
            return image
        elif pattern_values == [0, 1, 0, 1, 0]:
            is_valid = True

def add_pixel_list(image, pixel_values):
    """
    draw on tile image with pixel values
    :param image: Image
    :param pixel_values: Dictionary of (coordinates: pixel rgb values)
    :return: Image
    """
    if type(pixel_values) != dict:
        raise TypeError('pixel_values must be a dictionary.')
    if len(pixel_values) > 8:
        raise Exception("Too many pixels (>8)")
    else:
        pixels = image.load()
        for coordinates, rgb in pixel_values.items():
            if coordinates in [(1,0), (2,0), (0,1), (1,1), (2,1), (3,1), (1,2), (2,2)]:
                pixels[coordinates] = rgb
            # else coordinates are out of bounds
        return image


def get_dominance_matrix_name(frontier):
    left, corner_left, top, corner_right, right = frontier
    if top and right and left:
        return "right_and_left_and_top"
    elif top and not right and left:
        return "left_and_top"
    elif top and not left and right:
        return "right_and_top"
    elif top and not left and not right:
        return "top"
    elif right and not left and not right:
        return "right"
    elif left and not right and not top:
        return "left"
    elif right and left and not top:
        return "left_and_right"
    elif corner_right and not corner_left and not right and not top and not left:
        return "corner_right"
    elif corner_left and not corner_right and not left and not top and not right:
        return "corner_left"
    elif corner_right and corner_left and not top and not left and not right:
        return "corner_right_and_corner_left"
    elif corner_right and left and not right and not top:
        return "corner_right_and_left"
    elif corner_left and right and not left and not top:
        return "corner_left_and_right"
    else:
        return "full"


def generate_dominance_matrix_dict(chunk_size, variation_number):
    dominance_matrix = {}
    linear_border = simple_dominance_matrix(chunk_size, "linear")
    corner_border = simple_dominance_matrix(chunk_size, "corner")

    dominance_matrix["top"] = linear_border
    dominance_matrix["left"] = rotate_matrix(linear_border, 1)
    dominance_matrix["right"] = rotate_matrix(linear_border, -1)
    dominance_matrix["corner_left"] = corner_border
    dominance_matrix["corner_right"] = rotate_matrix(corner_border, -1)

    dominance_matrix["right_and_top"] = merge_matrix(dominance_matrix["right"], dominance_matrix["top"], chunk_size)
    dominance_matrix["left_and_top"] = merge_matrix(dominance_matrix["left"], dominance_matrix["top"], chunk_size)
    dominance_matrix["right_and_left_and_top"] = merge_matrix(dominance_matrix["left_and_top"], dominance_matrix["right"], chunk_size)
    dominance_matrix["left_and_right"] = merge_matrix(dominance_matrix["left"], dominance_matrix["right"], chunk_size)

    dominance_matrix["corner_left_and_right"] = merge_matrix(dominance_matrix["corner_left"], dominance_matrix["right"], chunk_size)
    dominance_matrix["corner_right_and_left"] = merge_matrix(dominance_matrix["corner_right"], dominance_matrix["left"], chunk_size)
    dominance_matrix["corner_right_and_corner_left"] = merge_matrix(dominance_matrix["corner_left"], dominance_matrix["corner_right"], chunk_size)
    dominance_matrix["full"] = [[0] * chunk_size] * chunk_size

    for key in dominance_matrix:
        dominance_matrix[key] = normalize_to_index(dominance_matrix[key], variation_number)
    return dominance_matrix


def normalize_to_index(matrix, variation_number):
    index_matrix = []
    for x in matrix:
        index_line = []
        for y in x:
            if int(variation_number * y) >= variation_number:
                y = variation_number - 1
            index_line.append(int(variation_number * y))
        index_matrix.append(index_line)
    return index_matrix


def simple_dominance_matrix(chunk_size, shape):
    matrix = [[0] * chunk_size for _ in range(chunk_size)]
    fade = [(fade_index/chunk_size) for fade_index in range(chunk_size)]
    matrix[0] = fade

    if shape == "corner":
        for i in range(1, chunk_size):
            matrix[i] = [(x * (chunk_size-i-1))/chunk_size for x in fade]

    elif shape == "linear":
        for i in range(1, chunk_size):
            matrix[i] = fade

    else:
        raise Exception("Invalid shape")
    return matrix


def rotate_matrix(matrix, rotation_90):
    new_matrix = np.rot90(matrix, rotation_90)
    return new_matrix.tolist()


def mix_values(val1, val2):
    return val1 + (1-val1)*val2


def merge_matrix(matrix1, matrix2, size):
    new_matrix = [[0] * size for _ in range(size)]
    for i in range(size):
        for j in range(size):
            new_matrix[i][j] = mix_values(matrix1[i][j], matrix2[i][j])
    return new_matrix

def get_height_index(height, variation_number, max_height=3):
    """
    Change the real height of the tile into the index of tile chosen in the asset list.
    :param height: height of the tile.
    :param variation_number: amount of assets for this biome.
    :param max_height: maximum height affected to the last asset.
    :return:
    """
    medium = max_height / 2
    normalized_height = height + medium
    unit_size = max_height/variation_number
    index = int(normalized_height/unit_size)
    if index <= 0 :
        return 0
    elif index >= variation_number:
        return variation_number - 1
    else:
        return index

def convert_assets_to_surface(assets):
    new_assets = {}
    for i in range(len(assets)):
        key = list(assets.keys())[i]
        pil_variants = assets[key]
        variant_list = []
        for variant in pil_variants.assets:
            image_list = []
            for image in variant:
                new_image = pil_to_surface(image)
                image_list.append(new_image)
            variant_list.append(image_list)
        new_assets[key] = variant_list
    return new_assets
