from __future__ import annotations
import math
import random
import Settings
from common.entities.Entity_c import BaseSprite, Coordinates
from common.biomes.properties.biome_generator_helper import get_dominance_matrix_name
from typing import Optional, Tuple, List, Dict, Any


class Chunk(BaseSprite):
    coordinates: Tuple[int, int]
    biome: Any
    neighbor_chunk: Dict[str, Dict[str, Any]]
    def __init__(self, app_handler, coordinates: Tuple[int, int], biome: Any, neighbor_chunk: Dict[str, Dict[str, Any]]) -> None:
        size = app_handler.map.biome_manager.chunk_rect_size
        float_coord_x: float = float(coordinates[0])
        float_coord_y: float = float(coordinates[1])
        super().__init__(app_handler, "chunk", (size, size), Coordinates(float_coord_x, float_coord_y))
        self.app_handler = app_handler
        self.variation: float = Settings.CHUNK_VARIATIONS
        self.tiles: List[List[float]] = []
        self.top_signal: List[float] = []
        self.bottom_signal : List[float] = []
        self.left_signal: List[float] = []
        self.right_signal: List[float] = []
        self.biome = biome
        self.chunk_x: int = coordinates[0]
        self.chunk_y: int = coordinates[1]
        self.entity_coord.set(self.chunk_x * Settings.CHUNK_PIXEL_WIDTH, self.chunk_y * Settings.CHUNK_PIXEL_WIDTH)

        self.frontier_biome: Optional[str] = None
        self.__get_frontier_biome()
        self.__generate_signals(
            neighbor_chunk.get("top"),
            neighbor_chunk.get("bottom"),
            neighbor_chunk.get("left"),
            neighbor_chunk.get("right")
        )

    def get_information(self) -> Dict[str, Any]:
        return {
            "top_signal": self.top_signal,
            "bottom_signal": self.bottom_signal,
            "left_signal": self.left_signal,
            "right_signal": self.right_signal
        }

    def get_coordinates(self) -> Tuple[int, int]:
        return self.chunk_x, self.chunk_y

    def __get_frontier_biome(self) -> None:
        left = self.app_handler.map.biome_manager.get_biome(self.chunk_x - 1, self.chunk_y).name == self.biome.next_biome.name
        top_left = self.app_handler.map.biome_manager.get_biome(self.chunk_x - 1, self.chunk_y + 1).name == self.biome.next_biome.name
        top = self.app_handler.map.biome_manager.get_biome(self.chunk_x, self.chunk_y + 1).name == self.biome.next_biome.name
        top_right = self.app_handler.map.biome_manager.get_biome(self.chunk_x + 1, self.chunk_y + 1).name == self.biome.next_biome.name
        right = self.app_handler.map.biome_manager.get_biome(self.chunk_x + 1, self.chunk_y).name == self.biome.next_biome.name

        self.frontier_biome =  get_dominance_matrix_name((left, top_left, top, top_right, right))

    def __generate_signals(self,
                           top_chunk: Optional[Dict[str, List[float]]],
                           bottom_chunk: Optional[Dict[str, List[float]]],
                           left_chunk: Optional[Dict[str, List[float]]],
                           right_chunk: Optional[Dict[str, List[float]]]) -> None:
        top_signal: List[float]     = []
        bottom_signal: List[float]  = []
        left_signal: List[float]    = []
        right_signal: List[float]   = []
        # Use neighbor information
        # Use neighbor information
        left_begin: Optional[float] = None
        right_begin: Optional[float] = None
        left_begin_derivative: float = 0.0
        right_begin_derivative: float = 0.0
        if top_chunk is not None:
            left_begin             = top_chunk["left_signal"][-1]
            right_begin            = top_chunk["right_signal"][-1]
            left_begin_derivative  = top_chunk["left_signal"][-1] - top_chunk["left_signal"][-2]
            right_begin_derivative = top_chunk["right_signal"][-1] - top_chunk["right_signal"][-2]
            top_signal = top_chunk["bottom_signal"]

        left_end: Optional[float] = None
        right_end: Optional[float] = None
        left_end_derivative: float = 0.0
        right_end_derivative: float = 0.0
        if bottom_chunk is not None:
            left_end                = bottom_chunk["left_signal"][0]
            right_end               = bottom_chunk["right_signal"][0]
            left_end_derivative     = bottom_chunk["left_signal"][1] - bottom_chunk["left_signal"][0]
            right_end_derivative    = bottom_chunk["right_signal"][1] - bottom_chunk["right_signal"][0]
            bottom_signal = bottom_chunk["top_signal"]

        top_begin: Optional[float] = None
        bottom_begin: Optional[float] = None
        top_begin_derivative: float = 0.0
        bottom_begin_derivative: float = 0.0
        if left_chunk is not None:
            top_begin = left_chunk["top_signal"][-1]
            bottom_begin = left_chunk["bottom_signal"][-1]
            top_begin_derivative = left_chunk["top_signal"][-1] - left_chunk["top_signal"][-2]
            bottom_begin_derivative = left_chunk["bottom_signal"][-1] - left_chunk["bottom_signal"][-2]
            left_signal = left_chunk["right_signal"]

        top_end: Optional[float] = None
        bottom_end: Optional[float] = None
        top_end_derivative: float = 0.0
        bottom_end_derivative: float = 0.0
        if right_chunk is not None:
            top_end = right_chunk["top_signal"][0]
            bottom_end = right_chunk["bottom_signal"][0]
            top_end_derivative = right_chunk["top_signal"][1] - right_chunk["top_signal"][0]
            bottom_end_derivative = right_chunk["bottom_signal"][1] - right_chunk["bottom_signal"][0]
            right_signal = right_chunk["left_signal"]

        if not top_signal:
            top_signal = create_curve(top_begin, top_end, top_begin_derivative, top_end_derivative)
        if not bottom_signal:
            bottom_signal = create_curve(bottom_begin, bottom_end, bottom_begin_derivative, bottom_end_derivative)
        if not left_signal:
            left_signal = create_curve(left_begin, left_end, left_begin_derivative, left_end_derivative)
        if not right_signal:
            right_signal = create_curve(right_begin, right_end, right_begin_derivative, right_end_derivative)

        self.top_signal = top_signal
        self.bottom_signal = bottom_signal
        self.left_signal = left_signal
        self.right_signal = right_signal

