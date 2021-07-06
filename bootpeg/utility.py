from typing import Tuple, TypeVar, Type
from functools import wraps

ascii_escapes = str.maketrans(
    {
        ord("\n"): "␤",
        ord("\t"): "␉",
        0: "␀",
    }
)


def mono(ascii: str) -> str:
    """Convert an ascii string to a monospace unicode form"""
    return ascii.translate(ascii_escapes)


def cache_hash(__hash__):
    """
    Cache the ``__hash__`` of an object to a ``_hash`` attribute

    Applied as a decorator to the ``__hash__`` method of a class.
    Instances must have a writeable ``_hash`` attribute that is *not* initialised.
    """

    @wraps(__hash__)
    def cached_hash(self):
        try:
            return self._hash
        except AttributeError:
            _hash = self._hash = __hash__(self)
            return _hash

    return cached_hash


def safe_recurse(default=False):
    """
    Mark a function/method as recursion-safe, returning ``default`` on recursion

    This function is *not* threadsafe.
    """

    def decorator(method):
        repr_running = set()

        @wraps(method)
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


def grammar_resource(location: str) -> Tuple[str, str]:
    """
    Given a module-like location, return the package and resource of a grammar

    :param location: a module-like location, such as ``"bootpeg.grammar.peg"``
    :return: a package and resource, such as ``"bootpeg.grammar", "peg.bpeg"``
    """
    if location == "__main__":
        location = __import__("__main__").__spec__.name
    package, _, name = location.rpartition(".")
    return package, f"{name}.bpeg"


T = TypeVar("T")


def slotted(cls: Type[T]) -> Type[T]:
    """
    Class decorator to add ``__repr__``, ``__eq__`` and ``__hash__`` from ``__slots__``
    """
    # use dict comprehension to get unique insertion order
    slots = tuple(
        {
            name: None
            for scls in reversed(cls.__mro__)
            for name in getattr(scls, "__slots__", ())
        }
    )

    def __repr__(self: T):
        members = ", ".join(f"{name}={getattr(self, name)!r}" for name in slots)
        return f"{self.__class__.__name__}({members})"

    def __eq__(self: T, other) -> bool:
        return isinstance(other, type(self)) and all(
            getattr(self, name) == getattr(other, name) for name in slots
        )

    def __hash__(self: T) -> int:
        return hash((*(getattr(self, name) for name in slots), hash(type(self))))

    cls.__repr__ = __repr__
    cls.__eq__ = __eq__
    cls.__hash__ = __hash__
    return cls
