from time import sleep

from dagster_graphql.test.utils import (
    execute_dagster_graphql,
    execute_dagster_graphql_and_finish_runs,
    infer_pipeline_selector,
)

from dagster import DagsterEventType
from dagster.core.execution.plan.objects import StepOutputHandle
from dagster.core.storage.intermediate_store import build_fs_intermediate_store
from dagster.core.storage.intermediates_manager import IntermediateStoreIntermediatesManager
from dagster.core.storage.tags import RESUME_RETRY_TAG
from dagster.core.utils import make_new_run_id

from .execution_queries import (
    LAUNCH_PIPELINE_EXECUTION_QUERY,
    LAUNCH_PIPELINE_REEXECUTION_QUERY,
    LAUNCH_PIPELINE_REEXECUTION_SNAPSHOT_QUERY,
    PIPELINE_REEXECUTION_INFO_QUERY,
)
from .graphql_context_test_suite import (
    ExecutingGraphQLContextTestMatrix,
    GraphQLContextVariant,
    make_graphql_context_test_suite,
)
from .setup import (
    PoorMansDataFrame,
    csv_hello_world_solids_config,
    csv_hello_world_solids_config_fs_storage,
    get_retry_multi_execution_params,
    retry_config,
)
from .utils import get_all_logs_for_finished_run_via_subscription, sync_execute_get_events


def step_did_not_run(logs, step_key):
    return not any(
        log['step']['key'] == step_key
        for log in logs
        if log['__typename']
        in ('ExecutionStepSuccessEvent', 'ExecutionStepSkippedEvent', 'ExecutionStepFailureEvent')
    )


def step_did_succeed(logs, step_key):
    return any(
        log['__typename'] == 'ExecutionStepSuccessEvent' and step_key == log['step']['key']
        for log in logs
    )


def step_did_skip(logs, step_key):
    return any(
        log['__typename'] == 'ExecutionStepSkippedEvent' and step_key == log['step']['key']
        for log in logs
    )


def step_did_fail(logs, step_key):
    return any(
        log['__typename'] == 'ExecutionStepFailureEvent' and step_key == log['step']['key']
        for log in logs
    )


def step_did_fail_in_records(records, step_key):
    return any(
        record.step_key == step_key
        and record.dagster_event.event_type_value == DagsterEventType.STEP_FAILURE.value
        for record in records
    )


def step_did_succeed_in_records(records, step_key):
    return any(
        record.step_key == step_key
        and record.dagster_event.event_type_value == DagsterEventType.STEP_SUCCESS.value
        for record in records
    )


def step_did_not_run_in_records(records, step_key):
    return not any(
        record.step_key == step_key
        and record.dagster_event.event_type_value
        in (
            DagsterEventType.STEP_SUCCESS.value,
            DagsterEventType.STEP_FAILURE.value,
            DagsterEventType.STEP_SKIPPED.value,
        )
        for record in records
    )


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


