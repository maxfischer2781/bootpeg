from typing import Sequence, Mapping, Generic, TypeVar, Union
from typing_extensions import Protocol

from .pika.peg import Parser, Clause
from .pika.act import transform
from .pika.boot import namespace as pika_namespace


#: Parser domain: The input type for parsing, such as str or bytes
D = TypeVar("D", covariant=True, bound=Sequence)
#: Transform domain/result: The internal input type and output type of transforming,
#: such as str, tuple, or ast.AST
T = TypeVar("T")
R = TypeVar("R", contravariant=True)


class Action(Protocol[D, R]):
    def __call__(self, *args: D, **kwargs: D) -> R:
        ...


def identity(x: T) -> T:
    return x


class Actions(Generic[D, T, R]):
    def __init__(
        self,
        names: Mapping[str, Union[Action[D, D], Action[D, T], Action[T, T]]],
        post: Action[T, R] = identity,
    ):
        self.names = names
        self.post = post

    def __repr__(self):
        return f"{self.__class__.__name__}({self.names!r}, {self.post!r})"


#: :py:class:`~.Actions` to construct a Pika parser
PikaActions: Actions[str, Union[str, Clause[str]], Parser] = Actions(
    names=pika_namespace,
    post=lambda *args, **kwargs: Parser(
        "top",
        **{name: clause for name, clause in args[0]},
    ),
)


def parse(source: D, parser: Parser[D], actions: Actions[D, T, R]) -> T:
    """Parse a ``source`` with a given ``parser`` and ``actions``"""
    head, memo = parser.parse(source)
    assert head.length == len(source), f"matched {head.length} of {len(source)}"
    args, kwargs = transform(head, memo, actions.names)
    return actions.post(*args, **kwargs)
