"""
Minimal parser required to bootstrap entire bootpeg parser
"""
from typing import Callable
import string

from .clauses import (
    Value,
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
)
from .interpret import Parser, Clause


def apply(__func: Callable, **captures) -> Transform:
    """Helper to create a Transform and Captures from keywords"""
    return Transform(
        Sequence(
            *(
                Capture(clause, name, False) if not name[0] == "_" else clause
                for name, clause in captures.items()
            )
        ),
        __func,
    )


def apegs_action(body: str) -> Callable[..., Clause]:
    return eval("lambda " + body, clause_globals)


clause_globals = {
    clause.__name__: clause
    for clause in (
        Value,
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
        apegs_action,
    )
}


# derived clauses
def neg(clause: Clause):
    return Sequence(Not(clause), Any(1))


spaces = Choice(Value(" "), Empty())

min_parser = Parser(
    "top",
    Rule(
        "end_line",
        Sequence(
            spaces,
            Choice(Sequence(Value("#"), Repeat(neg(Value("\n")))), Empty()),
            Choice(Value("\n"), Not(Any(1))),
        ),
    ),
    Rule(
        "identifier", Repeat(Choice(*(Value(ch) for ch in string.ascii_letters + "_")))
    ),
    # atomic clauses without sub-clauses
    Rule(
        "atom",
        Choice(
            apply(lambda: Empty(), _=Choice(Value('""'), Value("''"))),
            apply(lambda: Any(1), _=Value(".")),
            apply(
                lambda literal: Value(literal[1:-1]),
                literal=Choice(
                    *(
                        Sequence(Value(quote), Repeat(neg(Value(quote))), Value(quote))
                        for quote in ('"', "'")
                    )
                ),
            ),
            apply(lambda name: Reference(name), name=Reference("identifier")),
        ),
    ),
    # clauses with unambiguous, non-zero prefix
    Rule(
        "prefix",
        Choice(
            apply(lambda expr: Not(expr), _=Value("!"), expr=Reference("prefix")),
            Sequence(Value("("), spaces, Reference("expr"), spaces, Value(")")),
            apply(
                lambda expr: Choice(expr, Empty()),
                expr=Sequence(
                    Value("("), spaces, Reference("expr"), spaces, Value(")")
                ),
            ),
            apply(
                lambda name, expr, variadic: Capture(expr, name, variadic),
                variadic=Choice(
                    Transform(Value("*"), lambda: True),
                    Transform(Empty(), lambda: False),
                ),
                name=Reference("identifier"),
                _=Value("="),
                expr=Entail(Reference("expr")),
            ),
            Reference("atom"),
        ),
    ),
    # left-recursive clauses, highest precedence to lowest
    Rule(
        "repeat",
        Choice(
            apply(lambda expr: Repeat(expr), expr=Reference("prefix"), _=Value("+")),
            apply(
                lambda expr: Choice(Repeat(expr), Empty()),
                expr=Reference("prefix"),
                _=Value("*"),
            ),
            Reference("prefix"),
        ),
    ),
    Rule(
        "sequence",
        Choice(
            apply(
                lambda head, tail: Sequence(head, tail),
                head=Reference("sequence"),
                _=spaces,
                tail=Reference("repeat"),
            ),
            apply(
                lambda head, tail: Sequence(head, Entail(tail)),
                head=Reference("sequence"),
                _=Sequence(spaces, Value("~"), spaces),
                tail=Entail(Reference("sequence")),
            ),
            apply(
                lambda seq: Entail(seq),
                seq=Sequence(Value("~"), spaces, Entail(Reference("sequence"))),
            ),
            Reference("repeat"),
        ),
    ),
    Rule(
        "choice",
        Choice(
            apply(
                lambda first, otherwise: Choice(first, otherwise),
                first=Reference("choice"),
                _=Sequence(spaces, Value("|"), spaces),
                otherwise=Reference("sequence"),
            ),
            Reference("sequence"),
        ),
    ),
    Rule(
        "expr",
        Reference("choice"),
    ),
    Rule(
        "action",
        apply(
            apegs_action,
            _h=Value("{"),
            body=Repeat(neg(Value("}"))),
            _t=Value("}"),
        ),
    ),
    Rule(
        "rule_choice",
        Choice(
            apply(
                lambda expr, action: Transform(expr, action),
                _h=Value("| "),
                expr=Reference("expr"),
                _s=spaces,
                action=Reference("action"),
            ),
            Sequence(Value("| "), Reference("expr")),
        ),
    ),
    Rule(
        "rule_body",
        Choice(
            apply(
                lambda first, otherwise: Choice(first, otherwise),
                first=Reference("rule_body"),
                otherwise=Sequence(
                    Value("    "), Reference("rule_choice"), Value("\n")
                ),
            ),
            Sequence(Value("    "), Reference("rule_choice"), Value("\n")),
        ),
    ),
    Rule(
        "rule",
        apply(
            lambda name, body: Rule(name, body),
            name=Reference("identifier"),
            _=Sequence(Value(":\n")),
            body=Reference("rule_body"),
        ),
    ),
    Rule(
        "discard",
        Choice(
            Sequence(Value("#"), Repeat(neg(Value("\n"))), Value("\n")),
            Value("\n"),
        ),
    ),
    Rule(
        "top",
        Sequence(
            Transform(
                Capture(
                    Repeat(Choice(Reference("rule"), Reference("discard"))),
                    "rules",
                    variadic=True,
                ),
                lambda rules: Parser("top", *rules),
            ),
            Not(Any(1)),
        ),
    ),
)
