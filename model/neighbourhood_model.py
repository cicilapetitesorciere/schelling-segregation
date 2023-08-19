import itertools
from typing import Iterable
from model.area_model import Board2D
from model.base import Coordinate, Iterable


class BoardBN(Board2D):
    def __init__(self, width: int, height: int, neighbourhood_size: int = 5, **kwargs):
        if width % neighbourhood_size != 0 or height % neighbourhood_size != 0:
            raise ValueError(
                "The neighbourhood size must be able to evenly divide the width and height"
            )

        super().__init__(width, height, neighbourhood_size, **kwargs)

    def get_neighbourhood_size(self) -> int:
        return self._NEIGHBOURHOOD_SIZE

    def neighbours(self, xy: Coordinate) -> Iterable[Coordinate]:

        (x, y) = xy

        # We need to locate the top-right corner of the neighbourhood as a starting point
        corner_x: int = int(x / self.get_neighbourhood_size())
        corner_y: int = int(y / self.get_neighbourhood_size())

        # We then provide a way to iterate over all x and y in the neighbourhood
        return itertools.product(
            range(corner_x, corner_x + self.get_neighbourhood_size()),
            range(corner_y, corner_y + self.get_neighbourhood_size()),
        )
