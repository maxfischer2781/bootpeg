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
    """Cache the ``__hash__`` of an object to a ``_hash`` attribute"""

    @wraps(__hash__)
    def cached_hash(self):
        _hash = self._hash
        if _hash is None:
            _hash = self._hash = __hash__(self)
        return _hash

    return cached_hash
