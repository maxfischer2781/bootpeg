from typing import Tuple, Set
import re

# tokens
#   ENDLINE
# actions
#   re.escape


class MatchFailure(Exception):
    def __init__(self, expression: 'Expression', remainder: str):
        self.expression = expression
        self.remainder = remainder
        if not remainder:
            super().__init__(f"Failed to match {expression} at end of source")
        else:
            super().__init__(f"Failed to match {expression} at -{len(remainder)}")


class InternalFailure(MatchFailure):
    def __init__(self, expression: 'Expression', remainder: str, reason: BaseException):
        self.expression = expression
        self.remainder = remainder
        self.reason = reason
        if not remainder:
            Exception.__init__(self, f"Failed to match {expression} at end of source: {reason}")
        else:
            Exception.__init__(self, f"Failed to match {expression} at -{len(remainder)}: {reason}")


class Match:
    def __init__(self, *matches, **named):
        self.matches = matches
        self.named = named

    def __or__(self, other):
        if isinstance(other, Match):
            assert not other.named.keys() & self.named.keys()
            return Match(*self.matches, *other.matches, **self.named, **other.named)
        elif isinstance(other, dict):
            return Match(*self.matches, **self.named, **other)
        elif isinstance(other, str):
            return Match(*self.matches, other, **self.named)
        else:
            raise TypeError(f"Unknown match type {other}")

    def __getitem__(self, item):
        if type(item) is int:
            return self.matches[item]
        elif type(item) is str:
            return self.named[item]
        elif type(item) is slice:
            return self.matches[item]
        else:
            raise TypeError(f"Unknown key type for {item}")

    def name(self, name: str) -> 'Match':
        assert name not in self.named
        assert len(self.matches) == 1, f"can only name unique matches {name}={self}"
        return Match(*self.matches, **self.named, **{name: self.matches[0]})

    def __repr__(self):
        matches = ', '.join(map(repr, self.matches))
        named = ', '.join(f"{name}={match!r}" for name, match in self.named.items())
        return f"{self.__class__.__name__}({matches}{', ' if matches and named else ''}{named})"


def skip_recurse(func):
    def match(self, source: str, outer: 'Set[Expression]' = frozenset()):
        if self in outer:
            return False, 0, Match()
        try:
            return func.__get__(self)(source, outer | {self})
        except MatchFailure:
            raise
        except BaseException as err:
            raise InternalFailure(self, source, err)
    return match


def bind_all(children: 'Tuple[Expression, ...]', grammar: 'Grammar') -> 'Tuple[Expression, ...]':
    new_children = tuple(choice.bind(grammar) for choice in children)
    if any(new is not old for new, old in zip(new_children, children)):
        return new_children
    return children


class Expression:
    def match(self, source: str, outer: 'Set[Expression]' = frozenset()) -> Tuple[bool, int, Match]:
        return False, 0, Match()

    def __or__(self, other):
        return Choice(self, other)

    def __add__(self, other):
        assert isinstance(other, Expression), f"an expression is required, not {other}"
        if isinstance(self, Chain):
            chain = (*self.parts,)
        else:
            chain = (self,)
        if isinstance(other, Chain):
            return Chain(*chain, *other.parts)
        else:
            return Chain(*chain, other)

    def __invert__(self):
        return Required(self)

    def __getitem__(self, item):
        assert isinstance(item, slice) and item.start is not None
        return Repeat(self, item.start)

    def bind(self, grammar: 'Grammar') -> 'Expression':
        return self

    def label(self, name: str) -> 'Capture':
        return Capture(name, self)


class Regex(Expression):
    def __init__(self, of: str):
        self.of = of
        try:
            self._pattern = re.compile(f"^({self.of})")
        except re.error as err:
            raise ValueError(f"{err}: {self.of!r}") from None

    def __or__(self, other):
        if isinstance(other, Regex):
            return Regex(self.of + '|' + other.of)
        return super().__or__(other)

    @skip_recurse
    def match(self, source: str, outer: 'Set[Expression]' = frozenset()):
        matched = self._pattern.match(source)
        try:
            return True, len(matched.group(1)), Match(matched.group(1))
        except AttributeError:
            return super().match(source, outer)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.of!r})"


