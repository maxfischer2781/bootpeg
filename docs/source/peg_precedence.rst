.. _peg_choices:

======================
Choices and Precedence
======================

Every `bootpeg` grammar is unambiguous since the underlying PEG formalism enforces
unambiguous choices: the first choice matched always wins.
On the one hand, this is useful since it avoids distinct matches "magically"
invalidating each other.
On the other hand, it means that ordering in the grammar must be chosen with care
to achieve the desired language coverage and precedence.

Ordered vs. unordered Choices
=============================

An obvious demonstration for PEG's *ordered choice* are between two terminals
where one is a subsequence of the other::

    "a" | "ab"

With PEG, the second choice branch can never be reached:
Parsing ``"ab"`` will successfully match the first choice and consume ``"a"``,
then fail because there is no rule to consume the remaining ``"b"``.
The key is that later branches in a choice are only tried if earlier branches fail;
if a failure happens *after* the choice, there is no backtracking into the choice.

In contrast, other matching schemes such as RegEx will try every possible
combination of choices until one succeeds:

.. code-block::

    >>> import re
    >>> head, tail = r"a|ab", r"c"
    >>> rule = re.compile(rf"^({head}){tail}$")
    >>> rule.match("abc") is not None
    True

While ordered choices might seem impractical in such simple cases,
they simplify complex grammars and especially :term:`left-recursion`.

Order and left-recursion
========================

Any :term:`left-recursive` rule may be matched at the same position more than once.
This has a powerful implication for ordered choice:
"during" matching the first branch its match has neither failed nor succeeded,
so recursion will try trailing branches.
Whenever ordered choice recurses into itself, several of its branches are matched;
the choice order determines how they are nested into each other.

A simple demonstration uses recursion and an ordered choice to match a sequence::

    # during matching `as as` we can match `"a"` at the same position
    as: as as | "a"

This rule has a higher precedence for "multiple ``as``" over "one ``"a"``".
Due to left-recursion, matching the first branch ``as as`` uses
the second branch ``"a"`` for the *first* clause ``as`` but
the full rule ``as as | "a"`` for the *second* clause ``as``.

Notably, recursion is what makes the choice match several branches.
When swapping the branches to ``"a" | as as``,
either the first branch will match successfully and skip the second branch,
or the first branch will not match and thus make it impossible for the second
branch to match as well.

.. note::

    With recursive-choices,
    use terminals in early branches to *prevent* nesting but
    use terminals in later branches to *enable* nesting.

Precedence via ordered recursion
================================

Properly ordering choices not only decides what input is matched,
but also how it is matched –
in specific, choice order determines the *precedence* of its clauses.

A common example is precedence of mathematical operations.
For example, one can express the precedence of multiplication over addition as
"addition clauses may contain multiplication clauses"::

    addition:
        | lhr=addition ' '* '+' ~ ' '* rhs=multiplication { add(.lhs, .rhs) }
        | up=multiplication { .up }
    multiplication:
        | lhr=multiplication ' '* '*' ~ ' '* rhs=power { mul(.lhs, .rhs) }
        | up=power { .up }
    power:
        | lhs=primitive ' '* '^' ~ ' '* rhs=power { mul(.lhs, .rhs) }
        | up=primitive { .up }
    primitive:
        | '(' ~ exp=top ')' { .exp }
        | "1" - "9" ("0" - "9")* { int(.*) }
    top:
        | addition

This structure is called "precedence climbing":
Every clause may contain a clause of the next precedence level
and "climb ``up``" at the current position.
Notably, the ``top`` clause starts at the *lowest* precedence
which then works its way ``up`` to the highest precedence;
the jump back down from the highest to lowest precedence is only possible
after advancing the position (by a literal match of an opening ``(`` or a number).

In addition, the grammar expresses associativity via recursion:
*left-associative* rules such as ``addition`` use *left-recursion*,
whereas *right-associative* rules such as ``power`` use *right-recursion*. [#pika]_
This allows the rule to expand in the respective direction.

.. note::

    Use choice ordering for precedence, and
    left-/right-recursion for left-/right-associativity.

.. [#pika] Such use of left-recursion is only possible due to `bootpeg`'s
           :term:`Pika Parser`. Regular PEG parsers do not support such grammars/rules.
