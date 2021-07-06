"""
Abstract clauses understood by the PikaTwo parsing algorithm
"""
from typing import Generic, Union

from ..typing import D
from ..utility import slotted


Clauses = Union[
    "Value",
    "Empty",
    "Any",
    "Sequence",
    "Choice",
    "Repeat",
    "Not",
    "And",
    "Annotate",
    "Reference",
]


@slotted
class Value(Generic[D]):
    """A terminal clause, matching a predefined value"""

    __slots__ = ("value",)

    def __init__(self, value: D):
        self.value = value


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

    def __init__(self, *sub_clauses: "Clauses[D]"):
        self.sub_clauses = sub_clauses


@slotted
class Choice(Generic[D]):
    """A choice of clauses, matching the first matching clause of ``sub_clauses``"""

    __slots__ = ("sub_clauses",)

    def __init__(self, *sub_clauses: "Clauses[D]"):
        self.sub_clauses = sub_clauses


@slotted
class Repeat(Generic[D]):
    """A repetition of a clause, matching if the ``sub_clause`` matches at least once"""

    __slots__ = ("sub_clause",)

    def __init__(self, sub_clause: "Clauses[D]"):
        self.sub_clause = sub_clause


@slotted
class Not(Generic[D]):
    """The inversion of a clause, matching if the ``sub_clause`` does not match"""

    __slots__ = ("sub_clause",)

    def __init__(self, sub_clause: "Clauses[D]"):
        self.sub_clause = sub_clause


@slotted
class And(Generic[D]):
    """The lookahead of a clause, matching with the ``sub_clause`` without advancing"""

    __slots__ = ("sub_clause",)

    def __init__(self, sub_clause: "Clauses[D]"):
        self.sub_clause = sub_clause


@slotted
class Capture(Generic[D]):
    """The capturing of a clause match result with a name"""

    __slots__ = ("sub_clause", "name", "variadic")

    def __init__(self, sub_clause: "Clauses[D]", name, variadic):
        self.sub_clause = sub_clause
        self.name = name
        self.variadic = variadic


@slotted
class Transform(Generic[D]):
    """The transformation of a clause match result"""

    __slots__ = ("sub_clause", "py_call")

    def __init__(self, sub_clause: "Clauses[D]", py_call):
        self.sub_clause = sub_clause
        self.py_call = py_call


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

    def __init__(self, name: str, sub_clause: "Clauses[D]"):
        self.name = name
        self.sub_clause = sub_clause