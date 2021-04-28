from typing import Tuple, Optional

from .peg import (
    Literal,
    Sequence,
    Choice,
    Nothing,
    Anything,
    Not,
    And,
    Repeat,
    Reference,
    Parser,
    nested_str,
    MemoTable,
    MemoKey,
    Match,
    Clause,
    Terminal,
    D,
)
from .act import (
    Debug,
    Capture,
    Rule,
    transform,
    Action,
    Discard,
    Commit,
    CapturedParseFailure,
)
from ..utility import cache_hash

__all__ = [
    # peg
    "Literal",
    "Sequence",
    "Choice",
    "Nothing",
    "Anything",
    "Not",
    "And",
    "Repeat",
    "Reference",
    "Parser",
    # act
    "Debug",
    "Capture",
    "Rule",
    "Action",
    "Discard",
    "Commit",
    "CapturedParseFailure",
    "transform",
    # helpers
    "chain",
    "either",
    "Range",
    "Delimited",
    "unescape",
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
        assert len(first) == len(last) > 0, "Range bounds must be of same length"
        self.first = first
        self.last = last
        self._length = len(first)

    def match(self, source: D, at: int, memo: MemoTable):
        candidate = source[at : at + self._length]
        if len(candidate) == self._length and self.first <= candidate <= self.last:
            return Match(self._length, (), at, self)
        return None

    def __eq__(self, other):
        return (
            isinstance(other, Range)
            and self.first == other.first
            and self.last == other.last
        )

    def __hash__(self):
        return hash((self.first, self.last))

    def __repr__(self):
        return f"{self.__class__.__name__}({self.first!r}, {self.last!r})"

    def __str__(self):
        return f"{self.first!r} - {self.last!r}"


class Delimited(Clause[D]):
    """
    A pair of clauses with arbitrary intermediate filler
    """

    __slots__ = ("sub_clauses", "_hash")

    @property
    def maybe_zero(self):
        assert not self.sub_clauses[0].maybe_zero
        return False

    def __init__(self, start: Clause[D], stop: Clause[D]):
        self.sub_clauses = start, stop
        self._hash = None

    @property
    def triggers(self) -> "Tuple[Clause[D]]":
        return self.sub_clauses[:1]

    def match(self, source: D, at: int, memo: MemoTable) -> Optional[Match]:
        start, stop = self.sub_clauses
        head = memo[MemoKey(at, start)]
        for offset in range(head.length, len(source) - at):
            try:
                tail = memo[MemoKey(at + offset, stop)]
            except KeyError:
                pass
            else:
                return Match(offset + tail.length, (head, tail), at, self)
        return None

    def __eq__(self, other):
        return isinstance(other, Delimited) and self.sub_clauses == other.sub_clauses

    @cache_hash
    def __hash__(self):
        return hash(self.sub_clauses)

    def __repr__(self):
        start, stop = self.sub_clauses
        return f"{self.__class__.__name__}(start={start!r}, stop={stop!r})"

    def __str__(self):
        return " :: ".join(map(nested_str, self.sub_clauses))


def unescape(literal: str) -> str:
    """Evaluate Python escape sequences in a string, e.g. ``r"\n"`` to ``"\n"``"""
    # see https://stackoverflow.com/a/57192592/5349916
    return literal.encode("latin-1", "backslashreplace").decode("unicode-escape")
