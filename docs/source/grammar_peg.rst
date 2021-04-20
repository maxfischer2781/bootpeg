Canonical ``peg`` Grammar
=========================

The ``peg`` grammar provides the canonical PEG grammar as defined in
"Parsing Expression Grammars: A Recognition Based Syntactic Foundation".
It provides a concise rule declaration, freeform layout and literal escape sequences.

Top-level rules
---------------

spacing: ``" "* | end_line | "#" :: end_line``

    Any amount of whitespace and line-comments is allowed
    between elements of the grammar::

        name  <-  # rule name
            head  # first element
            then  # second element

define: ``name <- ["/"] rule ("/" rule)*``

    A named collection of ordered rules.
    If more than one rule matches, the leftmost matching rule is preferred.

    Definitions and rules have no end delimiter; a sequence of definitions is valid::

        # any sequence of a's and b's
        ab <- a / b a <- "a" ab? b <- "b" ab?

Compound Expressions
--------------------

sequence: ``e1 e2``

    Ordered sequence of clauses, matching ``e1`` followed by ``e2``.
    ::

        "return" expression

choice: ``e1 / e2``

    Ordered choice, matching either ``e1`` or ``e2``.
    If both match, ``e1`` is preferred.

group: ``( e )``

    Match ``e``. Useful to enforce precedence.
    ::

        expr (',' expr)*

option: ``e?``

    Match ``e`` or nothing. Always succeeds, may be zero width.
    ::

        "async"? "def"

not: ``!e``

    Match if ``e`` does not match. Matches with zero width.
    ::

        EndOfFile <- !.

and: ``&e``

    Match if ``e`` does match, but with zero width.
    This is an optimised form of ``!!e``.
    ::

        begin (& ':') colon_block

repeat: ``e+``

    Match ``e`` once or several times.
    ::

        ':' statement+

any: ``e*``

    Match ``e`` zero or several times.


Special Terminals
-----------------

nothing: ``''`` or ``""``

    Zero-length literal, always matches at any position.

anything: ``.``

    Match any input of width one.

Literal Terminals
-----------------

Literals interpret the escape sequences ``\n``, ``\r``, ``\t``,
octal escapes of the form ``\ooo`` and ``\oo``,
and
4-width and 8-with unicode escapes of the form ``\uhhhh`` and ``\Uhhhhhhhh``.
Use ``\'``, ``\"``, ``\[``, ``\]``, ``\\`` for literal special characters.
All other escape sequences are rejected.

literal: ``" :: "`` or ``' :: '``

    Match any input exactly equal to the literal.
    ::

        "def"

range: ``[start "-" stop]`` or ``[first second]``

    Match any single character in the range. Multiple ranges can be combined::

        atoz <- [ab-yzABC-Z]
