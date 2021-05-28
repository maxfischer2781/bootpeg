import subprocess
import sys

import pytest

from bootpeg_examples import math


def test_as_main():
    """Test the example as if run via `python -m`"""
    reply = subprocess.run(
        [sys.executable, "-m", "bootpeg_examples.math"],
        input="1\n2\nexit",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
    ).stdout.splitlines()
    assert reply == [f"{math.prompt}{expected}" for expected in ("1", "2", "")]


math_expressions = [
    ("1", math.Rational(False, 1, 1)),
    ("2/2", math.Rational(False, 1, 1)),
    ("-3/4", math.Rational(True, 3, 4)),
    ("3/-4", math.Rational(True, 3, 4)),
    ("-3/-4", math.Rational(False, 3, 4)),
    ("3.5 * -2", math.Rational(True, 7, 1)),
    ("12.5 + 3.5 - 2", math.Rational(False, 14, 1)),
]


@pytest.mark.parametrize("expression, expected", math_expressions)
def test_parsing(expression, expected):
    result = math.interpret(expression)
    assert result == expected
