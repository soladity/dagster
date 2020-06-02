import pytest

from dagster import (
    DependencyDefinition,
    InputDefinition,
    Int,
    OutputDefinition,
    PipelineDefinition,
    execute_pipeline,
    lambda_solid,
)
from dagster.core.definitions.executable import InMemoryExecutablePipeline
from dagster.core.errors import (
    DagsterExecutionStepNotFoundError,
    DagsterInvariantViolationError,
    DagsterRunNotFoundError,
)
from dagster.core.events import get_step_output_event
from dagster.core.execution.api import create_execution_plan, execute_plan, execute_run
from dagster.core.execution.plan.objects import StepOutputHandle
from dagster.core.instance import DagsterInstance
from dagster.core.storage.intermediate_store import build_fs_intermediate_store
from dagster.core.storage.intermediates_manager import IntermediateStoreIntermediatesManager
from dagster.utils import merge_dicts


def env_with_fs(environment_dict):
    return merge_dicts(environment_dict, {'storage': {'filesystem': {}}})


def define_addy_pipeline():
    @lambda_solid(input_defs=[InputDefinition('num', Int)], output_def=OutputDefinition(Int))
    def add_one(num):
        return num + 1

    @lambda_solid(input_defs=[InputDefinition('num', Int)], output_def=OutputDefinition(Int))
    def add_two(num):
        return num + 2

    @lambda_solid(input_defs=[InputDefinition('num', Int)], output_def=OutputDefinition(Int))
    def add_three(num):
        return num + 3

    pipeline_def = PipelineDefinition(
        name='execution_plan_reexecution',
        solid_defs=[add_one, add_two, add_three],
        dependencies={
            'add_two': {'num': DependencyDefinition('add_one')},
            'add_three': {'num': DependencyDefinition('add_two')},
        },
    )
    return pipeline_def


def test_execution_plan_reexecution():
    pipeline_def = define_addy_pipeline()
    instance = DagsterInstance.ephemeral()
    environment_dict = env_with_fs({'solids': {'add_one': {'inputs': {'num': {'value': 3}}}}})
    result = execute_pipeline(pipeline_def, environment_dict=environment_dict, instance=instance,)

    assert result.success

    intermediates_manager = IntermediateStoreIntermediatesManager(
        build_fs_intermediate_store(instance.intermediates_directory, result.run_id)
    )
    assert (
        intermediates_manager.get_intermediate(None, Int, StepOutputHandle('add_one.compute')).obj
        == 4
    )
    assert (
        intermediates_manager.get_intermediate(None, Int, StepOutputHandle('add_two.compute')).obj
        == 6
    )

    ## re-execute add_two

    execution_plan = create_execution_plan(pipeline_def, environment_dict=environment_dict)

    pipeline_run = instance.create_run_for_pipeline(
        pipeline_def=pipeline_def,
        execution_plan=execution_plan,
        environment_dict=environment_dict,
        parent_run_id=result.run_id,
        root_run_id=result.run_id,
    )

    step_events = execute_plan(
        execution_plan.build_subset_plan(['add_two.compute']),
        environment_dict=environment_dict,
        pipeline_run=pipeline_run,
        instance=instance,
    )

    intermediates_manager = IntermediateStoreIntermediatesManager(
        build_fs_intermediate_store(instance.intermediates_directory, result.run_id)
    )
    assert (
        intermediates_manager.get_intermediate(None, Int, StepOutputHandle('add_one.compute')).obj
        == 4
    )
    assert (
        intermediates_manager.get_intermediate(None, Int, StepOutputHandle('add_two.compute')).obj
        == 6
    )

    assert not get_step_output_event(step_events, 'add_one.compute')
    assert get_step_output_event(step_events, 'add_two.compute')


