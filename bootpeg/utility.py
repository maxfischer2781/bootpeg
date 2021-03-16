ascii_escapes = str.maketrans({
    ord('\n'): '␤',
    ord('\t'): '␉',
    0: '␀',
})


def mono(ascii: str) -> str:
    """Convert an ascii string to a monospace unicode form"""
    return ascii.translate(ascii_escapes)
