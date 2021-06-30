from typing import Generic, Iterable, Union, Set, Dict, Tuple

from .clauses import Rule
from .interpret import match_clause, Clause
from .pika_meta import _maybe_empty

from ..typing import D


def annotate(top: str, *rules: Rule[D]) -> Dict[str, Tuple[bool, bool, Set[str]]]:
    """
    For each rule reachable from `top` find maybe_empty, terminal and triggers

    `maybe_empty` if it can match the empty string,
    `terminal` if it can match without other rules, and
    `triggers` are the rules it requires for a (new) match.
    """


class Parser(Generic[D]):
    def __init__(self, top: str, *rules: Rule[D]):
        if len(set(rule.name for rule in rules)) < len(rules):
            raise ValueError("rules duplicate names")
        self.top = top
        self.rules = rules
        self._triggers = {rule: () for rule in rules}

    def _compile_rules(self, rules: Iterable[Rule]):
        terminals = []
        triggers = {}
        for rule in rules:
            for referent in references(rule):
                pass