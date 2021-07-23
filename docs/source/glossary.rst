=================
Glossary of Terms
=================

.. Rules for references in the glossary itself:
   When mentioning other items, always reference them.
   When mentioning the current item, never reference it.

.. glossary::

   APEGS
   APEGS Parser
      The "*Actions* and *PEG* *S*\ ystem" is a parsing algorithm for :term:`PEG`
      naturally supporting left-recursion and actions.
      It is a straightforward application of the PEG algorithm proposed in
      `Left Recursion in Parsing Expression Grammars <Medeiros Paper_>`_
      augmented with capture, transform, and require clauses.

      The APEGS algorithm is currently the only backend used by `bootpeg`.
      It is purposely simple and compatible with both
      imperative and functional paradigms.

   left-recursive
   left-recursion
      A rule that depends on itself in the "left-most" position::

         as: as as | "a"

      Problematic since it implies that for the rule to match, the rule must match.
      While the :term:`PEG` formalism makes this unambiguous, naive parser algorithms
      infinitely recurse or fail to parse left-recursive grammars.
      The :term:`APEGS Parser` used by `bootpeg` explicitly supports left-recursion.

      Left-recursion is a natural way to express many common grammars,
      such as mathematical expressions.
      Even when not using explicitly left-recursive rules,
      "hidden left-recursion" can arise from mixing options, choices and recursion.

   Pika
   Pika Parser
      A parsing algorithm for :term:`PEG` naturally supporting left-recursion,
      multiple error reporting, and linear runtime.
      Unlike naive and Packrat :term:`PEG` parsers, Pika parses "double reverse"
      by matching bottom-up from the back of the input.

      The Pika algorithm was first
      `published by Luke A. D. Hutchison <Pika Paper_>`_.
      It was the original algorithm used by `bootpeg` and
      only retired because its left-recursion behaviour
      was not practical for some desired grammars.

   PEG
   Parsing Expression Grammar
      An analytic formal grammar describing a language by the rules for matching
      subsets of the language.
      The term PEG is commonly used not just for the formal grammar itself,
      but also the fundamental set of matching rules
      and equivalent parser implementations.

      The key feature of PEG is that choices are ordered and matching is greedy;
      both reduce backtracking and enforce unambiguity.
      While this makes PEG straightforward to reason about and
      is ideal for an explicit, simple style without special cases,
      it means that grammars must be written with care since PEG does not allow
      to "guess" the intention of grammars.

.. _`Pika Paper`: https://arxiv.org/abs/2005.06444
.. _`Medeiros Paper`: Left Recursion in Parsing Expression Grammars
