from typing import Tuple
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