class TestRetryExecution(ExecutingGraphQLContextTestMatrix):
    def test_retry_pipeline_execution(self, graphql_context):
        selector = infer_pipeline_selector(graphql_context, 'eventually_successful')
        result = execute_dagster_graphql_and_finish_runs(
            graphql_context,
            LAUNCH_PIPELINE_EXECUTION_QUERY,
            variables={
                'executionParams': {
                    'mode': 'default',
                    'selector': selector,
                    'runConfigData': retry_config(0),
                }
            },
        )

        run_id = result.data['launchPipelineExecution']['run']['runId']
        logs = get_all_logs_for_finished_run_via_subscription(graphql_context, run_id)[
            'pipelineRunLogs'
        ]['messages']

        assert step_did_succeed(logs, 'spawn.compute')
        assert step_did_fail(logs, 'fail.compute')
        assert step_did_skip(logs, 'fail_2.compute')
        assert step_did_skip(logs, 'fail_3.compute')
        assert step_did_skip(logs, 'reset.compute')

        retry_one = execute_dagster_graphql_and_finish_runs(
            graphql_context,
            LAUNCH_PIPELINE_REEXECUTION_QUERY,
            variables={
                'executionParams': {
                    'mode': 'default',
                    'selector': selector,
                    'runConfigData': retry_config(1),
                    'executionMetadata': {
                        'rootRunId': run_id,
                        'parentRunId': run_id,
                        'tags': [{'key': RESUME_RETRY_TAG, 'value': 'true'}],
                    },
                }
            },
        )

        run_id = retry_one.data['launchPipelineReexecution']['run']['runId']
        logs = get_all_logs_for_finished_run_via_subscription(graphql_context, run_id)[
            'pipelineRunLogs'
        ]['messages']
        assert step_did_not_run(logs, 'spawn.compute')
        assert step_did_succeed(logs, 'fail.compute')
        assert step_did_fail(logs, 'fail_2.compute')
        assert step_did_skip(logs, 'fail_3.compute')
        assert step_did_skip(logs, 'reset.compute')

        retry_two = execute_dagster_graphql_and_finish_runs(
            graphql_context,
            LAUNCH_PIPELINE_REEXECUTION_QUERY,
            variables={
                'executionParams': {
                    'mode': 'default',
                    'selector': selector,
                    'runConfigData': retry_config(2),
                    'executionMetadata': {
                        'rootRunId': run_id,
                        'parentRunId': run_id,
                        'tags': [{'key': RESUME_RETRY_TAG, 'value': 'true'}],
                    },
                }
            },
        )

        run_id = retry_two.data['launchPipelineReexecution']['run']['runId']
        logs = get_all_logs_for_finished_run_via_subscription(graphql_context, run_id)[
            'pipelineRunLogs'
        ]['messages']

        assert step_did_not_run(logs, 'spawn.compute')
        assert step_did_not_run(logs, 'fail.compute')
        assert step_did_succeed(logs, 'fail_2.compute')
        assert step_did_fail(logs, 'fail_3.compute')
        assert step_did_skip(logs, 'reset.compute')

        retry_three = execute_dagster_graphql_and_finish_runs(
            graphql_context,
            LAUNCH_PIPELINE_REEXECUTION_QUERY,
            variables={
                'executionParams': {
                    'mode': 'default',
                    'selector': selector,
                    'runConfigData': retry_config(3),
                    'executionMetadata': {
                        'rootRunId': run_id,
                        'parentRunId': run_id,
                        'tags': [{'key': RESUME_RETRY_TAG, 'value': 'true'}],
                    },
                }
            },
        )

        run_id = retry_three.data['launchPipelineReexecution']['run']['runId']
        logs = get_all_logs_for_finished_run_via_subscription(graphql_context, run_id)[
            'pipelineRunLogs'
        ]['messages']

        assert step_did_not_run(logs, 'spawn.compute')
        assert step_did_not_run(logs, 'fail.compute')
        assert step_did_not_run(logs, 'fail_2.compute')
        assert step_did_succeed(logs, 'fail_3.compute')
        assert step_did_succeed(logs, 'reset.compute')

    def test_retry_resource_pipeline(self, graphql_context):
        context = graphql_context
        selector = infer_pipeline_selector(graphql_context, 'retry_resource_pipeline')
        result = execute_dagster_graphql_and_finish_runs(
            context,
            LAUNCH_PIPELINE_EXECUTION_QUERY,
            variables={
                'executionParams': {
                    'mode': 'default',
                    'selector': selector,
                    'runConfigData': {'storage': {'filesystem': {}}},
                }
            },
        )

        run_id = result.data['launchPipelineExecution']['run']['runId']
        logs = get_all_logs_for_finished_run_via_subscription(context, run_id)['pipelineRunLogs'][
            'messages'
        ]
        assert step_did_succeed(logs, 'start.compute')
        assert step_did_fail(logs, 'will_fail.compute')

        retry_one = execute_dagster_graphql_and_finish_runs(
            context,
            LAUNCH_PIPELINE_REEXECUTION_QUERY,
            variables={
                'executionParams': {
                    'mode': 'default',
                    'selector': selector,
                    'runConfigData': {'storage': {'filesystem': {}}},
                    'executionMetadata': {
                        'rootRunId': run_id,
                        'parentRunId': run_id,
                        'tags': [{'key': RESUME_RETRY_TAG, 'value': 'true'}],
                    },
                }
            },
        )
        run_id = retry_one.data['launchPipelineReexecution']['run']['runId']
        logs = get_all_logs_for_finished_run_via_subscription(context, run_id)['pipelineRunLogs'][
            'messages'
        ]
        assert step_did_not_run(logs, 'start.compute')
        assert step_did_fail(logs, 'will_fail.compute')

    def test_retry_multi_output(self, graphql_context):
        context = graphql_context
        result = execute_dagster_graphql_and_finish_runs(
            context,
            LAUNCH_PIPELINE_EXECUTION_QUERY,
            variables={
                'executionParams': get_retry_multi_execution_params(context, should_fail=True)
            },
        )

        run_id = result.data['launchPipelineExecution']['run']['runId']
        logs = get_all_logs_for_finished_run_via_subscription(context, run_id)['pipelineRunLogs'][
            'messages'
        ]
        assert step_did_succeed(logs, 'multi.compute')
        assert step_did_skip(logs, 'child_multi_skip.compute')
        assert step_did_fail(logs, 'can_fail.compute')
        assert step_did_skip(logs, 'child_fail.compute')
        assert step_did_skip(logs, 'child_skip.compute')
        assert step_did_skip(logs, 'grandchild_fail.compute')

        retry_one = execute_dagster_graphql_and_finish_runs(
            context,
            LAUNCH_PIPELINE_REEXECUTION_QUERY,
            variables={
                'executionParams': get_retry_multi_execution_params(
                    context, should_fail=True, retry_id=run_id
                )
            },
        )

        run_id = retry_one.data['launchPipelineReexecution']['run']['runId']
        logs = get_all_logs_for_finished_run_via_subscription(context, run_id)['pipelineRunLogs'][
            'messages'
        ]
        assert step_did_not_run(logs, 'multi.compute')
        assert step_did_not_run(logs, 'child_multi_skip.compute')
        assert step_did_fail(logs, 'can_fail.compute')
        assert step_did_skip(logs, 'child_fail.compute')
        assert step_did_skip(logs, 'child_skip.compute')
        assert step_did_skip(logs, 'grandchild_fail.compute')

        retry_two = execute_dagster_graphql_and_finish_runs(
            context,
            LAUNCH_PIPELINE_REEXECUTION_QUERY,
            variables={
                'executionParams': get_retry_multi_execution_params(
                    context, should_fail=False, retry_id=run_id
                )
            },
        )

        run_id = retry_two.data['launchPipelineReexecution']['run']['runId']
        logs = get_all_logs_for_finished_run_via_subscription(context, run_id)['pipelineRunLogs'][
            'messages'
        ]
        assert step_did_not_run(logs, 'multi.compute')
        assert step_did_not_run(logs, 'child_multi_skip.compute')
        assert step_did_succeed(logs, 'can_fail.compute')
        assert step_did_succeed(logs, 'child_fail.compute')
        assert step_did_skip(logs, 'child_skip.compute')
        assert step_did_succeed(logs, 'grandchild_fail.compute')

    def test_successful_pipeline_reexecution(self, graphql_context):
        selector = infer_pipeline_selector(graphql_context, 'csv_hello_world')
        run_id = make_new_run_id()
        result_one = execute_dagster_graphql_and_finish_runs(
            graphql_context,
            LAUNCH_PIPELINE_EXECUTION_QUERY,
            variables={
                'executionParams': {
                    'selector': selector,
                    'runConfigData': csv_hello_world_solids_config_fs_storage(),
                    'executionMetadata': {'runId': run_id},
                    'mode': 'default',
                }
            },
        )

        assert (
            result_one.data['launchPipelineExecution']['__typename'] == 'LaunchPipelineRunSuccess'
        )

        expected_value_repr = (
            '''[OrderedDict([('num1', '1'), ('num2', '2'), ('sum', 3), '''
            '''('sum_sq', 9)]), OrderedDict([('num1', '3'), ('num2', '4'), ('sum', 7), '''
            '''('sum_sq', 49)])]'''
        )

        instance = graphql_context.instance

        store = build_fs_intermediate_store(instance.intermediates_directory, run_id)
        intermediates_manager = IntermediateStoreIntermediatesManager(store)
        assert intermediates_manager.has_intermediate(None, StepOutputHandle('sum_solid.compute'))
        assert intermediates_manager.has_intermediate(
            None, StepOutputHandle('sum_sq_solid.compute')
        )
        assert (
            str(
                intermediates_manager.get_intermediate(
                    None, PoorMansDataFrame, StepOutputHandle('sum_sq_solid.compute')
                ).obj
            )
            == expected_value_repr
        )

        # retry
        new_run_id = make_new_run_id()

        result_two = execute_dagster_graphql_and_finish_runs(
            graphql_context,
            LAUNCH_PIPELINE_REEXECUTION_SNAPSHOT_QUERY,
            variables={
                'executionParams': {
                    'selector': selector,
                    'runConfigData': csv_hello_world_solids_config_fs_storage(),
                    'stepKeys': ['sum_sq_solid.compute'],
                    'executionMetadata': {
                        'runId': new_run_id,
                        'rootRunId': run_id,
                        'parentRunId': run_id,
                        'tags': [{'key': RESUME_RETRY_TAG, 'value': 'true'}],
                    },
                    'mode': 'default',
                }
            },
        )

        query_result = result_two.data['launchPipelineReexecution']
        assert query_result['__typename'] == 'LaunchPipelineRunSuccess'

        result = get_all_logs_for_finished_run_via_subscription(graphql_context, new_run_id)
        logs = result['pipelineRunLogs']['messages']

        assert isinstance(logs, list)
        assert has_event_of_type(logs, 'PipelineStartEvent')
        assert has_event_of_type(logs, 'PipelineSuccessEvent')
        assert not has_event_of_type(logs, 'PipelineFailureEvent')

        assert not get_step_output_event(logs, 'sum_solid.compute')
        assert get_step_output_event(logs, 'sum_sq_solid.compute')

        store = build_fs_intermediate_store(instance.intermediates_directory, new_run_id)
        intermediates_manager = IntermediateStoreIntermediatesManager(store)
        assert not intermediates_manager.has_intermediate(
            None, StepOutputHandle('sum_solid.inputs.num.read', 'input_thunk_output')
        )
        assert intermediates_manager.has_intermediate(None, StepOutputHandle('sum_solid.compute'))
        assert intermediates_manager.has_intermediate(
            None, StepOutputHandle('sum_sq_solid.compute')
        )
        assert (
            str(
                intermediates_manager.get_intermediate(
                    None, PoorMansDataFrame, StepOutputHandle('sum_sq_solid.compute')
                ).obj
            )
            == expected_value_repr
        )

    def test_pipeline_reexecution_info_query(self, graphql_context, snapshot):
        context = graphql_context
        selector = infer_pipeline_selector(graphql_context, 'csv_hello_world')

        run_id = make_new_run_id()
        execute_dagster_graphql_and_finish_runs(
            context,
            LAUNCH_PIPELINE_EXECUTION_QUERY,
            variables={
                'executionParams': {
                    'selector': selector,
                    'runConfigData': csv_hello_world_solids_config_fs_storage(),
                    'executionMetadata': {'runId': run_id},
                    'mode': 'default',
                }
            },
        )

        # retry
        new_run_id = make_new_run_id()
        execute_dagster_graphql_and_finish_runs(
            context,
            LAUNCH_PIPELINE_REEXECUTION_SNAPSHOT_QUERY,
            variables={
                'executionParams': {
                    'selector': selector,
                    'runConfigData': csv_hello_world_solids_config_fs_storage(),
                    'stepKeys': ['sum_sq_solid.compute'],
                    'executionMetadata': {
                        'runId': new_run_id,
                        'rootRunId': run_id,
                        'parentRunId': run_id,
                        'tags': [{'key': RESUME_RETRY_TAG, 'value': 'true'}],
                    },
                    'mode': 'default',
                }
            },
        )

        result_one = execute_dagster_graphql_and_finish_runs(
            context, PIPELINE_REEXECUTION_INFO_QUERY, variables={'runId': run_id}
        )
        query_result_one = result_one.data['pipelineRunOrError']
        assert query_result_one['__typename'] == 'PipelineRun'
        assert query_result_one['stepKeysToExecute'] is None

        result_two = execute_dagster_graphql_and_finish_runs(
            context, PIPELINE_REEXECUTION_INFO_QUERY, variables={'runId': new_run_id}
        )
        query_result_two = result_two.data['pipelineRunOrError']
        assert query_result_two['__typename'] == 'PipelineRun'
        stepKeysToExecute = query_result_two['stepKeysToExecute']
        assert stepKeysToExecute is not None
        snapshot.assert_match(stepKeysToExecute)

    def test_pipeline_reexecution_invalid_step_in_subset(self, graphql_context):
        run_id = make_new_run_id()
        selector = infer_pipeline_selector(graphql_context, 'csv_hello_world')
        execute_dagster_graphql_and_finish_runs(
            graphql_context,
            LAUNCH_PIPELINE_REEXECUTION_SNAPSHOT_QUERY,
            variables={
                'executionParams': {
                    'selector': selector,
                    'runConfigData': csv_hello_world_solids_config(),
                    'executionMetadata': {'runId': run_id},
                    'mode': 'default',
                }
            },
        )

        # retry
        new_run_id = make_new_run_id()

        result_two = execute_dagster_graphql_and_finish_runs(
            graphql_context,
            LAUNCH_PIPELINE_REEXECUTION_SNAPSHOT_QUERY,
            variables={
                'executionParams': {
                    'selector': selector,
                    'runConfigData': csv_hello_world_solids_config(),
                    'stepKeys': ['nope'],
                    'executionMetadata': {
                        'runId': new_run_id,
                        'rootRunId': run_id,
                        'parentRunId': run_id,
                        'tags': [{'key': RESUME_RETRY_TAG, 'value': 'true'}],
                    },
                    'mode': 'default',
                }
            },
        )

        query_result = result_two.data['launchPipelineReexecution']
        assert query_result['__typename'] == 'InvalidStepError'
        assert query_result['invalidStepKey'] == 'nope'


