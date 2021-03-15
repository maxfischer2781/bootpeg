import string
import time

from .pika import Literal, Sequence, Choice, Nothing, Anything, Not, Repeat, Reference, Parser, Clause, D, MemoKey, MemoTable

ascii_escapes = str.maketrans({
    ord('\n'): 'n\u1ab0'
})


def escape(ascii: str) -> str:
    return ascii.translate(ascii_escapes)


class Debug(Clause[D]):
    def __init__(self, sub_clause, name: str = None):
        self.sub_clauses = (sub_clause,)
        self.name = name or str(sub_clause)

    @property
    def maybe_zero(self):
        return self.sub_clauses[0].maybe_zero

    def match(self, source: D, at: int, memo: MemoTable):
        try:
            parent_match = memo[MemoKey(at, self.sub_clauses[0])]
        except KeyError:
            return None
        else:
            print('match', self.name, 'at', at, ':', parent_match.length)
            print("'", escape(source[at:at+parent_match.length]), "'", sep="")
            return parent_match

    def __eq__(self, other):
        return isinstance(other, Literal) and self.sub_clauses == other.sub_clauses

    def __hash__(self):
        return hash(self.sub_clauses)

    def __str__(self):
        return f":{self.name}:"


def range_parse(source: str, parser: Parser):
    start = time.perf_counter()
    match = parser.parse(source)
    until = time.perf_counter()
    print(*(i % 10 for i in range(len(source))), sep='')
    print(source.translate(ascii_escapes))
    print('^', '-' * (match.length - 2), '^', sep='')
    print(f"{until - start:.3f}s")


# TODO: Add automatic rule deduplication
Letters = Choice(*(Literal(ch) for ch in string.ascii_letters))
identifier = Repeat(Choice(Letters, Literal("_")))
spaces = Choice(Repeat(Literal(" ")), Nothing())
end_line = Literal("\n")
double_quote = Literal('"')
single_quote = Literal("'")

parser = Parser(
    "top",
    top=Reference("define"),
    literal=Sequence(double_quote, Anything(), double_quote),
    name=identifier,
    sequence=Sequence(Reference("expr"), spaces, Reference("expr")),
    expr=Choice(Reference("sequence"), Reference("literal"), Reference("name")),
    define=Sequence(identifier, Literal(':'), spaces, end_line, Reference("rule")),
    rule=Sequence(spaces, Literal("|"), spaces, Reference("expr")),
)
print('--------------------------------------------')
range_parse("""hello:\n    | a "+" b\n""", parser)
print('--------------------------------------------')
parser._prepare()
for name, clause in parser._compiled_parser[0].items():
    print(f"{name:<10} <-", clause)
    print('0:', clause.maybe_zero)
    if isinstance(clause, Debug):
        print(clause.sub_clauses[0])
