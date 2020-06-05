import os
import re
import subprocess
import sys

import pytest
import yaml
from dagster_cron import SystemCronScheduler

from dagster import ScheduleDefinition, check, file_relative_path
from dagster.core.definitions import lambda_solid, pipeline, repository
from dagster.core.instance import DagsterInstance, InstanceType
from dagster.core.launcher.sync_in_memory_run_launcher import SyncInMemoryRunLauncher
from dagster.core.scheduler import Schedule, ScheduleStatus
from dagster.core.scheduler.scheduler import (
    DagsterScheduleDoesNotExist,
    DagsterScheduleReconciliationError,
    DagsterSchedulerError,
)
from dagster.core.storage.event_log import InMemoryEventLogStorage
from dagster.core.storage.noop_compute_log_manager import NoOpComputeLogManager
from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.core.storage.root import LocalArtifactStorage
from dagster.core.storage.runs import InMemoryRunStorage
from dagster.core.storage.schedules import SqliteScheduleStorage
from dagster.seven import TemporaryDirectory


@pytest.fixture(scope='function')
def restore_cron_tab():
    with TemporaryDirectory() as tempdir:
        crontab_backup = os.path.join(tempdir, "crontab_backup.txt")
        with open(crontab_backup, 'wb+') as f:
            try:
                output = subprocess.check_output(['crontab', '-l'])
                f.write(output)
            except subprocess.CalledProcessError:
                # If a crontab hasn't been created yet, the command fails with a
                # non-zero error code
                pass

        try:
            subprocess.check_output(['crontab', '-r'])
        except subprocess.CalledProcessError:
            # If a crontab hasn't been created yet, the command fails with a
            # non-zero error code
            pass

        yield

        subprocess.check_output(['crontab', crontab_backup])


@pytest.fixture(scope='function')
def unset_dagster_home():
    old_env = os.getenv('DAGSTER_HOME')
    if old_env is not None:
        del os.environ['DAGSTER_HOME']
    yield
    if old_env is not None:
        os.environ['DAGSTER_HOME'] = old_env


@pipeline
def no_config_pipeline():
    @lambda_solid
    def return_hello():
        return 'Hello'

    return return_hello()


schedules_dict = {
    'no_config_pipeline_daily_schedule': ScheduleDefinition(
        name="no_config_pipeline_daily_schedule",
        cron_schedule="0 0 * * *",
        pipeline_name="no_config_pipeline",
        environment_dict={"storage": {"filesystem": None}},
    ),
    'no_config_pipeline_every_min_schedule': ScheduleDefinition(
        name="no_config_pipeline_every_min_schedule",
        cron_schedule="* * * * *",
        pipeline_name="no_config_pipeline",
        environment_dict={"storage": {"filesystem": None}},
    ),
    'default_config_pipeline_every_min_schedule': ScheduleDefinition(
        name="default_config_pipeline_every_min_schedule",
        cron_schedule="* * * * *",
        pipeline_name="no_config_pipeline",
    ),
}


def define_schedules():
    return list(schedules_dict.values())


@repository
def test_repository():
    return [no_config_pipeline] + define_schedules()


@repository(name="test_repository")
def smaller_repository():
    return [no_config_pipeline] + define_schedules()[:-1]


def get_cron_jobs():
    output = subprocess.check_output(['crontab', '-l'])
    return list(filter(None, output.decode('utf-8').strip().split("\n")))


def define_scheduler_instance(tempdir):
    return DagsterInstance(
        instance_type=InstanceType.EPHEMERAL,
        local_artifact_storage=LocalArtifactStorage(tempdir),
        run_storage=InMemoryRunStorage(),
        event_storage=InMemoryEventLogStorage(),
        compute_log_manager=NoOpComputeLogManager(),
        schedule_storage=SqliteScheduleStorage.from_local(os.path.join(tempdir, 'schedules')),
        scheduler=SystemCronScheduler(),
        run_launcher=SyncInMemoryRunLauncher(),
    )


