from dagster import check
from dagster.core.errors import DagsterUserCodeProcessError
from dagster.core.types.loadable_target_origin import LoadableTargetOrigin
from dagster.utils.error import SerializableErrorInfo

from .utils import execute_unary_api_cli_command


def sync_list_repositories(executable_path, python_file, module_name, working_directory, attribute):
    from dagster.grpc.types import ListRepositoriesResponse, ListRepositoriesInput

    result = check.inst(
        execute_unary_api_cli_command(
            executable_path,
            "list_repositories",
            ListRepositoriesInput(
                module_name=module_name,
                python_file=python_file,
                working_directory=working_directory,
                attribute=attribute,
            ),
        ),
        (ListRepositoriesResponse, SerializableErrorInfo),
    )
    if isinstance(result, SerializableErrorInfo):
        raise DagsterUserCodeProcessError(
            result.to_string(), user_code_process_error_infos=[result]
        )
    else:
        return result


def sync_list_repositories_grpc(api_client):
    from dagster.grpc.client import DagsterGrpcClient
    from dagster.grpc.types import ListRepositoriesResponse

    check.inst_param(api_client, "api_client", DagsterGrpcClient)
    result = check.inst(
        api_client.list_repositories(), (ListRepositoriesResponse, SerializableErrorInfo)
    )
    if isinstance(result, SerializableErrorInfo):
        raise DagsterUserCodeProcessError(
            result.to_string(), user_code_process_error_infos=[result]
        )
    else:
        return result


def sync_list_repositories_ephemeral_grpc(
    executable_path, python_file, module_name, working_directory, attribute
):
    from dagster.grpc.client import ephemeral_grpc_api_client

    check.str_param(executable_path, "executable_path")
    check.opt_str_param(python_file, "python_file")
    check.opt_str_param(module_name, "module_name")
    check.opt_str_param(working_directory, "working_directory")

    with ephemeral_grpc_api_client(
        loadable_target_origin=LoadableTargetOrigin(
            executable_path=executable_path,
            module_name=module_name,
            python_file=python_file,
            working_directory=working_directory,
            attribute=attribute,
        )
    ) as api_client:
        return sync_list_repositories_grpc(api_client)
