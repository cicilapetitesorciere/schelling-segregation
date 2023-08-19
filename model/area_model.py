from random import shuffle, random
from array import array
from typing import Iterable, cast, List, Tuple, Iterator, Final
from model.base import *


def neighbourhood(
    centre: Coordinate = (0, 0), pseudoradius: int = 1
) -> Iterator[Coordinate]:
    """
    Generates the points which draw a square entred at `centre` such that each of the four walls is offset `pseudoradius` units away from the centre

    For instance, `pseudoradius=1` and `centre=(10,-1)` produces the following points:

    `(11, 0), (10, 0), (9, -2), (10, -2), (9, 0), (9, -1), (11, -2), (11, -1)`

    or visually:

    ```
    x x x
    x c x
    x x x
    ```

    and `pseudoradius=2` with `centre=(0,0)` produces:

    `(2, 2), (1, 2), (0, 2), (-1, 2), (-2, -2), (-1, -2), (0, -2), (1, -2), (-2, 2), (-2, 1), (-2, 0), (-2, -1), (2, -2), (2, -1), (2, 0), (2, 1)`

    ```
    x x x x x
    x       x
    x   c   x
    x       x
    x x x x x
    ```

    This is achieved by generating each of the four walls of the square, each of which is given one corner. For instance, in the `pseudoradius=2` example, we can number each wall as from 1 to 4 to get the following and add arrows to show the direction in which the wall is generated, producing the following:

    ```
      ------>
      2 2 2 2 4 |
    ^ 3       4 |
    | 3   c   4 |
    | 3       4 v
    | 3 1 1 1 1
        <------
    ```

    Notice that this ordering corresponds to the order of the points listed for `pseudoradius=2`. It is also analagous to the points listed for `pseudoradius=1`.

    The algorithm is easiest to explain if we start by assuming `centre=(0,0)`

    Each wall's positition relative to the centre can be generated using two numbers -- one for the axis and a second for the direction in which the wall travels. For instance in the above `pseudoradius=2` example, wall 1 travels along the x-axis in the negative direction, wall 2 travels along the x-axis in the positive direction, wall 3 travels along the y-axis in the negative direction, and wall 4 travels along the y-axis in the positive direction.

    The four walls run respectively along the following lines:

    1: `y = +pseudoradius` (travels toward negative x)

    2: `y = -pseudoradius` (travels toward positve x)

    3: `x = -pseudoradius` (travels toward negative y)

    4: `x = +pseudoradius` (travels toward positive y)

    It's easy to exhaustively check that the RHS generalizes to `pseudoradius*direction*(2*axis-1)` where `axis=0` indicates the x-axis, and `axis=1` represents the y-axis

    Corners of any square can be defined by the set of points `(a,b)` such that `abs(a)==abs(b)`. Thus a corner on a square whose walls are each `pseudoradius` units away from the origin has the additional property `abs(a)==abs(b)==pseudoradius`. Hence a wall (not including corners) travelling parallel to the x-axis is characterized by `y=-(pseudoradius-1),-(pseudoradius-2),...,pseudoradius-1` if the direction is positive, or `y=pseudoradius-1,pseudoradius-2,...,-(pseudoradius-1)` if the direction is negative (notice that this second set of points is simply the first set with each element multiplied by `-1`, making it convienient to represent the direction of travel as either `+1` for positive and `-1` for negative). To include a corner at the start of the path, we add the point `y=pseudoradius*(-direction)=-pseudoradius*direction` where `direction=+1` indicates travel toward positive y, and `direction=-1` indicates travel toward negative y. This allows us to generalize the y-values to `y=-pseudoradius*direction,-(pseudoradius-1)*direction,...,(pseudoradius-1)*direction`

    Similar properties apply to walls travelling along the y-axis.

    Generalizing the function to other centres is then just a case of adding pair-wisethe elements of the new centre to the zero-centred output points
    """

    if pseudoradius < 1:
        raise ValueError("Pseudoradius must be a strictly positive integer")

    # Chooses wall
    for axis in [0, 1]:  # Zero is the x-axis and 1 is the y-axis
        for direction in [-1, +1]:
            # Generates wall
            ret: List[int] = [0, 0]
            # Note that python allows subscripting lists with negative values as a way to index from the end. Thus, because ret has two elements `ret[-1]=ret[2-1]=ret[1]` which is very helpful in this case
            ret[axis - 1] = centre[axis - 1] + pseudoradius * direction * (2 * axis - 1)
            for offset in range(-pseudoradius, pseudoradius):
                ret[axis] = centre[axis] + direction * offset
                yield cast(Coordinate, tuple(ret))


