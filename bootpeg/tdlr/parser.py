from typing import Generic, Dict
from .clauses import Rule, Reference
from .interpret import match_clause, Match, MatchClause

from ..typing import D


class Parser(Generic[D]):
    def __init__(self, top: str, *rules: Rule[D]):
        self.top = top
        self.rules = rules
        self._match_top = match_clause(Reference(self.top))
        self._match_rules: Dict[str, MatchClause] = {
            rule.name: match_clause(rule.sub_clause) for rule in rules
        }

    def match(self, source: D) -> Match:
        return self._match_top(
            of=source, at=0, memo={}, rules=self._match_rules
        )[-1]
