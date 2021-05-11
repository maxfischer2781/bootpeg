from typing import Sequence, Mapping, Generic, TypeVar, Union
from typing_extensions import Protocol
from functools import partial

import importlib_resources

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
    post=lambda *args, top="top", **kwargs: Parser(
        top,
        **{name: clause for name, clause in args[0]},
    ),
)


def parse(source: D, parser: Parser[D], actions: Actions[D, T, R], **kwargs) -> T:
    """Parse a ``source`` with a given ``parser`` and ``actions``"""
    head, memo = parser.parse(source)
    assert head.length == len(source), f"matched {head.length} of {len(source)}"
    pos_captures, kw_captures = transform(head, memo, actions.names)
    return actions.post(*pos_captures, **kw_captures, **kwargs)


def create_parser(source: str, actions: Actions, dialect, **kwargs):
    """
    Create a parser with specific `actions` from a `source` grammar

    :param source: a textual grammar
    :param actions: the actions to use for the new parser
    :param dialect: the `bootpeg` parser compatible with the grammar
    :param kwargs: any keyword arguments for the `dialect`'s post processing
    """
    dialect = dialect if not hasattr(dialect, "parse") else dialect.parse
    parser = dialect(source, **kwargs)
    return partial(parse, parser=parser, actions=actions)


def import_parser(location: str, actions: Actions, dialect, **kwargs):
    """
    Import a parser with specific `actions` from a grammar at a `location`

    :param location: a module or module-like name
    :param actions: the actions to use for the new parser
    :param dialect: the `bootpeg` parser compatible with the grammar
    :param kwargs: any keyword arguments for the `dialect`'s post processing

    The `location` is a dotted module name; it is used to look up the grammar using the
    import machinery. Grammar resources have the extension ``.bpeg`` instead of ``.py``.

    For example, the location ``"bootpeg.grammars.peg"`` looks for a resource named
    ``peg.bpeg`` in the module ``bootpeg.grammars``. Commonly, this means the file
    ``bootpeg/grammars/peg.bpeg``, though the import machinery also supports other
    resource types such as zip archive members.
    """
    package, _, name = location.rpartition(".")
    source = importlib_resources.read_text(package, name + ".bpeg")
    dialect = dialect if not hasattr(dialect, "parse") else dialect.parse
    parser = dialect(source, **kwargs)
    return partial(parse, parser=parser, actions=actions)
