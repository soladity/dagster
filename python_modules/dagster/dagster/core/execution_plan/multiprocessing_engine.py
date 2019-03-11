import multiprocessing
import os

from dagster import check
from dagster.core.errors import DagsterSubprocessExecutionError

from dagster.core.execution_context import (
    MultiprocessExecutorConfig,
    SystemPipelineExecutionContext,
)

from .create import create_execution_plan_core
from .intermediates_manager import FileSystemIntermediateManager
from .objects import (
    ExecutionPlan,
    ExecutionStepEvent,
    StepFailureData,
    StepOutputHandle,
    StepOutputData,
    ExecutionStepEventType,
)
from .simple_engine import start_inprocess_executor


def _execute_in_child_process(queue, environment_dict, run_config, step_key, input_meta_dict):
    from dagster.core.execution import yield_pipeline_execution_context

    check.inst(run_config.executor_config, MultiprocessExecutorConfig)
    check.dict_param(input_meta_dict, 'input_meta_data', key_type=str, value_type=StepOutputHandle)

    pipeline = run_config.executor_config.pipeline_fn()

    with yield_pipeline_execution_context(
        pipeline, environment_dict, run_config.with_tags(pid=str(os.getpid()))
    ) as pipeline_context:

        intermediates_manager = FileSystemIntermediateManager(pipeline_context.files)

        execution_plan = create_execution_plan_core(pipeline_context)

        for step_event in start_inprocess_executor(
            pipeline_context, execution_plan, intermediates_manager, step_keys_to_execute=[step_key]
        ):
            data_to_put = {
                'event_type': step_event.event_type,
                'step_output_data': {
                    'step_output_handle': step_event.step_output_data.step_output_handle,
                    'value_repr': step_event.step_output_data.value_repr,
                }
                if step_event.event_type == ExecutionStepEventType.STEP_OUTPUT
                else None,
                # TODO actually marshal data
                'step_failure_data': None,
                'step_key': step_event.step.key,
                'tags': step_event.tags,
            }

            queue.put(data_to_put)

    queue.put('DONE')
    queue.close()


def execute_step_out_of_process(step_context, step, intermediates_manager):
    queue = multiprocessing.Queue()

    check.invariant(
        not step_context.run_config.loggers,
        'Cannot inject loggers via ExecutionMetadata with the Multiprocess executor',
    )

    process = multiprocessing.Process(
        target=_execute_in_child_process,
        args=(
            queue,
            step_context.environment_dict,
            step_context.run_config,
            step.key,
            {step_input.name: step_input.prev_output_handle for step_input in step.step_inputs},
        ),
    )

    process.start()
    while process.is_alive():
        result = queue.get()
        if result == 'DONE':
            break
        event_type = result['event_type']

        # TODO: should we filter out? Need to think about the relationship between pipelines
        # and subplans
        if step.key != result['step_key']:
            continue

        check.invariant(step.key == result['step_key'])

        if event_type == ExecutionStepEventType.STEP_OUTPUT:
            yield ExecutionStepEvent(
                event_type=ExecutionStepEventType.STEP_OUTPUT,
                step=step,
                step_output_data=StepOutputData(
                    result['step_output_data']['step_output_handle'],
                    result['step_output_data']['value_repr'],
                    intermediates_manager,
                ),
                step_failure_data=None,
                tags=result['tags'],
            )
        elif event_type == ExecutionStepEventType.STEP_FAILURE:
            try:
                # This is pretty hacky for now but it works
                raise DagsterSubprocessExecutionError('TODO')
            except DagsterSubprocessExecutionError as dagster_error:
                yield ExecutionStepEvent(
                    event_type=ExecutionStepEventType.STEP_FAILURE,
                    step=step,
                    step_output_data=None,
                    step_failure_data=StepFailureData(dagster_error=dagster_error),
                    tags=result['tags'],
                )

    # Do something reasonable on total process failure
    process.join()


def _create_input_values(step_input_meta_dict, manager):
    input_values = {}
    for step_input_name, prev_output_handle_meta in step_input_meta_dict.items():
        input_value = manager.get_value(prev_output_handle_meta)
        input_values[step_input_name] = input_value
    return input_values


def _all_inputs_covered(step, intermediates_manager):
    for step_input in step.step_inputs:
        if not intermediates_manager.has_value(step_input.prev_output_handle):
            return False
    return True


def multiprocess_execute_plan(pipeline_context, execution_plan):
    check.inst_param(pipeline_context, 'pipeline_context', SystemPipelineExecutionContext)
    check.inst_param(execution_plan, 'execution_plan', ExecutionPlan)

    step_levels = execution_plan.topological_step_levels()

    intermediates_manager = FileSystemIntermediateManager(pipeline_context.files)

    # It would be good to implement a reference tracking algorithm here so we could
    # garbage collection results that are no longer needed by any steps
    # https://github.com/dagster-io/dagster/issues/811

    for step_level in step_levels:
        for step in step_level:
            step_context = pipeline_context.for_step(step)

            if not _all_inputs_covered(step, intermediates_manager):
                expected_outputs = [ni.prev_output_handle for ni in step.step_inputs]

                step_context.log.debug(
                    (
                        'Not all inputs covered for {step}. Not executing.'
                        'Outputs need for inputs {expected_outputs}'
                    ).format(expected_outputs=expected_outputs, step=step.key)
                )
                continue

            for step_event in check.generator(
                execute_step_out_of_process(step_context, step, intermediates_manager)
            ):
                check.inst(step_event, ExecutionStepEvent)
                yield step_event
