from typing import Mapping, Union
from functools import partial

import importlib_resources

from .pika.peg import Parser, Clause
from .pika.act import transform
from .pika.boot import namespace as pika_namespace
from .typing import Transform, R, TR, D, BootPegParser


def identity(x: TR) -> TR:
    return x


bootpeg_actions: Mapping[str, Union[Transform[str, Clause], Transform[Clause, Clause]]] = pika_namespace


def bootpeg_post(*args, top="top"):
    return Parser(top, **{name: clause for name, clause in args[0]})


def parse(
    source: D,
    parser: Parser[D],
    actions: Mapping[str, Union[Transform[D, TR], Transform[TR, TR]]],
    post: Transform[TR, R] = identity,
    **kwargs,
) -> R:
    """Parse a ``source`` with a given ``parser`` and ``actions``"""
    head, memo = parser.parse(source)
    assert head.length == len(source), f"matched {head.length} of {len(source)}"
    pos_captures, kw_captures = transform(head, memo, actions)
    return post(*pos_captures, **kw_captures, **kwargs)


def create_parser(
    source: str,
    dialect,
    actions: Mapping[str, Union[Transform[D, TR], Transform[TR, TR]]],
    post: Transform[TR, R] = identity,
    **kwargs,
) -> BootPegParser[D, R]:
    """
    Create a parser with specific `actions` from a `source` grammar

    :param source: a textual grammar
    :param actions: the actions to use for the new parser
    :param dialect: the `bootpeg` parser compatible with the grammar
    :param kwargs: any keyword arguments for the `dialect`'s post processing
    """
    dialect = dialect if not hasattr(dialect, "parse") else dialect.parse
    parser = dialect(source, **kwargs)
    return partial(parse, parser=parser, actions=actions, post=post)


def import_parser(
    location: str,
    dialect,
    actions: Mapping[str, Union[Transform[D, TR], Transform[TR, TR]]],
    post: Transform[TR, R] = identity,
    **kwargs,
) -> BootPegParser[D, R]:
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
    return partial(parse, parser=parser, actions=actions, post=post)
