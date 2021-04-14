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
   :caption: Usage
   :hidden:

   source/parse_actions

.. toctree::
   :maxdepth: 1
   :caption: Builtin Grammars
   :hidden:

   source/bpeg
   source/terminals

`bootpeg` is a PEG parser for creating parsers – including itself.
By default, it supports a modified EBNF with actions akin to `PEP 617`_.

.. code-block:: python3

   >>> # recreate the bootpeg parser
   >>> from bootpeg.grammars import bpeg
   >>> bpeg.parse(
   ...     bpeg.grammar_path.read_text()
   ... )

Unlike most other Python PEG parsers which are top-down Packrat parsers,
`bootpeg` provides a bottom-up `Pika parser`_:
it handles left-recursive grammars natively,
allows recovering partial parse results,
and runs in linear time for usual inputs.
This makes it straightforward to define custom grammars without
worrying about their implementation.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


.. _`PEP 617`: https://www.python.org/dev/peps/pep-0617/
.. _`Pika parser`: https://arxiv.org/pdf/2005.06444.pdf