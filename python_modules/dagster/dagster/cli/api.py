import os
import sys
from collections import namedtuple

import click
from dagster import check, seven
from dagster.cli.workspace.cli_target import (
    get_working_directory_from_kwargs,
    python_origin_target_argument,
)
from dagster.core.events import EngineEventData
from dagster.core.execution.api import create_execution_plan, execute_plan_iterator
from dagster.core.instance import DagsterInstance
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.core.test_utils import mock_system_timezone
from dagster.core.types.loadable_target_origin import LoadableTargetOrigin
from dagster.grpc import DagsterGrpcClient, DagsterGrpcServer
from dagster.grpc.impl import core_execute_run
from dagster.grpc.types import ExecuteRunArgs, ExecuteStepArgs
from dagster.serdes import deserialize_as, serialize_dagster_namedtuple, whitelist_for_serdes
from dagster.seven import nullcontext
from dagster.utils.hosted_user_process import recon_pipeline_from_origin
from dagster.utils.interrupts import capture_interrupts


@whitelist_for_serdes
class ExecuteRunArgsLoadComplete(namedtuple("_ExecuteRunArgsLoadComplete", "")):
    pass


@click.group(name="api")
def api_cli():
    """
    [INTERNAL] These commands are intended to support internal use cases. Users should generally
    not invoke these commands interactively.
    """


@api_cli.command(
    name="execute_run",
    help=(
        "[INTERNAL] This is an internal utility. Users should generally not invoke this command "
        "interactively."
    ),
)
@click.argument("input_json", type=click.STRING)
def execute_run_command(input_json):
    with capture_interrupts():
        args = deserialize_as(input_json, ExecuteRunArgs)
        recon_pipeline = recon_pipeline_from_origin(args.pipeline_origin)

        with (
            DagsterInstance.from_ref(args.instance_ref)
            if args.instance_ref
            else DagsterInstance.get()
        ) as instance:
            buffer = []

            def send_to_buffer(event):
                buffer.append(serialize_dagster_namedtuple(event))

            _execute_run_command_body(
                recon_pipeline, args.pipeline_run_id, instance, send_to_buffer
            )

            for line in buffer:
                click.echo(line)


def _execute_run_command_body(recon_pipeline, pipeline_run_id, instance, write_stream_fn):

    # we need to send but the fact that we have loaded the args so the calling
    # process knows it is safe to clean up the temp input file
    write_stream_fn(ExecuteRunArgsLoadComplete())

    pipeline_run = instance.get_run_by_id(pipeline_run_id)

    pid = os.getpid()
    instance.report_engine_event(
        "Started process for pipeline (pid: {pid}).".format(pid=pid),
        pipeline_run,
        EngineEventData.in_process(pid, marker_end="cli_api_subprocess_init"),
    )

    try:
        for event in core_execute_run(recon_pipeline, pipeline_run, instance):
            write_stream_fn(event)
    finally:
        instance.report_engine_event(
            "Process for pipeline exited (pid: {pid}).".format(pid=pid),
            pipeline_run,
        )


def get_step_stats_by_key(instance, pipeline_run, step_keys_to_execute):
    # When using the k8s executor, there whould only ever be one step key
    step_stats = instance.get_run_step_stats(pipeline_run.run_id, step_keys=step_keys_to_execute)
    step_stats_by_key = {step_stat.step_key: step_stat for step_stat in step_stats}
    return step_stats_by_key


