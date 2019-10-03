import os
import sys

from dagster_cron import SystemCronScheduler

from dagster import ScheduleDefinition, check
from dagster.core.instance import DagsterInstance
from dagster.core.scheduler import Schedule, SchedulerHandle
from dagster.seven import TemporaryDirectory


class MockSystemCronScheduler(SystemCronScheduler):
    '''Overwrite _start_cron_job and _end_crob_job to prevent polluting
    the user's crontab during tests
    '''

    def _start_cron_job(self, schedule):
        self._write_bash_script_to_file(schedule)

    def _end_cron_job(self, schedule):
        script_file = self._get_bash_script_file_path(schedule)
        if os.path.isfile(script_file):
            os.remove(script_file)


def define_scheduler(artifacts_dir, repository_name):
    no_config_pipeline_daily_schedule = ScheduleDefinition(
        name="no_config_pipeline_daily_schedule",
        cron_schedule="0 0 * * *",
        execution_params={
            "environmentConfigData": {"storage": {"filesystem": None}},
            "selector": {"name": "no_config_pipeline", "solidSubset": None},
            "mode": "default",
        },
    )

    no_config_pipeline_every_min_schedule = ScheduleDefinition(
        name="no_config_pipeline_every_min_schedule",
        cron_schedule="* * * * *",
        execution_params={
            "environmentConfigData": {"storage": {"filesystem": None}},
            "selector": {"name": "no_config_pipeline", "solidSubset": None},
            "mode": "default",
        },
    )

    return SchedulerHandle(
        scheduler_type=MockSystemCronScheduler,
        schedule_defs=[no_config_pipeline_daily_schedule, no_config_pipeline_every_min_schedule],
        repository_name=repository_name,
        artifacts_dir=artifacts_dir,
    )


def test_init():
    with TemporaryDirectory() as tempdir:
        instance = DagsterInstance.local_temp(tempdir=tempdir)
        scheduler_handle = define_scheduler(instance.schedules_directory(), 'test_repository')
        assert scheduler_handle

        # Initialize scheduler
        scheduler_handle.up(python_path=sys.executable, repository_path="")
        scheduler = scheduler_handle.get_scheduler()

        # Check schedules are saved to disk
        assert 'schedules' in os.listdir(tempdir)

        schedules = scheduler.all_schedules()

        for schedule in schedules:
            assert "/bin/python" in schedule.python_path

            assert "{}_{}.json".format(schedule.name, schedule.schedule_id) in os.listdir(
                os.path.join(tempdir, 'schedules', 'test_repository')
            )


def test_start_and_stop_schedule():
    with TemporaryDirectory() as tempdir:

        instance = DagsterInstance.local_temp(tempdir=tempdir)
        scheduler_handle = define_scheduler(instance.schedules_directory(), 'test_repository')
        assert scheduler_handle

        # Initialize scheduler
        scheduler_handle.up(python_path=sys.executable, repository_path="")
        scheduler = scheduler_handle.get_scheduler()
        schedule_def = scheduler_handle.get_schedule_def_by_name(
            "no_config_pipeline_every_min_schedule"
        )

        # Start schedule
        schedule = scheduler.start_schedule("no_config_pipeline_every_min_schedule")

        check.inst_param(schedule, 'schedule', Schedule)
        assert "/bin/python" in schedule.python_path

        assert 'schedules' in os.listdir(tempdir)

        assert "{}_{}.sh".format(schedule_def.name, schedule.schedule_id) in os.listdir(
            os.path.join(tempdir, 'schedules')
        )

        # End schedule
        scheduler.stop_schedule("no_config_pipeline_every_min_schedule")
        assert "{}_{}.sh".format(schedule_def.name, schedule.schedule_id) not in os.listdir(
            os.path.join(tempdir, 'schedules')
        )