def test_execution_plan_wrong_run_id():
    pipeline_def = define_addy_pipeline()

    unrun_id = 'not_a_run'
    environment_dict = env_with_fs({'solids': {'add_one': {'inputs': {'num': {'value': 3}}}}})

    instance = DagsterInstance.ephemeral()

    execution_plan = create_execution_plan(pipeline_def, environment_dict=environment_dict)

    pipeline_run = instance.create_run_for_pipeline(
        pipeline_def=pipeline_def,
        execution_plan=execution_plan,
        environment_dict=environment_dict,
        parent_run_id=unrun_id,
        root_run_id=unrun_id,
    )

    with pytest.raises(DagsterRunNotFoundError) as exc_info:
        execute_plan(
            execution_plan,
            environment_dict=environment_dict,
            pipeline_run=pipeline_run,
            instance=instance,
        )

    assert str(exc_info.value) == 'Run id {} set as parent run id was not found in instance'.format(
        unrun_id
    )

    assert exc_info.value.invalid_run_id == unrun_id


def test_execution_plan_reexecution_with_in_memory():
    pipeline_def = define_addy_pipeline()
    instance = DagsterInstance.ephemeral()
    environment_dict = {'solids': {'add_one': {'inputs': {'num': {'value': 3}}}}}
    result = execute_pipeline(pipeline_def, environment_dict=environment_dict, instance=instance)

    assert result.success

    ## re-execute add_two

    execution_plan = create_execution_plan(pipeline_def, environment_dict=environment_dict)

    pipeline_run = instance.create_run_for_pipeline(
        pipeline_def=pipeline_def,
        execution_plan=execution_plan,
        environment_dict=environment_dict,
        parent_run_id=result.run_id,
        root_run_id=result.run_id,
    )

    with pytest.raises(DagsterInvariantViolationError):
        execute_plan(
            execution_plan.build_subset_plan(['add_two.compute']),
            environment_dict=environment_dict,
            pipeline_run=pipeline_run,
            instance=instance,
        )


def test_pipeline_step_key_subset_execution():
    pipeline_def = define_addy_pipeline()
    instance = DagsterInstance.ephemeral()
    environment_dict = env_with_fs({'solids': {'add_one': {'inputs': {'num': {'value': 3}}}}})
    result = execute_pipeline(pipeline_def, environment_dict=environment_dict, instance=instance)

    assert result.success

    intermediates_manager = IntermediateStoreIntermediatesManager(
        build_fs_intermediate_store(instance.intermediates_directory, result.run_id)
    )
    assert (
        intermediates_manager.get_intermediate(None, Int, StepOutputHandle('add_one.compute')).obj
        == 4
    )
    assert (
        intermediates_manager.get_intermediate(None, Int, StepOutputHandle('add_two.compute')).obj
        == 6
    )

    ## re-execute add_two

    pipeline_run = instance.create_run_for_pipeline(
        pipeline_def,
        environment_dict=environment_dict,
        step_keys_to_execute=['add_two.compute'],
        parent_run_id=result.run_id,
        root_run_id=result.run_id,
    )

    pipeline_reexecution_result = execute_run(
        InMemoryExecutablePipeline(pipeline_def), pipeline_run, instance
    )

    assert pipeline_reexecution_result.success

    step_events = pipeline_reexecution_result.step_event_list
    assert step_events

    intermediates_manager = IntermediateStoreIntermediatesManager(
        build_fs_intermediate_store(instance.intermediates_directory, result.run_id)
    )
    assert (
        intermediates_manager.get_intermediate(None, Int, StepOutputHandle('add_one.compute')).obj
        == 4
    )
    assert (
        intermediates_manager.get_intermediate(None, Int, StepOutputHandle('add_two.compute')).obj
        == 6
    )

    assert not get_step_output_event(step_events, 'add_one.compute')
    assert get_step_output_event(step_events, 'add_two.compute')

    with pytest.raises(
        DagsterExecutionStepNotFoundError, match='Execution plan does not contain step'
    ):
        pipeline_run = instance.create_run_for_pipeline(
            pipeline_def,
            environment_dict=environment_dict,
            step_keys_to_execute=['nope.compute'],
            parent_run_id=result.run_id,
            root_run_id=result.run_id,
        )
