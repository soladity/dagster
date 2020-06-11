from dagster_graphql.client.mutations import (
    execute_execute_plan_mutation,
    execute_execute_plan_mutation_raw,
)

from dagster.cli.workspace.cli_target import ModuleTarget, workspace_from_load_target
from dagster.core.definitions.reconstructable import ReconstructablePipeline
from dagster.core.instance import DagsterInstance

EXPECTED_EVENTS = {
    ('STEP_INPUT', 'sleeper.compute'),
    ('STEP_INPUT', 'sleeper_2.compute'),
    ('STEP_INPUT', 'sleeper_3.compute'),
    ('STEP_INPUT', 'sleeper_4.compute'),
    ('STEP_INPUT', 'total.compute'),
    ('STEP_OUTPUT', 'giver.compute'),
    ('STEP_OUTPUT', 'sleeper.compute'),
    ('STEP_OUTPUT', 'sleeper_2.compute'),
    ('STEP_OUTPUT', 'sleeper_3.compute'),
    ('STEP_OUTPUT', 'sleeper_4.compute'),
    ('STEP_OUTPUT', 'total.compute'),
    ('STEP_START', 'giver.compute'),
    ('STEP_START', 'sleeper.compute'),
    ('STEP_START', 'sleeper_2.compute'),
    ('STEP_START', 'sleeper_3.compute'),
    ('STEP_START', 'sleeper_4.compute'),
    ('STEP_START', 'total.compute'),
    ('STEP_SUCCESS', 'giver.compute'),
    ('STEP_SUCCESS', 'sleeper.compute'),
    ('STEP_SUCCESS', 'sleeper_2.compute'),
    ('STEP_SUCCESS', 'sleeper_3.compute'),
    ('STEP_SUCCESS', 'sleeper_4.compute'),
    ('STEP_SUCCESS', 'total.compute'),
}


def test_execute_execute_plan_mutation():
    pipeline_name = 'sleepy_pipeline'
    pipeline = ReconstructablePipeline.for_module('dagster_examples.toys.sleepy', pipeline_name)
    workspace = workspace_from_load_target(
        ModuleTarget('dagster_examples.toys.sleepy', pipeline_name)
    )
    instance = DagsterInstance.local_temp()
    pipeline_run = instance.create_run_for_pipeline(pipeline_def=pipeline.get_definition())
    variables = {
        'executionParams': {
            'runConfigData': {},
            'mode': 'default',
            'selector': {
                'repositoryLocationName': pipeline_name,
                'repositoryName': '<<unnamed>>',
                'pipelineName': pipeline_name,
            },
            'executionMetadata': {'runId': pipeline_run.run_id},
        }
    }
    result = execute_execute_plan_mutation(workspace, variables, instance_ref=instance.get_ref())
    seen_events = set()
    for event in result:
        seen_events.add((event.event_type_value, event.step_key))

    assert seen_events == EXPECTED_EVENTS


def test_execute_execute_plan_mutation_raw():
    pipeline_name = 'sleepy_pipeline'
    workspace = workspace_from_load_target(
        ModuleTarget('dagster_examples.toys.sleepy', pipeline_name)
    )
    pipeline = ReconstructablePipeline.for_module('dagster_examples.toys.sleepy', pipeline_name)

    instance = DagsterInstance.local_temp()
    pipeline_run = instance.create_run_for_pipeline(pipeline_def=pipeline.get_definition())
    variables = {
        'executionParams': {
            'runConfigData': {},
            'mode': 'default',
            'selector': {
                'repositoryLocationName': pipeline_name,
                'repositoryName': '<<unnamed>>',
                'pipelineName': pipeline_name,
            },
            'executionMetadata': {'runId': pipeline_run.run_id},
        }
    }
    result = execute_execute_plan_mutation_raw(
        workspace, variables, instance_ref=instance.get_ref()
    )
    seen_events = set()
    for event in result:
        seen_events.add((event.dagster_event.event_type_value, event.step_key))

    assert seen_events == EXPECTED_EVENTS
