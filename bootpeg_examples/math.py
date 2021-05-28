"""
`bootpeg` example interpreter emulating Rational math via Integer math
"""
from typing import NamedTuple
import sys

from bootpeg.grammars import bpeg
from bootpeg import import_parser, __version__ as bootpeg_version


# Rational number implementation
class Rational(NamedTuple):
    """
    Representation of a rational number as a sign and a pair of integers
    """

    negative: bool
    numerator: int
    denominator: int

    @property
    def sign(self) -> int:
        return -1 if self.negative else 1

    def __str__(self):
        sign = "-" if self.negative else ""
        return (
            f"{sign}{self.numerator}"
            if self.denominator == 1
            else f"{sign}{self.numerator}/{self.denominator}"
        )


def gcd(a, b):
    """The greatest common divisor of ``a`` and ``b``"""
    # Euclidean algorithm
    while b > 0:
        b, a = a % b, b
    return a


def fraction(numerator: int, denominator: int) -> Rational:
    """Construct an optimal Rational from separate numerator and denominator"""
    negative = True if (numerator < 0) ^ (denominator < 0) else False
    numerator = abs(numerator)
    denominator = abs(denominator)
    divisor = gcd(numerator, denominator)
    return Rational(negative, numerator // divisor, denominator // divisor)


# Mathematical operations
def neg(of: Rational):
    """Unary negation"""
    return Rational(not of.negative, of.numerator, of.denominator)


def add(lhs: Rational, rhs: Rational):
    """Binary addition"""
    return fraction(
        lhs.sign * lhs.numerator * rhs.denominator
        + rhs.sign * rhs.numerator * lhs.denominator,
        lhs.denominator * rhs.denominator,
    )


def sub(lhs: Rational, rhs: Rational):
    """Binary subtraction"""
    return add(lhs, neg(rhs))


def inv(of: Rational):
    """Unary inversion"""
    return Rational(of.negative, of.denominator, of.numerator)


def mul(lhs: Rational, rhs: Rational):
    """Binary multiplication"""
    numerator = lhs.numerator * rhs.numerator
    denominator = lhs.denominator * rhs.denominator
    divisor = gcd(numerator, denominator)
    return Rational(lhs.sign ^ rhs.sign, numerator // divisor, denominator // divisor)


def div(lhs: Rational, rhs: Rational):
    """Binary division"""
    return mul(lhs, inv(rhs))


# Parsing of matched input
# There is no need to handle literals for negative numbers:
# the grammar treats them as the unary negation of *positive* numbers.
def parse_decimal(literal: str) -> Rational:
    """Parse a literal decimal, such as ``12.3``"""
    dot_index = literal.find(".")
    if dot_index == -1:
        return Rational(False, int(literal), 1)
    numerator = int(literal[:dot_index] + literal[dot_index + 1 :])
    return fraction(numerator, 10 ** (len(literal) - dot_index - 1))


def parse_integer(literal: str) -> Rational:
    """Parse a literal integer, such as ``12``"""
    return Rational(False, int(literal), 1)


# actions expected by the grammar
math_actions = {
    "integer": parse_integer,
    "decimal": parse_decimal,
    **{obj.__name__: obj for obj in (neg, add, sub, mul, div)},
}

interpret = import_parser(__name__, dialect=bpeg, actions=math_actions)
prompt = ">>> "


if __name__ == "__main__":
    print(f"Examples: math [bootpeg {bootpeg_version}]", file=sys.stderr)
    print("Type 'exit' to exit", file=sys.stderr)
    while True:
        try:
            expression = input(prompt)
            if expression == "exit":
                break
            print(interpret(expression))
        except (KeyboardInterrupt, EOFError):
            break
        except Exception as err:
            print(f"{type(err).__name__}: {err}")
