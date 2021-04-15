The ``bpeg`` Grammar
====================

The ``bpeg`` grammar is modelled after Python's own parser grammar as per `PEP 617`_.
It provides indentation based rules, a PEG-like expression grammar,
and efficient literal declarations.

See :ref:`terminals` for defining special and literal terminals.

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

        "return" expression

choice: ``e1 | e2``

    Ordered choice, matching either ``e1`` or ``e2``.
    If both match, ``e1`` is preferred.

group: ``( e )``

    Match ``e``. Useful to enforce precedence.

        expr (',' expr)*

option: ``[ e ]``

    Match ``e`` or nothing. Always succeeds, may be zero width.

        [ "async" ] "def"

not: ``!e``

    Match if ``e`` does not match. Matches with zero width.

        ! NEW_LINE

not: ``&e``

    Match if ``e`` does match, but with zero width.
    This is an optimised form of ``!!e``.

        begin (& ':') colon_block

repeat: ``e+``

    Match ``e`` once or several times.

        ':' statement+

any: ``e*``

    Match ``e`` zero or several times. Equivalent to ``[ e+ ]``.

.. _`PEP 617`: https://www.python.org/dev/peps/pep-0617/