from dagster import check
from dagster.api.utils import execute_unary_api_cli_command
from dagster.core.errors import DagsterSubprocessError
from dagster.core.origin import PipelineOrigin, PipelinePythonOrigin
from dagster.core.snap.execution_plan_snapshot import (
    ExecutionPlanSnapshot,
    ExecutionPlanSnapshotErrorData,
)
from dagster.grpc.types import ExecutionPlanSnapshotArgs


def sync_get_external_execution_plan(
    pipeline_origin,
    run_config,
    mode,
    pipeline_snapshot_id,
    solid_selection=None,
    step_keys_to_execute=None,
):

    check.inst_param(pipeline_origin, "pipeline_origin", PipelinePythonOrigin)
    check.opt_list_param(solid_selection, "solid_selection", of_type=str)
    check.dict_param(run_config, "run_config")
    check.str_param(mode, "mode")
    check.opt_list_param(step_keys_to_execute, "step_keys_to_execute", of_type=str)
    check.str_param(pipeline_snapshot_id, "pipeline_snapshot_id")

    result = check.inst(
        execute_unary_api_cli_command(
            pipeline_origin.executable_path,
            "execution_plan",
            ExecutionPlanSnapshotArgs(
                pipeline_origin=pipeline_origin,
                solid_selection=solid_selection,
                run_config=run_config,
                mode=mode,
                step_keys_to_execute=step_keys_to_execute,
                pipeline_snapshot_id=pipeline_snapshot_id,
            ),
        ),
        (ExecutionPlanSnapshot, ExecutionPlanSnapshotErrorData),
    )

    if isinstance(result, ExecutionPlanSnapshotErrorData):
        raise DagsterSubprocessError(
            result.error.to_string(), subprocess_error_infos=[result.error]
        )
    return result


def sync_get_external_execution_plan_grpc(
    api_client,
    pipeline_origin,
    run_config,
    mode,
    pipeline_snapshot_id,
    solid_selection=None,
    step_keys_to_execute=None,
):
    from dagster.grpc.client import DagsterGrpcClient

    check.inst_param(api_client, "api_client", DagsterGrpcClient)
    check.inst_param(pipeline_origin, "pipeline_origin", PipelineOrigin)
    check.opt_list_param(solid_selection, "solid_selection", of_type=str)
    check.dict_param(run_config, "run_config")
    check.str_param(mode, "mode")
    check.opt_list_param(step_keys_to_execute, "step_keys_to_execute", of_type=str)
    check.str_param(pipeline_snapshot_id, "pipeline_snapshot_id")

    result = check.inst(
        api_client.execution_plan_snapshot(
            execution_plan_snapshot_args=ExecutionPlanSnapshotArgs(
                pipeline_origin=pipeline_origin,
                solid_selection=solid_selection,
                run_config=run_config,
                mode=mode,
                step_keys_to_execute=step_keys_to_execute,
                pipeline_snapshot_id=pipeline_snapshot_id,
            )
        ),
        (ExecutionPlanSnapshot, ExecutionPlanSnapshotErrorData),
    )

    if isinstance(result, ExecutionPlanSnapshotErrorData):
        raise DagsterSubprocessError(
            result.error.to_string(), subprocess_error_infos=[result.error]
        )
    return result