def test_init(restore_cron_tab):  # pylint:disable=unused-argument,redefined-outer-name
    with TemporaryDirectory() as tempdir:
        instance = define_scheduler_instance(tempdir)

        # Initialize scheduler
        instance.reconcile_scheduler_state(
            python_path=sys.executable,
            repository_path=file_relative_path(__file__, '.../repository.yaml'),
            repository=test_repository,
        )

        # Check schedules are saved to disk
        assert 'schedules' in os.listdir(tempdir)

        schedules = instance.all_schedules(test_repository.name)

        for schedule in schedules:
            assert "/bin/python" in schedule.python_path


def test_re_init(restore_cron_tab):  # pylint:disable=unused-argument,redefined-outer-name
    with TemporaryDirectory() as tempdir:
        instance = define_scheduler_instance(tempdir)

        # Initialize scheduler
        instance.reconcile_scheduler_state(
            python_path=sys.executable,
            repository_path=file_relative_path(__file__, '.../repository.yaml'),
            repository=test_repository,
        )

        # Start schedule
        schedule = instance.start_schedule_and_update_storage_state(
            test_repository.name, "no_config_pipeline_every_min_schedule"
        )

        # Re-initialize scheduler
        instance.reconcile_scheduler_state(
            python_path=sys.executable,
            repository_path=file_relative_path(__file__, '.../repository.yaml'),
            repository=test_repository,
        )

        # Check schedules are saved to disk
        assert 'schedules' in os.listdir(tempdir)

        schedules = instance.all_schedules(test_repository.name)

        for schedule in schedules:
            assert "/bin/python" in schedule.python_path


def test_start_and_stop_schedule(
    restore_cron_tab,
):  # pylint:disable=unused-argument,redefined-outer-name
    with TemporaryDirectory() as tempdir:
        instance = define_scheduler_instance(tempdir)

        # Initialize scheduler
        instance.reconcile_scheduler_state(
            python_path=sys.executable,
            repository_path=file_relative_path(__file__, '.../repository.yaml'),
            repository=test_repository,
        )

        schedule_def = test_repository.get_schedule_def("no_config_pipeline_every_min_schedule")

        schedule = instance.start_schedule_and_update_storage_state(
            test_repository.name, "no_config_pipeline_every_min_schedule"
        )

        check.inst_param(schedule, 'schedule', Schedule)
        assert "/bin/python" in schedule.python_path

        assert 'schedules' in os.listdir(tempdir)

        assert "{}.{}.sh".format(test_repository.name, schedule_def.name) in os.listdir(
            os.path.join(tempdir, 'schedules', 'scripts')
        )

        instance.stop_schedule_and_update_storage_state(
            test_repository.name, "no_config_pipeline_every_min_schedule"
        )
        assert "{}.{}.sh".format(test_repository.name, schedule_def.name) not in os.listdir(
            os.path.join(tempdir, 'schedules', 'scripts')
        )


def test_start_non_existent_schedule(
    restore_cron_tab,
):  # pylint:disable=unused-argument,redefined-outer-name
    with TemporaryDirectory() as tempdir:
        instance = define_scheduler_instance(tempdir)

        with pytest.raises(DagsterScheduleDoesNotExist):
            # Initialize scheduler
            instance.start_schedule_and_update_storage_state(test_repository.name, "asdf")


