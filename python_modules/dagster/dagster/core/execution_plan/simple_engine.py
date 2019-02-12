from contextlib import contextmanager
import sys

from future.utils import raise_from

from dagster import check

from dagster.utils.logging import get_formatted_stack_trace

from dagster.utils.timing import time_execution_scope

from dagster.core.errors import (
    DagsterError,
    DagsterInvariantViolationError,
    DagsterRuntimeCoercionError,
    DagsterExecutionStepExecutionError,
    DagsterTypeError,
)

from dagster.core.execution_context import PipelineExecutionContext, StepExecutionContext

from .objects import (
    ExecutionPlan,
    ExecutionStep,
    ExecutionStepEvent,
    ExecutionStepEventType,
    StepOutputHandle,
    StepOutputValue,
    StepSuccessData,
    StepFailureData,
)


def _all_inputs_covered(step, results):
    for step_input in step.step_inputs:
        if step_input.prev_output_handle not in results:
            return False
    return True


def iterate_step_events_for_execution_plan(pipeline_context, execution_plan, throw_on_user_error):
    check.inst_param(pipeline_context, 'pipeline_context', PipelineExecutionContext)
    check.inst_param(execution_plan, 'execution_plan', ExecutionPlan)
    check.bool_param(throw_on_user_error, 'throw_on_user_error')

    step_levels = execution_plan.topological_step_levels()

    # It would be good to implement a reference tracking algorithm here so we could
    # garbage collection results that are no longer needed by any steps
    # https://github.com/dagster-io/dagster/issues/811
    all_results = {}

    for step_level in step_levels:
        for step in step_level:
            step_context = pipeline_context.for_step(step)

            if not _all_inputs_covered(step, all_results):
                result_keys = set(all_results.keys())
                expected_outputs = [ni.prev_output_handle for ni in step.step_inputs]

                step_context.log.debug(
                    (
                        'Not all inputs covered for {step}. Not executing. Keys in result: '
                        '{result_keys}. Outputs need for inputs {expected_outputs}'
                    ).format(
                        expected_outputs=expected_outputs, step=step.key, result_keys=result_keys
                    )
                )
                continue

            input_values = _create_input_values(step, all_results)

            for step_event in check.generator(
                iterate_step_events_for_step(step_context, input_values)
            ):
                check.inst(step_event, ExecutionStepEvent)

                if throw_on_user_error and step_event.is_step_failure:
                    step_event.reraise_user_error()

                yield step_event

                if step_event.event_type == ExecutionStepEventType.STEP_OUTPUT:
                    output_handle = StepOutputHandle(step, step_event.success_data.output_name)
                    all_results[output_handle] = step_event


def _create_input_values(step, prev_level_results):
    input_values = {}
    for step_input in step.step_inputs:
        prev_output_handle = step_input.prev_output_handle
        input_value = prev_level_results[prev_output_handle].success_data.value
        input_values[step_input.name] = input_value
    return input_values


def iterate_step_events_for_step(step_context, inputs):
    check.inst_param(step_context, 'step_context', StepExecutionContext)
    check.dict_param(inputs, 'inputs', key_type=str)

    try:
        for step_event in check.generator(_execute_steps_core_loop(step_context, inputs)):
            step_context.log.info(
                'Step {step} emitted {value} for output {output}'.format(
                    step=step_context.step.key,
                    value=repr(step_event.success_data.value),
                    output=step_event.success_data.output_name,
                )
            )
            yield step_event
    except DagsterError as dagster_error:
        step_context.log.error(str(dagster_error))
        yield ExecutionStepEvent.step_failure_event(
            step=step_context.step, failure_data=StepFailureData(dagster_error=dagster_error)
        )
        return


def _error_check_step_output_values(step, step_output_values):
    check.inst_param(step, 'step', ExecutionStep)
    check.generator_param(step_output_values, 'step_output_values')

    seen_outputs = set()
    for step_output_value in step_output_values:
        if not step.has_step_output(step_output_value.output_name):
            output_names = list(
                [output_def.name for output_def in step.solid.definition.output_defs]
            )
            raise DagsterInvariantViolationError(
                'Core transform for {step.solid.name} returned an output '
                '{step_output_value.output_name} that does not exist. The available '
                'outputs are {output_names}'.format(
                    step=step, step_output_value=step_output_value, output_names=output_names
                )
            )

        if step_output_value.output_name in seen_outputs:
            raise DagsterInvariantViolationError(
                'Core transform for {step.solid.name} returned an output '
                '{step_output_value.output_name} multiple times'.format(
                    step=step, step_output_value=step_output_value
                )
            )

        yield step_output_value
        seen_outputs.add(step_output_value.output_name)


