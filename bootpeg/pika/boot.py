import string
import time
import pathlib

from .peg import postorder_dfs
from .front import *
from ..utility import ascii_escapes


def range_parse(source: str, parser: Parser):
    """Parse ``source`` showing the matched range"""
    start = time.perf_counter()
    match, memo = parser.parse(source)
    until = time.perf_counter()
    print(*(i % 10 for i in range(len(source))), sep='')
    print(source.translate(ascii_escapes))
    print('^', '-' * (match.length - 2), '^', sep='')
    print(f"{until - start:.3f}s")
    # for name, clause in transform(match, memo, namespace)[0]:
    #     print(f"{name:<10} <-", clause)
    return Parser(
        "top",
        **{
            name: clause for name, clause in transform(match, memo, namespace)[0]
        }
    )


def display(parser: Parser):
    parser._prepare()
    print("Rules:", len(list(postorder_dfs(parser._compiled_parser[0][parser.top]))))
    for name, clause in parser._compiled_parser[0].items():
        print(f"{name:<10} <-", clause)
        if isinstance(clause, Debug):
            print('Debugs:', clause.sub_clauses[0])


namespace = {
    expression.__name__: expression for expression in
    (Literal, Sequence, chain, Choice, either, Nothing, Anything, Not, Repeat, Reference, Capture, Rule, Action)
}


Letters = Choice(*(Literal(ch) for ch in string.ascii_letters))
spaces = Choice(Repeat(Literal(" ")), Nothing())
end_line = Literal("\n")

parser = Parser(
    "top",
    literal=Rule(
        Choice(
            *(
                Sequence(quote, Repeat(Sequence(Not(quote), Anything())), quote)
                for quote in (Literal("'"), Literal('"'))
            )
        ),
        Action("Literal(.*[1:-1])"),
    ),
    nothing=Rule(
        Choice(Literal("''"), Literal('""')),
        Action("Nothing()"),
    ),
    anything=Rule(
        Literal("."),
        Action("Literal(.*)"),
    ),
    identifier=Repeat(Choice(Letters, Literal("_"))),
    choice=Rule(
        Sequence(Capture("try", Reference("expr")), spaces, Literal("|"), spaces, Capture("else", Reference("expr"))),
        Action("either(.try, .else)"),
    ),
    group=Rule(
        Sequence(Literal("("), spaces, Capture("expr", Reference("expr")), spaces, Literal(")")),
        Action(".expr"),
    ),
    sequence=Rule(
        Sequence(Capture("head", Reference("expr")), spaces, Capture("tail", Reference("expr"))),
        Action("chain(.head, .tail)"),
    ),
    repeat=Rule(
        Sequence(Capture("expr", Reference("expr")), spaces, Literal('+')),
        Action("Repeat(.expr)"),
    ),
    reference=Rule(
        Capture("name", Reference("identifier")),
        Action("Reference(.name)"),
    ),
    capture=Rule(
        Sequence(Capture("name", Reference("identifier")), spaces, Literal("="), spaces, Capture("expr", Choice(Reference("reference"), Reference("group")))),
        Action("Capture(.name, .expr)"),
    ),
    reject=Rule(
        Sequence(Literal("!"), spaces, Capture("expr", Reference("expr"))),
        Action("Not(.expr)")
    ),
    expr=Rule(
        Capture(
            "expr",
            Choice(
                Reference("choice"), Reference("sequence"), Reference("repeat"), Reference("capture"), Reference("reference"), Reference("group"), Reference("literal"), Reference("reject"), Reference("anything"), Reference("nothing")
            )
        ),
        Action(".expr"),
    ),
    action=Rule(
        Sequence(Literal("{"), Capture("body", Repeat(Sequence(Not(Literal("}")), Anything()))), Literal("}")),
        Action("Action(.body)"),
    ),
    rule=Rule(
        Sequence(Literal("|"), spaces, Capture("expr", Reference("expr")), spaces, Capture("action", Reference("action"))),
        Action("Rule(.expr, .action)"),
    ),
    rules=Rule(
        Capture(
            "rule",
            Choice(
                Rule(
                    Sequence(Literal(" "), spaces, Capture("try", Reference("rule")), spaces, end_line, Capture("else", Reference("rules"))),
                    Action("either(.try, .else)"),
                ),
                Rule(
                    Sequence(Literal(" "), spaces, Capture("rule", Reference("rule")), spaces, end_line),
                    Action(".rule"),
                ),
            )
        ),
        Action(".rule"),
    ),
    define=Rule(
        Sequence(Capture("name", Reference("identifier")), Literal(':'), spaces, end_line, Capture("rules", Reference("rules"))),
        Action("(.name, .rules)"),
    ),
    comment=Sequence(Literal("#"), Repeat(Sequence(Not(end_line), Anything())), end_line),
    blank=Sequence(spaces, end_line),
    top=Repeat(Choice(Reference("define"), Reference("comment"), Reference("blank"))),
)

display(parser)
for iteration in range(3):
    with open(pathlib.Path(__file__).parent / 'boot.peg') as boot_peg:
        print('Generation:', iteration)
        parser = range_parse(
            boot_peg.read(),
            parser,
        )
        display(parser)