def verify_step(instance, pipeline_run, retry_state, step_keys_to_execute):
    step_stats_by_key = get_step_stats_by_key(instance, pipeline_run, step_keys_to_execute)

    for step_key in step_keys_to_execute:
        step_stat_for_key = step_stats_by_key.get(step_key)
        current_attempt = retry_state.get_attempt_count(step_key) + 1

        # When using the k8s executor, it is possible to get into an edge case when deleting
        # a step pod. K8s will restart the pod immediately even though we don't want it to.
        # Pod can be deleted manually or due to or node failures (for example, when running on
        # a spot instance that is evicted).
        #
        # If we encounter one of the error cases below, we exit with a success exit code
        # so that we don't cause the "Encountered failed job pods" error.
        #
        # Instead, the step will be marked as being in an unknown state by the executor and the
        # pipeline will fail accordingly.
        if current_attempt == 1 and step_stat_for_key:
            # If this is the first attempt, there shouldn't be any step stats for this
            # event yet.
            instance.report_engine_event(
                "Attempted to run {step_key} again even though it was already started. "
                "Exiting to prevent re-running the step.".format(step_key=step_key),
                pipeline_run,
            )
            return False
        elif current_attempt > 1 and step_stat_for_key:
            # If this is a retry, then the number of previous attempts should be exactly one less
            # than the current attempt

            if step_stat_for_key.attempts != current_attempt - 1:
                instance.report_engine_event(
                    "Attempted to run retry attempt {current_attempt} for step {step_key} again "
                    "even though it was already started. Exiting to prevent re-running "
                    "the step.".format(current_attempt=current_attempt, step_key=step_key),
                    pipeline_run,
                )
                return False
        elif current_attempt > 1 and not step_stat_for_key:
            instance.report_engine_event(
                "Attempting to retry attempt {current_attempt} for step {step_key} "
                "but there is no record of the original attempt".format(
                    current_attempt=current_attempt, step_key=step_key
                ),
                pipeline_run,
            )
            return False

    return True


@api_cli.command(
    name="execute_step",
    help=(
        "[INTERNAL] This is an internal utility. Users should generally not invoke this command "
        "interactively."
    ),
)
@click.argument("input_json", type=click.STRING)
def execute_step_command(input_json):
    with capture_interrupts():

        args = deserialize_as(input_json, ExecuteStepArgs)

        with (
            DagsterInstance.from_ref(args.instance_ref)
            if args.instance_ref
            else DagsterInstance.get()
        ) as instance:
            pipeline_run = instance.get_run_by_id(args.pipeline_run_id)
            check.inst(
                pipeline_run,
                PipelineRun,
                "Pipeline run with id '{}' not found for step execution".format(
                    args.pipeline_run_id
                ),
            )

            if args.should_verify_step:
                success = verify_step(
                    instance,
                    pipeline_run,
                    args.known_state.get_retry_state(),
                    args.step_keys_to_execute,
                )
                if not success:
                    return

            recon_pipeline = recon_pipeline_from_origin(
                args.pipeline_origin
            ).subset_for_execution_from_existing_pipeline(pipeline_run.solids_to_execute)

            execution_plan = create_execution_plan(
                recon_pipeline,
                run_config=pipeline_run.run_config,
                step_keys_to_execute=args.step_keys_to_execute,
                mode=pipeline_run.mode,
                known_state=args.known_state,
            )

            buff = []

            for event in execute_plan_iterator(
                execution_plan,
                recon_pipeline,
                pipeline_run,
                instance,
                run_config=pipeline_run.run_config,
                retry_mode=args.retry_mode,
            ):
                buff.append(serialize_dagster_namedtuple(event))

            for line in buff:
                click.echo(line)


