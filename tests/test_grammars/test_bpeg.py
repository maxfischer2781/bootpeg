import pytest

from bootpeg import create_parser
from bootpeg.grammars import bpeg

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
    ParseFailure,
)


clauses = [
    Empty(),
    Any(1),
    *(Value(literal) for literal in ("A", "x", "ß", " ")),
    Sequence(Value("A"), Value("B"), Value("A")),
    Sequence(Value(" "), Value(" ")),
    Choice(Choice(Value("a"), Value("b")), Empty()),
    Repeat(Value("x")),
    Repeat(Sequence(Value("x"), Value("y"), Value("z"))),
    Not(Value("a")),
    And(Value("a")),
    Reference("some_rule"),
    Range("a", "b"),
    Entail(Value("a"), Value("b")),
    Sequence(Value("head"), Entail(Value("a"), Value("b"))),
    Capture(Value("expr"), "name", True),
    Capture(Value("expr"), "name", False),
    Transform(Value("body"), "{True}"),
]


@pytest.mark.parametrize("clause", clauses)
def test_roundtrip(clause):
    clause = clause
    literal = bpeg.unparse(clause)
    assert literal
    parsed_rule: Rule = bpeg.parse(f"parse_test:\n    | {literal}\n").rules[0]
    assert parsed_rule.sub_clause.sub_clauses[0] == clause


commit_failures = (("top:\n | ~\n", 9),)


@pytest.mark.parametrize("source, position", commit_failures)
def test_commit(source, position):
    try:
        bpeg.parse(source)
    except ParseFailure as pf:
        assert pf.index == position
    else:
        assert not position, "Expected parse failures, found none"


@pytest.mark.parametrize("source", ["a", "bcde"])
def test_multiuse_actions(source):
    """Test that using the same capture multiple times is valid"""
    multiuse_parse = create_parser("top:\n    | a=(.*) { (a, a) }\n", bpeg)
    result = multiuse_parse(source)
    assert result == (source, source)


def test_not_anything():
    """Test that ``Any`` does not match after the end"""
    not_anything_parse = create_parser("top:\n    | a=(.) !. { (a) }\n", bpeg)
    assert not_anything_parse("b") == "b"
    with pytest.raises(ParseFailure):
        not_anything_parse("bb")
