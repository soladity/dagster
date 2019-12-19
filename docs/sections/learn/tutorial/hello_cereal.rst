.. py:currentmodule:: dagster

Hello, cereal!
---------------
In this tutorial, we'll explore the feature set of Dagster with small examples that are intended to
be illustrative of real data problems.

We'll build these examples around a simple but scary .csv dataset, ``cereal.csv``, which contains
nutritional facts about 80 breakfast cereals. You can find this dataset on
`Github <https://raw.githubusercontent.com/dagster-io/dagster/master/examples/dagster_examples/intro_tutorial/cereal.csv>`_.
Or, if you've cloned the dagster git repository, you'll find this dataset at
``dagster/examples/dagster_examples/intro_tutorial/cereal.csv``.

To get the flavor of this dataset, let's look at the header and the first five rows:

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/cereal.csv
   :linenos:
   :lines: 1-6
   :caption: cereals.csv
   :language: text

Hello, solid!
^^^^^^^^^^^^^

Let's write our first Dagster solid and save it as ``hello_cereal.py``.

(You can also find this file, and all of the tutorial code, on
`Github <https://github.com/dagster-io/dagster/tree/master/examples/dagster_examples/intro_tutorial>`__
or, if you've cloned the git repo, at ``dagster/examples/dagster_examples/intro_tutorial/``.)

A solid is a unit of computation in a data pipeline. Typically, you'll define solids by
annotating ordinary Python functions with the :py:func:`@solid <solid>` decorator.

The logic in our first solid is very straightforward: it just reads in the csv from a hardcoded path
and logs the number of rows it finds.

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/hello_cereal.py
   :linenos:
   :lines: 1-18
   :caption: hello_cereal.py

In this simplest case, our solid takes no inputs except for the
:py:class:`context <SystemComputeExecutionContext>` in which it executes
(provided by the Dagster framework as the first argument to every solid), and also returns no
outputs. Don't worry, we'll soon encounter solids that are much more dynamic.

Hello, pipeline!
^^^^^^^^^^^^^^^^

To execute our solid, we'll embed it in an equally simple pipeline.

A pipeline is a set of solids arranged into a DAG (or
`directed acyclic graph <https://en.wikipedia.org/wiki/Directed_acyclic_graph>`_) of computation.
You'll typically define pipelines by annotating ordinary Python functions with the
:py:func:`@pipeline <pipeline>` decorator.

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/hello_cereal.py
   :linenos:
   :lineno-start: 21
   :lines: 21-23
   :caption: hello_cereal.py


Here you'll see that we call ``hello_cereal()``. This call doesn't actually execute the solid
-- within the body of functions decorated with :py:func:`@pipeline <pipeline>`, we use
function calls to indicate the dependency structure of the solids making up the pipeline. Here,
we indicate that the execution of ``hello_cereal`` doesn't depend on any other solids by calling
it with no arguments.

.. _executing-our-first-pipeline:

Executing our first pipeline
----------------------------

Assuming you've saved this pipeline as ``hello_cereal.py``, we can execute it via any of three
different mechanisms:

1. From the command line, using the ``dagster`` CLI.
2. From a rich graphical interface, using the ``dagit`` GUI tool.
3. From arbitrary Python scripts, using dagster's Python API.

Using the dagster CLI to execute a pipeline
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

From the directory in which you've saved the pipeline file, just run:

.. code-block:: console

    $ dagster pipeline execute -f hello_cereal.py -n hello_cereal_pipeline

You'll see the full stream of events emitted by dagster appear in the console, including our
call to the logging machinery, which will look like:

.. code-block:: console
  :emphasize-lines: 1

    2019-10-10 11:46:50 - dagster - INFO - system - a91a4cc4-d218-4c2b-800c-aac50fced1a5 - Found 77 cereals
                  solid = "hello_cereal"
        solid_definition = "hello_cereal"
                step_key = "hello_cereal.compute"

Success!

Using dagit to execute a pipeline
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To visualize your pipeline (which only has one node) in dagit, from the directory in which you've
saved the pipeline file, just run run:

.. code-block:: console

   $ dagit -f hello_cereal.py -n hello_cereal_pipeline

You'll see output like

.. code-block:: console

    Loading repository...
    Serving on http://127.0.0.1:3000

You should be able to navigate to http://127.0.0.1:3000/p/hello_cereal_pipeline/explore in
your web browser and view your pipeline. It isn't very interesting yet, because it only has one
node.

.. thumbnail:: hello_cereal_figure_one.png

Clicking on the "Execute" tab (http://127.0.0.1:3000/p/hello_world_pipeline/execute) and you'll
see the two-paned view below.

.. thumbnail:: hello_cereal_figure_two.png

The left hand pane is empty here, but in more complicated pipelines, this is where you'll be able
to edit pipeline configuration on the fly.

The right hand pane shows the concrete execution plan corresponding to the logical structure of
the pipeline -- which also only has one node, ``hello_cereal.compute``.

Click the "Start Execution" button to execute this plan directly from dagit. A new window should
open, and you'll see a much more structured view of the stream of Dagster events start to appear in
the left-hand pane.

(If you have pop-up blocking enabled, you may need to tell your browser to allow pop-ups from
127.0.0.1 -- or, just navigate to the "Runs" tab to see this, and every run of your pipeline.)

.. thumbnail:: hello_cereal_figure_three.png

In this view, you can filter and search through the logs corresponding to your pipeline run.

Using the Python API to execute a pipeline
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you'd rather execute your pipelines as a script, you can do that without using the dagster CLI
at all. Just add a few lines to ``hello_cereal.py``:

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/hello_cereal.py
   :linenos:
   :lineno-start: 26
   :lines: 26-28
   :caption: hello_cereal.py

Now you can just run:

.. code-block:: console

    $ python hello_cereal.py

The :py:func:`execute_pipeline` function called here is the core Python API for executing Dagster
pipelines from code.


Testing solids and pipelines
----------------------------

Our first solid and pipeline wouldn't be complete without some tests to ensure they're working as
expected. We'll use :py:func:`execute_pipeline` to test our pipeline, as well as
:py:func:`execute_solid` to test our solid in isolation.

These functions synchronously execute a pipeline or solid and return results objects (the
:py:class:`SolidExecutionResult` and :py:class:`PipelineExecutionResult`) whose methods let us
investigate, in detail, the success or failure of execution, the outputs produced by solids, and
(as we'll see later) other events associated with execution.

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/hello_cereal.py
   :linenos:
   :caption: hello_cereal.py
   :lineno-start: 31
   :lines: 31-40

Now you can use pytest, or your test runner of choice, to run unit tests as you develop your
data applications.

.. code-block:: console

    $ pytest hello_cereal.py

Note: pytest tests are typically in files prefixed with `test_`. However in order to simplify
the tutorial we have them in the same file.

Obviously, in production we'll often execute pipelines in a parallel, streaming way that doesn't
admit this kind of API, which is intended to enable local tests like this.

Dagster is written to make testing easy in a domain where it has historically been very difficult.
Throughout the rest of this tutorial, we'll explore the writing of unit tests for each piece of
the framework as we learn about it.
