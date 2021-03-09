from dagster import execute_pipeline
from dagster.cli.workspace.load import load_workspace_from_yaml_paths
from dagster.utils import file_relative_path
from docs_snippets.concepts.repositories_workspaces.hello_world_repository import (
    hello_world_pipeline,
    hello_world_repository,
)


def test_pipelines():
    result = execute_pipeline(hello_world_pipeline)
    assert result.success


def test_hello_world_repository():
    assert hello_world_repository
    assert len(hello_world_repository.get_all_pipelines()) == 1


def test_workspace_yamls():
    with load_workspace_from_yaml_paths(
        [
            file_relative_path(
                __file__,
                "../../../docs_snippets/concepts/repositories_workspaces/workspace.yaml",
            )
        ]
    ) as workspace:
        assert len(workspace.repository_location_handles) == 1

    with load_workspace_from_yaml_paths(
        [
            file_relative_path(
                __file__,
                "../../../docs_snippets/concepts/repositories_workspaces/workspace_working_directory.yaml",
            )
        ]
    ) as workspace:
        assert len(workspace.repository_location_handles) == 1

    with load_workspace_from_yaml_paths(
        [
            file_relative_path(
                __file__,
                "../../../docs_snippets/concepts/repositories_workspaces/workspace_one_repository.yaml",
            )
        ]
    ) as workspace:
        assert len(workspace.repository_location_handles) == 1

    with load_workspace_from_yaml_paths(
        [
            file_relative_path(
                __file__,
                "../../../docs_snippets/concepts/repositories_workspaces/workspace_python_package.yaml",
            )
        ]
    ) as workspace:
        assert len(workspace.repository_location_handles) == 0

    with load_workspace_from_yaml_paths(
        [
            file_relative_path(
                __file__,
                "../../../docs_snippets/concepts/repositories_workspaces/workspace_grpc.yaml",
            )
        ]
    ) as workspace:
        assert len(workspace.repository_location_handles) == 0