class Choice(Expression):
    def __init__(self, *choices: Expression):
        self.choices = choices

    def __or__(self, other):
        if isinstance(other, Choice):
            return Choice(*self.choices, *other.choices)
        return super().__or__(other)

    # @skip_recurse
    def match(self, source: str, outer: 'Set[Expression]' = frozenset()):
        for choice in self.choices:
            matched, length, found = choice.match(source, outer)
            if matched:
                return matched, length, found
        return super().match(source, outer)

    def __repr__(self):
        return ' | '.join(map(repr, self.choices))

    def bind(self, grammar: 'Grammar') -> 'Expression':
        choices = bind_all(self.choices, grammar)
        if choices is not grammar:
            return Choice(*choices)
        return self


class Chain(Expression):
    def __init__(self, *parts: Expression):
        self.parts = parts

    @skip_recurse
    def match(self, source: str, outer: 'Set[Expression]' = frozenset()):
        total_length, total_found = 0, Match()
        for part in self.parts:
            matched, length, found = part.match(source, outer)
            if not matched:
                return super().match(source, outer)
            total_length += length
            total_found |= found
            source = source[length:]
            outer = set()
        return True, total_length, total_found

    def bind(self, grammar: 'Grammar') -> 'Expression':
        choices = bind_all(self.parts, grammar)
        if choices is not grammar:
            return Chain(*choices)
        return self

    def __repr__(self):
        return "(" + " + ".join(map(repr, self.parts)) + ")"


class Inspect(Expression):
    def __init__(self, base: Expression):
        self.base = base

    def match(self, source: str, outer: 'Set[Expression]' = frozenset()):
        print('match', self.base, 'on', repr(source[:70]), '...')
        matched, length, found = self.base.match(source, outer)
        print('match', self.base, ':', matched, length, repr(found)[:70])
        return matched, length, found

    def bind(self, grammar: 'Grammar') -> 'Expression':
        base = self.base.bind(grammar)
        if base is not self.base:
            return Inspect(base)
        return self

    def __repr__(self):
        return f"{self.__class__.__name__}({self.base!r})"


class Maybe(Expression):
    def __init__(self, base: Expression):
        self.base = base

    @skip_recurse
    def match(self, source: str, outer: 'Set[Expression]' = frozenset()):
        matched, length, found = self.base.match(source, outer)
        return True, length, found

    def bind(self, grammar: 'Grammar') -> 'Expression':
        base = self.base.bind(grammar)
        if base is not self.base:
            return Maybe(base)
        return self

    def __repr__(self):
        return f"{self.__class__.__name__}({self.base!r})"


class Repeat(Expression):
    def __init__(self, base: Expression, min: int):
        self.base = base
        self.min = min

    @skip_recurse
    def match(self, source: str, outer: 'Set[Expression]' = frozenset()):
        matches, total_length, total_found = 0, 0, Match()
        while source:
            matched, length, found = self.base.match(source, outer)
            if not matched:
                return matches >= self.min, total_length, total_found
            matches += 1
            total_length += length
            total_found |= found
            source = source[length:]
            outer = set()
        return matches >= self.min, 0, total_found

    def bind(self, grammar: 'Grammar') -> 'Expression':
        base = self.base.bind(grammar)
        if base is not self.base:
            return Repeat(base, self.min)
        return self

    def __repr__(self):
        return f"{self.base}[{self.min}:]"


class Required(Expression):
    def __init__(self, base: Expression):
        self.base = base

    @skip_recurse
    def match(self, source: str, outer: 'Set[Expression]' = frozenset()):
        matched, length, found = self.base.match(source, outer)
        if not matched:
            raise MatchFailure(self, source)
        return True, length, found

    def bind(self, grammar: 'Grammar') -> 'Expression':
        base = self.base.bind(grammar)
        if base is not self.base:
            return Required(base)
        return self

    def __repr__(self):
        return f"~{self.base!r}"


class Capture(Expression):
    def __init__(self, name: str, base: Expression):
        self.name = name
        self.base = base

    @skip_recurse
    def match(self, source: str, outer: 'Set[Expression]' = frozenset()):
        matched, length, found = self.base.match(source, outer)
        if not matched:
            return super().match(source, outer)
        return matched, length, found.name(self.name)

    def bind(self, grammar: 'Grammar') -> 'Expression':
        base = self.base.bind(grammar)
        if base is not self.base:
            return Capture(self.name, base)
        return self

    def __repr__(self):
        return f"{self.base!r}.label({self.name!r})"