def create_curve(
        start: Optional[float]=None,
        stop: Optional[float]=None,
        start_derivative: float=0.0,
        stop_derivative: float=0.0,
        variations=1) -> List[float]:

    base_signal2: List[float]
    base_signal: List[float] = [0.0] * Settings.CHUNK_SIZE
    for i in range(1, Settings.HARMONIC_NUMBER+1):
        random_phase: float = random.uniform(-math.pi, math.pi)
        #random_amplitude: float = random.uniform(-1, 1)
        random_offset: float = random.uniform(-0.5, 0.5)
        random_amplitude: float = 1.0
        for j in range(Settings.CHUNK_SIZE):
            base_signal[j] += random_offset + (random_amplitude / i) * math.sin(((2 * math.pi * j)/Settings.CHUNK_SIZE) + random_phase)
    offset: float
    derivative: float
    if start is not None:
        assert start is not None
        offset = start - base_signal[0]
        derivative = start_derivative - (base_signal[1] - base_signal[0])
        base_signal2 = [a + b for a, b in zip(base_signal, correct_curve(offset, derivative, True))]
        base_signal = base_signal2
    if stop is not None:
        assert stop is not None
        offset = stop - base_signal[-1]
        derivative = stop_derivative - (base_signal[-2] - base_signal[-1])
        corrective: List[float] = correct_curve(offset, derivative, False)
        base_signal2 = [a + b for a, b in zip(base_signal, corrective)]
        base_signal = base_signal2
    return base_signal

def correct_curve(offset: float, derivative: float, starting: bool) -> List[float]:
    r"""
    f\left(x\right)=-ae^{-x}
    g\left(x\right)=\frac{\left(\cos\left(\frac{2\pi x}{2c}\right)+1\right)}{2}
    h\left(x\right)=be^{-\left(\frac{5x}{c}\right)^{2}}
    r\left(x\right)\ =\ \left(f\left(x\right)+h\left(x\right)\right)\cdot g\left(x\right)
    a=1
    b=1
    c=10
    """
    # Import in Desmos graph the formulas:

    # With
    # a derivative
    # b-a the offset
    # c the scale
    # r(x) the result

    size: int = Settings.CHUNK_SIZE
    a: float = derivative
    b: float = offset + derivative
    c: int = size
    first: int
    last: int
    increment: int
    if starting:
        first = 0
        last = size
        increment = 1
    else:
        first = size - 1
        last = -1
        increment = -1
    signal_correction: List[float] = []
    for x in range(first, last, increment):
        f_x = -a * math.exp(-x)
        g_x = (math.cos((2 * math.pi * x) / (2 * c)) + 1) / 2
        h_x = b * math.exp(-((5 * x) / (4 * c)) ** 2)

        # r(x) = (f(x) + h(x)) * g(x)
        r_x = (f_x + h_x) * g_x
        signal_correction.append(r_x)

    return signal_correction
