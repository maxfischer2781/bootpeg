import string

from .pika import Literal, Sequence, Choice, Not, Repeat, Reference, Parser

ascii_escapes = str.maketrans({
    ord('\n'): 'n\u1ab0'
})


def range_parse(source: str, parser: Parser):
    match = parser.parse(source)
    print(source.translate(ascii_escapes))
    print('^', '-' * (match.length - 2), '^', sep='')


Letters = Choice(*(Literal(ch) for ch in string.ascii_letters))
identifier = Repeat(Choice(Letters, Literal("_")))
end_line = Literal("\n")

parser = Parser(
    "top",
    top=Reference("define"),
    define=Sequence(identifier, Literal(':'), end_line),
)
range_parse("hello:\n", parser)
