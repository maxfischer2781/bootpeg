from typing import Union, Sequence, Tuple, Optional, Any as AnyT, Dict, Generic

from ..typing import D
from .clauses import Rule
from .interpret import (
    MatchFailure,
    FatalMatchFailure,
    Reference,
    MatchClause,
    Match,
    match_clause,
)


AnyMatchFailure = Union[MatchFailure, FatalMatchFailure]


def as_str(source: Union[str, bytes]):
    if isinstance(source, str):
        return source
    return source.decode("latin-1")


def context(source: Sequence, index: int) -> Tuple[str, str]:
    """Provide the context of ``source`` around ``index``"""
    if isinstance(source, (str, bytes)):
        new_line = "\n" if isinstance(source, str) else b"\n"
        line_start = source.rfind(new_line, 0, index) + 1
        line_end = source.find(new_line, index)
        if line_end == -1:
            line_end = None
        return as_str(source[line_start:index]), as_str(source[index:line_end])
    else:
        return str(source[index - 5 : index]), str(source[index : index + 5])


class ParseFailure(Exception):
    __slots__ = ("message", "source", "index", "path")

    def __init__(
        self, message: str, source: Sequence, index: int, path: Tuple[str, ...]
    ):
        self.message = message
        self.source = source
        self.index = index
        self.path = path

    def __str__(self):
        head, tail = context(self.source, self.index)
        return "\n".join(
            (
                f"in path {' -> '.join(self.path) if self.path else '[start]'}",
                self.message,
                f"{' ' * len(head)}v-[at index {self.index}]",
                head + tail,
            )
        )


def walk_failures(err: AnyMatchFailure):
    yield err
    while err.__cause__ is not None:
        err = err.__cause__
        yield err
        if not isinstance(err, (MatchFailure, FatalMatchFailure)):
            break


def report(source: Sequence, err: AnyMatchFailure):
    failures = list(walk_failures(err))
    failure, cause = (
        (failures[-1], None)
        if isinstance(failures[-1], (MatchFailure, FatalMatchFailure))
        else failures[-2:]
    )  # type: AnyMatchFailure, Optional[AnyMatchFailure]
    reference_path = tuple(
        mf.clause.name
        for mf in failures[: -1 if cause is None else -2]
        if isinstance(mf.clause, Reference)
    )
    reason = (
        f"transforming {failure.clause} failed ({type(cause)}: {cause})"
        if cause is not None
        else f"expected {failure.clause}"
    )
    raise ParseFailure(reason, source, failure.at, reference_path) from cause


def unpack(match: Match) -> AnyT:
    """Unpack the result of a top-level match with error reporting"""
    if match.captures:
        raise ValueError(
            f"found {len(match.captures)} unused captures after parsing\n"
            "hint: transform captured values to a mapping if they should be returned"
        )
    elif len(match.results) > 1:
        raise ValueError(
            f"found {len(match.results)} unused matches after parsing\n"
            "hint: transform matches into a sequence if they should be returned"
        )
    elif not match.results:
        raise ValueError(
            "found no resulting match after parsing\n"
            "hint: transform empty matches to a literal True or () to indicate success"
        )
    else:
        return match.results[0]


class Parser(Generic[D]):
    @property
    def top(self) -> str:
        return self._top

    def __init__(self, __top: Rule[D], *rules: Rule[D], **_globals: AnyT):
        self._top = __top.name
        self.rules = (__top, *rules)
        self.globals = _globals
        self._match_top = match_clause(Reference(self.top), _globals)
        self._match_rules: Dict[str, MatchClause] = {
            rule.name: match_clause(rule.sub_clause, _globals) for rule in self.rules
        }

    def __call__(self, source: D) -> AnyT:
        try:
            return unpack(
                self._match_top(of=source, at=0, memo={}, rules=self._match_rules)[-1]
            )
        except (MatchFailure, FatalMatchFailure) as mf:
            raise report(source, mf)


class Grammar(Generic[D]):
    def __init__(self, *rules: Rule[D]):
        self.rules = rules

    def parser(self, **_globals: AnyT) -> Parser:
        return Parser(*self.rules, **_globals)
