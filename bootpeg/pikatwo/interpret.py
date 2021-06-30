"""
Matching of clauses based on interpretation
"""
from typing import Mapping, Tuple, Any as AnyT, NamedTuple, Union
from typing_extensions import Protocol

from functools import singledispatch

from .clauses import Value, Empty, Any, Sequence, Choice, Repeat, Not, And, Annotate, Reference
from ..typing import D


Clause = Union[Value, Empty, Any, Sequence, Choice, Repeat, Not, And, Annotate, Reference]
Terminals = Union[Value, Empty, Any]


class MatchFailure(Exception):
    pass


class Match(NamedTuple):
    position: int
    length: int
    sub_matches: "Tuple[Match, ...]"
    annotation: AnyT

    def copy(self) -> "Match":
        return Match(*self)


Memo = Mapping[Tuple[int, str], Match]


class MatchClause(Protocol[D]):
    def __call__(self, source: D, at: int, memo: Memo, match: Match) -> Tuple[int, Match]:
        ...


@singledispatch
def match_clause(clause) -> MatchClause:
    """Create a callable to match `clause`"""
    raise NotImplementedError(f"_match_block for type({clause})")


@match_clause.register(Value)
def _(clause: Value[D]) -> MatchClause[D]:
    value = clause.value
    length = len(value)

    def do_match(source: D, at: int, memo: Memo, match: Match) -> Tuple[int, Match]:
        if source[at: at + length] == value:
            return at + length, match._replace(length=match.length + length)
        raise MatchFailure()

    return do_match


@match_clause.register(Empty)
def _(clause: Empty[D]) -> MatchClause[D]:

    def do_match(source: D, at: int, memo: Memo, match: Match) -> Tuple[int, Match]:
        return at, match

    return do_match


@match_clause.register(Any)
def _(clause: Any[D]) -> MatchClause[D]:
    length = clause.length

    def do_match(source: D, at: int, memo: Memo, match: Match) -> Tuple[int, Match]:
        if at + length >= len(source):
            return at + length, match._replace(length=match.length + length)
        raise MatchFailure()

    return do_match


@match_clause.register(Sequence)
def _(clause: Sequence[D]) -> MatchClause[D]:
    sub_matches = tuple(match_clause(sub_clause) for sub_clause in clause.sub_clauses)

    def do_match(source: D, at: int, memo: Memo, match: Match) -> Tuple[int, Match]:
        for sub_match in sub_matches:
            at, match = sub_match(source, at, memo, match)
        return at, match

    return do_match


@match_clause.register(Choice)
def _(clause: Choice[D]) -> MatchClause[D]:
    sub_matches = tuple(match_clause(sub_clause) for sub_clause in clause.sub_clauses)

    def do_match(source: D, at: int, memo: Memo, match: Match) -> Tuple[int, Match]:
        for sub_match in sub_matches:
            try:
                return sub_match(source, at, memo, match)
            except MatchFailure:
                pass
        raise MatchFailure()

    return do_match


@match_clause.register(Repeat)
def _(clause: Repeat[D]) -> MatchClause[D]:
    sub_match = match_clause(clause.sub_clause)

    def do_match(source: D, at: int, memo: Memo, match: Match) -> Tuple[int, Match]:
        new_at, match = sub_match(source, at, memo, match)
        while at < new_at < len(source):
            at = new_at
            try:
                new_at, match = sub_match(source, at, memo, match)
            except MatchFailure:
                break
        return at, match

    return do_match


@match_clause.register(Not)
def _(clause: Not[D]) -> MatchClause[D]:
    sub_match = match_clause(clause.sub_clause)

    def do_match(source: D, at: int, memo: Memo, match: Match) -> Tuple[int, Match]:
        try:
            sub_match(source, at, memo, match)
        except MatchFailure:
            return at, match
        else:
            raise MatchFailure()

    return do_match


@match_clause.register(And)
def _(clause: And[D]) -> MatchClause[D]:
    sub_match = match_clause(clause.sub_clause)

    def do_match(source: D, at: int, memo: Memo, match: Match) -> Tuple[int, Match]:
        sub_match(source, at, memo, match)
        return at, match

    return do_match


@match_clause.register(Annotate)
def _(clause: Annotate[D]) -> MatchClause[D]:
    sub_match = match_clause(clause.sub_clause)
    metadata = clause.metadata

    def do_match(source: D, at: int, memo: Memo, match: Match) -> Tuple[int, Match]:
        at, child_match = sub_match(source, at, memo, Match(at, 0, (), metadata))
        length = child_match.length
        return at + length, match._replace(
            length=match.length + length, sub_matches=match.sub_matches + (child_match,)
        )

    return do_match


@match_clause.register(Reference)
def _(clause: Reference[D]) -> MatchClause[D]:
    name = clause.name

    def do_match(source: D, at: int, memo: Memo, match: Match) -> Tuple[int, Match]:
        try:
            at, child_match = memo[at, name]
        except KeyError:
            raise MatchFailure()
        else:
            length = child_match.length
            return at + length, match._replace(
                length=match.length + length,
                sub_matches=match.sub_matches + (child_match,),
            )

    return do_match
