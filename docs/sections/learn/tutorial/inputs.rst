Parametrizing solids with inputs
--------------------------------

So far, we've only seen solids whose behavior is the same every time they're run:

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/serial_pipeline.py
   :lines: 6-15
   :linenos:
   :lineno-start: 6
   :caption: serial_pipeline.py

In general, though, rather than relying on hardcoded values like ``dataset_path``, we'd like to be
able to parametrize our solid logic. Appropriately parametrized solids are more testable, and
also more reusable. Consider the following more generic solid:

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/inputs.py
   :lines: 6-12
   :linenos:
   :lineno-start: 6
   :caption: inputs.py

Here, rather than hardcoding the value of ``dataset_path``, we use an input, ``csv_path``. It's
easy to see why this is better. We can reuse the same solid in all the different places we
might need to read in a .csv from a filepath. We can test the solid by pointing it at some known
test csv file. And we can use the output of another upstream solid to determine which file to load.

Let's rebuild a pipeline we've seen before, but this time using our newly parametrized solid.

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/inputs.py
   :lines: 1-32
   :linenos:
   :emphasize-lines: 32
   :caption: inputs.py

As you can see above, what's missing from this setup is a way to specify the ``csv_path``
input to our new ``read_csv`` solid in the absence of any upstream solids whose outputs we can
rely on.

Dagster provides the ability to stub inputs to solids that aren't satisfied by the pipeline
topology as part of its flexible configuration facility. We can specify config for a pipeline
execution regardless of which modality we use to execute the pipline -- the Python API, the Dagit
GUI, or the command line.


Specifying config in the Python API
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We previously encountered the :py:func:`execute_pipeline <dagster.execute_pipeline>` function.
Pipeline configuration is specified by the second argument to this function, which must be a dict
(the "environment dict").

This dict contains all of the user-provided configuration with which to execute a pipeline. As such,
it can have a lot of sections, but we'll only use one of them here: per-solid configuration, which
is specified under the key ``solids``:

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/inputs.py
    :linenos:
    :lineno-start: 36
    :lines: 36-40
    :dedent: 4
    :caption: inputs.py

The ``solids`` dict is keyed by solid name, and each solid is configured by a dict that may itself
have several sections. In this case we are only interested in the ``inputs`` section, so
that we can specify the value of the input ``csv_path``.

Now you can pass this environment dict to :py:func:`execute_pipeline <dagster.execute_pipeline>`:

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/inputs.py
    :linenos:
    :lines: 41-43
    :dedent: 4
    :lineno-start: 41
    :caption: inputs.py


Specifying config using YAML fragments and the dagster CLI
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When executing pipelines with the dagster CLI, we'll need to provide the environment dict in a
config file. We use YAML for the file-based representation of an environment dict, but the values
are the same as before:

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/inputs_env.yaml
   :language: YAML
   :linenos:
   :caption: inputs_env.yaml

We can pass config files in this format to the dagster CLI tool with the ``-e`` flag.

.. code-block:: console

    $ dagster pipeline execute -f inputs.py -n inputs_pipeline -e inputs_env.yaml

In practice, you might have different sections of your environment dict in different yaml files --
if, for instance, some sections change more often (e.g. in test and prod) while other are more
static. In this case, you can set multiple instances of the ``-e`` flag on CLI invocations, and
the CLI tools will assemble the YAML fragments into a single environment dict.


Using the Dagit config editor
-----------------------------

Dagit provides a powerful, schema-aware, typeahead-enabled config editor to enable rapid
experimentation with and debugging of parametrized pipeline executions. As always, run:

.. code-block:: console

   $ dagit -f inputs.py -n inputs_pipeline

Notice the error in the right hand pane of the Execute tab.

.. thumbnail:: inputs_figure_one.png

Because Dagit is schema-aware, it knows that this pipeline now requires configuration in order to
run without errors. In this case, since the pipeline is relatively trivial, it wouldn't be
especially costly to run the pipeline and watch it fail. But when pipelines are complex and slow,
it's invaluable to get this kind of feedback up front rather than have an unexpected failure deep
inside a pipeline.

Recall that the execution plan, which we would ordinarily see in the right-hand pane of the Execute
tab, is the concrete pipeline that Dagster will actually execute. Without a valid config, Dagster
can't construct a parametrization of the logical pipeline -- so no execution plan is available for
us to preview.

Press CTRL-Space in order to bring up the typeahead assistant.

.. thumbnail:: inputs_figure_two.png

Here you can see all of the sections available in the environment dict. Don't worry, we'll get to
them all later.

Let's enter the config we need in order to execute our pipeline.

.. thumbnail:: inputs_figure_three.png

Note that as you type and edit the config, the config minimap hovering on the right side of the
editor pane changes to provide context -- so you always know where in the nested config schema you
are while making changes.


Type-checking inputs
--------------------

Note that this section requires Python 3.

If you zoom in on the Explore tab in Dagit and click on one of our pipeline solids, you'll see
that its inputs and outputs are annotated with types.

.. thumbnail:: inputs_figure_four.png

By default, every untyped value in Dagster is assigned the catch-all type ``Any``. This means that
any errors in the config won't be surfaced until the pipeline is executed.

For example, when we execute our pipeline with this config, it'll fail at runtime:

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/inputs_env_bad.yaml
   :language: YAML
   :linenos:
   :caption: inputs_env_bad.yaml

When we enter this mistyped config in Dagit and execute our pipeline, you'll see that an error
appears in the structured log viewer pane of the Execute tab:

.. thumbnail:: inputs_figure_five.png

Click on "View Full Message" or on the red dot on the execution step that failed and a detailed
stacktrace will pop up.

.. thumbnail:: inputs_figure_six.png

It would be better if we could catch this error earlier, when we specify the config. So let's
make the inputs typed.

A user can apply types to inputs and outputs using Python 3's type annotation syntax. In this case,
we just want to type the input as the built-in ``str``.

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/inputs_typed.py
   :lines: 6-12
   :emphasize-lines: 2
   :linenos:
   :lineno-start: 6
   :caption: inputs_typed.py

By using typed input instead we can catch this error prior to execution.

.. thumbnail:: inputs_figure_seven.png
