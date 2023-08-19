from typing import Callable, TypeVar, Iterable, Iterator, List

A = TypeVar("A")
B = TypeVar("B")

# def count(pred: Callable[[A], bool], iter: Iterable[A]):
#     """
#     Counts the number of elements of `iter` which satisfy `pred`
#     """
#     return sum(map(pred, iter))


def interleave(a: Iterable[A], b: Iterable[B]) -> Iterator[A | B]:
    """
    Interleaves two iterators. If an iterator is spent, it simply removes that iterator and continues interleaving the others, and so on until there are no iterators left yielding anything
    """
    iter1: Iterator[A] = iter(a)
    iter2: Iterator[B] = iter(b)

    while True:
        try:
            yield next(iter1)
        except StopIteration:
            try:
                while True:
                    yield next(iter2)
            except StopIteration:
                return
        try:
            yield next(iter2)
        except StopIteration:
            try:
                while True:
                    yield next(iter1)
            except StopIteration:
                return


def percentage(p: float) -> str:
    """
    Displays p as a whole-number percentage
    """
    return f"{round(100 * p)}%"
