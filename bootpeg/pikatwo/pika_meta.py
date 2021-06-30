"""
Utility for fetching the metadata required by Pika

These aren't particularly complicated at their core, but adding them around objects via
dispatch and maps adds some scaffolding.
"""
from typing import Generic, Iterable, Union, Set, Dict, Tuple
from typing_extensions import Protocol
from functools import singledispatch

from .clauses import Rule, Value, Empty, Any, Sequence, Choice, Repeat, Not, And, Annotate, Reference
from .interpret import Clause

from ..typing import D


def maybe_empty(top: str, *rules: Rule[D]) -> Set[Union[Rule[D], Clause[D]]]:
    result = {}
    named_rules = {rule.name: rule for rule in rules}
    map_maybe_empty(named_rules[top], named_rules, result)
    return {rc for rc, me in result.items() if me}


def triggers(top: str, *rules: Rule[D], empty: Set[Union[Rule[D], Clause[D]]]):
    pass


@singledispatch
def map_maybe_empty(subject: Union[Clause[D], Rule[D]], rules: Dict[str, Rule[D]], result: Dict[Union[Rule[D], Clause[D]], bool]) -> bool:
    """Map all clauses reachable from `subject` as maybe_empty into `result`"""
    raise NotImplementedError(f"map_maybe_empty for type({subject})")


@singledispatch
def map_maybe_empty(subject: Union[Clause[D], Rule[D]], rules: Dict[str, Rule[D]], result: Dict[Union[Rule[D], Clause[D]], bool]) -> bool:
    """Map all clauses reachable from `subject` as maybe_empty into `result`"""
    raise NotImplementedError(f"map_maybe_empty for type({subject})")


def _cache_map_maybe_empty(fn):
    def wrapper(subject: Union[Clause[D], Rule[D]], rules: Dict[str, Rule[D]], result: Dict[Union[Rule[D], Clause[D]], bool]) -> bool:
        try:
            return result[subject]
        except KeyError:
            result[subject] = fn(subject, rules, result)
            return result[subject]

    return wrapper


@map_maybe_empty.register(Value)
@_cache_map_maybe_empty
def _(subject: Value, rules, result) -> bool:
    return not subject.value


@map_maybe_empty.register(Empty)
@_cache_map_maybe_empty
def _(subject: Empty, rules, result) -> bool:
    return True


@map_maybe_empty.register(Any)
@_cache_map_maybe_empty
def _(subject: Any, rules, result) -> bool:
    return subject.length == 0


@map_maybe_empty.register(Sequence)
@_cache_map_maybe_empty
def _(subject: Sequence, rules, result) -> bool:
    return all(map_maybe_empty(sub_clause, rules, result) for sub_clause in subject.sub_clauses)


@map_maybe_empty.register(Choice)
@_cache_map_maybe_empty
def _(subject: Choice, rules, result) -> bool:
    return any(map_maybe_empty(sub_clause, rules, result) for sub_clause in subject.sub_clauses)


@map_maybe_empty.register(Repeat)
@map_maybe_empty.register(Annotate)
@_cache_map_maybe_empty
def _(subject: Union[Repeat, Annotate], rules, result) -> bool:
    return map_maybe_empty(subject.sub_clause, rules, result)


@map_maybe_empty.register(Not)
@map_maybe_empty.register(And)
@_cache_map_maybe_empty
def _(subject: Union[Not, And], rules, result) -> bool:
    return True


@map_maybe_empty.register(Reference)
@_cache_map_maybe_empty
def _(subject: Rule, rules, result) -> bool:
    return map_maybe_empty(rules[subject.name], rules, result)


@map_maybe_empty.register(Rule)
@_cache_map_maybe_empty
def _(subject: Rule, rules, result) -> bool:
    result[subject.name] = True
    return map_maybe_empty(subject.sub_clause, rules, result)
