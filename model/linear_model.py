from model.base import *
from typing import Iterable, List, Final
from random import shuffle
from helpers import interleave


class Board1D(Board):
    def __init__(
        self,
        size: int,
        neighbourhood_size: int = 2,
        max_travel_distance: int | None = None,
        **kwargs,
    ):

        """
        `size`: The width of the board

        `neighbourhood_size`: The distance agents look to when considering their conspecificity

        `max_travel_distance`: The furthest distance an agent can travel in one round. If set to `None` then there is no maximum distance
        """

        # Lets first do all the basic stuff
        super().__init__(size, 1, kwargs)

        # Now we save some of the important parameters for later use in other methods
        if neighbourhood_size <= 0:
            raise ValueError("neighbourhood_size must be strictly positive")
        elif not (max_travel_distance is None) and max_travel_distance <= 0:
            raise ValueError("max_travel_distance must be strictly positive")
        else:
            self._NEIGHBOURHOOD_SIZE: Final[int] = neighbourhood_size
            self._MAX_TRAVEL_DISTANCE: Final[int | None] = max_travel_distance

        # The board starts as just an empty list
        self._data: List[Species] = list()

        # Then we fill it with agents
        for species in range(self.get_number_of_species()):
            for _ in range(self.get_population(species)):
                self._data.append(species)

        if len(self._data) > size:
            raise ValueError("There are too many agents for a board this size")

        # Then we fill any empty spots with `None`
        while len(self._data) < size:
            self._data.append(None)

        # And now we shuffle it up
        shuffle(self._data)

        # Finally, let's keep track of which cell gets to move at any given time
        self._current_turn = itertools.cycle(range(self.get_width()))

    def __getitem__(self, xy: Coordinate) -> Species:
        (x, y) = xy
        if y == 0:
            return self._data[x]
        else:

            raise IndexError()

    def neighbours(self, xy: Coordinate) -> Iterable[Coordinate]:
        (x, y) = xy
        if 0 <= x < self.get_width() and y == 0:
            for direction in [-1, +1]:
                for distance in range(self._NEIGHBOURHOOD_SIZE):
                    x_yield: int = x + direction * (distance + 1)
                    if 0 <= x_yield < self.get_width():
                        yield (x_yield, 0)
        else:
            raise OutOfBoundsError()

    def update(self) -> None:
        def try_out_spots(x: int) -> None:

            """
            Causes the agent initially located at `x` to check all the spots given until it finds one its satisfied with. If it can't find any, it will go back to where it started and be sad :(
            """

            lowest_spot: int = (
                -1
                if self._MAX_TRAVEL_DISTANCE is None
                or x - self._MAX_TRAVEL_DISTANCE < -1
                else x - self._MAX_TRAVEL_DISTANCE
            )
            highest_spot: int = (
                len(self._data)
                if self._MAX_TRAVEL_DISTANCE is None
                or x + self._MAX_TRAVEL_DISTANCE > len(self._data)
                else x + self._MAX_TRAVEL_DISTANCE
            )

            current_spot: int = x
            nearby_spots = interleave(
                range(x - 1, lowest_spot, -1), range(x + 1, highest_spot, +1)
            )

            for new_spot in itertools.chain(nearby_spots, list([x])):

                # We take the agent from its spot and place it in the new spot
                agent: Species = self._data.pop(current_spot)
                self._data.insert(new_spot, agent)
                current_spot = new_spot

                # Is it satisfied? If so then we're done. Otherwise, we try the next spot
                if self.is_satisfied((current_spot, 0)):
                    break

            self.log.append([((x, 0), (current_spot, 0))])

        # We're going to do this from left to right so we start at x=0 and move from there
        try_out_spots(next(self._current_turn))
