from PIL import Image


def assets_generator(main_color, next_color, color_variants_number=5, special_variants_list=None):
    if color_variants_number < 3:
        raise Exception('color_variants_number must be greater than 3')
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
    for rgb_list in rgb_matrix.values():
        assets.append(tile_generator(rgb) for rgb in rgb_list)
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
    image = Image.new("RGBA", size, rgb)
    alpha_color = (0, 0, 0, 0)
    pixels = image.load()
    pixels[0, 0] = alpha_color
    pixels[3, 0] = alpha_color

    if additional_pixel:
        image = add_pixel_list(image, additional_pixel)

    image = image.convert("RGBA")
    enlarged_size = (size[0] * scale_factor, size[1] * scale_factor)
    image = image.resize(enlarged_size, Image.NEAREST)
    image = image.rotate(45, expand=True, resample=Image.BICUBIC)
    image = auto_crop_left(image)
    image = auto_crop_right(image)
    return image


def auto_crop_left(image):
    pixels = image.load()
    for x in range(image.width):
        for y in range(image.height):
            if pixels[x, y] != (0, 0, 0, 0):
                image = image.crop((x ,x, image.width, image.height))
                return image

def auto_crop_right(image):
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
            image = image.crop((0 ,0, pattern[-1][1], pattern[-1][1]))
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
