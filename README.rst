######################################
`bootpeg` – a bootstrapping PEG parser
######################################

> Some people, when confronted with a problem, think "I know, I'll use regular expressions." Now they have two problems.

`bootpeg` is a PEG parser for creating parsers – including itself.
By default, it provides EBNF with actions akin to `PEP 617`_.

.. code-block:: bash

    $ python3 -m bootpeg.boot
    $ python3 -m bootpeg.bootpika

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

.. _`PEP 617`: https://www.python.org/dev/peps/pep-0617/#e1-e2
.. _`pyparsing`: https://pyparsing-docs.readthedocs.io/