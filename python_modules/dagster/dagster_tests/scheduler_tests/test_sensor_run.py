import os
import sys
import time
from contextlib import contextmanager

import pendulum
import pytest
from dagster import pipeline, repository, solid
from dagster.core.definitions.decorators.sensor import sensor
from dagster.core.definitions.job import JobType
from dagster.core.host_representation import (
    ManagedGrpcPythonEnvRepositoryLocationOrigin,
    RepositoryLocation,
    RepositoryLocationHandle,
)
from dagster.core.scheduler.job import JobState, JobStatus, JobTickStatus
from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.core.test_utils import instance_for_test
from dagster.core.types.loadable_target_origin import LoadableTargetOrigin
from dagster.daemon import get_default_daemon_logger
from dagster.scheduler.sensor import execute_sensor_iteration


@solid
def the_solid(_):
    return 1


@pipeline
def the_pipeline():
    the_solid()


@sensor(pipeline_name="the_pipeline")
def simple_sensor(context):
    if not context.last_evaluation_time:
        return False

    return int(context.last_evaluation_time) % 2 == 1


@sensor(pipeline_name="the_pipeline")
def always_on_sensor(_context):
    return True


@sensor(pipeline_name="the_pipeline")
def error_sensor(context):
    raise Exception("womp womp")


@repository
def the_repo():
    return [the_pipeline, simple_sensor, error_sensor, always_on_sensor]


@contextmanager
def instance_with_sensors(external_repo_context, overrides=None):
    with instance_for_test(overrides) as instance:
        with external_repo_context() as external_repo:
            yield (instance, external_repo)


@contextmanager
def default_repo():
    loadable_target_origin = LoadableTargetOrigin(
        executable_path=sys.executable,
        python_file=__file__,
        attribute="the_repo",
        working_directory=os.getcwd(),
    )

    with RepositoryLocationHandle.create_from_repository_location_origin(
        ManagedGrpcPythonEnvRepositoryLocationOrigin(
            loadable_target_origin=loadable_target_origin, location_name="test_location",
        )
    ) as handle:
        yield RepositoryLocation.from_handle(handle).get_repository("the_repo")


def repos():
    return [default_repo]


def validate_tick(
    tick,
    external_sensor,
    expected_datetime,
    expected_status,
    expected_run_id=None,
    expected_error=None,
):
    tick_data = tick.job_tick_data
    assert tick_data.job_origin_id == external_sensor.get_external_origin_id()
    assert tick_data.job_name == external_sensor.name
    assert tick_data.job_type == JobType.SENSOR
    assert tick_data.status == expected_status
    assert tick_data.timestamp == expected_datetime.timestamp()
    assert tick_data.run_id == expected_run_id
    if expected_error:
        assert expected_error in tick_data.error.message


def validate_run_started(run, expected_success=True):
    if expected_success:
        assert run.status == PipelineRunStatus.STARTED or run.status == PipelineRunStatus.SUCCESS
    else:
        assert run.status == PipelineRunStatus.FAILURE


def wait_for_all_runs_to_start(instance, timeout=10):
    start_time = time.time()
    while True:
        if time.time() - start_time > timeout:
            raise Exception("Timed out waiting for runs to start")
        time.sleep(0.5)

        not_started_runs = [
            run for run in instance.get_runs() if run.status == PipelineRunStatus.NOT_STARTED
        ]

        if len(not_started_runs) == 0:
            break


