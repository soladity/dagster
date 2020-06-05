import io
import os
import shutil
import stat

import six
from crontab import CronTab

from dagster import DagsterInstance, check, seven, utils
from dagster.core.scheduler import DagsterSchedulerError, Scheduler
from dagster.serdes import ConfigurableClass


class SystemCronScheduler(Scheduler, ConfigurableClass):
    '''Scheduler implementation that uses the local systems cron. Only works on unix systems that
    have cron.

    Enable this scheduler by adding it to your ``dagster.yaml`` in ``$DAGSTER_HOME``.
    '''

    def __init__(
        self, inst_data=None,
    ):
        self._inst_data = inst_data
        self._cron_tab = CronTab(user=True)

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return {}

    @staticmethod
    def from_config_value(inst_data, config_value):
        return SystemCronScheduler(inst_data=inst_data)

    def debug_info(self):
        return "Running Cron Jobs:\n{jobs}\n".format(
            jobs="\n".join(
                [str(job) for job in self._cron_tab if 'dagster-schedule:' in job.comment]
            )
        )

    def start_schedule(self, instance, repository_name, schedule_name):
        check.inst_param(instance, 'instance', DagsterInstance)
        check.str_param(repository_name, 'repository_name')
        check.str_param(schedule_name, 'schedule_name')

        schedule = self._get_schedule_by_name(instance, repository_name, schedule_name)

        # If the cron job already exists, remove it. This prevents duplicate entries.
        # Then, add a new cron job to the cron tab.
        if self.running_schedule_count(repository_name, schedule.name) > 0:
            self._end_cron_job(instance, repository_name, schedule)

        self._start_cron_job(instance, repository_name, schedule)

        # Verify that the cron job is running
        running_schedule_count = self.running_schedule_count(repository_name, schedule.name)
        if running_schedule_count == 0:
            raise DagsterSchedulerError(
                "Attempted to write cron job for schedule "
                "{schedule_name}, but failed. "
                "The scheduler is not running {schedule_name}.".format(schedule_name=schedule.name)
            )
        elif running_schedule_count > 1:
            raise DagsterSchedulerError(
                "Attempted to write cron job for schedule "
                "{schedule_name}, but duplicate cron jobs were found. "
                "There are {running_schedule_count} jobs running for the schedule."
                "To resolve, run `dagster schedule up`, or edit the cron tab to "
                "remove duplicate schedules".format(
                    schedule_name=schedule.name, running_schedule_count=running_schedule_count
                )
            )

    def stop_schedule(self, instance, repository_name, schedule_name):
        check.inst_param(instance, 'instance', DagsterInstance)
        check.str_param(repository_name, 'repository_name')
        check.str_param(schedule_name, 'schedule_name')

        schedule = self._get_schedule_by_name(instance, repository_name, schedule_name)

        self._end_cron_job(instance, repository_name, schedule)

        # Verify that the cron job has been removed
        running_schedule_count = self.running_schedule_count(repository_name, schedule.name)
        if running_schedule_count > 0:
            raise DagsterSchedulerError(
                "Attempted to remove existing cron job for schedule "
                "{schedule_name}, but failed. "
                "There are still {running_schedule_count} jobs running for the schedule.".format(
                    schedule_name=schedule.name, running_schedule_count=running_schedule_count
                )
            )

    def wipe(self, instance):
        # Note: This method deletes schedules from ALL repositories
        check.inst_param(instance, 'instance', DagsterInstance)

        # Delete all script files
        script_directory = os.path.join(instance.schedules_directory(), "scripts")
        if os.path.isdir(script_directory):
            shutil.rmtree(script_directory)

        # Delete all logs
        logs_directory = os.path.join(instance.schedules_directory(), "logs")
        if os.path.isdir(logs_directory):
            shutil.rmtree(logs_directory)

        # Remove all cron jobs
        for job in self._cron_tab:
            if 'dagster-schedule:' in job.comment:
                self._cron_tab.remove_all(comment=job.comment)

        self._cron_tab.write()

    def _get_bash_script_file_path(self, instance, repository_name, schedule):
        check.inst_param(instance, 'instance', DagsterInstance)
        check.str_param(repository_name, 'repository_name')

        script_directory = os.path.join(instance.schedules_directory(), "scripts")
        utils.mkdir_p(script_directory)

        script_file_name = "{}.{}.sh".format(repository_name, schedule.name)
        return os.path.join(script_directory, script_file_name)

    def _cron_tag_for_schedule(self, repository_name, schedule_name):
        return 'dagster-schedule: {repository_name}.{schedule_name}'.format(
            repository_name=repository_name, schedule_name=schedule_name
        )

    def _get_command(self, script_file, instance, repository_name, schedule):
        schedule_log_file_path = self.get_logs_path(instance, repository_name, schedule.name)
        command = "{script_file} > {schedule_log_file_path} 2>&1".format(
            script_file=script_file, schedule_log_file_path=schedule_log_file_path
        )

        return command

    def _start_cron_job(self, instance, repository_name, schedule):
        script_file = self._write_bash_script_to_file(instance, repository_name, schedule)
        command = self._get_command(script_file, instance, repository_name, schedule)

        job = self._cron_tab.new(
            command=command,
            comment='dagster-schedule: {repository_name}.{schedule_name}'.format(
                repository_name=repository_name, schedule_name=schedule.name
            ),
        )
        job.setall(schedule.cron_schedule)
        self._cron_tab.write()

    def _end_cron_job(self, instance, repository_name, schedule):
        self._cron_tab.remove_all(
            comment=self._cron_tag_for_schedule(repository_name, schedule.name)
        )
        self._cron_tab.write()

        script_file = self._get_bash_script_file_path(instance, repository_name, schedule)
        if os.path.isfile(script_file):
            os.remove(script_file)

    def running_schedule_count(self, repository_name, schedule_name):
        cron_tab = CronTab(user=True)
        matching_jobs = cron_tab.find_comment(
            self._cron_tag_for_schedule(repository_name, schedule_name)
        )

        return len(list(matching_jobs))

    def _get_or_create_logs_directory(self, instance, repository_name, schedule_name):
        check.inst_param(instance, 'instance', DagsterInstance)
        check.str_param(repository_name, 'repository_name')
        check.str_param(schedule_name, 'schedule_name')

        logs_directory = os.path.join(
            instance.schedules_directory(), "logs", repository_name, schedule_name
        )
        if not os.path.isdir(logs_directory):
            utils.mkdir_p(logs_directory)

        return logs_directory

    def get_logs_path(self, instance, repository_name, schedule_name):
        check.inst_param(instance, 'instance', DagsterInstance)
        check.str_param(repository_name, 'repository_name')
        check.str_param(schedule_name, 'schedule_name')

        logs_directory = self._get_or_create_logs_directory(
            instance, repository_name, schedule_name
        )
        return os.path.join(logs_directory, 'scheduler.log')

    def _write_bash_script_to_file(self, instance, repository_name, schedule):
        # Get path to store bash script
        script_file = self._get_bash_script_file_path(instance, repository_name, schedule)

        # Get path to store schedule attempt logs
        logs_directory = self._get_or_create_logs_directory(
            instance, repository_name, schedule.name
        )
        schedule_log_file_name = "{}_{}.result".format("${RUN_DATE}", schedule.name)
        schedule_log_file_path = os.path.join(logs_directory, schedule_log_file_name)

        # Environment information needed for execution
        dagster_graphql_path = os.path.join(
            os.path.dirname(schedule.python_path), 'dagster-graphql'
        )
        dagster_home = os.getenv('DAGSTER_HOME')

        script_contents = '''
            #!/bin/bash
            export DAGSTER_HOME={dagster_home}
            export LANG=en_US.UTF-8
            {env_vars}

            export RUN_DATE=$(date "+%Y%m%dT%H%M%S")

            {dagster_graphql_path} -p launchScheduledExecution -v '{variables}' -y "{repo_path}" --output "{result_file}"
        '''.format(
            dagster_graphql_path=dagster_graphql_path,
            repo_path=schedule.repository_path,
            variables=seven.json.dumps({"scheduleName": schedule.name}),
            result_file=schedule_log_file_path,
            dagster_home=dagster_home,
            env_vars="\n".join(
                [
                    "export {key}={value}".format(key=key, value=value)
                    for key, value in schedule.environment_vars.items()
                ]
            ),
        )

        with io.open(script_file, 'w', encoding='utf-8') as f:
            f.write(six.text_type(script_contents))

        st = os.stat(script_file)
        os.chmod(script_file, st.st_mode | stat.S_IEXEC)

        return script_file
