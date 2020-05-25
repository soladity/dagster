from dagster_graphql.client.query import LAUNCH_PIPELINE_EXECUTION_MUTATION
from dagster_graphql.test.utils import execute_dagster_graphql

from .graphql_context_test_suite import GraphQLContextVariant, make_graphql_context_test_suite

RUN_QUERY = '''
query RunQuery($runId: ID!) {
  pipelineRunOrError(runId: $runId) {
    __typename
    ... on PipelineRun {
      status
      stats {
        ... on PipelineRunStatsSnapshot {
          stepsSucceeded
        }
      }
    }
  }
}
'''


class TestMissingRunLauncher(
    make_graphql_context_test_suite(context_variants=GraphQLContextVariant.all_legacy_variants())
):
    def test_missing(self, graphql_context):
        result = execute_dagster_graphql(
            context=graphql_context,
            query=LAUNCH_PIPELINE_EXECUTION_MUTATION,
            variables={
                'executionParams': {'selector': {'name': 'no_config_pipeline'}, 'mode': 'default'}
            },
        )

        assert result.data['launchPipelineExecution']['__typename'] == 'RunLauncherNotDefinedError'


class TestBasicLaunch(
    make_graphql_context_test_suite(
        context_variants=[GraphQLContextVariant.sqlite_with_cli_api_hijack()]
    )
):
    def test_run_launcher(self, graphql_context):
        result = execute_dagster_graphql(
            context=graphql_context,
            query=LAUNCH_PIPELINE_EXECUTION_MUTATION,
            variables={
                'executionParams': {'selector': {'name': 'no_config_pipeline'}, 'mode': 'default'}
            },
        )

        assert result.data['launchPipelineExecution']['__typename'] == 'LaunchPipelineRunSuccess'
        assert result.data['launchPipelineExecution']['run']['status'] == 'NOT_STARTED'

        run_id = result.data['launchPipelineExecution']['run']['runId']

        graphql_context.instance.run_launcher.join()

        result = execute_dagster_graphql(
            context=graphql_context, query=RUN_QUERY, variables={'runId': run_id}
        )
        assert result.data['pipelineRunOrError']['__typename'] == 'PipelineRun'
        assert result.data['pipelineRunOrError']['status'] == 'SUCCESS'

    def test_run_launcher_subset(self, graphql_context):
        result = execute_dagster_graphql(
            context=graphql_context,
            query=LAUNCH_PIPELINE_EXECUTION_MUTATION,
            variables={
                'executionParams': {
                    'selector': {'name': 'more_complicated_config', 'solidSubset': ['noop_solid']},
                    'mode': 'default',
                }
            },
        )

        assert result.data['launchPipelineExecution']['__typename'] == 'LaunchPipelineRunSuccess'
        assert result.data['launchPipelineExecution']['run']['status'] == 'NOT_STARTED'

        run_id = result.data['launchPipelineExecution']['run']['runId']

        graphql_context.instance.run_launcher.join()

        result = execute_dagster_graphql(
            context=graphql_context, query=RUN_QUERY, variables={'runId': run_id}
        )
        assert result.data['pipelineRunOrError']['__typename'] == 'PipelineRun'
        assert result.data['pipelineRunOrError']['status'] == 'SUCCESS'
        assert result.data['pipelineRunOrError']['stats']['stepsSucceeded'] == 1
