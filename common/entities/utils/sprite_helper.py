from PIL import Image as PILImage
from PIL import ImageDraw as PILDraw


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