class Board2D(Board):
    def __init__(self, width: int, height: int, neighbourhood_size: int = 1, **kwargs):

        super().__init__(width, height, kwargs)

        if neighbourhood_size <= 0:
            raise ValueError("neighbourhood_size must be strictly positive")
        else:
            self._NEIGHBOURHOOD_SIZE: Final[int] = neighbourhood_size

        try:
            self._PROXIMITY_BIASES = (
                kwargs["proximity_bias"],
            ) * self.get_number_of_species()
            if "proximity_biases" in kwargs:
                raise OverdeterminationError(subject="proximity biases")
        except KeyError:
            try:
                self._PROXIMITY_BIASES = kwargs["proximity_biases"]
            except KeyError:
                self._PROXIMITY_BIASES = (
                    0.75,
                ) * self.get_number_of_species()  # Default value

        # We then create a structure to store all of the data, intializing all
        # squares to -1, which will be converted to `None` when using `__getitem__()`
        self._data: array[int] = array(
            "i",
            [
                -1,
            ]
            * self.get_area(),
        )

        # We will track which squares are vacant so that we can efficiently find
        # spots to place all of our agentsmoves: Iterator[Tuple[Point, Point]] = iter(())
        vacant_cells: List[Coordinate] = list(self.get_all_cells())

        shuffle(vacant_cells)

        for species in range(self.get_number_of_species()):
            for _ in range(self.get_population(species)):
                self[vacant_cells.pop(0)] = species

    def __getitem__(self, xy: Coordinate) -> Species:
        if self.includes(xy):
            (x, y) = xy
            pre: int = self._data[y * self._WIDTH + x]
            if pre >= 0:
                return pre
            else:
                return None
        else:
            raise OutOfBoundsError()

    def __setitem__(self, xy: Coordinate, newvalue: Species) -> None:

        (x, y) = xy

        def setnewvalue(nv: int) -> None:
            self._data[y * self.get_width() + x] = -1 if newvalue is None else newvalue

        if not self.includes(xy):
            raise OutOfBoundsError()
        elif not isinstance(newvalue, int):
            setnewvalue(-1)
        elif newvalue >= 0:
            setnewvalue(newvalue)
        else:
            raise ValueError("newvalue must be a valid species (i.e. non-negative)")

    def get_width(self) -> int:
        return self._WIDTH

    def get_height(self) -> int:
        return self._HEIGHT

    def neighbours(self, xy: Coordinate) -> Iterable[Coordinate]:
        if self.includes(xy):
            for neighbour in neighbourhood(xy, self._NEIGHBOURHOOD_SIZE):
                if self.includes(neighbour):
                    yield neighbour
        else:
            raise OutOfBoundsError

    def update(self) -> None:
        """
        Runs one full round of the simulation
        """

        def move(start: Coordinate, end: Coordinate) -> None:
            """
            Moves the agent located at `start` to `end`
            """
            if self[start] == None:
                raise EmptySpaceError(start)
            elif self[end] != None:
                raise IllegalMoveError(start, end)
            else:
                self[end] = self[start]
                self[start] = None

        def find_and_move_to_new_spot(xy: Coordinate) -> Coordinate:
            """
            Finds a suitable point for the agent at `xy` to move to and moves the agent to that location and produces that point as a return-value.

            Schelling allows for a variety of algorithms to achieve this. In this this particular case we use the following algorithm:

            The agent first chooses a search space. This search space will include at least the spaces immediately surrounding the agent (including corners). The agent then has the option to expand their search space outwards by one unit. If they do choose to expand the search space, they are given the option to expand it again. This outward expansion may theoretically continue forever. At each iteratetion, the probability that the agent chooses to expand the search space is `1-proximity_bias`.

            Once the search space is chosen, the agent will randomly choose a point from it to try to move to. If the piece is unable to succesfully make the move (i.e. it would move the piece off the board or if another agent is already occupying the chosen space) the agent will discard their first choice and choose another. If their are no open spots in the agent's search space, it will stay put.
            """

            species: Species = self[xy]

            if not isinstance(species, int):
                raise EmptySpaceError(xy)

            searchspace = list()
            for r in itertools.count(start=1):
                searchspace += list(neighbourhood(pseudoradius=r, centre=xy))
                if random() < self._PROXIMITY_BIASES[species]:
                    break

            shuffle(searchspace)

            while searchspace:
                candidate_spot: Coordinate = searchspace.pop(0)
                try:
                    move(xy, candidate_spot)
                    return candidate_spot
                except (IllegalMoveError, EmptySpaceError, OutOfBoundsError):
                    continue
            return xy

        dissatisfied_agents: List[Coordinate] = list()
        moves_this_round: List[Tuple[Coordinate, Coordinate]] = list()

        for (i, j) in self.get_all_cells():
            if not (self[(i, j)] == None or self.is_satisfied((i, j))):
                dissatisfied_agents.append((i, j))

        shuffle(dissatisfied_agents)

        for agent_location in dissatisfied_agents:
            destination = find_and_move_to_new_spot(agent_location)
            if (agent_location != destination) and (self.log != None):
                moves_this_round.append((agent_location, destination))

        if isinstance(self.log, list):
            self.log.append(moves_this_round)