def test_start_schedule_cron_job(
    restore_cron_tab,
):  # pylint:disable=unused-argument,redefined-outer-name
    with TemporaryDirectory() as tempdir:
        instance = define_scheduler_instance(tempdir)

        # Initialize scheduler
        instance.reconcile_scheduler_state(
            python_path=sys.executable,
            repository_path=file_relative_path(__file__, '.../repository.yaml'),
            repository=test_repository,
        )

        instance.start_schedule_and_update_storage_state(
            test_repository.name, "no_config_pipeline_every_min_schedule"
        )
        instance.start_schedule_and_update_storage_state(
            test_repository.name, "no_config_pipeline_daily_schedule"
        )
        instance.start_schedule_and_update_storage_state(
            test_repository.name, "default_config_pipeline_every_min_schedule"
        )

        # Inspect the cron tab
        cron_jobs = get_cron_jobs()

        assert len(cron_jobs) == 3

        for cron_job in cron_jobs:
            match = re.findall(
                r"^(.*?) (/.*) > (.*) 2>&1 # dagster-schedule: test_repository\.(.*)", cron_job
            )
            cron_schedule, command, log_file, schedule_name = match[0]

            schedule_def = schedules_dict[schedule_name]

            # Check cron schedule matches
            if schedule_def.cron_schedule == "0 0 * * *":
                assert cron_schedule == "@daily"
            else:
                assert cron_schedule == schedule_def.cron_schedule

            # Check bash file exists
            assert os.path.isfile(command)

            # Check log file is correct
            assert log_file.endswith("scheduler.log")


def test_remove_schedule_def(
    restore_cron_tab,
):  # pylint:disable=unused-argument,redefined-outer-name
    with TemporaryDirectory() as tempdir:
        instance = define_scheduler_instance(tempdir)

        # Initialize scheduler
        instance.reconcile_scheduler_state(
            python_path=sys.executable,
            repository_path=file_relative_path(__file__, '.../repository.yam'),
            repository=test_repository,
        )

        assert len(instance.all_schedules(repository_name=test_repository.name)) == 3

        instance.reconcile_scheduler_state(
            python_path=sys.executable,
            repository_path=file_relative_path(__file__, '.../repository.yam'),
            repository=smaller_repository,
        )

        assert len(instance.all_schedules(repository_name=test_repository.name)) == 2


def test_add_schedule_def(restore_cron_tab):  # pylint:disable=unused-argument,redefined-outer-name
    with TemporaryDirectory() as tempdir:
        instance = define_scheduler_instance(tempdir)

        # Initialize scheduler
        instance.reconcile_scheduler_state(
            python_path=sys.executable,
            repository_path=file_relative_path(__file__, '.../repository.yam'),
            repository=smaller_repository,
        )

        assert len(instance.all_schedules(repository_name=test_repository.name)) == 2

        instance.reconcile_scheduler_state(
            python_path=sys.executable,
            repository_path=file_relative_path(__file__, '.../repository.yam'),
            repository=test_repository,
        )

        assert len(instance.all_schedules(repository_name=test_repository.name)) == 3


