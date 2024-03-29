The ``bpeg`` Grammar
====================

The ``bpeg`` grammar is modelled after Python's own parser grammar as per `PEP 617`_.
It provides indentation based rules, a EBNF-like expression grammar,
and convenient action declarations.

Top-level rules
---------------

comment: ``'#' ... \n``

    A line comment, discarding the entire line starting at the ``#`` symbol.

define: ``name ':' \n INDENT case+``

    A rule collection of ordered match cases.
    If more than one case matches, the uppermost matching case is preferred.

case: ``'|' e [ '{' action '}' ] \n``

    A case to match any input matching the expression ``e``.
    The optional ``action`` defines how to translate the matched input.

    While a `case` is similar to `choice`, its higher precedence allows to
    concisely define separate actions per case.

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

        !\n

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

    Match ``e`` or fail the entire parse attempt.

    Useful to provide helpful reports on where parsing failed.
    ::

        # fail on empty and mismatched parentheses
        '(' ~ expr ')' | expr

    Binds tighter than sequences and less tight than choices:
    ``~e1 e2 | e3`` is equivalent to ``(~e1 ~e2) | e3``.

capture: ``name=e`` or ``*name=e``

    Capture the result of matching ``e`` with a given ``name`` for use in an action.

    Without ``*``, capture a single result and fail if no or more results are available.
    With ``*``, capture any results available as a tuple.

Special Terminals
-----------------

nothing: ``''`` or ``""``

    Zero-length literal, always matches at any position.
    Used to construct `optional` and `any` rules,
    which should be preferred for readability.

anything: ``.``

    Match any input of width one.
    Useful with `not` to capture any *but* some input::

        # literal quotes enclosing anything but quotes
        '"' (!'"' .)* '"'

Literal Terminals
-----------------

newline: ``\n``

    A literal newline.

literal: ``" ... "`` or ``' ... '``

    Match any input exactly equal to the literal.
    ::

        "def"

range: ``literal1 - literal2``

    Match any input smaller/larger or equal to `literal1`/`literal2`.
    ::

        "a" - "z"

    Literals may be longer than one, but must be of same length.

.. _`PEP 617`: https://www.python.org/dev/peps/pep-0617/