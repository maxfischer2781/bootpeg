"""
Pika bottom-up PEG parser backend

Based on https://arxiv.org/pdf/2005.06444.pdf, 2020 by Luke A. D. Hutchison
"""
from typing import NamedTuple, Generic, TypeVar, Dict, Tuple, Sequence, Optional, NoReturn, Iterable, Set, List
import copy
import heapq
import functools


#: Parser domain: The input type for parsing, such as str or bytes
D = TypeVar("D", covariant=True, bound=Sequence)


# Ascending memoization
class MemoKey(NamedTuple):
    position: int
    clause: 'Clause'


class Match(NamedTuple):
    length: int
    sub_matches: 'Tuple[Match, ...]'
    position: int
    clause: 'Clause'
    priority: int = 0

    def overrules(self, other: 'Match') -> bool:
        """Whether ``self`` is better than an ``other`` match *for the same clause*"""
        assert self.position == other.position and self.clause == other.clause, (
            f"{self.position}=={other.position} and {self.clause}=={other.clause}"
        )
        return self.priority < other.priority or self.length > other.length


class MemoTable(Generic[D]):
    __slots__ = ('matches', 'source')

    def __init__(self, source):
        self.source = source
        self.matches: Dict[MemoKey, Match] = {}

    def __getitem__(self, item: MemoKey):
        try:
            return self.matches[item]
        except KeyError:
            if isinstance(item.clause, (Not, Anything)):
                match = item.clause.match(self.source, item.position, self)
                if match is not None:
                    self.matches[item] = match
                    return match
            elif item.clause.maybe_zero:
                match = self.matches[item] = Match(0, (), item.position, item.clause)
                return match
            raise  # if you see this, the priorities are wrong. Please open a ticket!

    def insert(self, item: MemoKey, match: Optional[Match]) -> bool:
        """
        Insert new match for item and return whether an update occurred
        """
        if match is not None:
            prev_match = self.matches.get(item)
            if prev_match is None or match.overrules(prev_match):
                self.matches[item] = match
                return True
        return False


# Base Grammar elements
class Clause(Generic[D]):
    """
    Description for matching a specific grammar part
    """
    __slots__ = ()
    #: whether this clause can match zero-length source
    maybe_zero: bool
    #: concrete clauses that make up this clause
    sub_clauses: 'Tuple[Clause[D], ...]'

    @property
    def triggers(self) -> 'Tuple[Clause[D], ...]':
        """Clauses whose match implies that this clause can match"""
        return self.sub_clauses

    def match(self, source: D, at: int, memo: MemoTable) -> Optional[Match]:
        """
        Attempt to match ``source`` ``at`` a specific position

        :param source: entire match domain
        :param at: index at which to match ``source``
        :param memo: Previously memoized matches in the ``source``
        :return: A ``Match`` on success or :py:data:`None` otherwise
        """
        raise NotImplementedError(f"Method 'match' for {self.__class__.__name__}")

    def bind(self, clauses: 'Dict[str, Clause[D]]', canonicals: 'Dict[Clause[D], Clause[D]]'):
        """Inplace bind and deduplicate in the context of named ``clauses``"""
        if self not in canonicals:
            canonicals[self] = self
            sub_clauses = tuple(
                clause.bind(clauses, canonicals)
                for clause in self.sub_clauses
            )
            self.sub_clauses = sub_clauses
        return canonicals[self]


class Terminal(Clause[D]):
    """
    Any clause that does not depend on other clauses
    """
    __slots__ = ()
    sub_clauses = ()

    def bind(self, clauses, canonicals):
        if self not in canonicals:
            canonicals[self] = self
        return canonicals[self]


def postorder_dfs(*bases: Clause[D], _seen: Optional[Set[Clause[D]]] = None) -> Iterable[Clause[D]]:
    """
    Iterate over all clauses reachable from ``bases`` in depth first postorder

    Clauses are deduplicated, making this robust for cycles. The result is in
    bottom-up topological sort order:
    a clause will always occur after all its subclauses.
    """
    _seen = _seen if _seen is not None else set()
    for base in bases:
        if base in _seen:
            continue
        _seen.add(base)
        for sub_clause in reversed(base.sub_clauses):
            if sub_clause not in _seen:
                yield from postorder_dfs(sub_clause, _seen=_seen)
        yield base


def nested_str(clause: Clause):
    """Helper to format sub-clauses with grouping parentheses as required"""
    if isinstance(clause, (Reference, Terminal, Not, Repeat)):
        return str(clause)
    return f"({clause})"


