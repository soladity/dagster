import datetime

import pytest

from dagster import daily_schedule, lambda_solid, pipeline, repository, seven
from dagster.api.launch_scheduled_execution import sync_launch_scheduled_execution
from dagster.core.definitions.reconstructable import ReconstructableRepository
from dagster.core.errors import DagsterSubprocessError
from dagster.core.instance import DagsterInstance
from dagster.core.scheduler import (
    ScheduleTickStatus,
    ScheduledExecutionFailed,
    ScheduledExecutionSkipped,
    ScheduledExecutionSuccess,
)
from dagster.core.test_utils import environ


def _throw(_context):
    raise Exception('bananas')


def _never(_context):
    return False


@lambda_solid
def the_solid():
    return '0.8.0 was a lot of work'


@pipeline
def the_pipeline():
    the_solid()


@daily_schedule(
    pipeline_name='the_pipeline', start_date=datetime.datetime.now() - datetime.timedelta(days=1),
)
def simple_schedule(_context):
    return {}


@daily_schedule(
    pipeline_name='the_pipeline', start_date=datetime.datetime.now() - datetime.timedelta(days=1),
)
def bad_env_fn_schedule():  # forgot context arg
    return {}


@daily_schedule(
    pipeline_name='the_pipeline',
    start_date=datetime.datetime.now() - datetime.timedelta(days=1),
    should_execute=_throw,
)
def bad_should_execute_schedule(_context):
    return {}


@daily_schedule(
    pipeline_name='the_pipeline',
    start_date=datetime.datetime.now() - datetime.timedelta(days=1),
    should_execute=_never,
)
def skip_schedule(_context):
    return {}


@repository
def the_repo():
    return [
        the_pipeline,
        simple_schedule,
        bad_env_fn_schedule,
        bad_should_execute_schedule,
        skip_schedule,
    ]


def test_launch_scheduled_execution():
    with seven.TemporaryDirectory() as temp_dir:
        with environ({'DAGSTER_HOME': temp_dir}):
            instance = DagsterInstance.get()

            recon_repo = ReconstructableRepository.for_file(__file__, 'the_repo')
            simple = recon_repo.get_reconstructable_schedule('simple_schedule')
            result = sync_launch_scheduled_execution(simple.get_origin())

            assert isinstance(result, ScheduledExecutionSuccess)

            run = instance.get_run_by_id(result.run_id)
            assert run.is_success

            ticks = instance.get_schedule_ticks(simple.get_origin_id())
            assert ticks[0].status == ScheduleTickStatus.SUCCESS


def test_bad_env_fn():
    with seven.TemporaryDirectory() as temp_dir:
        with environ({'DAGSTER_HOME': temp_dir}):
            instance = DagsterInstance.get()

            recon_repo = ReconstructableRepository.for_file(__file__, 'the_repo')
            bad_env_fn = recon_repo.get_reconstructable_schedule('bad_env_fn_schedule')
            result = sync_launch_scheduled_execution(bad_env_fn.get_origin())

            assert isinstance(result, ScheduledExecutionFailed)
            assert (
                'Error occurred during the execution of environment_dict_fn for schedule bad_env_fn_schedule'
                in result.errors[0].to_string()
            )

            run = instance.get_run_by_id(result.run_id)
            assert run.is_failure

            ticks = instance.get_schedule_ticks(bad_env_fn.get_origin_id())
            assert ticks[0].status == ScheduleTickStatus.SUCCESS


def test_bad_should_execute():
    with seven.TemporaryDirectory() as temp_dir:
        with environ({'DAGSTER_HOME': temp_dir}):
            instance = DagsterInstance.get()

            recon_repo = ReconstructableRepository.for_file(__file__, 'the_repo')
            bad_should_execute = recon_repo.get_reconstructable_schedule(
                'bad_should_execute_schedule'
            )

            with pytest.raises(DagsterSubprocessError):
                sync_launch_scheduled_execution(bad_should_execute.get_origin())

            ticks = instance.get_schedule_ticks(bad_should_execute.get_origin_id())
            assert ticks[0].status == ScheduleTickStatus.FAILURE
            assert (
                'Error occurred during the execution of should_execute for schedule bad_should_execute_schedule'
                in ticks[0].error.message
            )


def test_skip():
    with seven.TemporaryDirectory() as temp_dir:
        with environ({'DAGSTER_HOME': temp_dir}):
            instance = DagsterInstance.get()

            recon_repo = ReconstructableRepository.for_file(__file__, 'the_repo')
            skip = recon_repo.get_reconstructable_schedule('skip_schedule')
            result = sync_launch_scheduled_execution(skip.get_origin())

            assert isinstance(result, ScheduledExecutionSkipped)

            ticks = instance.get_schedule_ticks(skip.get_origin_id())
            assert ticks[0].status == ScheduleTickStatus.SKIPPED
