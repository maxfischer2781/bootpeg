.. grammar_actions:

====================
Grammars and Actions
====================

`bootpeg` is designed to translate input sequences to arbitrary runtime objects.
A parser defines how to match and transform input,
which is realised in two separate stages:

* the *Grammar* matches the input to logical clauses, and
* the *Actions* transform the matched clauses to runtime objects.

For example, translating the input string ``"1/2"`` to the object ``Fraction(1, 2)``
requires a grammar clause to match the input and an action to transform it::

    fraction:
        | num=integer '/' denom=integer { Fraction(.num, .denom) }
    #     ^- - Parser match clause - -^  ^-- transform Action --^

`bootpeg` handles both separately:
The Parser can be automatically created from the grammar using `bootpeg` itself,
while the Actions are defined using regular code and simply provided to `bootpeg`.
This allows grammars to be optimised automatically,
and Actions to be changed without affecting the grammar.

Grammar Definition
==================

A Parser can be automatically created from a grammar written in any meta-grammar
supported by `bootpeg`.
Based on the grammar, the Parser encodes how to match input to Actions.

.. code:: python3

    >>> from bootpeg.grammars import bpeg
    >>> grammar = """
    ... integer:
    ...     | ( "0" - "9" )+ { Integer(.*) }
    ... fraction:
    ...     | num=integer ' '* '/' ' '* denom=integer { Fraction(.num, .denom) }
    ... rational:
    ...     | fraction | integer
    ... top:
    ...     | rational (',' ' '* rational)* { .* }
    ... """
    >>> parser = bpeg.parse(grammar)

All ``bootpeg.grammar.<name>.parse`` methods default to the Actions required
to create a Parser.

Actions Definition
==================

The Actions are Python callables which receive part of the matched input to
create the desired output.
A set of :py:class:`bootpeg.Actions` specifies:

``names``
    A mapping from names to callables and objects, which can be used in grammar actions.

``post``
    A single callable to apply a final transformation of the top-most action result.

These will frequently be classes, though functions and constants are valid as well.

.. code:: python3

    >>> from bootpeg import Actions
    >>> from fractions import Fraction
    >>> rational_actions = Actions(
    ...     names={'Integer': int, 'Fraction': Fraction},
    ...     post=list,
    ... )
