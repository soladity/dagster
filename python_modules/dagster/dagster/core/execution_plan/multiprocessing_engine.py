import os

from dagster import check

from dagster.core.execution_context import (
    MultiprocessExecutorConfig,
    SystemPipelineExecutionContext,
)


from .create import create_execution_plan_core
from .intermediates_manager import FileSystemIntermediateManager
from .objects import ExecutionPlan, ExecutionStepEvent
from .simple_engine import start_inprocess_executor

from .child_process_executor import ChildProcessCommand, execute_child_process_command


class InProcessExecutorChildProcessCommand(ChildProcessCommand):
    def __init__(self, environment_dict, run_config, step_key):
        self.environment_dict = environment_dict
        self.run_config = run_config
        self.step_key = step_key

    def execute(self):
        from dagster.core.execution import yield_pipeline_execution_context

        check.inst(self.run_config.executor_config, MultiprocessExecutorConfig)
        pipeline = self.run_config.executor_config.pipeline_fn()

        with yield_pipeline_execution_context(
            pipeline, self.environment_dict, self.run_config.with_tags(pid=str(os.getpid()))
        ) as pipeline_context:

            intermediates_manager = FileSystemIntermediateManager(pipeline_context.files)

            execution_plan = create_execution_plan_core(pipeline_context)

            for step_event in start_inprocess_executor(
                pipeline_context,
                execution_plan,
                intermediates_manager,
                step_keys_to_execute=[self.step_key],
            ):
                yield step_event


def execute_step_out_of_process(step_context, step):
    check.invariant(
        not step_context.run_config.loggers,
        'Cannot inject loggers via RunConfig with the Multiprocess executor',
    )

    command = InProcessExecutorChildProcessCommand(
        step_context.environment_dict, step_context.run_config, step.key
    )

    for step_event in execute_child_process_command(command):
        yield step_event


def _create_input_values(step_input_meta_dict, manager):
    input_values = {}
    for step_input_name, prev_output_handle_meta in step_input_meta_dict.items():
        input_value = manager.get_value(prev_output_handle_meta)
        input_values[step_input_name] = input_value
    return input_values


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

            if not intermediates_manager.all_inputs_covered(step):
                expected_outputs = [ni.prev_output_handle for ni in step.step_inputs]

                step_context.log.debug(
                    (
                        'Not all inputs covered for {step}. Not executing.'
                        'Outputs need for inputs {expected_outputs}'
                    ).format(expected_outputs=expected_outputs, step=step.key)
                )
                continue

            for step_event in check.generator(execute_step_out_of_process(step_context, step)):
                check.inst(step_event, ExecutionStepEvent)
                yield step_event
