import string
import time

from .pika_peg import Literal, Sequence, Choice, Nothing, Anything, Not, Repeat, Reference, Parser, postorder_dfs
from .pika_act import Debug, Capture, Rule
from .utility import ascii_escapes


def range_parse(source: str, parser: Parser):
    """Parse ``source`` showing the matched range"""
    start = time.perf_counter()
    match, _ = parser.parse(source)
    until = time.perf_counter()
    print(*(i % 10 for i in range(len(source))), sep='')
    print(source.translate(ascii_escapes))
    print('^', '-' * (match.length - 2), '^', sep='')
    print(f"{until - start:.3f}s")


Letters = Choice(*(Literal(ch) for ch in string.ascii_letters))
identifier = Repeat(Choice(Letters, Literal("_")))
spaces = Choice(Repeat(Literal(" ")), Nothing())
end_line = Literal("\n")
double_quote = Literal('"')
single_quote = Literal("'")

parser = Parser(
    "top",
    top=Repeat(Choice(Reference("define"), Reference("comment"))),
    comment=Sequence(Literal("#"), Repeat(Sequence(Not(end_line), Anything())), end_line),
    literal=Choice(
        *(
            Sequence(quote, Repeat(Sequence(Not(quote), Anything())), quote)
            for quote in (Literal("'"), Literal('"'))
        )
    ),
    name=identifier,
    chain=Sequence(Reference("expr"), spaces, Reference("expr")),
    expr=Choice(Reference("chain"), Reference("literal"), Reference("name")),
    define=Sequence(identifier, Literal(':'), spaces, end_line, Reference("rule")),
    rule=Sequence(spaces, Literal("|"), spaces, Reference("expr"), spaces, end_line),
)
print('--------------------------------------------')
range_parse('''#example\nhello:\n    | a ".\t+" b\n''', parser)
print('--------------------------------------------')
parser._prepare()
print("Rules:", len(list(postorder_dfs(parser._compiled_parser[0][parser.top]))))
for name, clause in parser._compiled_parser[0].items():
    print(f"{name:<10} <-", clause)
    if isinstance(clause, Debug):
        print('Debugs:', clause.sub_clauses[0])
