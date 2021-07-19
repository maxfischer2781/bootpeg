import pytest

from bootpeg.grammars.peg import unescape


named_escapes = [
    (r"\a", "\a"),
    (r"\b", "\b"),
    (r"\f", "\f"),
    (r"\n", "\n"),
    (r"\r", "\r"),
    (r"\t", "\t"),
    (r"\v", "\v"),
    (r"\\", "\\"),
    (r"\'", "'"),
    (r"\"", '"'),
]
octal_escapes = [
    (r"\12", "\n"),
    (r"\012", "\n"),
    (r"\141", "a"),
    (r"\60", "0"),
    (r"\060", "0"),
]
u16_escapes = [
    (r"\u0030", "0"),
    (r"\u0061", "a"),
    (r"\u007a", "z"),
    (r"\u00df", "ß"),
    (r"\u20ac", "€"),
]


@pytest.mark.parametrize(
    "cases", [named_escapes, octal_escapes, u16_escapes], ids=("named", "octal", "u16")
)
def test_unescape(cases):
    for escaped, target in cases:
        assert unescape(escaped) == target