def test_start_and_stop_schedule_cron_tab(
    restore_cron_tab,
):  # pylint:disable=unused-argument,redefined-outer-name
    with TemporaryDirectory() as tempdir:
        instance = define_scheduler_instance(tempdir)

        # Initialize scheduler
        instance.reconcile_scheduler_state(
            python_path=sys.executable,
            repository_path=file_relative_path(__file__, '.../repository.yaml'),
            repository=test_repository,
        )

        # Start schedule
        instance.start_schedule_and_update_storage_state(
            test_repository.name, "no_config_pipeline_every_min_schedule"
        )
        cron_jobs = get_cron_jobs()
        assert len(cron_jobs) == 1

        # Try starting it again
        with pytest.raises(DagsterSchedulerError):
            instance.start_schedule_and_update_storage_state(
                test_repository.name, "no_config_pipeline_every_min_schedule"
            )
        cron_jobs = get_cron_jobs()
        assert len(cron_jobs) == 1

        # Start another schedule
        instance.start_schedule_and_update_storage_state(
            test_repository.name, "no_config_pipeline_daily_schedule"
        )
        cron_jobs = get_cron_jobs()
        assert len(cron_jobs) == 2

        # Stop second schedule
        instance.stop_schedule_and_update_storage_state(
            test_repository.name, "no_config_pipeline_daily_schedule"
        )
        cron_jobs = get_cron_jobs()
        assert len(cron_jobs) == 1

        # Try stopping second schedule again
        instance.stop_schedule_and_update_storage_state(
            test_repository.name, "no_config_pipeline_daily_schedule"
        )
        cron_jobs = get_cron_jobs()
        assert len(cron_jobs) == 1

        # Start second schedule
        instance.start_schedule_and_update_storage_state(
            test_repository.name, "no_config_pipeline_daily_schedule"
        )
        cron_jobs = get_cron_jobs()
        assert len(cron_jobs) == 2

        # Reconcile schedule state, should be in the same state
        instance.reconcile_scheduler_state(
            python_path=sys.executable,
            repository_path=file_relative_path(__file__, '.../repository.yaml'),
            repository=test_repository,
        )
        cron_jobs = get_cron_jobs()
        assert len(cron_jobs) == 2

        instance.start_schedule_and_update_storage_state(
            test_repository.name, "default_config_pipeline_every_min_schedule"
        )
        cron_jobs = get_cron_jobs()
        assert len(cron_jobs) == 3

        # Reconcile schedule state, should be in the same state
        instance.reconcile_scheduler_state(
            python_path=sys.executable,
            repository_path=file_relative_path(__file__, '.../repository.yaml'),
            repository=test_repository,
        )
        cron_jobs = get_cron_jobs()
        assert len(cron_jobs) == 3

        # Stop all schedules
        instance.stop_schedule_and_update_storage_state(
            test_repository.name, "no_config_pipeline_every_min_schedule"
        )
        instance.stop_schedule_and_update_storage_state(
            test_repository.name, "no_config_pipeline_daily_schedule"
        )
        instance.stop_schedule_and_update_storage_state(
            test_repository.name, "default_config_pipeline_every_min_schedule"
        )

        cron_jobs = get_cron_jobs()
        assert len(cron_jobs) == 0

        # Reconcile schedule state, should be in the same state
        instance.reconcile_scheduler_state(
            python_path=sys.executable,
            repository_path=file_relative_path(__file__, '.../repository.yaml'),
            repository=test_repository,
        )
        cron_jobs = get_cron_jobs()
        assert len(cron_jobs) == 0


def test_script_execution(
    restore_cron_tab, unset_dagster_home
):  # pylint:disable=unused-argument,redefined-outer-name
    with TemporaryDirectory() as tempdir:
        os.environ["DAGSTER_HOME"] = tempdir
        config = {
            'scheduler': {'module': 'dagster_cron', 'class': 'SystemCronScheduler', 'config': {}},
            # This needs to synchronously execute to completion when
            # the generated bash script is invoked
            'run_launcher': {
                'module': 'dagster.core.launcher.sync_in_memory_run_launcher',
                'class': 'SyncInMemoryRunLauncher',
            },
        }

        with open(os.path.join(tempdir, 'dagster.yaml'), 'w+') as f:
            f.write(yaml.dump(config))

        instance = DagsterInstance.get()

        # Initialize scheduler
        instance.reconcile_scheduler_state(
            python_path=sys.executable,
            repository_path=file_relative_path(__file__, './repository.yaml'),
            repository=test_repository,
        )

        instance.start_schedule_and_update_storage_state(
            test_repository.name, "no_config_pipeline_every_min_schedule"
        )

        schedule_def = test_repository.get_schedule_def("no_config_pipeline_every_min_schedule")
        script = instance.scheduler._get_bash_script_file_path(  # pylint: disable=protected-access
            instance, test_repository.name, schedule_def
        )

        subprocess.check_output([script], shell=True, env={"DAGSTER_HOME": tempdir})

        runs = instance.get_runs()
        assert len(runs) == 1
        assert runs[0].status == PipelineRunStatus.SUCCESS


def test_start_schedule_fails(
    restore_cron_tab,
):  # pylint:disable=unused-argument,redefined-outer-name
    with TemporaryDirectory() as tempdir:
        instance = define_scheduler_instance(tempdir)

        # Initialize scheduler
        instance.reconcile_scheduler_state(
            python_path=sys.executable,
            repository_path=file_relative_path(__file__, '.../repository.yaml'),
            repository=test_repository,
        )

        schedule_def = test_repository.get_schedule_def("no_config_pipeline_every_min_schedule")

        def raises(*args, **kwargs):
            raise Exception('Patch')

        instance._scheduler._start_cron_job = raises  # pylint: disable=protected-access
        with pytest.raises(Exception, match='Patch'):
            instance.start_schedule_and_update_storage_state(
                test_repository.name, "no_config_pipeline_every_min_schedule"
            )

        schedule = instance.get_schedule_by_name(test_repository.name, schedule_def.name)

        assert schedule.status == ScheduleStatus.STOPPED


