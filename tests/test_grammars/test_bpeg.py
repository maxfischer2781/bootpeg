import pytest

from bootpeg.grammars import bpeg
from bootpeg.pika.front import Rule, Literal, Nothing, Anything


clauses = [
    *(Literal(literal) for literal in ("A", "x", "ß", " ")),
    Nothing(),
    Anything(1),
]


@pytest.mark.parametrize("clause", clauses)
def test_roundtrip(clause):
    clause = clause
    literal = bpeg.unparse(clause)
    assert literal
    parsed_rule: Rule = bpeg.parse(f"parse_test:\n    | {literal}\n").clauses[
        "parse_test"
    ]
    assert parsed_rule.sub_clauses[0] == clause
