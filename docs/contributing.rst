===========================
Contributing to ``bootpeg``
===========================

The `bootpeg` development is `hosted on Github <bootpeg github_>`_.
It is the place to go if you want to help us help you and everyone.
Feel free to use it to :ref:`report bugs<report>`,
:ref:`propose improvements<propose>`,
or contribute fixes or features.

.. _bootpeg github: https://github.com/maxfischer2781/bootpeg

.. _report:

Reporting Bugs and Issues
=========================

So you have encountered a bug – that's bad – and
you have decided to report it – that's good!
Now, before reporting a bug take a moment to look through the
`previously reported bugs <allbugs_>`_ if there is already a report.

.. first two bullets are practically the same for the next section

* Does a report exist and provide a solution?
  Great, go right ahead using it and enjoy `bootpeg`.

* Does a report exist but is still open?
  If it lacks some information that you can provide, leave a comment.
  Reports that seem not to be worked on might also benefit from a quick comment
  to raise awareness.
  Either way, consider to subscribe to the report to be notified on progress.

* Does no report exist on the bug?
  Open one and provide the information necessary to look into your problem.

  * What version of `bootpeg` and Python are you using?
    Have you tried another version, and did the bug occur there as well?

  * How can the issue be reproduced reliably?
    Try to strip away all parts that are not needed to reproduce the issue
    – the more `minimal and reproducible your example <mcve_>`_,
    the easier it is to help you.

  If you find a solution to the bug while coming up with an example,
  please open a report anyway.

.. _allbugs: https://github.com/maxfischer2781/bootpeg/issues?q=label%3Abug
.. _mcve: https://stackoverflow.com/help/mcve

.. _propose:

Proposing Features and Improvements
===================================

So you have a good idea how to make `bootpeg` even better – that's the spirit!
Now, extending a library is a lot of work,
so your help is needed to turn a good idea into a practical feature.
Before reporting your proposal take a moment to look through the
`previously suggested features <allsuggestions_>`_ if there is already a report.

.. first two bullets are practically the same for the previous section

* Does a report exist and provide a feature?
  Great, go right ahead using it and enjoy `bootpeg`.

* Does a report exist but is still open?
  If it lacks some information that you can provide, leave a comment.
  Reports that seem not to be worked on might also benefit from a quick comment
  to raise awareness.
  Either way, consider to subscribe to the report to be notified on progress.

* Does no report exist on the feature?
  Open one and provide the information necessary to look into your suggestion.

  * Are there any pre-existing publications on the feature?
    Provide links to webpages, papers or similar that put your suggestion into context.

  * Can you describe the feature as an API, algorithm or code?
    The better you can sketch out the feature,
    the easier it is to discuss and implement.

.. _allsuggestions: https://github.com/maxfischer2781/bootpeg/issues?q=label%3Aenhancement

.. _contribute:

Contributing Fixes and Features
===============================

So you want to actively contribute to `bootpeg` – You. Are. Awesome! 🥳
Now, with every great contribution comes great responsibility,
so here are some steps to help you leave `bootpeg` a little better than you found it.

* In case you just want to get started contributing to open source,
  check out the `recommended first issues <open first issues_>`_.
  These features are similar to existing features in `bootpeg`
  or build on common programming principles – perfect to learn the ropes
  of contributing without worrying much about technical details.

* Every contribution should have an issue for it – check out
  :ref:`propose` or :ref:`report` to find and possibly open
  an issue as appropriate.
  This allows you to get feedback before investing too much time,
  and shows to others that you are tackling the issue.

To actually contribute to the `bootpeg` repository,
you need to open and maintain a Pull Request.
By sticking to the `bootpeg` quality criteria
and responding to feedback on the PR.

.. _open first issues: https://github.com/maxfischer2781/bootpeg/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22

Managing a Pull Request
-----------------------

A Pull Request allows you to commit your changes to a copy of the `bootpeg` repository,
and request them to be merged ("pulled") into the `bootpeg` repository.
If you are not familiar with creating Pull Requests, check out the guides
on `forks <github forks_>`_ and `pull requests from forks <github fork PR_>`_.

When opening a Pull Request, make sure to provide the information needed
to understand your proposal.

* Use a title that summarises the contribution.
  By convention, use imperative mood such as "Add PEG meta-grammar".

* In the Pull Request description, give an outline of your contribution.

  * When the contribution consists of distinct elements, add a task list.
    You can check off tasks as they are completed,
    allowing you and us to track progress.

  * Refer to issues and other Pull Requests affected by your contribution.
    Make sure to mark the corresponding ticket of your contribution,
    such as "``Closes #9.``" (assuming your issue is #9).

After opening the Pull Request, respond to feedback and make new commits as needed.
Once you and us are happy with the contribution,
it will be `squash merged <github squash merge_>`_;
so don't sweat it – we can just rewrite history to fix any errors made along the way!

.. _github forks: https://docs.github.com/en/github/collaborating-with-issues-and-pull-requests/about-forks
.. _github fork PR: https://docs.github.com/en/github/collaborating-with-issues-and-pull-requests/creating-a-pull-request-from-a-fork
.. _github squash merge: https://docs.github.com/en/github/collaborating-with-issues-and-pull-requests/about-pull-request-merges#squash-and-merge-your-pull-request-commits

Keeping Quality High
--------------------

Having new things is great, but they must also fit to all the rest.
There are some formal and informal quality criteria you are asked
to stick to for every contribution:

* Code must be formatted to conform to the ``black`` and ``flake8`` tools.
  *This is enforced by the repository.*
  You can locally check your code by running the tools yourself.
  In most cases, ``black`` is capable of reformatting code adequately:

  .. code-block:: bash

     # use black to reformat code
     python3 -m black bootpeg tests
     # check for remaining code smells
     python3 -m flake8 bootpeg tests

* Code must pass all existing unittests via ``pytest`` for Python 3.6 and upwards.
  *This is enforced by the repository.*
  You can locally check your code by running the tools yourself.

  .. code-block:: bash

     # use black to reformat code
     python3 -m pytest

* Code should be covered by unittests.
  *This is checked but not enforced by the repository.*
  If you contribution is similar to an existing feature,
  take the latter's unittests as a template;
  if not, we will discuss with you how to best approach unittests.

* Any user-facing feature should be documented.
  The documentation is compiled using `sphinx <sphinx home_>`_
  from the ``./docs`` directory.
  If you contribution is similar to an existing feature,
  take the latter's documentation as a template;
  if not, we will discuss with you how to best approach documentation.

Phew! That was a lot to read!
Now go out there and put that knowledge to good use –
we are happy to help you along the way.

.. _sphinx home: https://www.sphinx-doc.org/en/master/
