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
    Callable,
    Set,
)
from typing_extensions import Protocol

from functools import singledispatch

from ..typing import D, D_contra
from .clauses import (
    Value,
    Range,
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
)


Clause = Union[
    Value[D],
    Range[D],
    Empty[D],
    Any[D],
    Sequence[D],
    Choice[D],
    Repeat[D],
    Not[D],
    And[D],
    Entail[D],
    Capture[D],
    Transform[D],
    Reference[D],
]


class MatchFailure(Exception):
    __slots__ = ("at", "clause")

    def __init__(self, at: int, clause: Clause):
        self.at = at
        self.clause = clause


class FatalMatchFailure(Exception):
    __slots__ = ("at", "clause")

    def __init__(self, at: int, clause: Clause):
        self.at = at
        self.clause = clause


@singledispatch
def discover_captures(clause: Clause) -> Set[str]:
    raise NotImplementedError(f"discover_captures for type({clause!r})")


@discover_captures.register(Value)
@discover_captures.register(Range)
@discover_captures.register(Any)
@discover_captures.register(Empty)
@discover_captures.register(And)
@discover_captures.register(Not)
@discover_captures.register(Reference)
@discover_captures.register(Transform)
def _(clause) -> Set[str]:
    return set()


@discover_captures.register(Sequence)
@discover_captures.register(Entail)
def _(clause: Union[Sequence, Entail]) -> Set[str]:
    return set.union(*map(discover_captures, clause.sub_clauses))


@discover_captures.register(Choice)
def _(clause: Choice) -> Set[str]:
    clause_captures = discover_captures(clause.sub_clauses[0])
    for sub_clause in clause.sub_clauses[1:]:
        unique_captures = clause_captures ^ discover_captures(sub_clause)
        if unique_captures:
            raise Value(
                f"Names {', '.join(unique_captures)} not captured "
                f"in all choices of {clause!r}"
            )
    return clause_captures


@discover_captures.register(Repeat)
def _(clause: Repeat) -> Set[str]:
    return discover_captures(clause.sub_clause)


@discover_captures.register(Capture)
def _(clause: Capture) -> Set[str]:
    return {clause.name}


def py_transform(clause: Transform, _globals: dict) -> Callable:
    """Create a ``lambda`` to execute a transform given some globals"""
    captures = discover_captures(clause.sub_clause)
    source = f"lambda {', '.join(captures)}: {clause.action.strip()}"
    code = compile(source, source, "eval")
    return eval(code, _globals)


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


class MatchClause(Protocol[D_contra]):
    def __call__(self, of: D_contra, at: int, memo: Memo, rules: Rules) -> Match: ...


@singledispatch
def match_clause(clause: Clause[D], _globals: dict) -> MatchClause[D]:
    """Create a callable to match `clause`"""
    raise NotImplementedError(f"match_clause for type({clause!r})")


@match_clause.register(Value)
def _(clause: Value[D], _globals: dict) -> MatchClause[D]:
    value = clause.value
    length = len(value)

    def do_match(of: D, at: int, memo: Memo, rules: Rules) -> Match:
        if of[at : at + length] == value:
            return Match(at, length)
        raise MatchFailure(at, clause) from None

    return do_match


@match_clause.register(Range)
def _(clause: Range[D], _globals: dict) -> MatchClause[D]:
    lower = clause.lower
    upper = clause.upper
    length = len(lower)

    def do_match(of: D, at: int, memo: Memo, rules: Rules) -> Match:
        candidate = of[at : at + length]
        if len(candidate) == length and lower <= candidate <= upper:
            return Match(at, length)
        raise MatchFailure(at, clause) from None

    return do_match


@match_clause.register(Empty)
def _(clause: Empty[D], _globals: dict) -> MatchClause[D]:
    def do_match(of: D, at: int, memo: Memo, rules: Rules) -> Match:
        return Match(at, 0)

    return do_match


@match_clause.register(Any)
def _(clause: Any[D], _globals: dict) -> MatchClause[D]:
    length = clause.length

    def do_match(of: D, at: int, memo: Memo, rules: Rules) -> Match:
        if at + length <= len(of):
            return Match(at, length)
        raise MatchFailure(at, clause) from None

    return do_match


@match_clause.register(Sequence)
def _(clause: Sequence[D], _globals: dict) -> MatchClause[D]:
    head_do_match, *sub_do_matches = (
        match_clause(sub_clause, _globals) for sub_clause in clause.sub_clauses
    )

    def do_match(of: D, at: int, memo: Memo, rules: Rules) -> Match:
        match = head_do_match(of, at, memo, rules)
        for sub_do_match in sub_do_matches:
            match += sub_do_match(of, match.end, memo, rules)
        return match

    return do_match


