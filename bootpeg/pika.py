"""
Pika bottom-up parser backend

Based on https://arxiv.org/pdf/2005.06444.pdf, 2020 by Luke A. D. Hutchison
"""
from typing import NamedTuple, Generic, TypeVar, Dict, Tuple, Sequence, Optional, NoReturn, Iterable, Set, List
import sys
import copy
import heapq


#: Parser domain: The input type for parsing, such as str or bytes
D = TypeVar("D", covariant=True, bound=Sequence)
#: Parser result: The output type for parsing, such as (str, ...)
R = TypeVar("R", contravariant=True)


# Ascending memoization
class MemoKey(NamedTuple):
    position: int
    clause: 'Clause'


class Match(NamedTuple):
    length: int
    sub_matches: 'Tuple[Match, ...]'
    priority: int = 0

    def overrules(self, other: 'Match') -> bool:
        """Whether ``self`` is better than an ``other`` match *for the same clause*"""
        return self.priority < other.priority or self.length > other.length


# sys.maxsize is the maximum container length => worst priority
empty_match = Match(0, (), sys.maxsize)


# TODO: Switch to a persistent data structure such as HAMT/PEP603
class MemoTable(Generic[D]):
    __slots__ = ('_matches', '_source')

    def __init__(self, source):
        self._source = source
        self._matches: Dict[MemoKey, Match] = {}

    def __getitem__(self, item: MemoKey):
        try:
            return self._matches[item]
        except KeyError:
            if isinstance(item.clause, Not):
                match = item.clause.match(self._source, item.position, self)
                if match is not None:
                    self._matches[item] = match
                    return match
            elif item.clause.maybe_zero:
                self._matches[item] = empty_match
                return empty_match
            raise  # if you see this, the priorities are wrong. Please open a ticket!

    def insert(self, item: MemoKey, match: Optional[Match]) -> bool:
        """
        Insert new match for item and return whether an update occurred
        """
        if match is not None:
            prev_match = self._matches.get(item)
            if prev_match is None or match.overrules(prev_match):
                self._matches[item] = match
                return True
        return False


# Base Grammar elements
class Clause(Generic[D]):
    __slots__ = ()
    # whether this clause can match zero-length source
    maybe_zero: bool
    # concrete clauses that make up this clause
    sub_clauses: 'Tuple[Clause[D], ...]'

    @property
    def triggers(self) -> 'Tuple[Clause[D], ...]':
        return self.sub_clauses

    def match(self, source: D, at: int, memo: MemoTable) -> Optional[Match]:
        raise NotImplementedError(f"Method bind for {self.__class__.__name__}")

    def bind(self, clauses: 'Dict[str, Clause[D]]', seen: 'Optional[Set[Clause[D]]]'):
        """Bind this clause into the context of ``clauses`` inplace"""
        for clause in self.sub_clauses:
            clause.bind(clauses, seen)


class Terminal(Clause[D]):
    __slots__ = ()
    sub_clauses = ()

    def bind(self, clauses, seen):
        pass


def postorder_dfs(*bases: Clause[D], _seen: Optional[Set[Clause[D]]] = None) -> Iterable[Clause[D]]:
    """
    Iterate over all clauses reachable from ``bases`` in depth first postorder

    Clauses are deduplicated, making this robust for cycles. The result is in
    bottom-up topological sort order:
    a clause will always occur after all its subclauses.
    """
    _seen = _seen if _seen is not None else set()
    for base in bases:
        _seen.add(base)
        for sub_clause in base.sub_clauses:
            if sub_clause not in _seen:
                _seen.add(sub_clause)
                yield from postorder_dfs(sub_clause, _seen=_seen)
                yield sub_clause
        yield base


# Specific Grammar elements
class Literal(Terminal[D]):
    __slots__ = ('value',)
    maybe_zero = False

    def __init__(self, value: D):
        assert value
        self.value = value

    def match(self, source: D, at: int, memo: MemoTable):
        if source[at:at+len(self.value)] == self.value:
            return Match(len(self.value), ())
        return None

    def __eq__(self, other):
        return isinstance(other, Literal) and self.value == other.value

    def __hash__(self):
        return hash(self.value)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.value!r})"


