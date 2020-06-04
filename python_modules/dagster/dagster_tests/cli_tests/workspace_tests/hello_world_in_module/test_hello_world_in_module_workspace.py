from dagster.cli.workspace import Workspace, load_workspace_from_yaml_path
from dagster.utils import file_relative_path


def test_load_in_process_location_handle_hello_world_terse():
    workspace = load_workspace_from_yaml_path(
        file_relative_path(__file__, 'terse_python_module_workspace.yaml')
    )
    assert isinstance(workspace, Workspace)
    assert len(workspace.repository_location_handles) == 1


def test_load_in_process_location_handle_hello_world_nested():
    workspace = load_workspace_from_yaml_path(
        file_relative_path(__file__, 'nested_python_module_workspace.yaml')
    )
    assert isinstance(workspace, Workspace)
    assert len(workspace.repository_location_handles) == 1


def test_load_in_process_location_handle_hello_world_nested_with_def():
    workspace = load_workspace_from_yaml_path(
        file_relative_path(__file__, 'nested_with_def_python_module_workspace.yaml')
    )
    assert isinstance(workspace, Workspace)
    assert len(workspace.repository_location_handles) == 1
