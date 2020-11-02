import sys

from dagster import repository
from dagster.core.code_pointer import CodePointer
from dagster.core.host_representation import (
    ExternalRepository,
    RepositoryHandle,
    external_repository_data_from_def,
)
from dagster.grpc.types import ListRepositoriesResponse
from dagster.seven import mock
from dagster_graphql.test.utils import execute_dagster_graphql

from .graphql_context_test_suite import GraphQLContextVariant, make_graphql_context_test_suite

# import dagster.api.utils


class TestReloadRepositoriesOutOfProcess(
    make_graphql_context_test_suite(
        context_variants=[GraphQLContextVariant.readonly_in_memory_instance_managed_grpc_env()]
    )
):
    def test_out_of_process_reload_location(self, graphql_context):
        result = execute_dagster_graphql(
            graphql_context, RELOAD_REPOSITORY_LOCATION_QUERY, {"repositoryLocationName": "test"}
        )

        assert result
        assert result.data
        assert result.data["reloadRepositoryLocation"]
        assert result.data["reloadRepositoryLocation"]["__typename"] == "RepositoryLocation"
        assert result.data["reloadRepositoryLocation"]["name"] == "test"
        assert result.data["reloadRepositoryLocation"]["repositories"] == [{"name": "test_repo"}]
        assert result.data["reloadRepositoryLocation"]["isReloadSupported"] is True

        with mock.patch(
            # note it where the function is *used* that needs to mocked, not
            # where it is defined.
            # see https://docs.python.org/3/library/unittest.mock.html#where-to-patch
            "dagster.core.host_representation.handle.sync_list_repositories_grpc"
        ) as cli_command_mock:

            with mock.patch(
                # note it where the function is *used* that needs to mocked, not
                # where it is defined.
                # see https://docs.python.org/3/library/unittest.mock.html#where-to-patch
                "dagster.core.host_representation.repository_location.sync_get_streaming_external_repositories_grpc"
            ) as external_repository_mock:

                @repository
                def new_repo():
                    return []

                new_repo_data = external_repository_data_from_def(new_repo)

                external_repository_mock.return_value = [
                    ExternalRepository(
                        new_repo_data,
                        RepositoryHandle(
                            "new_repo", graphql_context.repository_locations[0].location_handle
                        ),
                    )
                ]

                cli_command_mock.return_value = ListRepositoriesResponse(
                    repository_symbols=[],
                    executable_path=sys.executable,
                    repository_code_pointer_dict={
                        "new_repo": CodePointer.from_python_file(__file__, "new_repo", None)
                    },
                )

                result = execute_dagster_graphql(
                    graphql_context,
                    RELOAD_REPOSITORY_LOCATION_QUERY,
                    {"repositoryLocationName": "test"},
                )

                assert cli_command_mock.call_count == 1
                assert external_repository_mock.call_count == 1

                assert result.data["reloadRepositoryLocation"]["repositories"] == [
                    {"name": "new_repo"}
                ]


class TestReloadRepositoriesInProcess(
    make_graphql_context_test_suite(
        context_variants=[GraphQLContextVariant.readonly_in_memory_instance_in_process_env()]
    )
):
    def test_reload_not_supported(self, graphql_context):
        result = execute_dagster_graphql(
            graphql_context,
            RELOAD_REPOSITORY_LOCATION_QUERY,
            {"repositoryLocationName": "<<in_process>>"},
        )
        assert result.data["reloadRepositoryLocation"]["__typename"] == "ReloadNotSupported"

    def test_location_not_found(self, graphql_context):
        result = execute_dagster_graphql(
            graphql_context, RELOAD_REPOSITORY_LOCATION_QUERY, {"repositoryLocationName": "nope"},
        )
        assert result.data["reloadRepositoryLocation"]["__typename"] == "RepositoryLocationNotFound"


RELOAD_REPOSITORY_LOCATION_QUERY = """
mutation ($repositoryLocationName: String!) {
   reloadRepositoryLocation(repositoryLocationName: $repositoryLocationName) {
      __typename
      ... on RepositoryLocation {
        name
        repositories {
            name
        }
        isReloadSupported
      }
   }
}
"""


class TestReloadRepositoriesManagedGrpc(
    make_graphql_context_test_suite(
        context_variants=[GraphQLContextVariant.readonly_in_memory_instance_managed_grpc_env(),]
    )
):
    def test_managed_grpc_reload_location(self, graphql_context):
        result = execute_dagster_graphql(
            graphql_context, RELOAD_REPOSITORY_LOCATION_QUERY, {"repositoryLocationName": "test"}
        )

        assert result
        assert result.data
        assert result.data["reloadRepositoryLocation"]
        assert result.data["reloadRepositoryLocation"]["__typename"] == "RepositoryLocation"
        assert result.data["reloadRepositoryLocation"]["name"] == "test"
        assert result.data["reloadRepositoryLocation"]["repositories"] == [{"name": "test_repo"}]
        assert result.data["reloadRepositoryLocation"]["isReloadSupported"] is True
