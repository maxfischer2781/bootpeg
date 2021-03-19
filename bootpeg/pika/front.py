from .peg import Literal, Sequence, Choice, Nothing, Anything, Not, Repeat, Reference, Parser
from .act import Debug, Capture, Rule, transform, Action, Discard


def chain(left, right) -> Sequence:
    if isinstance(left, Sequence):
        if isinstance(right, Sequence):
            return Sequence(*left.sub_clauses, *right.sub_clauses)
        return Sequence(*left.sub_clauses, right)
    if isinstance(right, Sequence):
        return Sequence(left, *right.sub_clauses)
    return Sequence(left, right)


def either(left, right) -> Choice:
    if isinstance(left, Choice):
        if isinstance(right, Choice):
            return Choice(*left.sub_clauses, *right.sub_clauses)
        return Choice(*left.sub_clauses, right)
    if isinstance(right, Choice):
        return Choice(left, *right.sub_clauses)
    return Choice(left, right)
