import pytest

from bootpeg.grammars import bpeg
from bootpeg.pika.front import Literal, Nothing, Anything


canonicals = [
    *(Literal(literal) for literal in ("A", "x", "ß", " ", "\n")),
    Nothing(),
    Anything(1),
    Anything(5),
]


@pytest.mark.parametrize("clause", canonicals)
def test_roundtrip(clause):
    clause = clause
    literal = bpeg.unparse(clause)
    assert literal
