import sys
import time

import pytest
from dagster import file_relative_path, seven
from dagster.core.errors import DagsterLaunchFailedError
from dagster.core.host_representation import (
    GrpcServerRepositoryLocationOrigin,
    ManagedGrpcPythonEnvRepositoryLocationOrigin,
)
from dagster.core.host_representation.handle import RepositoryLocationHandle
from dagster.core.host_representation.repository_location import GrpcServerRepositoryLocation
from dagster.core.instance import DagsterInstance
from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.core.storage.tags import GRPC_INFO_TAG
from dagster.core.test_utils import instance_for_test, poll_for_finished_run, poll_for_step_start
from dagster.core.types.loadable_target_origin import LoadableTargetOrigin
from dagster.grpc.server import GrpcServerProcess
from dagster.utils import find_free_port, merge_dicts
from dagster_tests.core_tests.launcher_tests.test_default_run_launcher import (
    math_diamond,
    sleepy_pipeline,
    slow_pipeline,
)


def grpc_instance():
    return instance_for_test(
        overrides={
            "run_launcher": {
                "module": "dagster.core.launcher.grpc_run_launcher",
                "class": "GrpcRunLauncher",
            }
        },
    )


def test_run_always_finishes():  # pylint: disable=redefined-outer-name
    with seven.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance.local_temp(
            temp_dir,
            overrides={
                "run_launcher": {
                    "module": "dagster.core.launcher.grpc_run_launcher",
                    "class": "GrpcRunLauncher",
                }
            },
        )

        pipeline_run = instance.create_run_for_pipeline(pipeline_def=slow_pipeline, run_config=None)
        run_id = pipeline_run.run_id

        loadable_target_origin = LoadableTargetOrigin(
            executable_path=sys.executable,
            attribute="nope",
            python_file=file_relative_path(__file__, "test_default_run_launcher.py"),
        )
        server_process = GrpcServerProcess(
            loadable_target_origin=loadable_target_origin, max_workers=4
        )
        with server_process.create_ephemeral_client() as api_client:
            repository_location = GrpcServerRepositoryLocation(
                RepositoryLocationHandle.create_from_repository_location_origin(
                    GrpcServerRepositoryLocationOrigin(
                        location_name="test",
                        port=api_client.port,
                        socket=api_client.socket,
                        host=api_client.host,
                    )
                )
            )

            external_pipeline = repository_location.get_repository(
                "nope"
            ).get_full_external_pipeline("slow_pipeline")

            assert instance.get_run_by_id(run_id).status == PipelineRunStatus.NOT_STARTED

            instance.launch_run(run_id=pipeline_run.run_id, external_pipeline=external_pipeline)

        # Server process now receives shutdown event, run has not finished yet
        pipeline_run = instance.get_run_by_id(run_id)
        assert not pipeline_run.is_finished
        assert server_process.server_process.poll() is None

        # Server should wait until run finishes, then shutdown
        pipeline_run = poll_for_finished_run(instance, run_id)
        assert pipeline_run.status == PipelineRunStatus.SUCCESS

        start_time = time.time()
        while server_process.server_process.poll() is None:
            time.sleep(0.05)
            # Verify server process cleans up eventually
            assert time.time() - start_time < 5

        server_process.wait()


def test_terminate_after_shutdown():
    with grpc_instance() as instance:
        repository_location_handle = RepositoryLocationHandle.create_from_repository_location_origin(
            ManagedGrpcPythonEnvRepositoryLocationOrigin(
                loadable_target_origin=LoadableTargetOrigin(
                    executable_path=sys.executable,
                    attribute="nope",
                    python_file=file_relative_path(__file__, "test_default_run_launcher.py"),
                ),
                location_name="nope",
            )
        )
        repository_location = GrpcServerRepositoryLocation(repository_location_handle)

        external_pipeline = repository_location.get_repository("nope").get_full_external_pipeline(
            "sleepy_pipeline"
        )

        pipeline_run = instance.create_run_for_pipeline(
            pipeline_def=sleepy_pipeline, run_config=None
        )

        instance.launch_run(pipeline_run.run_id, external_pipeline)

        poll_for_step_start(instance, pipeline_run.run_id)

        # Tell the server to shut down once executions finish
        repository_location_handle.client.cleanup_server()

        # Trying to start another run fails
        doomed_to_fail_external_pipeline = repository_location.get_repository(
            "nope"
        ).get_full_external_pipeline("math_diamond")
        doomed_to_fail_pipeline_run = instance.create_run_for_pipeline(
            pipeline_def=math_diamond, run_config=None
        )

        with pytest.raises(DagsterLaunchFailedError):
            instance.launch_run(
                doomed_to_fail_pipeline_run.run_id, doomed_to_fail_external_pipeline
            )

        launcher = instance.run_launcher

        # Can terminate the run even after the shutdown event has been received
        assert launcher.can_terminate(pipeline_run.run_id)
        assert launcher.terminate(pipeline_run.run_id)

        # Server process now shuts down cleanly since there are no more executions


def test_server_down():
    with grpc_instance() as instance:
        loadable_target_origin = LoadableTargetOrigin(
            executable_path=sys.executable,
            attribute="nope",
            python_file=file_relative_path(__file__, "test_default_run_launcher.py"),
        )

        server_process = GrpcServerProcess(
            loadable_target_origin=loadable_target_origin, max_workers=4, force_port=True
        )

        with server_process.create_ephemeral_client() as api_client:
            repository_location = GrpcServerRepositoryLocation(
                RepositoryLocationHandle.create_from_repository_location_origin(
                    GrpcServerRepositoryLocationOrigin(
                        location_name="test",
                        port=api_client.port,
                        socket=api_client.socket,
                        host=api_client.host,
                    )
                )
            )

            external_pipeline = repository_location.get_repository(
                "nope"
            ).get_full_external_pipeline("sleepy_pipeline")

            pipeline_run = instance.create_run_for_pipeline(
                pipeline_def=sleepy_pipeline, run_config=None
            )

            instance.launch_run(pipeline_run.run_id, external_pipeline)

            poll_for_step_start(instance, pipeline_run.run_id)

            launcher = instance.run_launcher
            assert launcher.can_terminate(pipeline_run.run_id)

            original_run_tags = instance.get_run_by_id(pipeline_run.run_id).tags[GRPC_INFO_TAG]

            # Replace run tags with an invalid port
            instance.add_run_tags(
                pipeline_run.run_id,
                {
                    GRPC_INFO_TAG: seven.json.dumps(
                        merge_dicts({"host": "localhost"}, {"port": find_free_port()})
                    )
                },
            )

            assert not launcher.can_terminate(pipeline_run.run_id)

            instance.add_run_tags(
                pipeline_run.run_id, {GRPC_INFO_TAG: original_run_tags,},
            )

            assert launcher.terminate(pipeline_run.run_id)

        server_process.wait()
