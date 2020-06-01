from dagster_graphql.client.query import SUBSCRIPTION_QUERY
from dagster_graphql.implementation.context import DagsterGraphQLContext
from dagster_graphql.test.utils import execute_dagster_graphql

from dagster import check

from .execution_queries import LAUNCH_PIPELINE_EXECUTION_QUERY, SUBSCRIPTION_QUERY


def get_all_logs_for_finished_run_via_subscription(context, run_id):
    '''
    You should almost certainly ensure that this run has complete or terminated in order
    to get reliable results that you can test against.
    '''
    check.inst_param(context, 'context', DagsterGraphQLContext)

    run = context.instance.get_run_by_id(run_id)

    assert run.is_finished

    subscription = execute_dagster_graphql(context, SUBSCRIPTION_QUERY, variables={'runId': run_id})
    subscribe_results = []

    subscription.subscribe(subscribe_results.append)
    assert len(subscribe_results) == 1
    subscribe_result = subscribe_results[0]
    if subscribe_result.errors:
        raise Exception(subscribe_result.errors)
    assert not subscribe_result.errors
    assert subscribe_result.data
    return subscribe_result.data


def sync_execute_get_payload(variables, context):
    check.inst_param(context, 'context', DagsterGraphQLContext)

    result = execute_dagster_graphql(context, LAUNCH_PIPELINE_EXECUTION_QUERY, variables=variables)

    assert result.data

    if result.data['launchPipelineExecution']['__typename'] != 'LaunchPipelineRunSuccess':
        raise Exception(result.data)

    context.drain_outstanding_executions()

    run_id = result.data['launchPipelineExecution']['run']['runId']
    return get_all_logs_for_finished_run_via_subscription(context, run_id)


def sync_execute_get_run_log_data(variables, context):
    check.inst_param(context, 'context', DagsterGraphQLContext)
    payload_data = sync_execute_get_payload(variables, context)
    assert payload_data['pipelineRunLogs']
    return payload_data['pipelineRunLogs']


def sync_execute_get_events(variables, context):
    check.inst_param(context, 'context', DagsterGraphQLContext)
    return sync_execute_get_run_log_data(variables, context)['messages']
