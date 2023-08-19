# from helpers import count
from typing import Tuple, Iterator, Dict, Any, Final, List, Callable, Iterable
from abc import abstractmethod
import itertools

Coordinate = Tuple[int, int]

Species = int | None

class IllegalMoveError(Exception):
    """
    Occurs when an attempt is made to movde an agent in a way that is not allowed
    """
    def __init__(self, start: Coordinate, end: Coordinate):
        pass

class EmptySpaceError(Exception):
    """
    Occurs when actions that require an agent are attempted on empty cells
    """
    def __init__(self, xy: Coordinate):
        self.message = f'There is no agent located at {xy}'

class EveryoneIsSatisfiedException(Exception):
    """
    Occurs when a user tries to update a board where everyone is already satisfied and doesn't want to move
    """
    def __init__(self):
        self.message = 'There is nothing to update. Everyone is satisfied'

class OverdeterminationError(ValueError):
    """
    Occurs when too many parameters are used to initialize a board
    """
    def __init__(self, subject: str):
        self.message = f'Conflicting information provided for {subject}'

class UnderdeterminationError(ValueError):
    """
    Occurs when too little parameters are used to initialize a board
    """
    def __init__(self, subject: str):
        self.message = f'Cannot determine {subject}'

class OutOfBoundsError(ValueError):
    """
    Occurs when a user tries to reference locations on the board that don't exist
    """
    def __init__(self):
        self.message = 'Coordinate out of bounds'

