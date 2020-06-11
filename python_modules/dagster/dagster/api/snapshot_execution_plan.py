from dagster import check
from dagster.core.origin import PipelinePythonOrigin
from dagster.core.snap.execution_plan_snapshot import ExecutionPlanSnapshot

from .utils import execute_unary_api_cli_command


def sync_get_external_execution_plan(
    pipeline_origin,
    environment_dict,
    mode,
    snapshot_id,
    solid_selection=None,
    step_keys_to_execute=None,
):
    from dagster.cli.api import ExecutionPlanSnapshotArgs

    check.inst_param(pipeline_origin, 'pipeline_origin', PipelinePythonOrigin)
    check.opt_list_param(solid_selection, 'solid_selection', of_type=str)
    check.dict_param(environment_dict, 'environment_dict')
    check.str_param(mode, 'mode')
    check.opt_list_param(step_keys_to_execute, 'step_keys_to_execute', of_type=str)
    check.str_param(snapshot_id, 'snapshot_id')

    return check.inst(
        execute_unary_api_cli_command(
            pipeline_origin.executable_path,
            'execution_plan',
            ExecutionPlanSnapshotArgs(
                pipeline_origin=pipeline_origin,
                solid_selection=solid_selection,
                run_config=environment_dict,
                mode=mode,
                step_keys_to_execute=step_keys_to_execute,
                snapshot_id=snapshot_id,
            ),
        ),
        ExecutionPlanSnapshot,
    )
