"""
The default bootpeg grammar
"""
from typing import Union
from functools import singledispatch

from ..apegs.boot import (
    Value,
    Range,
    Any,
    Empty,
    Sequence,
    Choice,
    Repeat,
    And,
    Not,
    Entail,
    Capture,
    Transform,
    Reference,
    Rule,
    Clause,
    Parser,
    Grammar,
    boot_parser,
)
from ..api import bootpeg_actions, bootpeg_post, import_parser
from ..typing import BootPegParser


precedence = {
    clause: prec for prec, clauses in enumerate(
        (
            [Value, Range, Any, Empty, Reference],
            [Not, And, Capture],
            [Repeat],
            [Sequence, Entail],
            [Choice, Transform],
        )
    ) for clause in clauses
}


def _wrapped(clause: Clause, parent: Clause) -> str:
    return f"({unparse(clause)})" if precedence[parent] < precedence[Clause] else unparse(clause)


@singledispatch
def unparse(clause: Union[Clause, Parser, Grammar]) -> str:
    """Format a ``clause`` according to bootpeg standard grammar"""
    raise NotImplementedError(f"Cannot unparse {clause!r} as bpeg")


@unparse.register(Value)
def unparse_literal(clause: Value) -> str:
    return repr(clause.value)


@unparse.register(Range)
def unparse_range(clause: Range) -> str:
    return f"{clause.lower!r} - {clause.upper!r}"


@unparse.register(Empty)
def unparse_empty(clause: Empty) -> str:
    return '""'


@unparse.register(Any)
def unparse_any(clause: Any) -> str:
    return "." * clause.length


@unparse.register(Reference)
def unparse_reference(clause: Reference) -> str:
    return clause.name


@unparse.register(Sequence)
def unparse_sequence(clause: Sequence) -> str:
    return " ".join(
        _wrapped(sub_clause, clause) for sub_clause in clause.sub_clauses
    )


@unparse.register(Choice)
def unparse_choice(clause: Choice) -> str:
    return " | ".join(
        _wrapped(sub_clause, clause) for sub_clause in clause.sub_clauses
    )


@unparse.register(Repeat)
def unparse_repeat(clause: Repeat) -> str:
    return _wrapped(clause.sub_clause, clause) + "+"


@unparse.register(Not)
def unparse_not(clause: Not) -> str:
    return "!" + _wrapped(clause.sub_clause, clause)


@unparse.register(And)
def unparse_and(clause: And) -> str:
    return "&" + _wrapped(clause.sub_clause, clause)


@unparse.register(Capture)
def unparse_capture(clause: Capture) -> str:
    return f"{clause.name}={_wrapped(clause.sub_clause, clause)}"


@unparse.register(Rule)
def unparse_rule(clause: Rule) -> str:
    cases = clause.sub_clause.sub_clauses if isinstance(clause.sub_clause, Choice) else clause.sub_clause
    body = "\n".join(f"    | {unparse(case)}" for case in cases)
    return f"{clause.name}:\n{body}"


def boot_dialect(source):
    return boot_parser(source)[0]


parse: BootPegParser[str, BootPegParser] = import_parser(
    __name__,
    dialect=boot_dialect,
    actions=bootpeg_actions,
    post=bootpeg_post,
)
