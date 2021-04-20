import sys

import pytest

from bootpeg.grammars import peg
from bootpeg.pika.front import (
    Rule,
    Literal,
    Nothing,
    Anything,
    Sequence,
    Choice,
    Repeat,
    Not,
    And,
    Reference,
    Range,
    Delimited,
)


roundtrip_clauses = [
    Nothing(),
    Anything(1),
    *(Literal(literal) for literal in ("A", "x", "ß", " ")),
    Sequence(Literal("A"), Literal("B"), Literal("A")),
    Sequence(Literal(" "), Literal(" ")),
    Choice(Literal("a"), Literal("b"), Nothing()),
    Repeat(Literal("x")),
    Repeat(Sequence(Literal("x"), Literal("y"), Literal("z"))),
    Not(Literal("a")),
    And(Literal("a")),
    Reference("some_rule"),
    Range("a", "b"),
]


@pytest.mark.parametrize("clause", roundtrip_clauses)
def test_roundtrip(clause):
    clause = clause
    literal = peg.unparse(clause)
    assert literal
    parsed_rule: Rule = peg.parse(f"parse_test <- {literal}\n").clauses["parse_test"]
    assert parsed_rule.sub_clauses[0] == clause


emulated_clauses = [
    (
        Delimited(Literal("'"), Literal("'")),
        Sequence(Literal("'"), Repeat(Not(Anything(1))), Literal("'")),
    ),
]


sys.setrecursionlimit(30000)

peg_grammar = r"""
# Hierarchical syntax
Grammar    <- Spacing Definition+ EndOfFile
Definition <- Identifier LEFTARROW Expression

Expression <- Sequence (SLASH Sequence)*
Sequence   <- Prefix*
Prefix     <- (AND / NOT)? Suffix
Suffix     <- Primary (QUESTION / STAR / PLUS)?
Primary    <- Identifier !LEFTARROW
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
LEFTARROW <- '<-' Spacing
SLASH     <- '/' Spacing
AND       <- '&' Spacing
NOT       <- '!' Spacing
QUESTION  <- '?' Spacing
STAR      <- '*' Spacing
PLUS      <- '+' Spacing
OPEN      <- '(' Spacing
CLOSE     <- ')' Spacing
DOT       <- '.' Spacing

# Separators
Spacing   <- (Space / Comment)*
Comment   <- '#' (!EndOfLine .)* EndOfLine
Space     <- ' ' / '\t' / EndOfLine
EndOfLine <- '\r\n' / '\n' / '\r'
EndOfFile <- !.
"""


def test_parse_reference():
    """Parse the PEG reference grammar"""
    assert peg.parse(peg_grammar)


def test_parse_short():
    """Parse a single-line grammar"""
    assert peg.parse("""top <- ab ab <- a / b a <- "a" ab? b <- "b" ab?""")
