from dagster import check
from dagster.core.events import EngineEventData
from dagster.core.instance import DagsterInstance
from dagster.core.origin import PipelinePythonOrigin
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.serdes.ipc import ipc_read_event_stream, open_ipc_subprocess, write_unary_input
from dagster.utils import safe_tempfile_path


# mostly for test
def sync_cli_api_execute_run(
    instance, pipeline_origin, pipeline_name, environment_dict, mode, solids_to_execute
):
    with safe_tempfile_path() as output_file_path:
        pipeline_run = instance.create_run(
            pipeline_name=pipeline_name,
            run_id=None,
            environment_dict=environment_dict,
            mode=mode,
            solids_to_execute=solids_to_execute,
            step_keys_to_execute=None,
            status=None,
            tags=None,
            root_run_id=None,
            parent_run_id=None,
            pipeline_snapshot=None,
            execution_plan_snapshot=None,
            parent_pipeline_snapshot=None,
        )
        process = cli_api_execute_run(output_file_path, instance, pipeline_origin, pipeline_run)

        _stdout, _stderr = process.communicate()
        for message in ipc_read_event_stream(output_file_path):
            yield message


def cli_api_execute_run(output_file, instance, pipeline_origin, pipeline_run):
    check.str_param(output_file, 'output_file')
    check.inst_param(instance, 'instance', DagsterInstance)
    check.inst_param(pipeline_origin, 'pipeline_origin', PipelinePythonOrigin)
    check.inst_param(pipeline_run, 'pipeline_run', PipelineRun)

    from dagster.cli.api import ExecuteRunArgs, ExecuteRunArgsLoadComplete

    with safe_tempfile_path() as input_file:
        write_unary_input(
            input_file,
            ExecuteRunArgs(
                pipeline_origin=pipeline_origin,
                pipeline_run_id=pipeline_run.run_id,
                instance_ref=instance.get_ref(),
            ),
        )

        parts = [
            pipeline_origin.executable_path,
            '-m',
            'dagster',
            'api',
            'execute_run',
            input_file,
            output_file,
        ]

        instance.report_engine_event(
            'About to start process for pipeline "{pipeline_name}" (run_id: {run_id}).'.format(
                pipeline_name=pipeline_run.pipeline_name, run_id=pipeline_run.run_id
            ),
            pipeline_run,
            engine_event_data=EngineEventData(marker_start='cli_api_subprocess_init'),
        )

        process = open_ipc_subprocess(parts)

        # we need to process this event in order to ensure that the called process loads the input
        event = next(ipc_read_event_stream(output_file))

        check.inst(event, ExecuteRunArgsLoadComplete)

        return process
