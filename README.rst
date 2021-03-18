######################################
`bootpeg` – a bootstrapping PEG parser
######################################

> Some people, when confronted with a problem, think "I know, I'll use regular expressions." Now they have two problems.

`bootpeg` is a PEG parser for creating parsers – including itself.
By default, it supports EBNF with actions akin to `PEP 617`_.

.. code-block:: bash

    # legacy naive PEG parser
    $ python3 -m bootpeg.boot
    # memoizing bottom-up PEG parser
    $ python3 -m bootpeg.pika.boot

Unlike most other Python PEG parsers which are top-down Packrat parsers,
``bootpeg`` provides a bottom-up `Pika parser`_:
it handles left-recursive grammars natively,
allows recovering partial parse results,
and runs in linear time for usual inputs.

Do I need a bigger boot?
------------------------

> Some people, when confronted with a problem, think "I know, I'll use self-writing parsers." Now they have problems+.

If you need a battle-hardened, production ready parser suite
then `pyparsing`_ should be your first choice.
If you are the choosy type, make it your second choice as well.

Pick `bootpeg` when you need safe left-recursion and self-parsing.
It will never bite off your left peg via infinite recursion.
It will take care of itself and all its grammars to make you happy.
`bootpeg` is the friend you need when you know `bootpeg` is the friend you need.

Well, *eventually* it will be; ``bootpeg`` is still a cute little puppy.
Don't let it lift too heavy.
So far it is only lifting itself.

.. _`PEP 617`: https://www.python.org/dev/peps/pep-0617/#e1-e2
.. _`pyparsing`: https://pyparsing-docs.readthedocs.io/
.. _`Pika parser`: https://arxiv.org/pdf/2005.06444.pdf
