from dagster_graphql.client.query import LAUNCH_PIPELINE_EXECUTION_MUTATION
from dagster_graphql.test.utils import execute_dagster_graphql, infer_pipeline_selector

from .graphql_context_test_suite import GraphQLContextVariant, make_graphql_context_test_suite

GET_ASSET_KEY_QUERY = '''
{
    assetsOrError {
        __typename
        ...on AssetConnection {
            nodes {
                key {
                    path
                }
            }
        }
    }
}
'''

GET_ASSET_MATERIALIZATION = '''
    query AssetQuery($assetKey: AssetKeyInput!) {
        assetOrError(assetKey: $assetKey) {
            ... on Asset {
                assetMaterializations(limit: 1) {
                    materializationEvent {
                        materialization {
                            label
                        }
                    }
                }
            }
        }
    }
'''

GET_ASSET_RUNS = '''
    query AssetRunsQuery($assetKey: AssetKeyInput!) {
        assetOrError(assetKey: $assetKey) {
            ... on Asset {
                runs {
                    runId
                }
            }
        }
    }
'''


class TestAssetAwareEventLog(
    make_graphql_context_test_suite(
        context_variants=[
            GraphQLContextVariant.in_memory_instance_in_process_env(),
            GraphQLContextVariant.asset_aware_sqlite_instance_in_process_env(),
        ]
    )
):
    def test_get_all_asset_keys(self, graphql_context, snapshot):
        selector = infer_pipeline_selector(graphql_context, 'multi_asset_pipeline')
        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PIPELINE_EXECUTION_MUTATION,
            variables={'executionParams': {'selector': selector, 'mode': 'default'}},
        )
        assert result.data['launchPipelineExecution']['__typename'] == 'LaunchPipelineRunSuccess'

        result = execute_dagster_graphql(graphql_context, GET_ASSET_KEY_QUERY)
        assert result.data
        snapshot.assert_match(result.data)

    def test_get_asset_key_materialization(self, graphql_context, snapshot):
        selector = infer_pipeline_selector(graphql_context, 'single_asset_pipeline')
        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PIPELINE_EXECUTION_MUTATION,
            variables={'executionParams': {'selector': selector, 'mode': 'default'}},
        )
        assert result.data['launchPipelineExecution']['__typename'] == 'LaunchPipelineRunSuccess'
        result = execute_dagster_graphql(
            graphql_context, GET_ASSET_MATERIALIZATION, variables={'assetKey': {'path': ['a']}}
        )
        assert result.data
        snapshot.assert_match(result.data)

    def test_get_asset_runs(self, graphql_context):
        single_selector = infer_pipeline_selector(graphql_context, 'single_asset_pipeline')
        multi_selector = infer_pipeline_selector(graphql_context, 'multi_asset_pipeline')
        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PIPELINE_EXECUTION_MUTATION,
            variables={'executionParams': {'selector': single_selector, 'mode': 'default'}},
        )
        assert result.data['launchPipelineExecution']['__typename'] == 'LaunchPipelineRunSuccess'
        single_run_id = result.data['launchPipelineExecution']['run']['runId']

        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PIPELINE_EXECUTION_MUTATION,
            variables={'executionParams': {'selector': multi_selector, 'mode': 'default'}},
        )
        assert result.data['launchPipelineExecution']['__typename'] == 'LaunchPipelineRunSuccess'
        multi_run_id = result.data['launchPipelineExecution']['run']['runId']

        result = execute_dagster_graphql(
            graphql_context, GET_ASSET_RUNS, variables={'assetKey': {'path': ['a']}}
        )
        assert result.data
        fetched_runs = [run['runId'] for run in result.data['assetOrError']['runs']]
        assert len(fetched_runs) == 2
        assert multi_run_id in fetched_runs
        assert single_run_id in fetched_runs
