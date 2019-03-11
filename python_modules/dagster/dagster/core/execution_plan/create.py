from dagster import check

from dagster.core.definitions import (
    solids_in_topological_order,
    InputDefinition,
    OutputDefinition,
    Solid,
    SolidOutputHandle,
)

from dagster.core.errors import DagsterInvariantViolationError

from dagster.core.execution_context import SystemPipelineExecutionContext

from .expectations import create_expectations_subplan, decorate_with_expectations

from .input_thunk import create_input_thunk_execution_step

from .materialization_thunk import decorate_with_output_materializations

from .objects import (
    ExecutionPlan,
    ExecutionStep,
    ExecutionValueSubplan,
    StepInput,
    StepOutputHandle,
    StepKind,
)

from .transform import create_transform_step


class StepOutputMap(dict):
    def __getitem__(self, key):
        check.inst_param(key, 'key', SolidOutputHandle)
        return dict.__getitem__(self, key)

    def __setitem__(self, key, val):
        check.inst_param(key, 'key', SolidOutputHandle)
        check.inst_param(val, 'val', StepOutputHandle)
        return dict.__setitem__(self, key, val)


# This is the state that is built up during the execution plan build process.
# steps is just a list of the steps that have been created
# step_output_map maps logical solid outputs (solid_name, output_name) to particular
# step outputs. This covers the case where a solid maps to multiple steps
# and one wants to be able to attach to the logical output of a solid during execution
class PlanBuilder:
    def __init__(self):
        self.steps = []
        self.step_output_map = StepOutputMap()


def create_execution_plan_core(pipeline_context):
    check.inst_param(pipeline_context, 'pipeline_context', SystemPipelineExecutionContext)

    plan_builder = PlanBuilder()

    for solid in solids_in_topological_order(pipeline_context.pipeline_def):

        step_inputs = create_step_inputs(pipeline_context, plan_builder, solid)

        solid_transform_step = create_transform_step(pipeline_context, solid, step_inputs)

        plan_builder.steps.append(solid_transform_step)

        for output_def in solid.definition.output_defs:
            subplan = create_subplan_for_output(
                pipeline_context, solid, solid_transform_step, output_def
            )
            plan_builder.steps.extend(subplan.steps)

            output_handle = solid.output_handle(output_def.name)
            plan_builder.step_output_map[output_handle] = subplan.terminal_step_output_handle

    return create_execution_plan_from_steps(pipeline_context, plan_builder.steps)


def create_execution_plan_from_steps(pipeline_context, steps):
    check.inst_param(pipeline_context, 'pipeline_context', SystemPipelineExecutionContext)
    check.list_param(steps, 'steps', of_type=ExecutionStep)

    step_dict = {step.key: step for step in steps}
    deps = {step.key: set() for step in steps}

    seen_keys = set()

    for step in steps:
        if step.key in seen_keys:
            keys = [s.key for s in steps]
            check.failed(
                'Duplicated key {key}. Full list: {key_list}.'.format(key=step.key, key_list=keys)
            )

        seen_keys.add(step.key)

        for step_input in step.step_inputs:
            deps[step.key].add(step_input.prev_output_handle.step_key)

    return ExecutionPlan(pipeline_context.pipeline_def, step_dict, deps)


def create_subplan_for_input(pipeline_context, solid, prev_step_output_handle, input_def):
    check.inst_param(pipeline_context, 'pipeline_context', SystemPipelineExecutionContext)
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(prev_step_output_handle, 'prev_step_output_handle', StepOutputHandle)
    check.inst_param(input_def, 'input_def', InputDefinition)

    if pipeline_context.environment_config.expectations.evaluate and input_def.expectations:
        return create_expectations_subplan(
            pipeline_context,
            solid,
            input_def,
            prev_step_output_handle,
            kind=StepKind.INPUT_EXPECTATION,
        )
    else:
        return ExecutionValueSubplan.empty(prev_step_output_handle)


def create_subplan_for_output(pipeline_context, solid, solid_transform_step, output_def):
    check.inst_param(pipeline_context, 'pipeline_context', SystemPipelineExecutionContext)
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(solid_transform_step, 'solid_transform_step', ExecutionStep)
    check.inst_param(output_def, 'output_def', OutputDefinition)

    subplan = decorate_with_expectations(pipeline_context, solid, solid_transform_step, output_def)

    return decorate_with_output_materializations(pipeline_context, solid, output_def, subplan)


def get_input_source_step_handle(pipeline_context, plan_builder, solid, input_def):
    check.inst_param(pipeline_context, 'pipeline_context', SystemPipelineExecutionContext)
    check.inst_param(plan_builder, 'plan_builder', PlanBuilder)
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(input_def, 'input_def', InputDefinition)

    input_handle = solid.input_handle(input_def.name)
    solid_config = pipeline_context.environment_config.solids.get(solid.name)
    dependency_structure = pipeline_context.pipeline_def.dependency_structure
    if solid_config and input_def.name in solid_config.inputs:
        step_creation_data = create_input_thunk_execution_step(
            pipeline_context, solid, input_def, solid_config.inputs[input_def.name]
        )
        plan_builder.steps.append(step_creation_data.step)
        return step_creation_data.step_output_handle
    elif dependency_structure.has_dep(input_handle):
        solid_output_handle = dependency_structure.get_dep(input_handle)
        return plan_builder.step_output_map[solid_output_handle]
    else:
        raise DagsterInvariantViolationError(
            (
                'In pipeline {pipeline_name} solid {solid_name}, input {input_name} '
                'must get a value either (a) from a dependency or (b) from the '
                'inputs section of its configuration.'
            ).format(
                pipeline_name=pipeline_context.pipeline.name,
                solid_name=solid.name,
                input_name=input_def.name,
            )
        )


def create_step_inputs(pipeline_context, plan_builder, solid):
    check.inst_param(pipeline_context, 'pipeline_context', SystemPipelineExecutionContext)
    check.inst_param(plan_builder, 'plan_builder', PlanBuilder)
    check.inst_param(solid, 'solid', Solid)

    step_inputs = []

    for input_def in solid.definition.input_defs:
        prev_step_output_handle = get_input_source_step_handle(
            pipeline_context, plan_builder, solid, input_def
        )

        subplan = create_subplan_for_input(
            pipeline_context, solid, prev_step_output_handle, input_def
        )

        plan_builder.steps.extend(subplan.steps)
        step_inputs.append(
            StepInput(input_def.name, input_def.runtime_type, subplan.terminal_step_output_handle)
        )

    return step_inputs
