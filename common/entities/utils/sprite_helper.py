from PIL import Image as PILImage
from PIL import ImageDraw as PILDraw
from math import sqrt


def create_sprite_bank():
    alpha, green, red = alpha_color(), green_color(), red_color()

    def circle(size: tuple[int, int], color: tuple[int, int, int, int]):
        center = tuple(x // 2 for x in size)
        im: PILImage = PILImage.new("RGBA", size, alpha)
        PILDraw.ImageDraw(im, "RGBA").circle(center, min(center), fill=color)
        return im

    sprite_dict = {
        0: [circle((20, 20), color) for color in [green, red]],
        1: [circle((800, 800), color) for color in [green, red]],
        20: [PILImage.new("RGBA", (20, 20), color) for color in [green, red]],
        21: [PILImage.new("RGBA", (800, 800), color) for color in [green, red]]
    }
    return sprite_dict


def red_color():
    return 255, 0, 0, 150


def green_color():
    return 0, 255, 0, 150


def alpha_color():
    return 0, 0, 0, 0


def truncate(im):
    pixels = im.load()
    w = im.width
    h = im.height

    new_w = w/sqrt(2)
    new_h = h/sqrt(2)

    left    = (w - new_w)//2
    right   = w - left
    top     = (h - new_h)//2
    bottom  = h - top

    im = im.crop((left, top, right, bottom))
    return im


def pixel_art(base_image, pixel_size):

    image_size = base_image.size
    sub_size = tuple(x//pixel_size for x in image_size)
    upper_size =  tuple(x*2 for x in image_size)

    base_image = base_image.resize(upper_size)
    base_image = base_image.rotate(45, expand=True)
    base_image = base_image.resize(sub_size, PILImage.NEAREST)
    base_image = base_image.resize(upper_size, PILImage.NEAREST)
    base_image = base_image.rotate(-45)
    base_image = truncate(base_image)

    return base_image

