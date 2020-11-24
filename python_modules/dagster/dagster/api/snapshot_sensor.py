from dagster import check
from dagster.core.host_representation.external_data import (
    ExternalSensorExecutionData,
    ExternalSensorExecutionErrorData,
)
from dagster.core.host_representation.handle import RepositoryHandle
from dagster.grpc.types import SensorExecutionArgs


def sync_get_external_sensor_execution_data_ephemeral_grpc(
    instance, repository_handle, sensor_name, last_evaluation_time
):
    from dagster.grpc.client import ephemeral_grpc_api_client

    origin = repository_handle.get_external_origin()
    with ephemeral_grpc_api_client(
        origin.repository_location_origin.loadable_target_origin
    ) as api_client:
        return sync_get_external_sensor_execution_data_grpc(
            api_client, instance, repository_handle, sensor_name, last_evaluation_time
        )


def sync_get_external_sensor_execution_data_grpc(
    api_client, instance, repository_handle, sensor_name, last_evaluation_time
):
    check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
    check.str_param(sensor_name, "sensor_name")
    check.opt_float_param(last_evaluation_time, "last_evaluation_time")

    origin = repository_handle.get_external_origin()

    return check.inst(
        api_client.external_sensor_execution(
            sensor_execution_args=SensorExecutionArgs(
                repository_origin=origin,
                instance_ref=instance.get_ref(),
                sensor_name=sensor_name,
                last_evaluation_time=last_evaluation_time,
            )
        ),
        (ExternalSensorExecutionData, ExternalSensorExecutionErrorData),
    )
