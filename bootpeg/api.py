from typing import Mapping, Callable, Protocol, Union
from functools import partial
from types import MappingProxyType

import importlib_resources

from .utility import grammar_resource
from .apegs.boot import apegs_globals, Parser, Grammar, Clause
from .typing import R, TR, D, D_contra, BootPegParser


def identity(x: TR) -> TR:
    return x


bootpeg_actions: Mapping[str, Callable[..., Clause]] = apegs_globals


def bootpeg_post(*args, top=None):
    if len(args) != 1:
        raise ValueError(f"Expected one parse result, got {len(args)}")
    grammar = args[0]
    if top is not None:
        grammar.top = top
    print(grammar, grammar.top, top)
    return args[0]


class Dialect(Protocol[D]):
    unparse: Callable
    parse: Parser[D]


def parse(
    source: D,
    parser: Parser[D],
    post: Callable[..., R] = identity,
    **kwargs,
) -> R:
    """Parse a ``source`` with a given ``parser`` and ``post`` processing"""
    result = parser(source)
    return (
        post(**result, **kwargs)
        if isinstance(result, Mapping)
        else post(*result, **kwargs)
    )


def create_parser(
    source: str,
    dialect: Union[Dialect[str], Parser[str]],
    actions: Mapping[str, Callable] = MappingProxyType({}),
    post: Callable[..., R] = identity,
    **kwargs,
) -> BootPegParser[D, R]:
    """
    Create a parser from a `source` grammar

    :param source: a textual grammar
    :param dialect: the `bootpeg` parser compatible with the grammar
    :param actions: the actions to use for the new parser
    :param post: the postprocessing action to use for the new parser
    :param kwargs: any keyword arguments for the `dialect`'s post processing
    """
    dialect: Parser = getattr(dialect, "parse", dialect)
    grammar = dialect(source, **kwargs)
    if not isinstance(grammar, Grammar):
        raise TypeError(
            f"expected parsing to return a {Grammar.__name__}, got {grammar}"
        )
    return partial(parse, parser=grammar.parser(**actions), post=post)


def import_parser(
    location: str,
    dialect,
    actions: Mapping[str, Callable] = MappingProxyType({}),
    post: Callable[..., R] = identity,
    **kwargs,
) -> BootPegParser[D, R]:
    """
    Import a parser from a grammar at a `location`

    :param location: a module or module-like name
    :param dialect: the `bootpeg` parser compatible with the grammar
    :param actions: the actions to use for the new parser
    :param post: the postprocessing action to use for the new parser
    :param kwargs: any keyword arguments for the `dialect`'s post processing

    The `location` is a dotted module name; it is used to look up the grammar
    using the Python resource import machinery.
    Grammar resources have the extension ``.bpeg`` instead of ``.py``.

    For example, the location ``"bootpeg.grammars.peg"`` looks for a resource named
    ``peg.bpeg`` in the module ``bootpeg.grammars``. Commonly, this means the file
    ``bootpeg/grammars/peg.bpeg``, though the import machinery also supports other
    resource types such as zip archive members.
    """
    source = importlib_resources.read_text(*grammar_resource(location))
    return create_parser(source, dialect, actions, post, **kwargs)