# Specific Grammar elements
class Nothing(Terminal[D]):
    """
    The empty terminal "ε", matches at any point consuming nothing
    """
    maybe_zero = True

    def match(self, source: D, at: int, memo: MemoTable):
        return Match(0, (), at, self)

    def __eq__(self, other):
        return isinstance(other, Nothing)

    def __hash__(self):
        return hash(Nothing)

    def __repr__(self):
        return f"{self.__class__.__name__}()"

    def __str__(self):
        return "ε"


class Anything(Terminal[D]):
    """
    The Any terminal ".", matches at any point with sufficient remainder
    """
    __slots__ = ('length',)
    maybe_zero = False

    def __init__(self, length=1):
        self.length = length

    def match(self, source: D, at: int, memo: MemoTable):
        if at + self.length < len(source):
            return Match(self.length, (), at, self)
        return None

    def __eq__(self, other):
        return isinstance(other, Anything) and self.length == other.length

    def __hash__(self):
        return hash(self.length)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.length})"

    def __str__(self):
        return "." * self.length


class Literal(Terminal[D]):
    """
    A terminal matching a fixed literal
    """
    __slots__ = ('value',)
    maybe_zero = False

    def __init__(self, value: D):
        assert value
        self.value = value

    def match(self, source: D, at: int, memo: MemoTable):
        if source[at:at+len(self.value)] == self.value:
            return Match(len(self.value), (), at, self)
        return None

    def __eq__(self, other):
        return isinstance(other, Literal) and self.value == other.value

    def __hash__(self):
        return hash(self.value)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.value!r})"

    def __str__(self):
        return repr(self.value)


class Sequence(Clause[D]):
    """
    A sequence of clauses, matching if all ``sub_clauses`` match in order
    """
    __slots__ = ('sub_clauses', '_maybe_zero')

    @property
    def maybe_zero(self):
        if self._maybe_zero is None:
            self._maybe_zero = all(
                clause.maybe_zero for clause in self.sub_clauses
            )
        return self._maybe_zero

    @property
    def triggers(self) -> 'Tuple[Clause[D], ...]':
        first_required = next(
            (n for n, scl in enumerate(self.sub_clauses, start=1) if not scl.maybe_zero),
            len(self.sub_clauses)
        )
        return self.sub_clauses[:first_required]

    def __init__(self, *sub_clauses: Clause[D]):
        self.sub_clauses = sub_clauses
        self._maybe_zero = None

    def match(self, source: D, at: int, memo: MemoTable):
        offset, matches = at, ()
        try:
            for sub_clause in self.sub_clauses:
                sub_match = memo[MemoKey(offset, sub_clause)]
                matches += (sub_match,)
                offset += sub_match.length
            return Match(offset - at, matches, at, self)
        except KeyError:
            return None

    def __eq__(self, other):
        return isinstance(other, Sequence) and self.sub_clauses == other.sub_clauses

    def __hash__(self):
        return hash(self.sub_clauses)

    def __repr__(self):
        return f"{self.__class__.__name__}({', '.join(map(repr, self.sub_clauses))})"

    def __str__(self):
        return ' '.join(map(nested_str, self.sub_clauses))


class Choice(Clause[D]):
    """
    A choice of clauses, matching with the first matching clause of ``sub_clauses``
    """
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
                return Match(sub_match.length, (sub_match,), at, self, index)
        return None

    def __eq__(self, other):
        return isinstance(other, Choice) and self.sub_clauses == other.sub_clauses

    def __hash__(self):
        return hash(self.sub_clauses)

    def __repr__(self):
        return f"{self.__class__.__name__}({', '.join(map(repr, self.sub_clauses))})"

    def __str__(self):
        return ' | '.join(map(nested_str, self.sub_clauses))


class Repeat(Clause[D]):
    """
    A repetition of a clause, matching if the sub_clause matches at least once
    """
    __slots__ = ('_sub_clause',)

    @property
    def maybe_zero(self):
        assert not self._sub_clause.maybe_zero, "repeated zero matches infinitely"
        return self._sub_clause.maybe_zero

    @property
    def sub_clauses(self) -> Tuple[Clause[D]]:
        return self._sub_clause,

    @sub_clauses.setter
    def sub_clauses(self, values: Tuple[Clause[D]]):
        self._sub_clause, = values

    def __init__(self, sub_clause: Clause[D]):
        self._sub_clause = sub_clause

    def match(self, source: D, at: int, memo: MemoTable):
        try:
            sub_match = memo[MemoKey(at, self._sub_clause)]
        except KeyError:
            return None
        if sub_match.length == 0:
            return Match(sub_match.length, (sub_match,), at, self)
        # check if there was a previous match by us at the next position
        try:
            prev_match = memo[MemoKey(at + sub_match.length, self)]
        except KeyError:
            return Match(sub_match.length, (sub_match,), at, self)
        else:
            return Match(sub_match.length + prev_match.length, (sub_match, prev_match), at, self)

    def __eq__(self, other):
        return isinstance(other, Not) and self._sub_clause == other._sub_clause

    def __hash__(self):
        return hash(self.sub_clauses)

    def __repr__(self):
        return f"{self.__class__.__name__}({self._sub_clause!r})"

    def __str__(self):
        return f"{nested_str(self._sub_clause)}+"


