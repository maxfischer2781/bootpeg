"""
Matching of clauses based on interpretation
"""
from typing import (
    Mapping,
    MutableMapping,
    Tuple,
    Any as AnyT,
    NamedTuple,
    Union,
    Optional,
    Generic,
    Dict,
)
from typing_extensions import Protocol

from functools import singledispatch

from .clauses import (
    Value,
    Empty,
    Any,
    Sequence,
    Choice,
    Repeat,
    Not,
    And,
    Entail,
    Capture,
    Transform,
    Reference,
    Rule,
)
from ..typing import D


Clause = Union[
    Value,
    Empty,
    Any,
    Sequence,
    Choice,
    Repeat,
    Not,
    And,
    Entail,
    Capture,
    Transform,
    Reference,
]


class MatchFailure(Exception):
    __slots__ = ("at", "expected")

    def __init__(self, at: int, expected: Clause):
        self.at = at
        self.expected = expected


class FatalMatchFailure(Exception):
    __slots__ = ("at", "expected")

    def __init__(self, at: int, expected: Clause):
        self.at = at
        self.expected = expected


class Match(NamedTuple):
    at: int
    length: int = 0
    results: Tuple[AnyT, ...] = ()
    captures: Tuple[Tuple[str, AnyT], ...] = ()

    @property
    def end(self):
        return self.at + self.length

    def __add__(self, other: "Match") -> "Match":
        """Join two adjacent matches"""
        assert (
            self.end == other.at
        ), f"not adjacent: {self.at + self.length} vs {other.at} ({self} vs {other})"
        return Match(
            at=self.at,
            length=self.length + other.length,
            results=self.results + other.results,
            captures=self.captures + other.captures,
        )

    def copy(self) -> "Match":
        return Match(*self)


Memo = MutableMapping[Tuple[int, str], Optional[Match]]
Rules = Mapping[str, "MatchClause"]


class MatchClause(Protocol[D]):
    def __call__(self, of: D, at: int, memo: Memo, rules: Rules) -> Tuple[int, Match]:
        ...


@singledispatch
def match_clause(clause) -> MatchClause:
    """Create a callable to match `clause`"""
    raise NotImplementedError(f"match_clause for type({clause!r})")


@match_clause.register(Value)
def _(clause: Value[D]) -> MatchClause[D]:
    value = clause.value
    length = len(value)

    def do_match(of: D, at: int, memo: Memo, rules: Rules) -> Tuple[int, Match]:
        if of[at : at + length] == value:
            return at + length, Match(at, length)
        raise MatchFailure(at, clause)

    return do_match


@match_clause.register(Empty)
def _(clause: Empty[D]) -> MatchClause[D]:
    def do_match(of: D, at: int, memo: Memo, rules: Rules) -> Tuple[int, Match]:
        return at, Match(at, 0)

    return do_match


@match_clause.register(Any)
def _(clause: Any[D]) -> MatchClause[D]:
    length = clause.length

    def do_match(of: D, at: int, memo: Memo, rules: Rules) -> Tuple[int, Match]:
        if at + length <= len(of):
            return at + length, Match(at, length)
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
    match_sub_clauses = tuple(
        match_clause(sub_clause) for sub_clause in clause.sub_clauses
    )

    def do_match(of: D, at: int, memo: Memo, rules: Rules) -> Tuple[int, Match]:
        for match_sub_clause in match_sub_clauses[:-1]:
            try:
                return match_sub_clause(of, at, memo, rules)
            except MatchFailure:
                pass
        return match_sub_clauses[-1](of, at, memo, rules)

    return do_match


@match_clause.register(Repeat)
def _(clause: Repeat[D]) -> MatchClause[D]:
    match_sub_clause = match_clause(clause.sub_clause)

    def do_match(of: D, at: int, memo: Memo, rules: Rules) -> Tuple[int, Match]:
        new_at, match = match_sub_clause(of, at, memo, rules)
        while at < new_at < len(of):
            at = new_at
            try:
                new_at, new_match = match_sub_clause(of, at, memo, rules)
                match += new_match
            except MatchFailure:
                break
        return at, match

    return do_match


