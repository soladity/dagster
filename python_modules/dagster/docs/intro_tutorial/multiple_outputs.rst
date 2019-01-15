Multiple Outputs
----------------

So far all of the examples have been solids that have a single output. However
solids support an arbitrary number of outputs. This allows for downstream
solids to only tie their dependency to a single output. Additionally -- by
allowing for multiple outputs to conditionally fire -- this also ends up
supporting dynamic branching and conditional execution of pipelines.


``MultipleResults`` Class
^^^^^^^^^^^^^^^^^^^^^^^^^

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/multiple_outputs.py
   :linenos:
   :caption: multiple_outputs.py
   :lines: 26-33

Notice how ``return_dict_results`` has two outputs. For the first time
we have provided the name argument to an :py:class:`OutputDefinition`. (It
defaults to ``'result'``, as it does in a :py:class:`DependencyDefinition`)
These names must be unique and results returns by a solid transform function
must be named one of these inputs. (In all previous examples the value returned
by the transform had been implicitly wrapped in a :py:class:`Result` object
with the name ``'result'``.)

So from ``return_dict_results`` we used :py:class:`MultipleResults` to return
all outputs from this transform.

Next let's examine the :py:class:`PipelineDefinition`:

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/multiple_outputs.py
   :linenos:
   :caption: multiple_outputs.py
   :lines: 64-73


Just like this tutorial is the first example of an :py:class:`OutputDefinition` with
a name, this is also the first time that a :py:class:`DependencyDefinition` has
specified name, because dependencies point to a particular **output** of a solid,
rather than to the solid itself. In previous examples the name of output has
defaulted to ``'result'``.

With this we can run the pipeline:

.. code-block:: sh

    $ dagster pipeline execute -f multiple_outputs.py \
    -n define_multiple_outputs_step_one_pipeline

    ... log spew
    2019-01-15 15:44:36 - dagster - INFO - orig_message="Solid return_dict_results emitted output \"out_one\" value 23" log_message_id="f7d90092-523e-41c3-ac43-f9124ea896ad" run_id="50733509-1dfb-4e1b-9f12-fc6be42f2376" pipeline="multiple_outputs_step_one_pipeline" solid="return_dict_results" solid_definition="return_dict_results"
    2019-01-15 15:44:36 - dagster - INFO - orig_message="Solid return_dict_results emitted output \"out_two\" value 45" log_message_id="343ac9fb-4afd-4b96-85a6-0e15a1b22a6e" run_id="50733509-1dfb-4e1b-9f12-fc6be42f2376" pipeline="multiple_outputs_step_one_pipeline" solid="return_dict_results" solid_definition="return_dict_results"
    ... more log spew

Iterator of ``Result``
^^^^^^^^^^^^^^^^^^^^^^

The :py:class:`MultipleResults` class is not the only way to return multiple
results from a solid transform function. You can also yield multiple instances
of the ``Result`` object. (Note: this is actually the core specification
of the transform function: all other forms are implemented in terms of
the iterator form.)

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/multiple_outputs.py
   :linenos:
   :caption: multiple_outputs.py
   :lines: 15-24,75-84

... and you'll see the same log spew around outputs in this version:

.. code-block:: console

    $ dagster pipeline execute -f multiple_outputs.py \
    -n define_multiple_outputs_step_two_pipeline

    2018-11-08 10:54:15 - dagster - INFO - orig_message="Solid yield_outputs emitted output \"out_one\" value 23" log_message_id="5e1cc181-b74d-47f8-8d32-bc262d555b73" run_id="4bee891c-e04f-4221-be77-17576abb9da2" pipeline="part_eleven_step_two" solid="yield_outputs" solid_definition="yield_outputs"
    2018-11-08 10:54:15 - dagster - INFO - orig_message="Solid yield_outputs emitted output \"out_two\" value 45" log_message_id="8da32946-596d-4783-b7c5-4edbb3a1dbc2" run_id="4bee891c-e04f-4221-be77-17576abb9da2" pipeline="part_eleven_step_two" solid="yield_outputs" solid_definition="yield_outputs"

Conditional Outputs
^^^^^^^^^^^^^^^^^^^

Multiple outputs are the mechanism by which we implement branching or conditional execution.

Let's modify the first solid above to conditionally emit one output or the other based on config
and then execute that pipeline.

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/multiple_outputs.py
    :linenos:
    :caption: multiple_outputs.py
    :lines: 36-51,86-94

You must create a config file

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/conditional_outputs.yml
    :linenos:
    :caption: conditional_outputs.yml

And then run it.

.. code-block:: console

    $ dagster pipeline execute -f multiple_outputs.py \
    -n define_multiple_outputs_step_three_pipeline \
    -e conditional_outputs.yml
    ... log spew
    2018-09-16 18:58:32 - dagster - INFO - orig_message="Solid conditional emitted output \"out_two\" value 45" log_message_id="f6fd78c5-c25e-40ea-95ef-6b80d12155de" pipeline="part_eleven_step_three" solid="conditional"
    2018-09-16 18:58:32 - dagster - INFO - orig_message="Solid conditional did not fire outputs {'out_one'}" log_message_id="d548ea66-cb10-42b8-b150-aed8162cc25c" pipeline="part_eleven_step_three" solid="conditional"    
    ... log spew

Note that we are configuring this solid to *only* emit out_two which will end up
only triggering log_num_squared. log_num will never be executed.
