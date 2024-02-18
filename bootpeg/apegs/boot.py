"""
Minimal parser required to bootstrap entire bootpeg parser
"""

import string

import importlib_resources

from .clauses import (
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
)
from .interpret import Clause
from .front import Parser, Grammar


def apply(__func: str, **captures) -> Transform:
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


apegs_actions = {
    clause.__name__: clause
    for clause in (
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
        Grammar,
        Parser,
    )
}


# derived clauses
def neg(*clauses: Clause):
    return Sequence(*(Not(clause) for clause in clauses), Any(1))


spaces: Choice[str] = Choice(Value(" "), Empty())

boot_parser: Parser[str, Grammar] = Parser(
    Rule(
        "top",
        Sequence(
            Transform(
                Capture(
                    Repeat(Choice(Reference("rule"), Reference("end_line"))),
                    "rules",
                    variadic=True,
                ),
                "Grammar(*rules)",
            ),
            Not(Any(1)),
        ),
    ),
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
    Rule(
        "literal",
        Choice(
            *(
                Sequence(Value(quote), Repeat(neg(Value(quote))), Entail(Value(quote)))
                for quote in ('"', "'")
            )
        ),
    ),
    # rule matching
    Rule(
        "action_body",
        Repeat(
            Choice(
                neg(Value("{"), Value("}")),
                Sequence(Value("{"), Reference("action_body"), Entail(Value("}"))),
            )
        ),
    ),
    Rule(
        "action",
        apply(
            "body", _h=Value("{"), body=Reference("action_body"), _t=Entail(Value("}"))
        ),
    ),
    Rule(
        "rule_choice",
        Choice(
            apply(
                "Transform(expr, action)",
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
                "Choice(first, otherwise)",
                first=Reference("rule_body"),
                otherwise=Sequence(
                    Value("    "), Reference("rule_choice"), Reference("end_line")
                ),
            ),
            Sequence(Value("    "), Reference("rule_choice"), Reference("end_line")),
        ),
    ),
    Rule(
        "rule",
        apply(
            "Rule(name, body)",
            name=Reference("identifier"),
            _=Sequence(Value(":"), Reference("end_line")),
            body=Reference("rule_body"),
        ),
    ),
    # atomic clauses without sub-clauses
    Rule(
        "atom",
        Choice(
            Transform(Choice(Value('""'), Value("''")), "Empty()"),
            Transform(Value("."), "Any(1)"),
            Transform(Value("\\n"), "Value('\\n')"),
            apply(
                "Range(lower[1:-1], upper[1:-1])",
                lower=Reference("literal"),
                _=Sequence(spaces, Value("-"), spaces),
                upper=Entail(Reference("literal")),
            ),
            apply("Value(literal[1:-1])", literal=Reference("literal")),
            apply("Reference(name)", name=Reference("identifier")),
        ),
    ),
    # clauses with unambiguous, non-zero prefix
    Rule(
        "prefix",
        Choice(
            apply("Not(expr)", _=Value("!"), expr=Entail(Reference("prefix"))),
            Sequence(
                Value("("),
                spaces,
                Entail(Sequence(Reference("expr"), spaces, Value(")"))),
            ),
            apply(
                "Choice(expr, Empty())",
                expr=Sequence(
                    Value("["),
                    spaces,
                    Entail(Sequence(Reference("expr"), spaces, Value("]"))),
                ),
            ),
            Reference("atom"),
        ),
    ),
    Rule(
        "repeat",
        Choice(
            apply("Repeat(expr)", expr=Reference("prefix"), _=Value("+")),
            apply(
                "Choice(Repeat(expr), Empty())", expr=Reference("prefix"), _=Value("*")
            ),
            Reference("prefix"),
        ),
    ),
    Rule(
        "capture",
        Choice(
            apply(
                "Capture(expr, name, variadic)",
                variadic=Choice(
                    Transform(Value("*"), "True"),
                    Transform(Empty(), "False"),
                ),
                name=Reference("identifier"),
                _=Value("="),
                expr=Entail(Reference("repeat")),
            ),
            Reference("repeat"),
        ),
    ),
    Rule(
        "sequence",
        Choice(
            apply(
                "Sequence(head, tail)",
                head=Reference("sequence"),
                _=spaces,
                tail=Reference("capture"),
            ),
            apply(
                "Sequence(head, Entail(tail))",
                head=Reference("sequence"),
                _=Sequence(spaces, Value("~"), spaces),
                tail=Entail(Reference("sequence")),
            ),
            apply(
                "Entail(seq)",
                seq=Sequence(Value("~"), spaces, Entail(Reference("sequence"))),
            ),
            Reference("capture"),
        ),
    ),
    Rule(
        "choice",
        Choice(
            apply(
                "Choice(first, otherwise)",
                first=Reference("choice"),
                _=Sequence(spaces, Value("|"), spaces),
                otherwise=Entail(Reference("sequence")),
            ),
            Reference("sequence"),
        ),
    ),
    Rule(
        "expr",
        Reference("choice"),
    ),
    **apegs_actions,
)

bpeg_parser: Parser[str, Grammar] = boot_parser(
    importlib_resources.read_text("bootpeg.grammars", "bpeg.bpeg")
).parser(**apegs_actions)
