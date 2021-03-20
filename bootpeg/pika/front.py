from typing import NamedTuple, Callable
from .peg import (
    Literal,
    Sequence,
    Choice,
    Nothing,
    Anything,
    Not,
    Repeat,
    Reference,
    Parser,
    MemoTable,
    Match,
    Terminal,
    D,
)
from .act import Debug, Capture, Rule, transform, Action, Discard

__all__ = [
    # peg
    "Literal",
    "Sequence",
    "Choice",
    "Nothing",
    "Anything",
    "Not",
    "Repeat",
    "Reference",
    "Parser",
    # act
    "Debug",
    "Capture",
    "Rule",
    "Action",
    "Discard",
    "transform",
    # helpers
    "chain",
    "either",
    "Range",
]


def chain(left, right) -> Sequence:
    """Chain two clauses efficiently"""
    if isinstance(left, Sequence):
        if isinstance(right, Sequence):
            return Sequence(*left.sub_clauses, *right.sub_clauses)
        return Sequence(*left.sub_clauses, right)
    if isinstance(right, Sequence):
        return Sequence(left, *right.sub_clauses)
    return Sequence(left, right)


def either(left, right) -> Choice:
    """Choose between two clauses efficiently"""
    if isinstance(left, Choice):
        if isinstance(right, Choice):
            return Choice(*left.sub_clauses, *right.sub_clauses)
        return Choice(*left.sub_clauses, right)
    if isinstance(right, Choice):
        return Choice(left, *right.sub_clauses)
    return Choice(left, right)


class Range(Terminal[D]):
    """
    A terminal matching anything between two bounds inclusively
    """

    __slots__ = ("first", "last", "_length")
    maybe_zero = False

    def __init__(self, first: D, last: D):
        assert len(first) == len(last) > 0
        self.first = first
        self.last = last
        self._length = len(first)

    def match(self, source: D, at: int, memo: MemoTable):
        candidate = source[at : at + self._length]
        if len(candidate) == self._length and self.first <= candidate <= self.last:
            return Match(self._length, (), at, self)
        return None

    def __eq__(self, other):
        return isinstance(other, Range) and self.first == other.first and self.last == other.last

    def __hash__(self):
        return hash((self.first, self.last))

    def __repr__(self):
        return f"{self.__class__.__name__}({self.first!r}, {self.last!r})"

    def __str__(self):
        return f"{self.first!r} - {self.last!r}"
