===========
Quick Guide
===========

Using `bootpeg` to create a parser is done in three steps:
Define a *Grammar* to match input,
provide some *Actions* to transform matches,
and
tell `bootpeg` to use both to create the parser.

This guide shows the parts needed to create a parser for
basic scientific number notation.
It can parse numbers as `integer`, such as ``10`` or ``-16``,
or `scientific`, such as ``1e1`` or ``-160E-1``.

Grammar and Actions
===================

The *Grammar* is a textual definition how to match input. [#anysequence]_
You can write a grammar in one of many meta-grammars,
though we suggest the `bootpeg` meta-grammar by default.
A grammar consists of *rules* that decide which input is valid
and how it is to be interpreted:

.. code::

    # bootpeg uses # for line comments
    # the first rule must match the entire input, usually via other rules
    top:
        | scientific | integer

    # a named rule – can be referred to in other rules by name
    integer:
        | literal=([ "-" ] "1"-"9" "0"-"9"*) { Integer(literal) }
    #     ^        ^       ^                  ^ interpret match as Integer
    #     |        |       \ match a digit between 1 and 9 followed by arbitrary many digits
    #     |        \ match an optional leading sign
    #     \ capture (parts of) match to transform them

    scientific:
        | base=integer ("E" | "e")  exponent=integer { base * (10 ** exponent) }
    #     ^             ^ either E or e may be used for the exponent
    #     \ capture part of the match to interpret it separately

The *Actions* are callables and constants needed to transform input.
You can define actions freely using any code you like;
``bootpeg`` merely expects them in a mapping from each
of the grammar's names to the respective action:

.. code:: python3

    >>> # map from names used in the grammar to callables
    >>> example_actions = {
    ...     # use the builtin `int` to interpret any matched Integer
    ...     'Integer': int
    ... }

The Grammar uses *captures* like ``base=integer`` to select part of the input.
The *transformations* like ``{ Integer(literal) }`` define how captured values
are passed to Actions.

Boot the PEG
============

There are two convenient ways to create a parser from the grammar and actions:

* use ``bootpeg.create_parser`` to load the grammar from a *string*, or
* use ``bootpeg.import_parser`` to load the grammar from a *packaged file*.

Generally, you should work with a string for interactive development,
and a packaged file in any other case.
In addition to the grammar, both functions also take
the *actions* of your new parser,
and the `bootpeg` *dialect* of the grammar.

Simply pass in the grammar, the actions defined, and the dialect
– in this case ``bootpeg.grammars.bpeg`` for the `bootpeg` meta-grammar.

.. code:: python3

    >>> from bootpeg import create_parser
    >>> from bootpeg.grammars import bpeg
    >>> example_grammar = """\
    ... top:
    ...     | scientific | integer
    ... integer:
    ...     | [ "-" ] "1" - "9" ("0" - "9")* { Integer(.*) }
    ... scientific:
    ...     | base=integer ("E" | "e")  exponent=integer { .base * (10 ** .exponent) }
    ... """
    >>> example_actions = {'Integer': int}
    >>> parse = create_parser(example_grammar, bpeg, example_actions)
    >>> parse("12")
    12
    >>> parse("12E6")
    12000000

Where to next?
==============

As `bootpeg` uses the PEG formalism, grammars are order-dependent.
In the example, swapping ``| scientific | integer`` for ``| integer | scientific``
would not work well:
matching ``12E6`` would just match ``12`` as an ``integer`` and be done.
See :ref:`peg_choices` on how to use ordering to your advantage.

Separating the task of grammars and actions is integral to how `bootpeg` operates.
Likewise, one should aim at creating parsers where each part handles its strong point.
In the example, the grammar *recognizes* numbers but the actions *interpret* them.
See :ref:`grammar_actions` on how to best match the tasks of grammars and actions.

.. [#anysequence] `bootpeg` itself can handle arbitrary input sequences,
                  not just strings/text.
