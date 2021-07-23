import sys

import pytest

from bootpeg import create_parser, actions
from bootpeg.grammars import peg
from bootpeg.apegs import (
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
    Parser,
)


roundtrip_clauses = [
    Empty(),
    Any(1),
    *(Value(literal) for literal in ("A", "x", "ß", " ")),
    Sequence(Value("A"), Value("B"), Value("A")),
    Sequence(Value(" "), Value(" ")),
    Choice(Value("a"), Value("b"), Empty()),
    Repeat(Value("x")),
    Repeat(Sequence(Value("x"), Value("y"), Value("z"))),
    Not(Value("a")),
    And(Value("a")),
    Reference("some_rule"),
    Range("a", "b"),
    Entail(Value("a"), Value("b")),
    Sequence(Value("head"), Entail(Value("a"), Value("b"))),
    Capture(Value("expr"), "name", True, False),
    Capture(Value("expr"), "name", False, False),
    Transform(Value("body"), "{True}"),
]


@pytest.mark.parametrize("clause", roundtrip_clauses)
def test_roundtrip(clause):
    clause = clause
    literal = peg.unparse(clause)
    assert literal
    parsed_rule: Rule = peg.parse(f"parse_test <- {literal}\n").rules[0]
    assert parsed_rule.sub_clause == clause


sys.setrecursionlimit(30000)

# Adapted from PEG paper
# Some fixes due to errors in the original grammar
peg_grammar = r"""
# Hierarchical syntax
Grammar    <- (Spacing Definition)+ EndOfFile
Definition <- Identifier LEFTARROW Expression Spacing

Expression <- Sequence (SLASH Sequence)*
Sequence   <- (Prefix Spacing)+
Prefix     <- (AND / NOT)? Suffix
Suffix     <- Primary (QUESTION / STAR / PLUS)?
Primary    <- Identifier !(LEFTARROW)
            / OPEN Expression CLOSE
            / Literal / Class / DOT

# Lexical syntax
Identifier <- IdentStart IdentCont* Spacing
IdentStart <- [a-zA-Z_]
IdentCont  <- IdentStart / [0-9]
Literal    <- ['] (!['] Char)* ['] Spacing
            / ["] (!["] Char)* ["] Spacing
Class      <- '[' (!']' Range)* ']' Spacing
Range      <- Char '-' Char / Char
Char       <- '\\' [nrt'"\[\]\\]
            / '\\' [0-2][0-7][0-7]
            / '\\' [0-7][0-7]?
            / !'\\' .

# Symbols
LEFTARROW <- Spacing '<-' Spacing
SLASH     <- Spacing '/' Spacing
AND       <- Spacing '&' Spacing
NOT       <- Spacing '!' Spacing
QUESTION  <- Spacing '?' Spacing
STAR      <- Spacing '*' Spacing
PLUS      <- Spacing '+' Spacing
OPEN      <- Spacing '(' Spacing
CLOSE     <- Spacing ')' Spacing
DOT       <- Spacing '.' Spacing

# Separators
Spacing   <- (Space / Comment)*
Comment   <- '#' (!EndOfLine .)* EndOfLine
Space     <- ' ' / '\t' / EndOfLine
EndOfLine <- '\r\n' / '\n' / '\r'
EndOfFile <- !.
"""


def test_parse_reference():
    """Parse the PEG reference grammar"""
    parse = create_parser(peg_grammar, dialect=peg)
    # reference PEG does not understand results, but bootpeg requires them
    parse = Parser(
        Rule(parse.rules[0].name, Transform(parse.rules[0].sub_clause, "()")),
        *parse.rules[1:],
    )
    assert parse(peg_grammar) == ()


def test_parse_short():
    """Parse a single-line grammar"""
    assert peg.parse("""top <- ab ab <- a / b a <- "a" ab? b <- "b" ab?""")


def test_unparse():
    """Test that unparsing produces valid grammars"""
    parser = peg.parse
    for i in range(3):
        prev_gram = peg.unparse(parser)
        parser = create_parser(prev_gram, parser, {**actions, "unescape": peg.unescape})
        # grammar is not optimal for peg when coming from bpeg
        assert i == 0 or prev_gram == peg.unparse(parser)
