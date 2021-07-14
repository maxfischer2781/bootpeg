from typing import Union, Sequence, Tuple, Optional, Any as AnyT, Dict, Generic

from ..typing import D
from .interpret import MatchFailure, FatalMatchFailure, Rule, Reference, MatchClause, Match, match_clause


AnyMatchFailure = Union[MatchFailure, FatalMatchFailure]


def as_str(source: Union[str, bytes]):
    if isinstance(source, str):
        return source
    return source.decode("latin-1")


def context(source: Sequence, index: int) -> Tuple[str, str]:
    """Provide the context of ``source`` around ``index`` """
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
    __slots__ = ("message", "source", "index")

    def __init__(self, message: str, source: Sequence, index: int):
        self.message = message
        self.source = source
        self.index = index

    def __str__(self):
        head, tail = context(self.source, self.index)
        return "\n".join((self.message, " " * len(head) + "v", head + tail))


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
    reason = (
        f"transforming {failure.expected} failed ({type(cause)}: {cause})"
        if cause is not None
        else f"expected {failure.expected}"
    )
    raise ParseFailure(reason, source, failure.at) from cause


def unpack(match: Match) -> Union[Tuple, Dict]:
    if match.captures:
        return dict(match.captures)
    else:
        return match.results


class Parser(Generic[D]):
    def __init__(self, top: str, *rules: Rule[D], **_globals: AnyT):
        self.top = top
        self.rules = rules
        self.globals = _globals
        self._match_top = match_clause(Reference(self.top), _globals)
        self._match_rules: Dict[str, MatchClause] = {
            rule.name: match_clause(rule.sub_clause, _globals) for rule in rules
        }

    def __call__(self, source: D) -> Union[Tuple, Dict]:
        try:
            return unpack(
                self._match_top(
                    of=source, at=0, memo={}, rules=self._match_rules
                )[-1]
            )
        except (MatchFailure, FatalMatchFailure) as mf:
            raise report(source, mf)


class Grammar(Generic[D]):
    def __init__(self, top: str, *rules: Rule[D]):
        self.top = top
        self.rules = rules

    def parser(self, **_globals: AnyT) -> Parser:
        return Parser(self.top, *self.rules, **_globals)