class Not(Clause[D]):
    """
    The inversion of a clause, matching if the sub_clause does not match
    """
    __slots__ = ('_sub_clause',)
    maybe_zero = True

    @property
    def sub_clauses(self) -> Tuple[Clause[D]]:
        return self._sub_clause,

    @sub_clauses.setter
    def sub_clauses(self, value: Tuple[Clause[D]]):
        self._sub_clause, = value

    @property
    def triggers(self):
        return ()

    def __init__(self, sub_clause: Clause[D]):
        self._sub_clause = sub_clause

    def match(self, source: D, at: int, memo: MemoTable):
        try:
            _ = memo[MemoKey(at, self._sub_clause)]
        except KeyError:
            return Match(0, (), at, self)
        else:
            return None

    def __eq__(self, other):
        return isinstance(other, Not) and self._sub_clause == other._sub_clause

    def __hash__(self):
        return hash(self.sub_clauses)

    def __repr__(self):
        return f"{self.__class__.__name__}({self._sub_clause!r})"

    def __str__(self):
        return f"!{nested_str(self._sub_clause)}"


# Grammar Definitions
# TODO: Add Actions/Rules/Transforms
class UnboundReference(LookupError):
    def __init__(self, target: str):
        self.target = target
        super().__init__(f"Reference {target!r} not bound in a grammar/parser")


def safe_recurse(default=False):
    def decorator(method):
        repr_running = set()

        @functools.wraps(method)
        def wrapper(self):
            if self in repr_running:
                return default
            repr_running.add(self)
            try:
                result = method(self)
            finally:
                repr_running.remove(self)
            return result
        return wrapper
    return decorator


class Reference(Clause[D]):
    """
    Placeholder for another named clause, matching if the target matches
    """
    __slots__ = ('target', '_sub_clause', '_maybe_zero')

    def __init__(self, target: str):
        self.target = target
        self._sub_clause = None
        # TODO: Correct?
        self._maybe_zero: Optional[bool] = None

    @property
    @safe_recurse(default=False)
    def maybe_zero(self):
        if self._maybe_zero is None:
            if self._sub_clause is None:
                self._virtual_clause_()
            else:
                self._maybe_zero = self._sub_clause.maybe_zero
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
            raise
        else:
            return Match(sub_match.length, (sub_match,), at, self)

    def bind(self, clauses: 'Dict[str, Clause[D]]', canonicals: 'Dict[Clause[D], Clause[D]]'):
        """Bind this clause into the context of ``clauses`` inplace"""
        if self not in canonicals:
            canonicals[self] = self
            assert self._sub_clause is None
            self._sub_clause = clauses[self.target].bind(clauses, canonicals)
        return canonicals[self]

    def _virtual_clause_(self) -> NoReturn:
        raise UnboundReference(self.target)

    def __eq__(self, other):
        return isinstance(other, Reference) and self.target == other.target

    def __hash__(self):
        return hash(self.target)

    def __repr__(self):
        if self._sub_clause is None:
            return f"{self.__class__.__name__}({self.target!r},)"
        return f"{self.__class__.__name__}({self.target!r})"

    def __str__(self):
        if self._sub_clause is None:
            return f"<{self.target}>"
        return f"{self.target}"


class ParseFailure(Exception):
    """
    Parsing failed for ``source`` up to the current ``memo`` progress
    """
    def __init__(self, memo: MemoTable):
        self.memo = memo
        super().__init__("Failed to parse source")


class Parser(Generic[D]):
    __slots__ = "top", "clauses", "_compiled_parser"

    def __init__(self, __top__: str, **clauses: Clause[D]):
        self.top = __top__
        self.clauses = clauses
        self._compiled_parser = None

    def _prepare(self):
        if self._compiled_parser is None:
            self._compiled_parser = self._compile(self.top, self.clauses)

    def parse(self, source: D):
        """Parse a ``source`` sequence"""
        if self._compiled_parser is None:
            self._compiled_parser = self._compile(self.top, self.clauses)
        owned_clauses, triggers, priorities = self._compiled_parser
        terminals: List[Tuple[int, Clause[D]], ...] = [
            (-i, clause) for i, clause in enumerate(priorities) if
            isinstance(clause, Terminal)
            and not clause.maybe_zero
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
            return memo[MemoKey(0, owned_clauses[self.top])], memo
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
        owned_clauses[top].bind(owned_clauses, {})
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
