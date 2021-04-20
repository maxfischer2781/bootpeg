import sys

from bootpeg.grammars import peg

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
    assert peg.parse(
        """top <- ab ab <- a / b a <- "a" ab? b <- "b" ab?"""
    )