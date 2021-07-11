"""
Minimal parser required to bootstrap entire bootpeg parser
"""
import pathlib
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
from .interpret import Parser, Clause, Grammar


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


apegs_globals = {
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
        Grammar,
        Parser,
    )
}


# derived clauses
def neg(*clauses: Clause):
    return Sequence(*(Not(clause) for clause in clauses), Any(1))


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
            Transform(Choice(Value('""'), Value("''")), "Empty()"),
            Transform(Value("."), "Any(1)"),
            apply(
                "Value(literal[1:-1])",
                literal=Choice(
                    *(
                        Sequence(Value(quote), Repeat(neg(Value(quote))), Value(quote))
                        for quote in ('"', "'")
                    )
                ),
            ),
            apply("Reference(name)", name=Reference("identifier")),
        ),
    ),
    # clauses with unambiguous, non-zero prefix
    Rule(
        "prefix",
        Choice(
            apply("Not(expr)", _=Value("!"), expr=Entail(Reference("prefix"))),
            Sequence(Value("("), spaces, Entail(Sequence(Reference("expr"), spaces, Value(")")))),
            apply(
                "Choice(expr, Empty())",
                expr=Sequence(
                    Value("["), spaces, Entail(Sequence(Reference("expr"), spaces, Value("]")))
                ),
            ),
            apply(
                "Capture(expr, name, variadic)",
                variadic=Choice(
                    Transform(Value("*"), "True"),
                    Transform(Empty(), "False"),
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
            apply("Repeat(expr)", expr=Reference("prefix"), _=Value("+")),
            apply(
                "Choice(Repeat(expr), Empty())", expr=Reference("prefix"), _=Value("*")
            ),
            Reference("prefix"),
        ),
    ),
    Rule(
        "sequence",
        Choice(
            apply(
                "Sequence(head, tail)",
                head=Reference("sequence"),
                _=spaces,
                tail=Reference("repeat"),
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
            Reference("repeat"),
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
    Rule(
        "action_body",
        Repeat(
            Choice(
                neg(Value("{"), Value("}")),
                Sequence(Value("{"), Reference("action_body"), Entail(Value("}")))
            )
        )
    ),
    Rule(
        "action",
        apply(
            "body", _h=Value("{"), body=Reference("action_body"), _t=Entail(Value("}"))
        )
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
                    Value("    "), Reference("rule_choice"), Reference("end_line"),
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
    Rule(
        "top",
        Sequence(
            Transform(
                Capture(
                    Repeat(Choice(Reference("rule"), Reference("end_line"))),
                    "rules",
                    variadic=True,
                ),
                "Grammar(\"top\", *rules)",
            ),
            Not(Any(1)),
        ),
    ),
    **apegs_globals
)

bpeg_path = pathlib.Path(__file__).parent.parent / "grammars" / "bpeg.bpeg"
fail_idx = 177
print(
    repr(bpeg_path.read_text()[fail_idx-12:fail_idx]),
    repr(bpeg_path.read_text()[fail_idx:fail_idx+12])
)
min_parser.match(bpeg_path.read_text())
