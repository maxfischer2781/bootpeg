from typing import Mapping, Callable, Union
from typing_extensions import Protocol
from types import MappingProxyType
import importlib.resources

from .utility import grammar_resource
from .apegs.boot import apegs_actions, Parser, Grammar, Clause
from .typing import R, D


#: the default actions to create a :py:mod:`bootpeg` parser
bootpeg_actions: Mapping[str, Callable[..., Clause]] = apegs_actions


class Dialect(Protocol[D]):
    unparse: Callable[[Union[Parser, Grammar, Clause]], str]
    parse: Parser[str, Grammar]


def create_parser(
    source: str,
    dialect: Union[Dialect[str], Parser[str, Grammar]],
    actions: Mapping[str, Callable] = MappingProxyType({}),
) -> Parser[D, R]:
    """
    Create a parser from a `source` grammar

    :param source: a textual grammar
    :param dialect: the `bootpeg` parser compatible with the grammar
    :param actions: the actions to use for the new parser
    """
    parser: Parser = getattr(dialect, "parse", dialect)
    grammar = parser(source)
    if not isinstance(grammar, Grammar):
        raise TypeError(
            f"expected parsing to return a {Grammar.__name__}, got {grammar}"
        )
    return grammar.parser(**actions)


def import_parser(
    location: str,
    dialect,
    actions: Mapping[str, Callable] = MappingProxyType({}),
) -> Parser[D, R]:
    """
    Import a parser from a grammar at a `location`

    :param location: a module or module-like name
    :param dialect: the `bootpeg` parser compatible with the grammar
    :param actions: the actions to use for the new parser

    The `location` is a dotted module name; it is used to look up the grammar
    using the Python resource import machinery.
    Grammar resources have the extension ``.bpeg`` instead of ``.py``.

    For example, the location ``"bootpeg.grammars.peg"`` looks for a resource named
    ``peg.bpeg`` in the module ``bootpeg.grammars``. Commonly, this means the file
    ``bootpeg/grammars/peg.bpeg``, though the import machinery also supports other
    resource types such as zip archive members.
    """
    source = importlib.resources.read_text(*grammar_resource(location))
    return create_parser(source, dialect, actions)
