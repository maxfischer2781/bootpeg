########################################
`bootpeg` – the bootstrapping PEG parser
########################################

.. image:: https://readthedocs.org/projects/bootpeg/badge/?version=latest
    :target: https://bootpeg.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. image:: https://img.shields.io/pypi/v/bootpeg.svg
    :alt: Available on PyPI
    :target: https://pypi.python.org/pypi/bootpeg/

.. image:: https://github.com/maxfischer2781/bootpeg/actions/workflows/unittests.yml/badge.svg
    :target: https://github.com/maxfischer2781/bootpeg/actions/workflows/unittests.yml
    :alt: Unit Tests (master)

.. image:: https://github.com/maxfischer2781/bootpeg/actions/workflows/verification.yml/badge.svg
    :target: https://github.com/maxfischer2781/bootpeg/actions/workflows/verification.yml
    :alt: Verification (master)

.. image:: https://codecov.io/gh/maxfischer2781/bootpeg/branch/main/graph/badge.svg
    :target: https://codecov.io/gh/maxfischer2781/bootpeg
    :alt: Test Coverage

> Some people, when confronted with a problem, think "I know, I'll use regular expressions." Now they have two problems.

`bootpeg` is a PEG parser for creating parsers – including itself.
By default, it supports a modified EBNF with actions akin to `PEP 617`_.

.. code-block:: python3

   >>> # recreate the bootpeg parser from itself
   >>> from bootpeg.api import import_parser, bootpeg_actions
   >>> from bootpeg.grammars import bpeg
   >>> parse_bpeg = bpeg.parse
   >>> for _ in range(5):
   ...     parse_bpeg = import_parser(
   ...         bpeg.__name__, dialect=parse_bpeg, actions=bootpeg_actions
   ...     )
   >>> print(bpeg.unparse(parse_bpeg))

Unlike most other Python PEG parsers,
``bootpeg`` is built for one job and one job only:
Define how to transform input into a runtime representation.
There is
no fancy operator overloading,
no custom AST formats,
no clever PEG extensions,
no whitespace special casing,
no nothing.

``bootpeg`` supports left-recursive PEG parsing with actions.
That's it.

To get started using or contributing to `bootpeg`,
head straight to the `bootpeg documentation`_.

Do I need a bigger boot?
------------------------

> Some people, when confronted with a problem, think "I know, I'll use self-writing parsers." Now they have problems in problems.

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

.. _`PEP 617`: https://www.python.org/dev/peps/pep-0617/
.. _`pyparsing`: https://pyparsing-docs.readthedocs.io/
.. _`bootpeg documentation`: https://bootpeg.readthedocs.io