def _do_retry_intermediates_test(graphql_context, run_id, reexecution_run_id):
    selector = infer_pipeline_selector(graphql_context, 'eventually_successful')
    logs = sync_execute_get_events(
        context=graphql_context,
        variables={
            'executionParams': {
                'mode': 'default',
                'selector': selector,
                'executionMetadata': {'runId': run_id},
            }
        },
    )

    assert step_did_succeed(logs, 'spawn.compute')
    assert step_did_fail(logs, 'fail.compute')
    assert step_did_skip(logs, 'fail_2.compute')
    assert step_did_skip(logs, 'fail_3.compute')
    assert step_did_skip(logs, 'reset.compute')

    retry_one = execute_dagster_graphql_and_finish_runs(
        graphql_context,
        LAUNCH_PIPELINE_REEXECUTION_QUERY,
        variables={
            'executionParams': {
                'mode': 'default',
                'selector': selector,
                'executionMetadata': {
                    'runId': reexecution_run_id,
                    'rootRunId': run_id,
                    'parentRunId': run_id,
                    'tags': [{'key': RESUME_RETRY_TAG, 'value': 'true'}],
                },
            }
        },
    )

    return retry_one


class TestRetryExecutionSyncOnlyBehavior(
    make_graphql_context_test_suite(
        context_variants=[GraphQLContextVariant.in_memory_instance_in_process_env()]
    )
):
    def test_retry_requires_intermediates_sync_only(self, graphql_context):
        run_id = make_new_run_id()
        reexecution_run_id = make_new_run_id()

        retry_one = _do_retry_intermediates_test(graphql_context, run_id, reexecution_run_id)
        assert not retry_one.errors
        assert retry_one.data
        assert retry_one.data['launchPipelineReexecution']['__typename'] == 'PythonError'
        assert (
            'Cannot perform reexecution with non persistent intermediates manager'
            in retry_one.data['launchPipelineReexecution']['message']
        )