@match_clause.register(Not)
def _(clause: Not[D]) -> MatchClause[D]:
    match_sub_clause = match_clause(clause.sub_clause)

    def do_match(of: D, at: int, memo: Memo, rules: Rules) -> Tuple[int, Match]:
        try:
            match_sub_clause(of, at, memo, rules)
        except MatchFailure:
            return at, Match(at, 0)
        else:
            raise MatchFailure(at, clause)

    return do_match


@match_clause.register(And)
def _(clause: And[D]) -> MatchClause[D]:
    match_sub_clause = match_clause(clause.sub_clause)

    def do_match(of: D, at: int, memo: Memo, rules: Rules) -> Tuple[int, Match]:
        match_sub_clause(of, at, memo, rules)
        return at, Match(at, 0)

    return do_match


@match_clause.register(Entail)
def _(clause: Entail[D]) -> MatchClause[D]:
    match_sub_clause = match_clause(clause.sub_clause)

    def do_match(of: D, at: int, memo: Memo, rules: Rules) -> Tuple[int, Match]:
        try:
            return match_sub_clause(of, at, memo, rules)
        except MatchFailure:
            raise FatalMatchFailure(at, clause)

    return do_match


@match_clause.register(Capture)
def _(clause: Capture[D]) -> MatchClause[D]:
    match_sub_clause = match_clause(clause.sub_clause)
    name = clause.name
    variadic = clause.variadic

    def do_match(of: D, at: int, memo: Memo, rules: Rules) -> Tuple[int, Match]:
        at, match = match_sub_clause(of, at, memo, rules)
        results = match.results
        if variadic:
            return at, Match(match.at, match.length, captures=((name, results),))
        elif not match.results:
            return at, Match(
                match.at, match.length, captures=((name, of[match.at : match.end]),)
            )
        elif len(results) == 1:
            return at, Match(match.at, match.length, captures=((name, results[0]),))
        else:
            raise MatchFailure(at, clause)

    return do_match


@match_clause.register(Transform)
def _(clause: Transform[D]) -> MatchClause[D]:
    match_sub_clause = match_clause(clause.sub_clause)
    py_call = clause.py_call

    def do_match(of: D, at: int, memo: Memo, rules: Rules) -> Tuple[int, Match]:
        at, match = match_sub_clause(of, at, memo, rules)
        try:
            result = py_call(**dict(match.captures))
        except Exception:
            raise FatalMatchFailure(at, clause)
        return at, Match(match.at, match.length, results=(result,))

    return do_match


@match_clause.register(Reference)
def _(clause: Reference[D]) -> MatchClause[D]:
    name = clause.name

    # Adapted from Medeiros et al.
    def do_match(of: D, at: int, memo: Memo, rules: Rules) -> Tuple[int, Match]:
        try:
            child_match = memo[at, name]
        except (MatchFailure, FatalMatchFailure) as mf:
            raise type(mf)(at, clause)
        except KeyError:
            # mark this Rule as unmatched ...
            match = memo[at, name] = None
            old_end = at - 1
            # ... then iteratively expand the match
            while True:
                try:
                    new_end, new_match = rules[name](of, at, memo, rules)
                except MatchFailure:
                    raise MatchFailure(at, clause)  # raise for rule to mark path
                if new_end > old_end:
                    match = memo[at, name] = new_match
                    old_end = new_end
                else:
                    assert match is not None
                    return old_end, match
        else:
            if child_match is None:
                raise MatchFailure(at, clause)
            else:
                return child_match.end, child_match

    return do_match


class Parser(Generic[D]):
    def __init__(self, top: str, *rules: Rule[D]):
        self.top = top
        self.rules = rules
        self._match_top = match_clause(Reference(self.top))
        self._match_rules: Dict[str, MatchClause] = {
            rule.name: match_clause(rule.sub_clause) for rule in rules
        }

    def match(self, source: D) -> Match:
        return self._match_top(of=source, at=0, memo={}, rules=self._match_rules)[-1]