def test_start_schedule_unsuccessful(
    restore_cron_tab,
):  # pylint:disable=unused-argument,redefined-outer-name
    with TemporaryDirectory() as tempdir:
        instance = define_scheduler_instance(tempdir)

        # Initialize scheduler
        instance.reconcile_scheduler_state(
            python_path=sys.executable,
            repository_path=file_relative_path(__file__, '.../repository.yaml'),
            repository=test_repository,
        )

        def do_nothing(*_):
            pass

        instance._scheduler._start_cron_job = do_nothing  # pylint: disable=protected-access

        # End schedule
        with pytest.raises(
            DagsterSchedulerError,
            match="Attempted to write cron job for schedule no_config_pipeline_every_min_schedule, "
            "but failed. The scheduler is not running no_config_pipeline_every_min_schedule.",
        ):
            instance.start_schedule_and_update_storage_state(
                test_repository.name, "no_config_pipeline_every_min_schedule"
            )


def test_start_schedule_manual_delete_debug(
    restore_cron_tab, snapshot  # pylint:disable=unused-argument,redefined-outer-name
):
    with TemporaryDirectory() as tempdir:
        instance = define_scheduler_instance(tempdir)

        # Initialize scheduler
        instance.reconcile_scheduler_state(
            python_path="fake path",
            repository_path=file_relative_path(__file__, '.../repository.yaml'),
            repository=test_repository,
        )

        instance.start_schedule_and_update_storage_state(
            test_repository.name, "no_config_pipeline_every_min_schedule"
        )

        # Manually delete the schedule from the crontab
        instance.scheduler._end_cron_job(  # pylint: disable=protected-access
            instance,
            test_repository.name,
            instance.get_schedule_by_name(
                test_repository.name, "no_config_pipeline_every_min_schedule"
            ),
        )

        # Check debug command
        debug_info = instance.scheduler_debug_info()
        assert len(debug_info.errors) == 1

        # Reconcile should fix error
        instance.reconcile_scheduler_state(
            python_path="fake path",
            repository_path=file_relative_path(__file__, '.../repository.yaml'),
            repository=test_repository,
        )
        debug_info = instance.scheduler_debug_info()
        assert len(debug_info.errors) == 0


def test_start_schedule_manual_add_debug(
    restore_cron_tab, snapshot  # pylint:disable=unused-argument,redefined-outer-name
):
    with TemporaryDirectory() as tempdir:
        instance = define_scheduler_instance(tempdir)

        # Initialize scheduler
        instance.reconcile_scheduler_state(
            python_path="fake path",
            repository_path=file_relative_path(__file__, '.../repository.yaml'),
            repository=test_repository,
        )

        # Manually add the schedule from to the crontab
        instance.scheduler._start_cron_job(  # pylint: disable=protected-access
            instance,
            test_repository.name,
            instance.get_schedule_by_name(
                test_repository.name, "no_config_pipeline_every_min_schedule"
            ),
        )

        # Check debug command
        debug_info = instance.scheduler_debug_info()
        assert len(debug_info.errors) == 1

        # Reconcile should fix error
        instance.reconcile_scheduler_state(
            python_path="fake path",
            repository_path=file_relative_path(__file__, '.../repository.yaml'),
            repository=test_repository,
        )
        debug_info = instance.scheduler_debug_info()
        assert len(debug_info.errors) == 0


