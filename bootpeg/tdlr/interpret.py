"""
Matching of clauses based on interpretation
"""
from typing import Mapping, MutableMapping, Tuple, Any as AnyT, NamedTuple, Union, Optional
from typing_extensions import Protocol

from functools import singledispatch

from .clauses import Value, Empty, Any, Sequence, Choice, Repeat, Not, And, Annotate, Reference
from ..typing import D


Clause = Union[Value, Empty, Any, Sequence, Choice, Repeat, Not, And, Annotate, Reference]


class MatchFailure(Exception):
    __slots__ = ('at', 'expected')

    def __init__(self, at, expected):
        self.at = at
        self.expected = expected


class Match(NamedTuple):
    at: int
    length: int
    sub_matches: "Tuple[Match, ...]"
    annotation: Optional[AnyT]

    @property
    def end(self):
        return self.at + self.length

    def __add__(self, other: "Match") -> "Match":
        """Join two adjacent matches"""
        assert (
            self.end == other.at
        ), f"not adjacent: {self.at + self.length} vs {other.at} ({self} vs {other})"
        if self.annotation is other.annotation is None:
            return self._replace(
                length=self.length + other.length,
                sub_matches=self.sub_matches + other.sub_matches,
            )
        elif self.annotation is None:
            return self._replace(
                length=self.length + other.length,
                sub_matches=(*self.sub_matches, other),
            )
        elif other.annotation is None:
            return other._replace(
                at=self.at,
                length=self.length + other.length,
                sub_matches=(self, *other.sub_matches),
            )
        else:
            return self._replace(
                length=self.length + other.length,
                sub_matches=(self, other),
                annotation=None,
            )

    def copy(self) -> "Match":
        return Match(*self)

    @classmethod
    def plain(cls, at: int, length: int):
        return cls(at, length, (), None)


Memo = MutableMapping[Tuple[int, str], Optional[Match]]
Rules = Mapping[str, "MatchClause"]


class MatchClause(Protocol[D]):
    def __call__(self, of: D, at: int, memo: Memo, rules: Rules) -> Tuple[int, Match]:
        ...


@singledispatch
def match_clause(clause) -> MatchClause:
    """Create a callable to match `clause`"""
    raise NotImplementedError(f"_match_block for type({clause})")


@match_clause.register(Value)
def _(clause: Value[D]) -> MatchClause[D]:
    value = clause.value
    length = len(value)

    def do_match(of: D, at: int, memo: Memo, rules: Rules) -> Tuple[int, Match]:
        if of[at: at + length] == value:
            return at + length, Match.plain(at, length)
        raise MatchFailure(at, clause)

    return do_match


@match_clause.register(Empty)
def _(clause: Empty[D]) -> MatchClause[D]:

    def do_match(of: D, at: int, memo: Memo, rules: Rules) -> Tuple[int, Match]:
        return at, Match.plain(at, 0)

    return do_match


@match_clause.register(Any)
def _(clause: Any[D]) -> MatchClause[D]:
    length = clause.length

    def do_match(of: D, at: int, memo: Memo, rules: Rules) -> Tuple[int, Match]:
        if at + length >= len(of):
            return at + length, Match.plain(at, length)
        raise MatchFailure(at, clause)

    return do_match


@match_clause.register(Sequence)
def _(clause: Sequence[D]) -> MatchClause[D]:
    head_do_match, *sub_do_matches = map(match_clause, clause.sub_clauses)

    def do_match(of: D, at: int, memo: Memo, rules: Rules) -> Tuple[int, Match]:
        at, match = head_do_match(of, at, memo, rules)
        for sub_do_match in sub_do_matches:
            match += sub_do_match(of, match.end, memo, rules)[-1]
        return match.end, match

    return do_match


@match_clause.register(Choice)
def _(clause: Choice[D]) -> MatchClause[D]:
    sub_matches = tuple(match_clause(sub_clause) for sub_clause in clause.sub_clauses)

    def do_match(of: D, at: int, memo: Memo, rules: Rules) -> Tuple[int, Match]:
        for sub_match in sub_matches:
            try:
                return sub_match(of, at, memo, rules)
            except MatchFailure:
                pass
        raise MatchFailure(at, clause)

    return do_match


@match_clause.register(Repeat)
def _(clause: Repeat[D]) -> MatchClause[D]:
    sub_match = match_clause(clause.sub_clause)

    def do_match(of: D, at: int, memo: Memo, rules: Rules) -> Tuple[int, Match]:
        new_at, match = sub_match(of, at, memo, rules)
        while at < new_at < len(of):
            at = new_at
            try:
                new_at, new_match = sub_match(of, at, memo, rules)
                match += new_match
            except MatchFailure:
                break
        return at, match

    return do_match


@match_clause.register(Not)
def _(clause: Not[D]) -> MatchClause[D]:
    sub_match = match_clause(clause.sub_clause)

    def do_match(of: D, at: int, memo: Memo, rules: Rules) -> Tuple[int, Match]:
        try:
            sub_match(of, at, memo, rules)
        except MatchFailure:
            return at, Match.plain(at, 0)
        else:
            raise MatchFailure(at, clause)

    return do_match


@match_clause.register(And)
def _(clause: And[D]) -> MatchClause[D]:
    sub_match = match_clause(clause.sub_clause)

    def do_match(of: D, at: int, memo: Memo, rules: Rules) -> Tuple[int, Match]:
        sub_match(of, at, memo, rules)
        return at, Match.plain(at, 0)

    return do_match


@match_clause.register(Annotate)
def _(clause: Annotate[D]) -> MatchClause[D]:
    sub_match = match_clause(clause.sub_clause)
    metadata = clause.metadata

    def do_match(of: D, at: int, memo: Memo, rules: Rules) -> Tuple[int, Match]:
        at, match = sub_match(of, at, memo, rules)
        if match.annotation is None:
            return at, match._replace(annotation=metadata)
        else:
            return at, match._replace(sub_matches=match, annotation=metadata)

    return do_match


@match_clause.register(Reference)
def _(clause: Reference[D]) -> MatchClause[D]:
    name = clause.name

    # Adapted from Medeiros et al.
    def do_match(of: D, at: int, memo: Memo, rules: Rules) -> Tuple[int, Match]:
        try:
            child_match = memo[at, name]
            if child_match is None:
                raise MatchFailure(at, clause)
            else:
                return child_match.end, child_match
        except KeyError:
            # mark this Rule as unmatched ...
            match = memo[at, name] = None
            old_end = at - 1
            # ... then iteratively expand the match
            while True:
                new_end, new_match = rules[name](of, at, memo, rules)
                if new_end > old_end:
                    match = memo[at, name] = new_match
                    old_end = new_end
                else:
                    assert match is not None
                    return old_end, match

    return do_match
