.. bootpeg documentation master file, created by
   sphinx-quickstart on Tue Mar 30 17:33:14 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

`bootpeg` – the bootstrapping PEG parser
========================================

.. image:: https://readthedocs.org/projects/bootpeg/badge/?version=latest
    :target: https://bootpeg.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. image:: https://img.shields.io/pypi/v/bootpeg.svg
    :alt: Available on PyPI
    :target: https://pypi.python.org/pypi/bootpeg/

.. toctree::
   :maxdepth: 1
   :caption: Usage and Guides
   :hidden:

   source/getting_started
   source/parse_actions
   source/peg_precedence
   source/glossary

.. toctree::
   :maxdepth: 1
   :caption: Builtin Meta Grammars
   :hidden:

   source/grammar_bpeg
   source/grammar_peg

.. toctree::
   :maxdepth: 1
   :caption: Development
   :hidden:

   contributing

`bootpeg` is a PEG parser for creating parsers from grammars – including itself.
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

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


.. _`PEP 617`: https://www.python.org/dev/peps/pep-0617/