class Board:

    def __init__(self, width: int, height: int, kwargs: Dict[str, Any]):

        self.log: List[List[Tuple[Coordinate, Coordinate]]] = list()

        self._WIDTH: int = width
        self._HEIGHT: int = height

        # We make sure the keyword arguments we've been have the correct types
        TUPLE_ARGS: Final[List[str]] = ['populations', 'fill_proportions', 'thresholds']

        def check_args(args, type):
            for arg in args:
                try:
                    if not isinstance(kwargs[arg], type):
                        raise TypeError(f'{arg} must be of type {type}')
                except:
                    continue

        check_args(TUPLE_ARGS, tuple)
        check_args(['total_population', 'threshold'], int)
        check_args(['total_fill_proportion'], float)

        # Let's find the number of species
        try:
            # Let's see, maybe the user explicitly specified a number of species...
            self._NUMBER_OF_SPECIES = kwargs['number_of_species']
            
            # But also let's make sure it's a positive integer
            if not isinstance(self._NUMBER_OF_SPECIES, int):
                raise TypeError('Number of species must be a positive integer')
            elif self._NUMBER_OF_SPECIES <= 0:
                raise ValueError('Number of species must be positive')
            
        except KeyError:
            
            # Okay, the user didn't specify a number of species? Lets see if one of the arguments implies a specific number of species
            for arg in TUPLE_ARGS:
                try:
                    self._NUMBER_OF_SPECIES = len(kwargs[arg])
                    break
                except KeyError:
                    # If they didn't specify one of those arguments, we just move onto the next. That's fine. They don't necessarily need to specify all of them. Hopefully we find a value for number of species though
                    continue

            # Okay, we've done all our searching. We should have found and saved the number of species by now. If not, we whine now rather than whining about it later
            try:
                self._NUMBER_OF_SPECIES
            except AttributeError:
                raise UnderdeterminationError(subject='number of species')
        
        finally:

            # Now that we ostensibly have a number of species, let's make sure it matches up with everything else
            for arg in TUPLE_ARGS:
                try:
                    if self.get_number_of_species() != len(kwargs[arg]):
                        raise OverdeterminationError(subject = 'number of species')
                except KeyError:
                    continue

        # Let's make a couple helper functions to initialize self._POPULATIONS with
        def initialize_populations(arg: str, expression: Callable[[Any], Tuple[int, ...]]) -> None:
            """
            Initializes self._POPULATIONS using the provided argument and expression
            """
            try:
                # This is a trap! If we don't get an attribute error here, we've done something wrong and the population sizes are actually overdetermined
                self._POPULATION
                raise OverdeterminationError(subject = 'population sizes')
            
            except AttributeError:
                # Now that we've gotten an attribute error, we know that self._POPULATIONS is not defined, and we can define it.
                try:
                    self._POPULATIONS: Tuple[int, ...] = expression(kwargs[arg])
                
                except KeyError:
                    # But oh no! the argument we're trying to define it with wasn't provided. No worries. We just won't initialize it. Hopefully it will be initialized later (don't worry, we will check)
                    pass
        
        def proportion_of_area(proportion: float) -> int:
            return int(proportion * self.get_area())

        # Now let's try initializing self._POPULATIONS with the various arguments. Only one of these should work, and if more than one of them works, they will fall into my cleverly designed trap within the function. Mwahahahaha!
        initialize_populations('populations'            , lambda pops: pops)
        initialize_populations('total_population'       , lambda tpop: (int(tpop / self.get_number_of_species()), ) * self.get_number_of_species())
        initialize_populations('fill_proportions'       , lambda fprs: map(proportion_of_area, fprs))
        initialize_populations('total_fill_proportion'  , lambda tfpr: (int(proportion_of_area(tfpr) / self.get_number_of_species()), ) * self.get_number_of_species())

        # Alright so did we manage to successfully initialize the popuatations in one of those calls? Does it make any sense? Let's examine it
        try:
            for pop in self._POPULATIONS:
                if pop <= 0:
                    raise ValueError("Populations must be strictly postive")
        except AttributeError:

            # If nothing else, we can just default to making it an even split everywhere
            self._POPULATIONS = (int(self.get_area() / self.get_number_of_species()), ) * self.get_number_of_species()

        # Finally, thresholds
        try:
            # We're first of all going to try using thresholds
            self._THRESHOLDS: Tuple[float, ...] = kwargs['thresholds']
            
            # If this works and we don't get a key error, we need to make sure that threshold wasn't also provided as this would conflict
            if 'threshold' in kwargs:
                raise OverdeterminationError(subject='thresholds')
        
        except KeyError:

            # If we do get a key error, then we need to define thresholds using threshold. If this also raises a key error though, mistakes were obviously made
            try: 
                self._THRESHOLDS: Tuple[float, ...] = (kwargs['threshold'], ) * self.get_number_of_species()
            except KeyError:
                raise UnderdeterminationError(subject='thresholds')

    @abstractmethod
    def __getitem__(xy: Coordinate) -> Species:
        """
        Returns the species of the agent located at `xy`
        """
        pass
    
    def get_width(self) -> int:
        """
        Returns the width of the board
        """
        return self._WIDTH

    def get_height(self) -> int:
        """
        Returns the height of the board
        """
        return self._HEIGHT

    def get_area(self) -> int:
        return self.get_height()*self.get_width()
    
    def get_all_cells(self) -> Iterator[Coordinate]:
        """
        Returns an iterator for all cells on the board
        """
        return itertools.product(range(self.get_width()), range(self.get_height()))
    
    def includes(self, xy: Coordinate) -> bool:
        """
        Returns `True` if `xy` is on the board
        """
        (x, y) = xy
        return (0 <= x < self.get_width()) and (0 <= y < self.get_height())
    
    def get_number_of_species(self) -> int:
        """
        Returns the total number of species occupying the board
        """
        return self._NUMBER_OF_SPECIES

    def get_population(self, species: Species) -> int:
        """
        Returns the total population of the specified species
        """
        if species == None:
            self.get_area() - self.get_total_population()
        else:
            return self._POPULATIONS[species]

    def get_total_population(self) -> int:
        return sum(map(self.get_population, range(self.get_number_of_species())))

    @abstractmethod
    def neighbours(self, xy: Coordinate) -> Iterable[Coordinate]:
        """
        Yields the location of all the neighbours of the agent located at `xy` in no particular order
        """
        pass
    
    def conspecificity(self, xy: Coordinate) -> float:
        """
        Returns the proportion of neighbours who are similar to the agent located at `xy`
        """
        if self[xy] == None:
            raise EmptySpaceError(xy)
        else:
            number_of_neighbours: int = 0
            number_of_conspecific_neighbours: int = 0
            for neighbour in self.neighbours(xy):
                if self[neighbour] != None:
                    number_of_neighbours += 1
                    if self[xy] == self[neighbour]:
                        number_of_conspecific_neighbours += 1
            try:
                return number_of_conspecific_neighbours / number_of_neighbours
            except ZeroDivisionError:
                return 0

    def is_satisfied(self, xy: Coordinate) -> bool:
        """
        Returns `True` iff the agent located at `xy` is satisfied
        """
        if self[xy] == None:
            raise EmptySpaceError(xy)
        else:
            return self.conspecificity(xy) >= self._THRESHOLDS[self[xy]]

    def get_total_satisfied(self) -> int:
        """
        Returns the total number of agents on the board who are satisfied
        """
        n: int = 0
        for xy in self.get_all_cells():
            try:
                if self.is_satisfied(xy):
                    n += 1
            except EmptySpaceError:
                continue
        return n
    
    def get_proportion_satisfied(self) -> int:
        """
        Returns the proportion of agents on the board who are satisfied
        """
        return self.get_total_satisfied() / self.get_total_population()

    @abstractmethod
    def update(self) -> None:
        """
        Runs one full round of the simulation. Note this function mutates the board
        """
        pass
    
    