def test_start_schedule_manual_duplicate_schedules_add_debug(
    restore_cron_tab, snapshot  # pylint:disable=unused-argument,redefined-outer-name
):
    with TemporaryDirectory() as tempdir:
        instance = define_scheduler_instance(tempdir)

        # Initialize scheduler
        instance.reconcile_scheduler_state(
            python_path="fake path",
            repository_path=file_relative_path(__file__, '.../repository.yaml'),
            repository=test_repository,
        )

        instance.start_schedule_and_update_storage_state(
            test_repository.name, "no_config_pipeline_every_min_schedule"
        )

        # Manually add  extra cron tabs
        instance.scheduler._start_cron_job(  # pylint: disable=protected-access
            instance,
            test_repository.name,
            instance.get_schedule_by_name(
                test_repository.name, "no_config_pipeline_every_min_schedule"
            ),
        )
        instance.scheduler._start_cron_job(  # pylint: disable=protected-access
            instance,
            test_repository.name,
            instance.get_schedule_by_name(
                test_repository.name, "no_config_pipeline_every_min_schedule"
            ),
        )

        # Check debug command
        debug_info = instance.scheduler_debug_info()
        assert len(debug_info.errors) == 1

        # Reconcile should fix error
        instance.reconcile_scheduler_state(
            python_path="fake path",
            repository_path=file_relative_path(__file__, '.../repository.yaml'),
            repository=test_repository,
        )
        debug_info = instance.scheduler_debug_info()
        assert len(debug_info.errors) == 0


def test_stop_schedule_fails(
    restore_cron_tab,  # pylint:disable=unused-argument,redefined-outer-name
):
    with TemporaryDirectory() as tempdir:
        instance = define_scheduler_instance(tempdir)

        # Initialize scheduler
        instance.reconcile_scheduler_state(
            python_path=sys.executable,
            repository_path=file_relative_path(__file__, '.../repository.yaml'),
            repository=test_repository,
        )

        schedule_def = test_repository.get_schedule_def("no_config_pipeline_every_min_schedule")

        def raises(*args, **kwargs):
            raise Exception('Patch')

        instance._scheduler._end_cron_job = raises  # pylint: disable=protected-access

        schedule = instance.start_schedule_and_update_storage_state(
            test_repository.name, "no_config_pipeline_every_min_schedule"
        )

        check.inst_param(schedule, 'schedule', Schedule)
        assert "/bin/python" in schedule.python_path

        assert 'schedules' in os.listdir(tempdir)

        assert "{}.{}.sh".format(test_repository.name, schedule_def.name) in os.listdir(
            os.path.join(tempdir, 'schedules', 'scripts')
        )

        # End schedule
        with pytest.raises(Exception, match='Patch'):
            instance.stop_schedule_and_update_storage_state(
                test_repository.name, "no_config_pipeline_every_min_schedule"
            )

        schedule = instance.get_schedule_by_name(test_repository.name, schedule_def.name)

        assert schedule.status == ScheduleStatus.RUNNING


def test_stop_schedule_unsuccessful(
    restore_cron_tab,
):  # pylint:disable=unused-argument,redefined-outer-name
    with TemporaryDirectory() as tempdir:
        instance = define_scheduler_instance(tempdir)

        # Initialize scheduler
        instance.reconcile_scheduler_state(
            python_path=sys.executable,
            repository_path=file_relative_path(__file__, '.../repository.yaml'),
            repository=test_repository,
        )

        def do_nothing(*_):
            pass

        instance._scheduler._end_cron_job = do_nothing  # pylint: disable=protected-access

        instance.start_schedule_and_update_storage_state(
            test_repository.name, "no_config_pipeline_every_min_schedule"
        )

        # End schedule
        with pytest.raises(
            DagsterSchedulerError,
            match="Attempted to remove existing cron job for schedule "
            "no_config_pipeline_every_min_schedule, but failed. There are still 1 jobs running for "
            "the schedule.",
        ):
            instance.stop_schedule_and_update_storage_state(
                test_repository.name, "no_config_pipeline_every_min_schedule"
            )


