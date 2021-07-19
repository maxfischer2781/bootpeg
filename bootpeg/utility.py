from typing import Tuple, TypeVar, Type


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
