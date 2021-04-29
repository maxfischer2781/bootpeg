The ``bpeg`` Grammar
====================

The ``bpeg`` grammar is modelled after Python's own parser grammar as per `PEP 617`_.
It provides indentation based rules, a EBNF-like expression grammar,
and efficient literal declarations.

Top-level rules
---------------

comment: ``'#' :: NEW_LINE``

    A line comment, discarding the entire line starting at the ``#`` symbol.

define: ``name ':' NEW_LINE INDENT rule+``

    A named collection of ordered rules.
    If more than one rule matches, the uppermost matching rule is preferred.

rule: ``'|' e [ '{' action '}' ] NEW_LINE``

    A rule to match any input matching the expression ``e``.
    The optional ``action`` defines how to translate the matched input.

Compound Expressions
--------------------

sequence: ``e1 e2``

    Ordered sequence of clauses, matching ``e1`` followed by ``e2``.
    ::

        "return" expression

choice: ``e1 | e2``

    Ordered choice, matching either ``e1`` or ``e2``.
    If both match, ``e1`` is preferred.

group: ``( e )``

    Match ``e``. Useful to enforce precedence.
    ::

        expr (',' expr)*

option: ``[ e ]``

    Match ``e`` or nothing. Always succeeds, may be zero width.
    ::

        [ "async" ] "def"

not: ``!e``

    Match if ``e`` does not match. Matches with zero width.
    ::

        ! NEW_LINE

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

    Match ``e`` zero or several times. Equivalent to ``[ e+ ]``.

commit: ``~ e``

    Match ``e`` or fail. Always succeeds, may be zero width.

    Failure to match ``e`` records the failure but proceeds "as if" ``e`` matched.
    Useful for accurate failure reports.
    ::

        # fail on empty and mismatched parentheses
        '(' ~ expr ')' | expr

    Binds tighter than sequences and less tight than choices:
    ``~e1 e2 | e3`` is equivalent to ``(~e1 ~e2) | e3``.

capture: ``name=e``

    Capture the result of matching ``e`` with a given ``name`` for use in a rule action.

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
    ::

        "def"

range: ``literal1 - literal2``

    Match any input smaller/larger or equal to `literal1`/`literal2`.
    ::

        "a" - "z"

delimited: ``literal1 :: literal2``

    Match `literal1` followed by the `literal2` with arbitrary matches in between.
    More efficient version of ``literal1 ( !literal2 . ) literal2``.
    ::

        literal:
            | '"' :: '"'
            | "'" :: "'"


.. _`PEP 617`: https://www.python.org/dev/peps/pep-0617/