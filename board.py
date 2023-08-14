import itertools
from random import shuffle, random
from array import array
from typing import cast, List, Tuple, Iterator, Final, TypeVar


class NoSuchSpeciesError(Exception):
    pass

class IllegalMoveError(Exception):
    pass

class EmptySpaceError(Exception):
    pass

Point = Tuple[int, int]
X: Final = 0
Y: Final = 1

def neighbourhood(pseudoradius: int = 1, centre: Point = (0, 0)) -> Iterator[Point]:
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
    assert pseudoradius >= 1
    # Chooses wall
    for axis in [X, Y]:
        for direction in [-1, +1]:
            # Generates wall
            ret: List[int] = [0, 0]
            # Note that python allows subscripting lists with negative values
            # as a way to index from the end. Thus, because ret has two elements
            # ret[-1]=ret[2-1]=ret[1]
            ret[axis - 1] = centre[axis - 1] + pseudoradius * direction * (2 * axis - 1)
            for offset in range(-pseudoradius, pseudoradius):
                ret[axis] = centre[axis] + direction * offset
                yield cast(Point, tuple(ret))

class Board:

    def __init__(
        self,
        shape: Tuple[int, int],
        n: int | Tuple[int, ...],
        thresholds: int | Tuple[int, ...],
        proximity_bias: float | Tuple[float, ...] = 0.75,
        k: int | None = None,
        record_moves: bool = False,
    ) -> None:
        def allgte0(q: int | Tuple[int, ...]) -> bool:
            """
            If `q` is an integer, then this function returns True iff `q` is greater than or equal to 0. If `q` is a tuple, then this function returns True iff each element of `q` is greater than or equal to zero
            """
            return (min(q) if isinstance(q, tuple) else q) >= 0

        assert shape[X] > 0 and shape[Y] > 0
        assert allgte0(n)
        assert allgte0(thresholds)
        assert (
            0 < min(proximity_bias)
            if isinstance(proximity_bias, tuple)
            else proximity_bias <= 1
        )

        if k == None:
            if isinstance(n, tuple):
                k = len(n)
            elif isinstance(thresholds, tuple):
                k = len(thresholds)
            elif isinstance(proximity_bias, tuple):
                k = len(proximity_bias)
            else:
                raise (Exception("Cannot determine number of species"))

        assert isinstance(k, int)
        assert k >= 0

        if (
            (isinstance(n, tuple) and k != len(n))
            or (isinstance(thresholds, tuple) and k != len(thresholds))
            or (isinstance(proximity_bias, tuple) and k != len(proximity_bias))
        ):
            raise (
                Exception(
                    "The arguments provided give conflicting information on the number of species present"
                )
            )

        self.populations: Final[Tuple[int, ...]] = (
            n if isinstance(n, tuple) else (n,) * k
        )
        assert self.populations

        area_of_board: Final[int] = shape[X] * shape[Y]
        self.number_of_agents: Final[int] = sum(self.populations)

        if self.number_of_agents > area_of_board:
            raise (Exception("The board is not big enough to handle that many units"))

        self.shape: Final[Tuple[int, int]] = shape
        self.thresholds: Final[Tuple[int, ...]] = (
            thresholds if isinstance(thresholds, tuple) else (thresholds,) * k
        )
        self.proximity_bias: Final[Tuple[float, ...]] = (
            proximity_bias
            if isinstance(proximity_bias, tuple)
            else (proximity_bias,) * k
        )

        # We then create a structure to store all of the data, intializing all
        # squares to -1
        self._data: array[int] = array(
            "i",
            [
                -1,
            ]
            * area_of_board,
        )

        self.log: List[List[Tuple[Point, Point]]] | None = [] if record_moves else None

        # We will track which squares are vacant so that we can efficiently find
        # spots to place all of our agentsmoves: Iterator[Tuple[Point, Point]] = iter(())
        vacant_squares: List[Point] = list(self.all_spaces())

        shuffle(vacant_squares)

        # And finally we fill the board
        for species in range(k):
            for _ in range(self.populations[species]):
                self[vacant_squares.pop(0)] = species

    def __getitem__(self, xy: Point) -> int:
        if self.includes_point(xy):
            (x, y) = xy
            return self._data[y * self.shape[X] + x]
        else:
            raise IndexError()

    def __setitem__(self, xy: Point, newvalue: int) -> None:
        assert newvalue >= -1
        if self.includes_point(xy):
            (x, y) = xy
            self._data[y * self.shape[X] + x] = newvalue
        else:
            raise IndexError()

    def __str__(self) -> str:
        ret: str = ""
        for y in range(self.shape[Y]):
            for x in range(self.shape[X]):
                ret += str(self[(x, y)]) if self[(x, y)] != -1 else "*"
                ret += " "
            ret += "\n"
        return ret

    def all_spaces(self) -> Iterator[Point]:
        return itertools.product(range(self.shape[X]), range(self.shape[Y]))

    def includes_point(self, xy: Point) -> bool:
        """
        Returns True iff `xy` is a valid point on the board
        """
        return (0 <= xy[X] < self.shape[X]) and (0 <= xy[Y] < self.shape[Y])

    def move(self, start: Point, end: Point) -> None:
        """
        Moves the agent located at `start` to `end`
        """
        if self[start] == -1:
            raise EmptySpaceError
        elif self[end] != -1:
            raise IllegalMoveError
        else:
            self[end] = self[start]
            self[start] = -1

    def conspecificity(self, xy: Point, pseudoradius: int = 1) -> float:
        """
        Returns the proportion of neighbours which are conspecific to the agent located at `xy`
        """
        if self[xy] < 0:
            raise EmptySpaceError
        else:
            number_of_neighbours: int = 0
            number_of_similar_neighbours: int = 0
            for neighbour in neighbourhood(centre=xy, pseudoradius=pseudoradius):
                try:
                    if self[neighbour] != -1:
                        number_of_neighbours += 1
                        if self[neighbour] == self[xy]:
                            number_of_similar_neighbours += 1
                except IndexError:
                    pass

            try:
                return number_of_similar_neighbours / number_of_neighbours
            except ZeroDivisionError:
                return 0.0

    def is_satisfied(self, xy: Point) -> bool:
        """
        Returns True if the unit at position `xy` is disatisfied
        """
        return self.conspecificity(xy) >= self.thresholds[self[xy]]

    def total_satisfied(self) -> int:
        """
        Returns the total number of agents on the board who are satisfied
        """
        ret: int = 0
        for x in range(self.shape[X]):
            for y in range(self.shape[Y]):
                if self[(x, y)] != -1 and self.is_satisfied((x, y)):
                    ret += 1
        return ret

    def update(self) -> None:
        """
        Runs one full round of the simulation
        """

        def find_and_move_to_new_spot(xy: Point) -> Point:
            """
            Finds a suitable point for the agent at `xy` to move to and moves the agent to that location and produces that point as a return-value.

            Schelling allows for a variety of algorithms to achieve this. In this this particular case we use the following algorithm:

            The agent first chooses a search space. This search space will include at least the spaces immediately surrounding the agent (including corners). The agent then has the option to expand their search space outwards by one unit. If they do choose to expand the search space, they are given the option to expand it again. This outward expansion may theoretically continue forever. At each iteratetion, the probability that the agent chooses to expand the search space is `1-proximity_bias`.

            Once the search space is chosen, the agent will randomly choose a point from it to try to move to. If the piece is unable to succesfully make the move (i.e. it would move the piece off the board or if another agent is already occupying the chosen space) the agent will discard their first choice and choose another. If their are no open spots in the agent's search space, it will stay put.
            """
            r = 1
            searchspace: List[Point] = list(neighbourhood(pseudoradius=r, centre=xy))
            while random() >= self.proximity_bias[self[xy]]:
                r += 1
                searchspace += list(neighbourhood(pseudoradius=r, centre=xy))

            shuffle(searchspace)

            while searchspace:
                candidate_spot: Point = searchspace.pop(0)
                try:
                    self.move(xy, candidate_spot)
                    return candidate_spot
                except (IllegalMoveError, EmptySpaceError, IndexError):
                    continue
            return xy

        dissatisfied_agents: List[Point] = list()
        moves_this_round: List[Tuple[Point, Point]] = list()

        for i in range(self.shape[X]):
            for j in range(self.shape[Y]):
                if self[(i, j)] != -1 and (not self.is_satisfied((i, j))):
                    dissatisfied_agents.append((i, j))

        shuffle(dissatisfied_agents)

        for agent_location in dissatisfied_agents:
            destination = find_and_move_to_new_spot(agent_location)
            if (agent_location != destination) and (self.log != None):
                moves_this_round.append((agent_location, destination))

        if isinstance(self.log, list):
            self.log.append(moves_this_round)