class TestRetryExecutionAsyncOnlyBehavior(
    make_graphql_context_test_suite(
        context_variants=[GraphQLContextVariant.sqlite_with_cli_api_run_launcher_in_process_env()]
    )
):
    def test_retry_requires_intermediates_async_only(self, graphql_context):
        run_id = make_new_run_id()
        reexecution_run_id = make_new_run_id()

        _do_retry_intermediates_test(graphql_context, run_id, reexecution_run_id)
        reexecution_run = graphql_context.instance.get_run_by_id(reexecution_run_id)

        assert reexecution_run.is_failure

    def test_retry_early_terminate(self, graphql_context):
        instance = graphql_context.instance
        selector = infer_pipeline_selector(
            graphql_context, 'retry_multi_input_early_terminate_pipeline'
        )
        run_id = make_new_run_id()
        execute_dagster_graphql(
            graphql_context,
            LAUNCH_PIPELINE_EXECUTION_QUERY,
            variables={
                'executionParams': {
                    'mode': 'default',
                    'selector': selector,
                    'runConfigData': {
                        'solids': {
                            'get_input_one': {'config': {'wait_to_terminate': True}},
                            'get_input_two': {'config': {'wait_to_terminate': True}},
                        },
                        'storage': {'filesystem': {}},
                    },
                    'executionMetadata': {'runId': run_id},
                }
            },
        )
        # Wait until the first step succeeded
        while instance.get_run_stats(run_id).steps_succeeded < 1:
            sleep(0.1)
        # Terminate the current pipeline run at the second step
        graphql_context.instance.run_launcher.terminate(run_id)

        records = instance.all_logs(run_id)

        # The first step should succeed, the second should fail or not start,
        # and the following steps should not appear in records
        assert step_did_succeed_in_records(records, 'return_one.compute')
        assert any(
            [
                step_did_fail_in_records(records, 'get_input_one.compute'),
                step_did_not_run_in_records(records, 'get_input_one.compute'),
            ]
        )
        assert step_did_not_run_in_records(records, 'get_input_two.compute')
        assert step_did_not_run_in_records(records, 'sum_inputs.compute')

        # Start retry
        new_run_id = make_new_run_id()

        execute_dagster_graphql_and_finish_runs(
            graphql_context,
            LAUNCH_PIPELINE_REEXECUTION_QUERY,
            variables={
                'executionParams': {
                    'mode': 'default',
                    'selector': selector,
                    'runConfigData': {
                        'solids': {
                            'get_input_one': {'config': {'wait_to_terminate': False}},
                            'get_input_two': {'config': {'wait_to_terminate': False}},
                        },
                        'storage': {'filesystem': {}},
                    },
                    'executionMetadata': {
                        'runId': new_run_id,
                        'rootRunId': run_id,
                        'parentRunId': run_id,
                        'tags': [{'key': RESUME_RETRY_TAG, 'value': 'true'}],
                    },
                }
            },
        )

        retry_records = instance.all_logs(new_run_id)
        # The first step should not run and the other three steps should succeed in retry
        assert step_did_not_run_in_records(retry_records, 'return_one.compute')
        assert step_did_succeed_in_records(retry_records, 'get_input_one.compute')
        assert step_did_succeed_in_records(retry_records, 'get_input_two.compute')
        assert step_did_succeed_in_records(retry_records, 'sum_inputs.compute')
