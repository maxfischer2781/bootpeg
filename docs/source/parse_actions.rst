.. _grammar_actions:

====================
Actions and Captures
====================

`bootpeg` is designed to translate input sequences to arbitrary runtime objects.
A parser defines how to match and transform input,
which is realised in two separate stages:

* the *Grammar* matches the input and captures logical clauses, and
* the *Actions* transform the matched clauses to runtime objects.

For example, translating the input string ``"1/2"`` to the object ``Fraction(1, 2)``
requires a grammar clause to match the input and an action to transform it::

    fraction:
        | num=integer '/' denom=integer { Fraction(num, denom) }
    #     ^- -  match and capture  - -^  ^-     transform     -^

Actions Definition
==================

Actions consist of two parts
* the action expressions in the grammar, denoted by ``{ }``, and
* the action namespace when creating a parser.

An action expression is interpreted as a Python expression.
``bootpeg`` treats captured names as local variables
and supplies the action namespace as global.

Capturing Results
=================

Parsing does not expose some intermediate syntax tree or similar,
but requires to explicitly capture *results* of matching the input.
Depending on the capture method used, this covers either
a single slice of the input,
a single result of transforming the input, or
several results of transforming the input.

A regular capture ``name=expression`` where expression is, directly or indirectly,
a literal input match captures the entire matched input as a slice.
This is the case when matching values like ``"abc"``, ranges like ``"a"-"z"``,
any value ``.``, and any combination thereof::

    # capture a numeric sequence from the input
    integer:
        | literal=('1'-'9' '0'-'9'*) { Integer(literal) }

A regular capture ``name=expression`` where expression is, partially or completely,
an application of an action captures the *single* result of that action.
This ignores any matched input not transformed by an action,
and requires to capture exactly one result::

    # capture previously transformed input
    fraction:
        | num=integer '/' denom=integer { Fraction(num, denom) }

A variadic capture ``*name=expression`` captures all results of actions
applied by ``expression`` as a tuple.
This ignores any matched input not transformed by an action,
and may capture no or arbitrary many results::

    # capture arbitrary many trailing items
    sequence:
        | '[' head=fraction *tail=(',' fraction) [',']  ']' { Sequence(head, *tail) }

