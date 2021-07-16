import sys

import pytest

from bootpeg import create_parser
from bootpeg.grammars import peg
from bootpeg.apegs.boot import (
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
    Clause,
    Parser,
    Grammar,
    bpeg_parser,
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
]


@pytest.mark.parametrize("clause", roundtrip_clauses)
def test_roundtrip(clause):
    clause = clause
    literal = peg.unparse(clause)
    assert literal
    parsed_rule: Rule = peg.parse(f"parse_test <- {literal}\n").clauses["parse_test"]
    assert parsed_rule.sub_clauses[0] == clause


sys.setrecursionlimit(30000)

# Adapted from PEG paper
# Some fixes due to errors in the original grammar
peg_grammar = r"""
# Hierarchical syntax
Grammar    <- (Spacing Definition)+ # EndOfFile
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
    parse = create_parser(peg_grammar, actions={}, dialect=peg, top="Grammar")
    assert parse(peg_grammar)


def test_parse_short():
    """Parse a single-line grammar"""
    assert peg.parse("""top <- ab ab <- a / b a <- "a" ab? b <- "b" ab?""")
