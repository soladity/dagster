import uuid
from contextlib import contextmanager

import pytest
from dagster_graphql.implementation.utils import UserFacingGraphQLError
from dagster_graphql.test.utils import execute_dagster_graphql, infer_pipeline_selector
from graphql import parse

from dagster import check, seven
from dagster.core.instance import DagsterInstance
from dagster.core.storage.pipeline_run import PipelineRunsFilter
from dagster.utils import file_relative_path, merge_dicts
from dagster.utils.test import get_temp_file_name

from .execution_queries import LAUNCH_PIPELINE_EXECUTION_QUERY, SUBSCRIPTION_QUERY
from .graphql_context_test_suite import ExecutingGraphQLContextTestMatrix
from .setup import csv_hello_world_solids_config
from .utils import sync_execute_get_run_log_data


class TestExecutePipeline(ExecutingGraphQLContextTestMatrix):
    def test_start_pipeline_execution(self, graphql_context):
        selector = infer_pipeline_selector(graphql_context, 'csv_hello_world')
        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PIPELINE_EXECUTION_QUERY,
            variables={
                'executionParams': {
                    'selector': selector,
                    'runConfigData': csv_hello_world_solids_config(),
                    'mode': 'default',
                }
            },
        )

        assert not result.errors
        assert result.data

        # just test existence
        assert result.data['launchPipelineExecution']['__typename'] == 'LaunchPipelineRunSuccess'
        assert uuid.UUID(result.data['launchPipelineExecution']['run']['runId'])
        assert (
            result.data['launchPipelineExecution']['run']['pipeline']['name'] == 'csv_hello_world'
        )

    def test_basic_start_pipeline_execution_with_preset(self, graphql_context):
        selector = infer_pipeline_selector(graphql_context, 'csv_hello_world')
        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PIPELINE_EXECUTION_QUERY,
            variables={'executionParams': {'selector': selector, 'preset': 'test_inline',}},
        )

        assert not result.errors
        assert result.data

        # just test existence
        assert result.data['launchPipelineExecution']['__typename'] == 'LaunchPipelineRunSuccess'
        assert uuid.UUID(result.data['launchPipelineExecution']['run']['runId'])
        assert (
            result.data['launchPipelineExecution']['run']['pipeline']['name'] == 'csv_hello_world'
        )

    def test_basic_start_pipeline_execution_with_pipeline_def_tags(self, graphql_context):
        selector = infer_pipeline_selector(graphql_context, 'hello_world_with_tags')
        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PIPELINE_EXECUTION_QUERY,
            variables={'executionParams': {'selector': selector, 'mode': 'default',},},
        )

        assert not result.errors
        assert result.data['launchPipelineExecution']['run']['tags'] == [
            {'key': 'tag_key', 'value': 'tag_value'}
        ]

        # just test existence
        assert result.data['launchPipelineExecution']['__typename'] == 'LaunchPipelineRunSuccess'
        assert uuid.UUID(result.data['launchPipelineExecution']['run']['runId'])
        assert (
            result.data['launchPipelineExecution']['run']['pipeline']['name']
            == 'hello_world_with_tags'
        )

    def test_basic_start_pipeline_execution_with_non_existent_preset(self, graphql_context):
        selector = infer_pipeline_selector(graphql_context, 'csv_hello_world')
        with pytest.raises(UserFacingGraphQLError) as exc_info:
            execute_dagster_graphql(
                graphql_context,
                LAUNCH_PIPELINE_EXECUTION_QUERY,
                variables={
                    'executionParams': {'selector': selector, 'preset': 'undefined_preset',}
                },
            )

        assert (
            exc_info.value.dauphin_error.message
            == 'Preset undefined_preset not found in pipeline csv_hello_world.'
        )

    def test_basic_start_pipeline_execution_with_preset_failure(self, graphql_context):
        subset_selector = infer_pipeline_selector(
            graphql_context, 'csv_hello_world', ['sum_sq_solid']
        )
        # These should check for proper graphql errors rather than check errors
        # https://github.com/dagster-io/dagster/issues/2507
        with pytest.raises(check.CheckError):
            execute_dagster_graphql(
                graphql_context,
                LAUNCH_PIPELINE_EXECUTION_QUERY,
                variables={
                    'executionParams': {'selector': subset_selector, 'preset': 'test_inline',}
                },
            )

        selector = infer_pipeline_selector(graphql_context, 'csv_hello_world')
        with pytest.raises(check.CheckError):
            execute_dagster_graphql(
                graphql_context,
                LAUNCH_PIPELINE_EXECUTION_QUERY,
                variables={
                    'executionParams': {
                        'selector': selector,
                        'preset': 'test_inline',
                        'runConfigData': csv_hello_world_solids_config(),
                    }
                },
            )

        with pytest.raises(check.CheckError):
            execute_dagster_graphql(
                graphql_context,
                LAUNCH_PIPELINE_EXECUTION_QUERY,
                variables={
                    'executionParams': {
                        'selector': selector,
                        'preset': 'test_inline',
                        'mode': 'default',
                    }
                },
            )

    def test_basic_start_pipeline_execution_config_failure(self, graphql_context):
        selector = infer_pipeline_selector(graphql_context, 'csv_hello_world')
        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PIPELINE_EXECUTION_QUERY,
            variables={
                'executionParams': {
                    'selector': selector,
                    'runConfigData': {'solids': {'sum_solid': {'inputs': {'num': 384938439}}}},
                    'mode': 'default',
                }
            },
        )

        assert not result.errors
        assert result.data
        assert (
            result.data['launchPipelineExecution']['__typename']
            == 'PipelineConfigValidationInvalid'
        )

    def test_basis_start_pipeline_not_found_error(self, graphql_context):
        selector = infer_pipeline_selector(graphql_context, 'sjkdfkdjkf')
        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PIPELINE_EXECUTION_QUERY,
            variables={
                'executionParams': {
                    'selector': selector,
                    'runConfigData': {'solids': {'sum_solid': {'inputs': {'num': 'test.csv'}}}},
                    'mode': 'default',
                }
            },
        )

        assert not result.errors
        assert result.data

        # just test existence
        assert result.data['launchPipelineExecution']['__typename'] == 'PipelineNotFoundError'
        assert result.data['launchPipelineExecution']['pipelineName'] == 'sjkdfkdjkf'

    def test_basic_start_pipeline_execution_and_subscribe(self, graphql_context):
        selector = infer_pipeline_selector(graphql_context, 'csv_hello_world')
        run_logs = sync_execute_get_run_log_data(
            context=graphql_context,
            variables={
                'executionParams': {
                    'selector': selector,
                    'runConfigData': {
                        'solids': {
                            'sum_solid': {
                                'inputs': {'num': file_relative_path(__file__, '../data/num.csv')}
                            }
                        }
                    },
                    'mode': 'default',
                }
            },
        )

        assert run_logs['__typename'] == 'PipelineRunLogsSubscriptionSuccess'
        non_engine_event_types = [
            message['__typename']
            for message in run_logs['messages']
            if message['__typename'] != 'EngineEvent'
        ]
        expected_non_engine_event_types = [
            'PipelineStartEvent',
            'ExecutionStepStartEvent',
            'ExecutionStepInputEvent',
            'ExecutionStepOutputEvent',
            'ExecutionStepSuccessEvent',
            'ExecutionStepStartEvent',
            'ExecutionStepInputEvent',
            'ExecutionStepOutputEvent',
            'ExecutionStepSuccessEvent',
            'PipelineSuccessEvent',
        ]
        assert non_engine_event_types == expected_non_engine_event_types

    def test_subscription_query_error(self, graphql_context):
        selector = infer_pipeline_selector(graphql_context, 'naughty_programmer_pipeline')
        run_logs = sync_execute_get_run_log_data(
            context=graphql_context,
            variables={'executionParams': {'selector': selector, 'mode': 'default',}},
        )

        assert run_logs['__typename'] == 'PipelineRunLogsSubscriptionSuccess'

        step_run_log_entry = _get_step_run_log_entry(
            run_logs, 'throw_a_thing.compute', 'ExecutionStepFailureEvent'
        )

        assert step_run_log_entry
        # Confirm that it is the user stack

        assert step_run_log_entry['message'] == 'Execution of step "throw_a_thing.compute" failed.'
        assert step_run_log_entry['error']
        assert step_run_log_entry['level'] == 'ERROR'
        assert isinstance(step_run_log_entry['error']['stack'], list)

        assert 'bad programmer' in step_run_log_entry['error']['stack'][-1]

    def test_subscribe_bad_run_id(self, graphql_context):
        run_id = 'nope'
        subscription = execute_dagster_graphql(
            graphql_context, parse(SUBSCRIPTION_QUERY), variables={'runId': run_id}
        )

        subscribe_results = []
        subscription.subscribe(subscribe_results.append)

        assert len(subscribe_results) == 1
        subscribe_result = subscribe_results[0]

        assert (
            subscribe_result.data['pipelineRunLogs']['__typename']
            == 'PipelineRunLogsSubscriptionFailure'
        )
        assert subscribe_result.data['pipelineRunLogs']['missingRunId'] == 'nope'

    def test_basic_sync_execution_no_config(self, graphql_context):
        selector = infer_pipeline_selector(graphql_context, 'no_config_pipeline')
        result = sync_execute_get_run_log_data(
            context=graphql_context,
            variables={
                'executionParams': {'selector': selector, 'runConfigData': None, 'mode': 'default',}
            },
        )
        logs = result['messages']
        assert isinstance(logs, list)
        assert has_event_of_type(logs, 'PipelineStartEvent')
        assert has_event_of_type(logs, 'PipelineSuccessEvent')
        assert not has_event_of_type(logs, 'PipelineFailureEvent')

    def test_basic_inmemory_sync_execution(self, graphql_context):
        selector = infer_pipeline_selector(graphql_context, 'csv_hello_world')
        result = sync_execute_get_run_log_data(
            context=graphql_context,
            variables={
                'executionParams': {
                    'selector': selector,
                    'mode': 'default',
                    'runConfigData': csv_hello_world_solids_config(),
                }
            },
        )

        logs = result['messages']
        assert isinstance(logs, list)
        assert has_event_of_type(logs, 'PipelineStartEvent')
        assert has_event_of_type(logs, 'PipelineSuccessEvent')
        assert not has_event_of_type(logs, 'PipelineFailureEvent')

        assert first_event_of_type(logs, 'PipelineStartEvent')['level'] == 'DEBUG'

        sum_solid_output = get_step_output_event(logs, 'sum_solid.compute')
        assert sum_solid_output['step']['key'] == 'sum_solid.compute'

    def test_basic_filesystem_sync_execution(self, graphql_context):
        selector = infer_pipeline_selector(graphql_context, 'csv_hello_world')
        result = sync_execute_get_run_log_data(
            context=graphql_context,
            variables={
                'executionParams': {
                    'selector': selector,
                    'runConfigData': merge_dicts(
                        csv_hello_world_solids_config(), {'storage': {'filesystem': {}}}
                    ),
                    'mode': 'default',
                }
            },
        )

        logs = result['messages']
        assert isinstance(logs, list)
        assert has_event_of_type(logs, 'PipelineStartEvent')
        assert has_event_of_type(logs, 'PipelineSuccessEvent')
        assert not has_event_of_type(logs, 'PipelineFailureEvent')

        assert first_event_of_type(logs, 'PipelineStartEvent')['level'] == 'DEBUG'

        sum_solid_output = get_step_output_event(logs, 'sum_solid.compute')
        assert sum_solid_output['step']['key'] == 'sum_solid.compute'
        assert sum_solid_output['outputName'] == 'result'

    def test_basic_start_pipeline_execution_with_tags(self, graphql_context):
        selector = infer_pipeline_selector(graphql_context, 'csv_hello_world')
        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PIPELINE_EXECUTION_QUERY,
            variables={
                'executionParams': {
                    'selector': selector,
                    'runConfigData': csv_hello_world_solids_config(),
                    'executionMetadata': {
                        'tags': [{'key': 'dagster/test_key', 'value': 'test_value'}]
                    },
                    'mode': 'default',
                }
            },
        )

        assert not result.errors
        assert result.data
        assert result.data['launchPipelineExecution']['__typename'] == 'LaunchPipelineRunSuccess'

        run = result.data['launchPipelineExecution']['run']
        run_id = run['runId']
        assert len(run['tags']) > 0
        assert any(
            [x['key'] == 'dagster/test_key' and x['value'] == 'test_value' for x in run['tags']]
        )

        # Check run storage
        runs_with_tag = graphql_context.instance.get_runs(
            filters=PipelineRunsFilter(tags={'dagster/test_key': 'test_value'})
        )
        assert len(runs_with_tag) == 1
        assert runs_with_tag[0].run_id == run_id

    def test_basic_start_pipeline_execution_with_materialization(self, graphql_context):
        selector = infer_pipeline_selector(graphql_context, 'csv_hello_world')

        with get_temp_file_name() as out_csv_path:

            environment_dict = {
                'solids': {
                    'sum_solid': {
                        'inputs': {'num': file_relative_path(__file__, '../data/num.csv')},
                        'outputs': [{'result': out_csv_path}],
                    }
                }
            }

            run_logs = sync_execute_get_run_log_data(
                context=graphql_context,
                variables={
                    'executionParams': {
                        'selector': selector,
                        'runConfigData': environment_dict,
                        'mode': 'default',
                    }
                },
            )

            step_mat_event = None

            for message in run_logs['messages']:
                if message['__typename'] == 'StepMaterializationEvent':
                    # ensure only one event
                    assert step_mat_event is None
                    step_mat_event = message

            # ensure only one event
            assert step_mat_event
            assert len(step_mat_event['materialization']['metadataEntries']) == 1
            assert step_mat_event['materialization']['metadataEntries'][0]['path'] == out_csv_path


@contextmanager
def sqlite_instance_with_manager_disabled():
    with seven.TemporaryDirectory() as temp_dir:
        yield DagsterInstance.local_temp(
            tempdir=temp_dir, overrides={'dagit': {'execution_manager': {'disabled': True}}}
        )


def _get_step_run_log_entry(pipeline_run_logs, step_key, typename):
    for message_data in pipeline_run_logs['messages']:
        if message_data['__typename'] == typename:
            if message_data['step']['key'] == step_key:
                return message_data


def first_event_of_type(logs, message_type):
    for log in logs:
        if log['__typename'] == message_type:
            return log
    return None


def has_event_of_type(logs, message_type):
    return first_event_of_type(logs, message_type) is not None


def get_step_output_event(logs, step_key, output_name='result'):
    for log in logs:
        if (
            log['__typename'] == 'ExecutionStepOutputEvent'
            and log['step']['key'] == step_key
            and log['outputName'] == output_name
        ):
            return log

    return None
