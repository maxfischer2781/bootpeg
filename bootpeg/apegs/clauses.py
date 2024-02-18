"""
Abstract clauses understood by the PikaTwo parsing algorithm
"""

from typing import Generic, Union

from ..typing import D
from ..utility import slotted


Clause = Union[
    "Value[D]",
    "Range[D]",
    "Empty[D]",
    "Any[D]",
    "Sequence[D]",
    "Choice[D]",
    "Repeat[D]",
    "Not[D]",
    "And[D]",
    "Entail[D]",
    "Capture[D]",
    "Transform[D]",
    "Reference[D]",
]


@slotted
class Value(Generic[D]):
    """A terminal clause, matching a predefined value"""

    __slots__ = ("value",)

    def __init__(self, value: D):
        self.value = value


@slotted
class Range(Generic[D]):
    """A terminal clause, matching an inclusive range of predefined values"""

    __slots__ = ("lower", "upper")

    def __init__(self, lower: D, upper: D):
        if len(lower) != len(upper):
            raise ValueError(f"Bounds must be of same length, got {lower} and {upper}")
        self.lower, self.upper = (lower, upper) if lower < upper else (upper, lower)


@slotted
class Empty(Generic[D]):
    """The zero-length terminal ε, matching everywhere in the input"""

    __slots__ = ()


@slotted
class Any(Generic[D]):
    """Any fixed length terminal, matching at any point with sufficient remainder"""

    __slots__ = ("length",)

    def __init__(self, length: int):
        assert length > 0
        self.length = length


@slotted
class Sequence(Generic[D]):
    """A sequence of clauses, matching if all ``sub_clauses`` match in order"""

    __slots__ = ("sub_clauses",)

    def __init__(self, *sub_clauses: "Clause[D]"):
        self.sub_clauses = sub_clauses


@slotted
class Entail(Generic[D]):
    """Mark ``sub_clauses`` as inevitable by the match so far, making failure fatal"""

    __slots__ = ("sub_clauses",)

    def __init__(self, *sub_clauses: "Clause[D]"):
        self.sub_clauses = sub_clauses


@slotted
class Choice(Generic[D]):
    """A choice of clauses, matching the first matching clause of ``sub_clauses``"""

    __slots__ = ("sub_clauses",)

    def __init__(self, *sub_clauses: "Clause[D]"):
        self.sub_clauses = sub_clauses


@slotted
class Repeat(Generic[D]):
    """A repetition of a clause, matching if the ``sub_clause`` matches at least once"""

    __slots__ = ("sub_clause",)

    def __init__(self, sub_clause: "Clause[D]"):
        self.sub_clause = sub_clause


@slotted
class Not(Generic[D]):
    """The inversion of a clause, matching if the ``sub_clause`` does not match"""

    __slots__ = ("sub_clause",)

    def __init__(self, sub_clause: "Clause[D]"):
        self.sub_clause = sub_clause


@slotted
class And(Generic[D]):
    """The lookahead of a clause, matching with the ``sub_clause`` without advancing"""

    __slots__ = ("sub_clause",)

    def __init__(self, sub_clause: "Clause[D]"):
        self.sub_clause = sub_clause


@slotted
class Capture(Generic[D]):
    """The capturing of a clause match result with a name"""

    __slots__ = ("sub_clause", "name", "variadic")

    def __init__(self, sub_clause: "Clause[D]", name, variadic):
        self.sub_clause = sub_clause
        self.name = name
        self.variadic = variadic


@slotted
class Transform(Generic[D]):
    """The transformation of a clause match result"""

    __slots__ = ("sub_clause", "action")

    def __init__(self, sub_clause: "Clause[D]", action: str):
        self.sub_clause = sub_clause
        self.action = action


@slotted
class Reference(Generic[D]):
    """Reference to a named clause, i.e. a rule"""

    __slots__ = ("name",)

    def __init__(self, name: str):
        self.name = name


@slotted
class Rule(Generic[D]):
    """A named clause"""

    __slots__ = ("name", "sub_clause")

    def __init__(self, name: str, sub_clause: "Clause[D]"):
        self.name = name
        self.sub_clause = sub_clause