@api_cli.command(name="grpc", help="Serve the Dagster inter-process API over GRPC")
@click.option(
    "--port",
    "-p",
    type=click.INT,
    required=False,
    help="Port over which to serve. You must pass one and only one of --port/-p or --socket/-s.",
)
@click.option(
    "--socket",
    "-s",
    type=click.Path(),
    required=False,
    help="Serve over a UDS socket. You must pass one and only one of --port/-p or --socket/-s.",
)
@click.option(
    "--host",
    "-h",
    type=click.STRING,
    required=False,
    default="localhost",
    help="Hostname at which to serve. Default is localhost.",
)
@click.option(
    "--max_workers",
    "-n",
    type=click.INT,
    required=False,
    default=None,
    help="Maximum number of (threaded) workers to use in the GRPC server",
)
@click.option(
    "--heartbeat",
    is_flag=True,
    help=(
        "If set, the GRPC server will shut itself down when it fails to receive a heartbeat "
        "after a timeout configurable with --heartbeat-timeout."
    ),
)
@click.option(
    "--heartbeat-timeout",
    type=click.INT,
    required=False,
    default=30,
    help="Timeout after which to shutdown if --heartbeat is set and a heartbeat is not received",
)
@click.option(
    "--lazy-load-user-code",
    is_flag=True,
    required=False,
    default=False,
    help="Wait until the first LoadRepositories call to actually load the repositories, instead of "
    "waiting to load them when the server is launched. Useful for surfacing errors when the server "
    "is managed directly from Dagit",
)
@python_origin_target_argument
@click.option(
    "--ipc-output-file",
    type=click.Path(),
    help="[INTERNAL] This option should generally not be used by users. Internal param used by "
    "dagster when it automatically spawns gRPC servers to communicate the success or failure of the "
    "server launching.",
)
@click.option(
    "--fixed-server-id",
    type=click.STRING,
    required=False,
    help="[INTERNAL] This option should generally not be used by users. Internal param used by "
    "dagster to spawn a gRPC server with the specified server id.",
)
@click.option(
    "--override-system-timezone",
    type=click.STRING,
    required=False,
    help="[INTERNAL] This option should generally not be used by users. Override the system "
    "timezone for tests.",
)
def grpc_command(
    port=None,
    socket=None,
    host=None,
    max_workers=None,
    heartbeat=False,
    heartbeat_timeout=30,
    lazy_load_user_code=False,
    ipc_output_file=None,
    fixed_server_id=None,
    override_system_timezone=None,
    **kwargs,
):
    if seven.IS_WINDOWS and port is None:
        raise click.UsageError(
            "You must pass a valid --port/-p on Windows: --socket/-s not supported."
        )
    if not (port or socket and not (port and socket)):
        raise click.UsageError("You must pass one and only one of --port/-p or --socket/-s.")

    loadable_target_origin = None
    if any(
        kwargs[key]
        for key in [
            "attribute",
            "working_directory",
            "module_name",
            "package_name",
            "python_file",
            "empty_working_directory",
        ]
    ):
        loadable_target_origin = LoadableTargetOrigin(
            executable_path=sys.executable,
            attribute=kwargs["attribute"],
            working_directory=get_working_directory_from_kwargs(kwargs),
            module_name=kwargs["module_name"],
            python_file=kwargs["python_file"],
            package_name=kwargs["package_name"],
        )

    with (
        mock_system_timezone(override_system_timezone)
        if override_system_timezone
        else nullcontext()
    ):
        server = DagsterGrpcServer(
            port=port,
            socket=socket,
            host=host,
            loadable_target_origin=loadable_target_origin,
            max_workers=max_workers,
            heartbeat=heartbeat,
            heartbeat_timeout=heartbeat_timeout,
            lazy_load_user_code=lazy_load_user_code,
            ipc_output_file=ipc_output_file,
            fixed_server_id=fixed_server_id,
        )

        server.serve()


@api_cli.command(name="grpc-health-check", help="Check the status of a dagster GRPC server")
@click.option(
    "--port",
    "-p",
    type=click.INT,
    required=False,
    help="Port over which to serve. You must pass one and only one of --port/-p or --socket/-s.",
)
@click.option(
    "--socket",
    "-s",
    type=click.Path(),
    required=False,
    help="Serve over a UDS socket. You must pass one and only one of --port/-p or --socket/-s.",
)
@click.option(
    "--host",
    "-h",
    type=click.STRING,
    required=False,
    default="localhost",
    help="Hostname at which to serve. Default is localhost.",
)
def grpc_health_check_command(port=None, socket=None, host="localhost"):
    if seven.IS_WINDOWS and port is None:
        raise click.UsageError(
            "You must pass a valid --port/-p on Windows: --socket/-s not supported."
        )
    if not (port or socket and not (port and socket)):
        raise click.UsageError("You must pass one and only one of --port/-p or --socket/-s.")

    client = DagsterGrpcClient(port=port, socket=socket, host=host)
    status = client.health_check_query()
    if status != "SERVING":
        sys.exit(1)