@match_clause.register(Entail)
def _(clause: Entail[D], _globals: dict) -> MatchClause[D]:
    head_do_match, *sub_do_matches = (
        match_clause(sub_clause, _globals) for sub_clause in clause.sub_clauses
    )

    def do_match(of: D, at: int, memo: Memo, rules: Rules) -> Match:
        try:
            match = head_do_match(of, at, memo, rules)
            for sub_do_match in sub_do_matches:
                match += sub_do_match(of, match.end, memo, rules)
            return match
        except MatchFailure as mf:
            raise FatalMatchFailure(mf.at, mf.clause) from mf

    return do_match


@match_clause.register(Choice)
def _(clause: Choice[D], _globals: dict) -> MatchClause[D]:
    match_sub_clauses = tuple(
        match_clause(sub_clause, _globals) for sub_clause in clause.sub_clauses
    )

    def do_match(of: D, at: int, memo: Memo, rules: Rules) -> Match:
        for match_sub_clause in match_sub_clauses:
            try:
                return match_sub_clause(of, at, memo, rules)
            except MatchFailure:
                pass
        raise MatchFailure(at, clause)

    return do_match


@match_clause.register(Repeat)
def _(clause: Repeat[D], _globals: dict) -> MatchClause[D]:
    match_sub_clause = match_clause(clause.sub_clause, _globals)

    def do_match(of: D, at: int, memo: Memo, rules: Rules) -> Match:
        match = match_sub_clause(of, at, memo, rules)
        while at < match.end < len(of):
            at = match.end
            try:
                match += match_sub_clause(of, at, memo, rules)
            except MatchFailure:
                break
        return match

    return do_match


@match_clause.register(Not)
def _(clause: Not[D], _globals: dict) -> MatchClause[D]:
    match_sub_clause = match_clause(clause.sub_clause, _globals)

    def do_match(of: D, at: int, memo: Memo, rules: Rules) -> Match:
        try:
            match_sub_clause(of, at, memo, rules)
        except MatchFailure:
            return Match(at, 0)
        else:
            raise MatchFailure(at, clause)

    return do_match


@match_clause.register(And)
def _(clause: And[D], _globals: dict) -> MatchClause[D]:
    match_sub_clause = match_clause(clause.sub_clause, _globals)

    def do_match(of: D, at: int, memo: Memo, rules: Rules) -> Match:
        match_sub_clause(of, at, memo, rules)
        return Match(at, 0)

    return do_match


@match_clause.register(Capture)
def _(clause: Capture[D], _globals: dict) -> MatchClause[D]:
    match_sub_clause = match_clause(clause.sub_clause, _globals)
    name = clause.name

    if clause.variadic:

        def do_match(of: D, at: int, memo: Memo, rules: Rules) -> Match:
            match = match_sub_clause(of, at, memo, rules)
            results = match.results
            return Match(match.at, match.length, captures=((name, results),))

    else:

        def do_match(of: D, at: int, memo: Memo, rules: Rules) -> Match:
            match = match_sub_clause(of, at, memo, rules)
            results = match.results
            if not results:
                result = of[match.at : match.end]
            elif len(results) == 1:
                result = results[0]
            else:
                raise MatchFailure(at, clause)
            return Match(match.at, match.length, captures=((name, result),))

    return do_match


@match_clause.register(Transform)
def _(clause: Transform[D], _globals: dict) -> MatchClause[D]:
    match_sub_clause = match_clause(clause.sub_clause, _globals)
    py_call = py_transform(clause, _globals)

    def do_match(of: D, at: int, memo: Memo, rules: Rules) -> Match:
        match = match_sub_clause(of, at, memo, rules)
        try:
            result = py_call(**dict(match.captures))
        except Exception as err:
            raise FatalMatchFailure(at, clause) from err
        return Match(match.at, match.length, results=(result,))

    return do_match


@match_clause.register(Reference)
def _(clause: Reference[D], _globals: dict) -> MatchClause[D]:
    name = clause.name

    # Adapted from Medeiros et al.
    def do_match(of: D, at: int, memo: Memo, rules: Rules) -> Match:
        try:
            child_match = memo[at, name]
        except KeyError:
            # mark this Rule as unmatched ...
            match = memo[at, name] = None
            old_end = at - 1
            # ... then iteratively expand the match
            while True:
                try:
                    new_match = rules[name](of, at, memo, rules)
                except (MatchFailure, FatalMatchFailure) as mf:
                    raise type(mf)(at, clause) from mf  # raise for rule to record path
                if new_match.end > old_end:
                    match = memo[at, name] = new_match
                    old_end = new_match.end
                else:
                    assert match is not None
                    return match
        else:
            if child_match is None:
                raise MatchFailure(at, clause)
            else:
                return child_match

    return do_match