@pytest.mark.parametrize("external_repo_context", repos())
def test_simple_sensor(external_repo_context, capfd):
    freeze_datetime = pendulum.datetime(
        year=2019, month=2, day=27, hour=23, minute=59, second=59,
    ).in_tz("US/Central")
    with instance_with_sensors(external_repo_context) as (instance, external_repo):
        with pendulum.test(freeze_datetime):
            external_sensor = external_repo.get_external_sensor("simple_sensor")
            instance.add_job_state(
                JobState(external_sensor.get_external_origin(), JobType.SENSOR, JobStatus.RUNNING)
            )
            assert instance.get_runs_count() == 0
            ticks = instance.get_job_ticks(external_sensor.get_external_origin_id())
            assert len(ticks) == 0

            # launch_scheduled_runs does nothing before the first tick
            execute_sensor_iteration(instance, get_default_daemon_logger("SensorDaemon"))

            assert instance.get_runs_count() == 0
            ticks = instance.get_job_ticks(external_sensor.get_external_origin_id())
            assert len(ticks) == 1
            validate_tick(
                ticks[0], external_sensor, freeze_datetime, JobTickStatus.SKIPPED,
            )

            captured = capfd.readouterr()
            assert (
                captured.out
                == """2019-02-27 17:59:59 - SensorDaemon - INFO - Checking for new runs for the following sensors: simple_sensor
2019-02-27 17:59:59 - SensorDaemon - INFO - Sensor returned false for simple_sensor, skipping
"""
            )

            freeze_datetime = freeze_datetime.add(seconds=1)

        with pendulum.test(freeze_datetime):
            execute_sensor_iteration(instance, get_default_daemon_logger("SensorDaemon"))
            wait_for_all_runs_to_start(instance)
            assert instance.get_runs_count() == 1
            run = instance.get_runs()[0]
            validate_run_started(run)
            ticks = instance.get_job_ticks(external_sensor.get_external_origin_id())
            assert len(ticks) == 1  # reuse the skipped tick

            expected_datetime = pendulum.datetime(year=2019, month=2, day=28)
            validate_tick(
                ticks[0], external_sensor, expected_datetime, JobTickStatus.SUCCESS, run.run_id,
            )

            captured = capfd.readouterr()
            assert (
                captured.out
                == """2019-02-27 18:00:00 - SensorDaemon - INFO - Checking for new runs for the following sensors: simple_sensor
2019-02-27 18:00:00 - SensorDaemon - INFO - Launching run for simple_sensor
2019-02-27 18:00:00 - SensorDaemon - INFO - Completed launch of run {run_id} for simple_sensor
""".format(
                    run_id=run.run_id
                )
            )


@pytest.mark.parametrize("external_repo_context", repos())
def test_error_sensor(external_repo_context, capfd):
    freeze_datetime = pendulum.datetime(
        year=2019, month=2, day=27, hour=23, minute=59, second=59,
    ).in_tz("US/Central")
    with instance_with_sensors(external_repo_context) as (instance, external_repo):
        with pendulum.test(freeze_datetime):
            external_sensor = external_repo.get_external_sensor("error_sensor")
            instance.add_job_state(
                JobState(external_sensor.get_external_origin(), JobType.SENSOR, JobStatus.RUNNING)
            )
            assert instance.get_runs_count() == 0
            ticks = instance.get_job_ticks(external_sensor.get_external_origin_id())
            assert len(ticks) == 0

            # launch_scheduled_runs does nothing before the first tick
            execute_sensor_iteration(instance, get_default_daemon_logger("SensorDaemon"))

            assert instance.get_runs_count() == 0
            ticks = instance.get_job_ticks(external_sensor.get_external_origin_id())
            assert len(ticks) == 1
            validate_tick(
                ticks[0],
                external_sensor,
                freeze_datetime,
                JobTickStatus.FAILURE,
                None,
                "Error occurred during the execution of should_execute for sensor error_sensor",
            )

            captured = capfd.readouterr()
            assert ("Failed to resolve sensor for error_sensor : ") in captured.out

            assert (
                "Error occurred during the execution of should_execute for sensor error_sensor"
            ) in captured.out


@pytest.mark.parametrize("external_repo_context", repos())
def test_launch_failure(external_repo_context, capfd):
    freeze_datetime = pendulum.datetime(
        year=2019, month=2, day=27, hour=23, minute=59, second=59,
    ).in_tz("US/Central")
    with instance_with_sensors(
        external_repo_context,
        overrides={
            "run_launcher": {"module": "dagster.core.test_utils", "class": "ExplodingRunLauncher",},
        },
    ) as (instance, external_repo):
        with pendulum.test(freeze_datetime):

            external_sensor = external_repo.get_external_sensor("always_on_sensor")
            instance.add_job_state(
                JobState(external_sensor.get_external_origin(), JobType.SENSOR, JobStatus.RUNNING)
            )
            assert instance.get_runs_count() == 0
            ticks = instance.get_job_ticks(external_sensor.get_external_origin_id())
            assert len(ticks) == 0

            # launch_scheduled_runs does nothing before the first tick
            execute_sensor_iteration(instance, get_default_daemon_logger("SensorDaemon"))

            assert instance.get_runs_count() == 1
            run = instance.get_runs()[0]
            ticks = instance.get_job_ticks(external_sensor.get_external_origin_id())
            assert len(ticks) == 1
            validate_tick(
                ticks[0], external_sensor, freeze_datetime, JobTickStatus.SUCCESS, run.run_id
            )

            captured = capfd.readouterr()
            assert (
                "Run {run_id} created successfully but failed to launch.".format(run_id=run.run_id)
            ) in captured.out
