.. _terminals:

Terminal Expressions
====================

Terminals form the bottom of each grammar:
they are compared against the actual input to check for a match.

Special Terminals
-----------------

nothing: ``''`` or ``""``

    Zero-length literal, always matches at any position.
    Used to construct `optional` and `any` rules,
    which should be preferred for readability.

anything: ``.``

    Match any input of width one.
    May lead to excessive matches;
    prefer `range` or `delimited` literals.

Literal Terminals
-----------------

literal: ``" :: "`` or ``' :: '``

    Match any input exactly equal to the literal.

        "def"

range: ``literal1 - literal2``

    Match any input smaller/larger or equal to `literal1`/`literal2`.

        "a" - "z"

delimited: ``literal1 :: literal2``

    Match `literal1` followed by the `literal2` with arbitrary matches in between.
    More efficient version of ``literal1 ( !literal2 . ) literal2``.

        literal:
            | '"' :: '"'
            | "'" :: "'"
