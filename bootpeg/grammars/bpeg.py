"""
The default bootpeg grammar
"""
from typing import Union
from functools import singledispatch

from ..pika.peg import (
    Clause,
    Nothing,
    Anything,
    Literal,
    Sequence,
    Choice,
    Repeat,
    Not,
    And,
    Reference,
    Parser,
)
from ..pika.act import Capture, Rule
from ..pika.front import Range, Delimited
from ..pika.boot import bootpeg, boot
from ..api import PikaActions, import_parser


@singledispatch
def unparse(clause: Union[Clause, Parser], top=True) -> str:
    """Format a ``clause`` according to bootpeg standard grammar"""
    raise NotImplementedError(f"Cannot unparse {clause!r} as bpeg")


@unparse.register(Nothing)
def unparse_nothing(clause: Nothing, top=True) -> str:
    return '""'


@unparse.register(Anything)
def unparse_anything(clause: Anything, top=True) -> str:
    return "." * clause.length


@unparse.register(Literal)
def unparse_literal(clause: Literal, top=True) -> str:
    return repr(clause.value)


@unparse.register(Sequence)
def unparse_sequence(clause: Sequence, top=True) -> str:
    children = " ".join(
        unparse(sub_clause, top=False) for sub_clause in clause.sub_clauses
    )
    return f"({children})" if not top else children


@unparse.register(Choice)
def unparse_choice(clause: Choice, top=True) -> str:
    children = " | ".join(
        unparse(sub_clause, top=False) for sub_clause in clause.sub_clauses
    )
    return f"({children})" if not top else children


@unparse.register(Repeat)
def unparse_repeat(clause: Repeat, top=True) -> str:
    return unparse(clause.sub_clauses[0], top=False) + "+"


@unparse.register(Not)
def unparse_not(clause: Not, top=True) -> str:
    return "!" + unparse(clause.sub_clauses[0], top=False)


@unparse.register(And)
def unparse_and(clause: And, top=True) -> str:
    return "&" + unparse(clause.sub_clauses[0], top=False)


@unparse.register(Reference)
def unparse_reference(clause: Reference, top=True) -> str:
    return clause.target


@unparse.register(Capture)
def unparse_capture(clause: Capture, top=True) -> str:
    return f"{clause.name}={unparse(clause.sub_clauses[0], top=False)}"


@unparse.register(Rule)
def unparse_rule(clause: Rule, top=True) -> str:
    return f"| {unparse(clause.sub_clauses[0])} {{{clause.action.literal}}}"


@unparse.register(Range)
def unparse_range(clause: Range, top=True) -> str:
    return f"{clause.first!r} - {clause.last!r}"


@unparse.register(Delimited)
def unparse_delimited(clause: Delimited, top=True) -> str:
    first, last = clause.sub_clauses
    return f"{unparse(first, top=False)} :: {unparse(last, top=False)}"


def boot_dialect(source):
    return boot(bootpeg(), source)


parse = import_parser(__name__, actions=PikaActions, dialect=boot_dialect)