class Sequence(Clause[D]):
    __slots__ = ('sub_clauses', '_maybe_zero')

    @property
    def triggers(self) -> 'Tuple[Clause[D], ...]':
        first_required = next(
            (n for n, scl in enumerate(self.sub_clauses, start=1) if scl.maybe_zero),
            len(self.sub_clauses)
        )
        return self.sub_clauses[:first_required]

    def __init__(self, *sub_clauses: Clause[D]):
        self.sub_clauses = sub_clauses

    def match(self, source: D, at: int, memo: MemoTable):
        offset, matches = at, ()
        try:
            for sub_clause in self.sub_clauses:
                sub_match = memo[MemoKey(offset, sub_clause)]
                matches += (sub_match,)
                offset += sub_match.length
            return Match(offset - at, matches)
        except KeyError:
            return None

    def __eq__(self, other):
        return isinstance(other, Sequence) and self.sub_clauses == other.sub_clauses

    def __hash__(self):
        return hash(self.sub_clauses)

    def __repr__(self):
        return f"{self.__class__.__name__}({', '.join(map(repr, self.sub_clauses))})"


class Choice(Clause[D]):
    __slots__ = ('sub_clauses', '_maybe_zero')

    @property
    def maybe_zero(self):
        if self._maybe_zero is None:
            self._maybe_zero = any(
                clause.maybe_zero for clause in self.sub_clauses
            )
        return self._maybe_zero

    def __init__(self, *sub_clauses: Clause[D]):
        self.sub_clauses = sub_clauses
        self._maybe_zero = None

    def match(self, source: D, at: int, memo: MemoTable):
        for index, sub_clause in enumerate(self.sub_clauses):
            try:
                sub_match = memo[MemoKey(at, sub_clause)]
            except KeyError:
                pass
            else:
                return Match(sub_match.length, (sub_match,), index)
        return None

    def __eq__(self, other):
        return isinstance(other, Choice) and self.sub_clauses == other.sub_clauses

    def __hash__(self):
        return hash(self.sub_clauses)

    def __repr__(self):
        return f"{self.__class__.__name__}({', '.join(map(repr, self.sub_clauses))})"


class Repeat(Clause[D]):
    __slots__ = ('_sub_clause',)

    @property
    def maybe_zero(self):
        return self._sub_clause.maybe_zero

    @property
    def sub_clauses(self) -> Tuple[Clause[D]]:
        return self._sub_clause,

    def __init__(self, sub_clause: Clause[D]):
        self._sub_clause = sub_clause

    def match(self, source: D, at: int, memo: MemoTable):
        try:
            sub_match = memo[MemoKey(at, self._sub_clause)]
        except KeyError:
            return None
        if sub_match.length == 0:
            return Match(sub_match.length, (sub_match,))
        # check if there was a previous match by us at the next position
        try:
            prev_match = memo[MemoKey(at + sub_match.length, self)]
        except KeyError:
            return Match(sub_match.length, (sub_match,))
        else:
            return Match(sub_match.length + prev_match.length, (sub_match, prev_match))

    def __eq__(self, other):
        return isinstance(other, Not) and self._sub_clause == other._sub_clause

    def __hash__(self):
        return hash(self.sub_clauses)

    def __repr__(self):
        return f"{self.__class__.__name__}({self._sub_clause!r})"


class Not(Clause[D]):
    __slots__ = ('_sub_clause',)
    maybe_zero = True

    @property
    def sub_clauses(self) -> Tuple[Clause[D]]:
        return self._sub_clause,

    @property
    def triggers(self):
        return ()

    def __init__(self, sub_clause: Clause[D]):
        self._sub_clause = sub_clause

    def match(self, source: D, at: int, memo: MemoTable):
        try:
            _ = memo[MemoKey(at, self._sub_clause)]
        except KeyError:
            return empty_match
        else:
            return None

    def __eq__(self, other):
        return isinstance(other, Not) and self._sub_clause == other._sub_clause

    def __hash__(self):
        return hash(self.sub_clauses)

    def __repr__(self):
        return f"{self.__class__.__name__}({self._sub_clause!r})"


# Grammar Definitions
# TODO: Add Actions/Rules/Transforms
class UnboundReference(LookupError):
    def __init__(self, target: str):
        self.target = target
        super().__init__(f"Reference {target!r} not bound in a grammar/parser")


