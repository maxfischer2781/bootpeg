import string
import time
from functools import partial

from .peg import Literal, Sequence, Choice, Nothing, Anything, Not, Repeat, Reference, Parser, postorder_dfs
from .act import Debug, Capture, Rule, transform, Action
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
    for clause in transform(match, memo)[0]:
        print(clause)


namespace = {
    expression.__name__: expression for expression in
    (Literal, Sequence, Choice, Nothing, Anything, Not, Repeat, Reference, Capture, Rule)
}
namespace['ParseAction'] = ParseAction = partial(Action, namespace=namespace)


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
        ParseAction("Literal(.(*))"),
    ),
    identifier=Repeat(Choice(Letters, Literal("_"))),
    choice=Rule(
        Sequence(Capture("try", Reference("expr")), spaces, Literal("|"), spaces, Capture("else", Reference("expr"))),
        ParseAction("Choice(.try, .else)"),
    ),
    group=Rule(
        Sequence(Literal("("), spaces, Capture("expr", Reference("expr")), spaces, Literal(")")),
        ParseAction(".expr"),
    ),
    sequence=Rule(
        Sequence(Capture("head", Reference("expr")), spaces, Capture("tail", Reference("expr"))),
        ParseAction("Sequence(.head, .tail)"),
    ),
    repeat=Rule(
        Sequence(Capture("base", Reference("expr")), spaces, Literal('+')),
        ParseAction("Repeat(.base)"),
    ),
    reference=Rule(
        Reference("identifier"),
        ParseAction("Reference(.(*))"),
    ),
    capture=Rule(
        Sequence(Capture("name", Reference("identifier")), spaces, Literal("="), spaces, Capture("rule", Reference("expr"))),
        ParseAction("Capture(.name, .rule)"),
    ),
    expr=Rule(
        Capture(
            "expr",
            Choice(
                Reference("choice"), Reference("sequence"), Reference("repeat"), Reference("group"), Reference("capture"), Reference("reference"), Reference("literal")
            )
        ),
        ParseAction(".expr"),
    ),
    action=Rule(
        Sequence(Literal("{"), spaces, Capture("body", Repeat(Sequence(Not(Literal("}")), Anything()))), spaces, Literal("}")),
        ParseAction("ParseAction(.body)"),
    ),
    rule=Rule(
        Sequence(Literal("|"), spaces, Capture("expr", Reference("expr")), spaces, Capture("action", Reference("action"))),
        ParseAction("Rule(.expr, .action)"),
    ),
    rules=Rule(
        Capture(
            "rule",
            Choice(
                Rule(
                    Sequence(Literal(" "), spaces, Capture("try", Reference("rule")), spaces, end_line, Capture("else", Reference("rules"))),
                    ParseAction("Choice(.try, .else)"),
                ),
                Rule(
                    Sequence(Literal(" "), spaces, Capture("rule", Reference("rule")), spaces, end_line),
                    ParseAction(".rule"),
                ),
            )
        ),
        ParseAction(".rule"),
    ),
    define=Rule(
        Sequence(Capture("name", Reference("identifier")), Literal(':'), spaces, end_line, Capture("rules", Reference("rules"))),
        ParseAction("{ .name : .rules }"),
    ),
    comment=Sequence(Literal("#"), Repeat(Sequence(Not(end_line), Anything())), end_line),
    blank=Sequence(spaces, end_line),
    top=Repeat(Choice(Reference("define"), Reference("comment"), Reference("blank"))),
)
print('--------------------------------------------')
range_parse('''\
#example
hello:
    | a "+" b | a {.(*)}
    | c "+" d {.(*)}

world:
    | (a=a)+ {.(*)}
''',
parser
)
print('--------------------------------------------')
parser._prepare()
print("Rules:", len(list(postorder_dfs(parser._compiled_parser[0][parser.top]))))
for name, clause in parser._compiled_parser[0].items():
    print(f"{name:<10} <-", clause)
    if isinstance(clause, Debug):
        print('Debugs:', clause.sub_clauses[0])