def test_wipe(restore_cron_tab):  # pylint:disable=unused-argument,redefined-outer-name
    with TemporaryDirectory() as tempdir:
        instance = define_scheduler_instance(tempdir)

        # Initialize scheduler
        instance.reconcile_scheduler_state(
            python_path=sys.executable,
            repository_path=file_relative_path(__file__, '.../repository.yaml'),
            repository=test_repository,
        )

        # Start schedule
        instance.start_schedule_and_update_storage_state(
            test_repository.name, "no_config_pipeline_every_min_schedule"
        )

        # Wipe scheduler
        instance.wipe_all_schedules()

        # Check schedules are wiped
        assert instance.all_schedules(test_repository.name) == []


def test_log_directory(restore_cron_tab):  # pylint:disable=unused-argument,redefined-outer-name
    with TemporaryDirectory() as tempdir:

        instance = define_scheduler_instance(tempdir)
        schedule_log_path = instance.logs_path_for_schedule(
            test_repository.name, "no_config_pipeline_every_min_schedule"
        )

        assert schedule_log_path.endswith(
            "/schedules/logs/{repository_name}/{schedule_name}/scheduler.log".format(
                repository_name=test_repository.name,
                schedule_name="no_config_pipeline_every_min_schedule",
            )
        )

        # Initialize scheduler
        instance.reconcile_scheduler_state(
            python_path=sys.executable,
            repository_path=file_relative_path(__file__, '.../repository.yaml'),
            repository=test_repository,
        )

        # Start schedule
        instance.start_schedule_and_update_storage_state(
            test_repository.name, "no_config_pipeline_every_min_schedule"
        )

        # Wipe scheduler
        instance.wipe_all_schedules()

        # Check schedules are wiped
        assert instance.all_schedules(test_repository.name) == []


def test_reconcile_failure(restore_cron_tab):  # pylint:disable=unused-argument,redefined-outer-name
    with TemporaryDirectory() as tempdir:
        instance = define_scheduler_instance(tempdir)
        instance.reconcile_scheduler_state(
            python_path=sys.executable,
            repository_path=file_relative_path(__file__, '.../repository.yam'),
            repository=test_repository,
        )
        instance.start_schedule_and_update_storage_state(
            test_repository.name, "no_config_pipeline_every_min_schedule"
        )

        def failed_start_job(*_):
            raise DagsterSchedulerError("Failed to start")

        def failed_end_job(*_):
            raise DagsterSchedulerError("Failed to stop")

        instance._scheduler.start_schedule = failed_start_job  # pylint: disable=protected-access
        instance._scheduler.stop_schedule = failed_end_job  # pylint: disable=protected-access

        # Initialize scheduler
        with pytest.raises(
            DagsterScheduleReconciliationError,
            match="Error 1: Failed to stop\n    Error 2: Failed to stop\n    Error 3: Failed to stop",
        ):
            instance.reconcile_scheduler_state(
                python_path=sys.executable,
                repository_path=file_relative_path(__file__, '.../repository.yam'),
                repository=test_repository,
            )


def test_reconcile_failure_when_deleting_schedule_def(
    restore_cron_tab,
):  # pylint:disable=unused-argument,redefined-outer-name
    with TemporaryDirectory() as tempdir:
        instance = define_scheduler_instance(tempdir)

        # Initialize scheduler
        instance.reconcile_scheduler_state(
            python_path=sys.executable,
            repository_path=file_relative_path(__file__, '.../repository.yam'),
            repository=test_repository,
        )

        assert len(instance.all_schedules(repository_name=test_repository.name)) == 3

        def failed_end_job(*_):
            raise DagsterSchedulerError("Failed to stop")

        instance._scheduler.stop_schedule_and_delete_from_storage = (  # pylint: disable=protected-access
            failed_end_job
        )

        with pytest.raises(
            DagsterScheduleReconciliationError, match="Error 1: Failed to stop",
        ):
            instance.reconcile_scheduler_state(
                python_path=sys.executable,
                repository_path=file_relative_path(__file__, '.../repository.yam'),
                repository=smaller_repository,
            )