def _execute_steps_core_loop(step_context, inputs):
    check.inst_param(step_context, 'step_context', StepExecutionContext)
    check.dict_param(inputs, 'inputs', key_type=str)

    evaluated_inputs = {}
    # do runtime type checks of inputs versus step inputs
    for input_name, input_value in inputs.items():
        evaluated_inputs[input_name] = _get_evaluated_input(
            step_context.step, input_name, input_value
        )

    step_output_value_iterator = check.generator(
        _iterate_step_output_values_within_boundary(step_context, evaluated_inputs)
    )

    for step_output_value in check.generator(
        _error_check_step_output_values(step_context.step, step_output_value_iterator)
    ):

        yield _create_step_event(step_context.step, step_output_value)


def _create_step_event(step, step_output_value):
    check.inst_param(step, 'step', ExecutionStep)
    check.inst_param(step_output_value, 'step_output_value', StepOutputValue)

    step_output = step.step_output_named(step_output_value.output_name)

    try:
        return ExecutionStepEvent.step_output_event(
            step=step,
            success_data=StepSuccessData(
                output_name=step_output_value.output_name,
                value=step_output.runtime_type.coerce_runtime_value(step_output_value.value),
            ),
        )
    except DagsterRuntimeCoercionError as e:
        raise DagsterInvariantViolationError(
            (
                'Solid {step.solid.name} output name {output_name} output '
                '{step_output_value.value} type failure: {error_msg}.'
            ).format(
                step=step,
                step_output_value=step_output_value,
                error_msg=','.join(e.args),
                output_name=step_output_value.output_name,
            )
        )


def _get_evaluated_input(step, input_name, input_value):
    check.inst_param(step, 'step', ExecutionStep)
    check.str_param(input_name, 'input_name')

    step_input = step.step_input_named(input_name)
    try:
        return step_input.runtime_type.coerce_runtime_value(input_value)
    except DagsterRuntimeCoercionError as evaluate_error:
        raise_from(
            DagsterTypeError(
                (
                    'Solid {step.solid.name} input {input_name} received value {input_value} '
                    'which does not pass the typecheck for Dagster type '
                    '{step_input.runtime_type.name}. Step {step.key}'
                ).format(
                    step=step, input_name=input_name, input_value=input_value, step_input=step_input
                )
            ),
            evaluate_error,
        )


def _iterate_step_output_values_within_boundary(step_context, evaluated_inputs):
    check.inst_param(step_context, 'step_context', StepExecutionContext)
    check.dict_param(evaluated_inputs, 'evaluated_inputs', key_type=str)

    error_str = 'Error occured during step {key}'.format(key=step_context.step.key)
    with _execution_step_error_boundary(step_context, error_str):
        gen = check.opt_generator(step_context.step.compute_fn(step_context, evaluated_inputs))

        if gen is not None:
            for step_output_value in gen:
                yield step_output_value


@contextmanager
def _execution_step_error_boundary(step_context, msg, **kwargs):
    '''
    Wraps the execution of user-space code in an error boundary. This places a uniform
    policy around an user code invoked by the framework. This ensures that all user
    errors are wrapped in the SolidUserCodeExecutionError, and that the original stack
    trace of the user error is preserved, so that it can be reported without confusing
    framework code in the stack trace, if a tool author wishes to do so. This has
    been especially help in a notebooking context.
    '''
    check.inst_param(step_context, 'step_context', StepExecutionContext)
    check.str_param(msg, 'msg')

    step = step_context.step
    step_context.events.execution_plan_step_start(step.key)
    try:
        with time_execution_scope() as timer_result:
            yield

        step_context.events.execution_plan_step_success(step.key, timer_result.millis)
    except Exception as e:  # pylint: disable=W0703
        step_context.events.execution_plan_step_failure(step.key, sys.exc_info())

        stack_trace = get_formatted_stack_trace(e)
        step_context.log.error(str(e), stack_trace=stack_trace)

        if isinstance(e, DagsterError):
            raise e
        else:
            raise_from(
                DagsterExecutionStepExecutionError(
                    msg.format(**kwargs), user_exception=e, original_exc_info=sys.exc_info()
                ),
                e,
            )