class Reference(Clause[D]):
    __slots__ = ('target', '_sub_clause', '_maybe_zero')

    def __init__(self, target: str):
        self.target = target
        self._sub_clause = None
        self._maybe_zero: Optional[bool] = None

    @property
    def maybe_zero(self):
        if self._maybe_zero is None:
            if self._sub_clause is None:
                self._virtual_clause_()
            self._maybe_zero = any(
                node.maybe_zero for node in postorder_dfs(
                    *self._sub_clause.sub_clauses, _seen={self}
                ) if node != self
            )
        return self._maybe_zero

    @property
    def sub_clauses(self):
        if self._sub_clause is None:
            self._virtual_clause_()
        return self._sub_clause,

    def match(self, source: D, at: int, memo: MemoTable) -> Optional[Match]:
        try:
            sub_match = memo[MemoKey(at, self._sub_clause)]
        except KeyError:
            return None
        else:
            return Match(sub_match.length, (sub_match,))

    def bind(self, clauses: 'Dict[str, Clause[D]]', seen: Optional[Set[Clause[D]]]):
        """Bind this clause into the context of ``clauses`` inplace"""
        assert self._sub_clause is None, "Cannot rebind reference"
        seen.add(self)
        self._sub_clause = clauses[self.target]
        self._sub_clause.bind(clauses, seen)

    def _virtual_clause_(self) -> NoReturn:
        raise UnboundReference(self.target)

    def __eq__(self, other):
        return isinstance(other, Reference) and self.target == other.target

    def __hash__(self):
        return hash(self.target)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.target!r})"


class ParseFailure(Exception):
    def __init__(self, memo: MemoTable):
        self.memo = memo
        super().__init__("Failed to parse source")


class Parser(Generic[D]):
    __slots__ = "top", "clauses", "_compiled_parser"

    def __init__(self, __top__: str, **clauses: Clause[D]):
        self.top = __top__
        self.clauses = clauses
        self._compiled_parser = None

    def parse(self, source: D):
        if self._compiled_parser is None:
            self._compiled_parser = self._compile(self.top, self.clauses)
        owned_clauses, triggers, priorities = self._compiled_parser
        terminals: List[Tuple[int, Clause[D]], ...] = [
            (-i, clause) for i, clause in enumerate(priorities) if
            isinstance(clause, Terminal) and not clause.maybe_zero
        ]
        heapq.heapify(terminals)
        memo = MemoTable(source)
        for position in reversed(range(len(source))):
            outstanding = terminals[:]
            while outstanding:
                clause = heapq.heappop(outstanding)[1]
                result = clause.match(source, position, memo)
                if memo.insert(MemoKey(position, clause), result):
                    for parent_clause in triggers[clause]:
                        heapq.heappush(
                            outstanding, (priorities[parent_clause], parent_clause)
                        )
        try:
            return memo[MemoKey(0, owned_clauses[self.top])]
        except KeyError:
            raise ParseFailure(memo) from None

    def _compile(self, top: str, clauses: Dict[str, Clause[D]]):
        # TODO: add magic
        #   - embed non-recursive rules
        owned_clauses = self._bind_references(top, clauses)
        triggers = self._compile_triggers(owned_clauses[top])
        priorities = self._compile_priorities(owned_clauses[top])
        return owned_clauses, triggers, priorities

    def _bind_references(self, top: str, clauses: Dict[str, Clause[D]]) -> Dict[str, Clause[D]]:
        owned_clauses = copy.deepcopy(clauses)
        owned_clauses[top].bind(clauses, set())
        return owned_clauses

    @staticmethod
    def _compile_triggers(top_clause: Clause[D]) -> Dict[Clause[D], Tuple[Clause[D], ...]]:
        triggers = {trigger: () for trigger in postorder_dfs(top_clause)}
        for parent in postorder_dfs(top_clause):
            for trigger in parent.triggers:
                triggers[trigger] += (parent,)
        return triggers

    @staticmethod
    def _compile_priorities(top_clause: Clause[D]) -> Dict[Clause[D], int]:
        return {
            clause: prio for prio, clause in enumerate(postorder_dfs(top_clause))
        }
