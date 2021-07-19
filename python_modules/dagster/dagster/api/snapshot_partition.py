from dagster import check
from dagster.core.errors import DagsterUserCodeProcessError
from dagster.core.host_representation.external_data import (
    ExternalPartitionConfigData,
    ExternalPartitionExecutionErrorData,
    ExternalPartitionNamesData,
    ExternalPartitionSetExecutionParamData,
    ExternalPartitionTagsData,
)
from dagster.core.host_representation.handle import RepositoryHandle
from dagster.grpc.types import PartitionArgs, PartitionNamesArgs, PartitionSetExecutionParamArgs
from dagster.serdes import deserialize_json_to_dagster_namedtuple


def sync_get_external_partition_names_grpc(api_client, repository_handle, partition_set_name):
    from dagster.grpc.client import DagsterGrpcClient

    check.inst_param(api_client, "api_client", DagsterGrpcClient)
    check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
    check.str_param(partition_set_name, "partition_set_name")
    repository_origin = repository_handle.get_external_origin()
    result = check.inst(
        deserialize_json_to_dagster_namedtuple(
            api_client.external_partition_names(
                partition_names_args=PartitionNamesArgs(
                    repository_origin=repository_origin,
                    partition_set_name=partition_set_name,
                ),
            )
        ),
        (ExternalPartitionNamesData, ExternalPartitionExecutionErrorData),
    )
    if isinstance(result, ExternalPartitionExecutionErrorData):
        raise DagsterUserCodeProcessError.from_error_info(result.error)

    return result


def sync_get_external_partition_config_grpc(
    api_client, repository_handle, partition_set_name, partition_name
):
    from dagster.grpc.client import DagsterGrpcClient

    check.inst_param(api_client, "api_client", DagsterGrpcClient)
    check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
    check.str_param(partition_set_name, "partition_set_name")
    check.str_param(partition_name, "partition_name")
    repository_origin = repository_handle.get_external_origin()
    result = check.inst(
        deserialize_json_to_dagster_namedtuple(
            api_client.external_partition_config(
                partition_args=PartitionArgs(
                    repository_origin=repository_origin,
                    partition_set_name=partition_set_name,
                    partition_name=partition_name,
                ),
            ),
        ),
        (ExternalPartitionConfigData, ExternalPartitionExecutionErrorData),
    )
    if isinstance(result, ExternalPartitionExecutionErrorData):
        raise DagsterUserCodeProcessError.from_error_info(result.error)

    return result


def sync_get_external_partition_tags_grpc(
    api_client, repository_handle, partition_set_name, partition_name
):
    from dagster.grpc.client import DagsterGrpcClient

    check.inst_param(api_client, "api_client", DagsterGrpcClient)
    check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
    check.str_param(partition_set_name, "partition_set_name")
    check.str_param(partition_name, "partition_name")

    repository_origin = repository_handle.get_external_origin()
    result = check.inst(
        deserialize_json_to_dagster_namedtuple(
            api_client.external_partition_tags(
                partition_args=PartitionArgs(
                    repository_origin=repository_origin,
                    partition_set_name=partition_set_name,
                    partition_name=partition_name,
                ),
            ),
        ),
        (ExternalPartitionTagsData, ExternalPartitionExecutionErrorData),
    )
    if isinstance(result, ExternalPartitionExecutionErrorData):
        raise DagsterUserCodeProcessError.from_error_info(result.error)

    return result


def sync_get_external_partition_set_execution_param_data_grpc(
    api_client, repository_handle, partition_set_name, partition_names
):
    from dagster.grpc.client import DagsterGrpcClient

    check.inst_param(api_client, "api_client", DagsterGrpcClient)
    check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
    check.str_param(partition_set_name, "partition_set_name")
    check.list_param(partition_names, "partition_names", of_type=str)

    repository_origin = repository_handle.get_external_origin()

    result = check.inst(
        deserialize_json_to_dagster_namedtuple(
            api_client.external_partition_set_execution_params(
                partition_set_execution_param_args=PartitionSetExecutionParamArgs(
                    repository_origin=repository_origin,
                    partition_set_name=partition_set_name,
                    partition_names=partition_names,
                ),
            ),
        ),
        (ExternalPartitionSetExecutionParamData, ExternalPartitionExecutionErrorData),
    )
    if isinstance(result, ExternalPartitionExecutionErrorData):
        raise DagsterUserCodeProcessError.from_error_info(result.error)

    return result
