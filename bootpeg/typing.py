from typing import TypeVar
from typing_extensions import Protocol


# Generic input/output type variables
T = TypeVar("T", contravariant=True)
R = TypeVar("R", covariant=True)
TR = TypeVar("TR")

#: Parser domain: The input type for parsing, such as `str` or `bytes`
D = TypeVar("D", bound="Domain")
D_contra = TypeVar("D_contra", bound="Domain", contravariant=True)


class Domain(Protocol):
    """
    Protocol for types parse-able by :py:mod:`bootpeg`

    Requires a length, slicing and ordering (this implies equality).
    For example, this matches :py:class:`str` and :py:class:`bytes`,
    as well as :py:class:`tuple` and :py:class:`list` if their
    elements support ordering.
    """

    def __len__(self) -> int:
        raise NotImplementedError

    def __getitem__(self: D, item: slice) -> D:
        raise NotImplementedError

    def __le__(self: D, other: D) -> bool:
        raise NotImplementedError


class Transform(Protocol[T, R]):
    """
    Protocol for any callable mapping from input type(s) ``T`` to output type ``R``
    """

    def __call__(self, *args: T, **kwargs: T) -> R:
        raise NotImplementedError


class BootPegParser(Protocol[D_contra, R]):
    """
    Protocol for all :py:mod:`bootpeg` parsers creating parsers
    """

    def __call__(self, source: D_contra, top: str = "top") -> R:
        """
        Parse a parser ``source`` with a known ``top`` rule
        """
        raise NotImplementedError
