from typing import Any, Callable, Dict, Iterator, List, Set, Union

from dagster import check
from dagster.core.definitions import (
    AssetMaterialization,
    DynamicOutput,
    ExpectationResult,
    Materialization,
    Output,
    Solid,
    SolidHandle,
)
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.execution.context.compute import SolidExecutionContext
from dagster.core.execution.context.system import SystemComputeExecutionContext
from dagster.core.system_config.objects import EnvironmentConfig

from .outputs import StepOutput

SolidOutputUnion = Union[
    DynamicOutput, Output, AssetMaterialization, Materialization, ExpectationResult
]


def create_step_outputs(
    solid: Solid, handle: SolidHandle, environment_config: EnvironmentConfig
) -> List[StepOutput]:
    check.inst_param(solid, "solid", Solid)
    check.inst_param(handle, "handle", SolidHandle)

    # the environment config has the solid output name configured
    config_output_names: Set[str] = set()
    current_handle = handle
    while current_handle:
        solid_config = environment_config.solids.get(current_handle.to_string())
        current_handle = current_handle.parent
        config_output_names = config_output_names.union(solid_config.outputs.output_names)

    return [
        StepOutput(
            solid_handle=handle,
            name=output_def.name,
            dagster_type_key=output_def.dagster_type.key,
            is_required=output_def.is_required,
            should_materialize=output_def.name in config_output_names,
        )
        for name, output_def in solid.definition.output_dict.items()
    ]


def _yield_compute_results(
    compute_context: SystemComputeExecutionContext, inputs: Dict[str, Any], compute_fn: Callable
) -> Iterator[SolidOutputUnion]:
    check.inst_param(compute_context, "compute_context", SystemComputeExecutionContext)
    step = compute_context.step
    user_event_sequence = compute_fn(SolidExecutionContext(compute_context), inputs)

    if isinstance(user_event_sequence, Output):
        raise DagsterInvariantViolationError(
            (
                "Compute function for solid {solid_name} returned a Output rather than "
                "yielding it. The compute_fn of the core SolidDefinition must yield "
                "its results"
            ).format(solid_name=str(step.solid_handle))
        )

    if user_event_sequence is None:
        return

    for event in user_event_sequence:
        if isinstance(
            event,
            (DynamicOutput, Output, AssetMaterialization, Materialization, ExpectationResult),
        ):
            yield event
        else:
            raise DagsterInvariantViolationError(
                (
                    "Compute function for solid {solid_name} yielded a value of type {type_} "
                    "rather than an instance of Output, AssetMaterialization, or ExpectationResult."
                    " Values yielded by solids must be wrapped in one of these types. If your "
                    "solid has a single output and yields no other events, you may want to use "
                    "`return` instead of `yield` in the body of your solid compute function. If "
                    "you are already using `return`, and you expected to return a value of type "
                    "{type_}, you may be inadvertently returning a generator rather than the value "
                    "you expected."
                ).format(solid_name=str(step.solid_handle), type_=type(event))
            )


def execute_core_compute(
    compute_context: SystemComputeExecutionContext, inputs: Dict[str, Any], compute_fn
) -> Iterator[SolidOutputUnion]:
    """
    Execute the user-specified compute for the solid. Wrap in an error boundary and do
    all relevant logging and metrics tracking
    """
    check.inst_param(compute_context, "compute_context", SystemComputeExecutionContext)
    check.dict_param(inputs, "inputs", key_type=str)

    step = compute_context.step

    all_results = []
    for step_output in _yield_compute_results(compute_context, inputs, compute_fn):
        yield step_output
        if isinstance(step_output, (DynamicOutput, Output)):
            all_results.append(step_output)

    emitted_result_names = {r.output_name for r in all_results}
    solid_output_names = {output.name for output in step.step_outputs}
    omitted_outputs = solid_output_names.difference(emitted_result_names)
    if omitted_outputs:
        compute_context.log.info(
            "Solid {solid} did not fire outputs {outputs}".format(
                solid=str(step.solid_handle), outputs=repr(omitted_outputs)
            )
        )