class Rule(Expression):
    def __init__(self, base: Expression, action=lambda match: Match(*match.matches)):
        self.base = base
        self.action = action

    # @skip_recurse
    def match(self, source: str, outer: 'Set[Expression]' = frozenset()):
        matched, length, found = self.base.match(source, outer)
        if not matched:
            return super().match(source, outer)
        # TODO: Should result be unpacked?
        return matched, length, self.action(found)

    def bind(self, grammar: 'Grammar') -> 'Rule':
        base = self.base.bind(grammar)
        if base is not self.base:
            return Rule(base, self.action)
        return self

    def __repr__(self):
        return f"{self.__class__.__name__}({self.base!r}, {self.action!r})"


class ForwardReference(Expression):
    def __init__(self, name: str):
        self.name = name

    @skip_recurse
    def match(self, source: str, outer: 'Set[Expression]' = frozenset()):
        raise NotImplementedError(f"Rule {self.name} is not implemented by the grammar")

    def bind(self, grammar: 'Grammar') -> 'Expression':
        if self.name in grammar.rules:
            return Reference(self.name, grammar)
        return self

    def __repr__(self):
        return f"<{self.name}?>"


class Reference(Expression):
    def __init__(self, name: str, grammar: 'Grammar'):
        self.name = name
        self.grammar = grammar

    @skip_recurse
    def match(self, source: str, outer: 'Set[Expression]' = frozenset()):
        return self.grammar.rules[self.name].match(source, outer)

    def bind(self, grammar: 'Grammar') -> 'Expression':
        if grammar is not self.grammar:
            return Reference(self.name, grammar)
        return self

    def __repr__(self):
        return f"{self.name}"


class Grammar:
    def __init__(self, **rules: Rule):
        self.rules = rules
        # todo: use topological sort instead?
        for name, rule in rules.items():
            self.rules[name] = rule.bind(self)
        for name, rule in rules.items():
            self.rules[name] = rule.bind(self)

    def add(self, **rules: Rule) -> 'Grammar':
        return Grammar(**self.rules, **rules)


class Action:
    positional = re.compile(r"\.(\d+)")
    unpack = re.compile(r"\.\*")
    named = re.compile(r"(^|[ (])\.([a-zA-Z]+)")

    def __init__(self, literal: str, namespace: dict):
        self.literal = literal
        self.code = self._encode(literal)
        self._callable = eval(self.code, namespace)

    def __call__(self, match: Match):
        try:
            return self._callable(match)
        except Exception as err:
            raise type(err)(f"{err} <{self.code}> {match}")

    @classmethod
    def _encode(cls, literal):
        body = cls.named.sub(
            r"\1__match['\2']",
            cls.positional.sub(
                r" __match[\1]",
                cls.unpack.sub(r" *__match[:]", literal)
            )
        )
        return f'lambda __match: Match({body})'

    def __repr__(self):
        return f"{self.__class__.__name__}({self.literal!r})"


class Parser:
    def __init__(self, grammar: Grammar, top: str):
        self.top = top
        self.grammar = grammar

    def parse(self, source: str):
        top_rule = self.grammar.rules[self.top]
        try:
            matched, consumed, result = top_rule.match(source)
            if not matched:
                raise MatchFailure(top_rule, source)
        except MatchFailure as mf:
            failed_index = len(source) - len(mf.remainder)
            line_start = source.rfind("\n", 0, failed_index) + 1
            failed_line, *_ = source[line_start:].partition('\n')
            print("'", failed_line, "'", sep='')
            print(' ' * (failed_index - line_start), '^~~~>')
            print(mf)
        else:
            return result


def try_match(expr: Expression, source: str):
    try:
        print(expr.match(source))
    except MatchFailure as mf:
        print("!!!", mf)
        print(source)
        print(' ' * (len(source) - len(mf.remainder)), '^')


if __name__ == "__main__":
    white = Regex(" ")[0:]
    pattern = (
        Regex("Hello") | Regex("World")
    ) + white + Capture("name", Regex("Bruce") + Maybe(Regex("Wayne")))
    rule = Rule(pattern, lambda match: Match(*match.named['name']))
    print(rule, rule.match("Hello Bruce"))
    print("-------------")
    g = Grammar(
        parens=Rule(Regex("\(") + ~ForwardReference("expr") + ~Regex("\)")),
    )
    g = g.add(
        expr=Rule(ForwardReference("parens") | Regex("[^()]")[1:])
    )
    try_match(g.rules["parens"], "((((Hello))))")
    print(Action(".0 | .1 + .bar")(Match(1, 2, bar=5)))
