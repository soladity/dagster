import sys
import time
from datetime import datetime

import click
from croniter import croniter_range

from dagster import check
from dagster.core.errors import DagsterLaunchFailedError, DagsterSubprocessError
from dagster.core.events import EngineEventData
from dagster.core.host_representation import (
    ExternalPipeline,
    ExternalScheduleExecutionErrorData,
    PipelineSelector,
    RepositoryLocation,
    RepositoryLocationHandle,
)
from dagster.core.instance import DagsterInstance
from dagster.core.scheduler import (
    ScheduleState,
    ScheduleStatus,
    ScheduleTickData,
    ScheduleTickStatus,
)
from dagster.core.storage.pipeline_run import PipelineRun, PipelineRunStatus, PipelineRunsFilter
from dagster.core.storage.tags import SCHEDULED_EXECUTION_TIME_TAG, check_tags
from dagster.grpc.types import ScheduleExecutionDataMode
from dagster.seven import get_utc_timezone
from dagster.utils import merge_dicts
from dagster.utils.error import serializable_error_info_from_exc_info


class ScheduleTickHolder:
    def __init__(self, tick, instance):
        self._tick = tick
        self._instance = instance

    @property
    def status(self):
        return self._tick.status

    def update_with_status(self, status, **kwargs):
        self._tick = self._tick.with_status(status=status, **kwargs)

    def _write(self):
        self._instance.update_schedule_tick(self._tick)

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        if exception_value and not isinstance(exception_value, KeyboardInterrupt):
            error_data = serializable_error_info_from_exc_info(sys.exc_info())
            self.update_with_status(ScheduleTickStatus.FAILURE, error=error_data)
            self._write()
            return True  # Swallow the exception after logging in the tick DB

        self._write()


@click.command(
    name="run", help="Poll for scheduled runs form all running schedules and launch them",
)
@click.option("--interval", help="How frequently to check for runs to launch", default=30)
def scheduler_run_command(interval):
    execute_scheduler_command(interval)


def execute_scheduler_command(interval):
    while True:
        instance = DagsterInstance.get()
        start_time = datetime.now()
        launch_scheduled_runs(instance)

        time_left = interval - (datetime.now() - start_time).seconds

        if time_left > 0:
            time.sleep(time_left)


def launch_scheduled_runs(instance):
    schedules = [
        s for s in instance.all_stored_schedule_state() if s.status == ScheduleStatus.RUNNING
    ]

    for schedule_state in schedules:
        launch_scheduled_runs_for_schedule(instance, schedule_state)


def launch_scheduled_runs_for_schedule(instance, schedule_state):
    check.inst_param(instance, "instance", DagsterInstance)
    check.inst_param(schedule_state, "schedule_state", ScheduleState)

    latest_tick = instance.get_latest_tick(schedule_state.schedule_origin_id)

    if not latest_tick:
        start_timestamp_utc = schedule_state.start_timestamp
    elif latest_tick.status == ScheduleTickStatus.STARTED:
        # Scheduler was interrupted while performing this tick, re-do it
        start_timestamp_utc = latest_tick.timestamp
    else:
        start_timestamp_utc = latest_tick.timestamp + 1

    start_time_utc = datetime.fromtimestamp(start_timestamp_utc, tz=get_utc_timezone())

    for schedule_time_utc in croniter_range(
        start_time_utc, datetime.now(get_utc_timezone()), schedule_state.cron_schedule
    ):
        if latest_tick and latest_tick.timestamp == schedule_time_utc.timestamp():
            tick = latest_tick

        else:
            tick = instance.create_schedule_tick(
                ScheduleTickData(
                    schedule_origin_id=schedule_state.schedule_origin_id,
                    schedule_name=schedule_state.name,
                    timestamp=schedule_time_utc.timestamp(),
                    cron_schedule=schedule_state.cron_schedule,
                    status=ScheduleTickStatus.STARTED,
                )
            )

        with ScheduleTickHolder(tick, instance) as tick_holder:
            _schedule_run_at_time(instance, schedule_state, schedule_time_utc, tick_holder)


def _schedule_run_at_time(
    instance, schedule_state, schedule_time_utc, tick_holder,
):
    schedule_origin = schedule_state.origin
    schedule_name = schedule_state.name

    repo_location = RepositoryLocation.from_handle(
        RepositoryLocationHandle.create_from_repository_origin(
            schedule_origin.repository_origin, instance,
        )
    )

    repo_dict = repo_location.get_repositories()
    check.invariant(
        len(repo_dict) == 1, "Reconstructed repository location should have exactly one repository",
    )
    external_repo = next(iter(repo_dict.values()))

    external_schedule = external_repo.get_external_schedule(schedule_name)

    pipeline_selector = PipelineSelector(
        location_name=repo_location.name,
        repository_name=external_repo.name,
        pipeline_name=external_schedule.pipeline_name,
        solid_selection=external_schedule.solid_selection,
    )

    subset_pipeline_result = repo_location.get_subset_external_pipeline_result(pipeline_selector)
    external_pipeline = ExternalPipeline(
        subset_pipeline_result.external_pipeline_data, external_repo.handle,
    )

    # Rule out the case where the scheduler crashed between creating a run for this time
    # and launching it
    runs_filter = PipelineRunsFilter(
        tags=merge_dicts(
            PipelineRun.tags_for_schedule(schedule_state),
            {SCHEDULED_EXECUTION_TIME_TAG: schedule_time_utc.isoformat()},
        )
    )
    existing_runs = instance.get_runs(runs_filter)

    run_to_launch = None

    if len(existing_runs):
        check.invariant(len(existing_runs) == 1)

        run = existing_runs[0]

        if run.status != PipelineRunStatus.NOT_STARTED:
            # A run already exists and was launched for this time period,
            # but the scheduler must have crashed before the tick could be put
            # into a SUCCESS state
            return
        run_to_launch = run
    else:
        run_to_launch = _create_scheduler_run(
            instance,
            schedule_time_utc,
            repo_location,
            external_repo,
            external_schedule,
            external_pipeline,
            tick_holder,
        )

    if not run_to_launch:
        check.invariant(
            tick_holder.status != ScheduleTickStatus.STARTED
            and tick_holder.status != ScheduleTickStatus.SUCCESS
        )
        return

    try:
        instance.launch_run(run_to_launch.run_id, external_pipeline)
    except DagsterLaunchFailedError:
        error = serializable_error_info_from_exc_info(sys.exc_info())
        instance.report_engine_event(
            error.message, run_to_launch, EngineEventData.engine_error(error),
        )
        instance.report_run_failed(run_to_launch.run_id)
        raise

    tick_holder.update_with_status(ScheduleTickStatus.SUCCESS, run_id=run_to_launch.run_id)


def _create_scheduler_run(
    instance,
    schedule_time_utc,
    repo_location,
    external_repo,
    external_schedule,
    external_pipeline,
    tick_holder,
):
    schedule_execution_data = repo_location.get_external_schedule_execution_data(
        instance=instance,
        repository_handle=external_repo.handle,
        schedule_name=external_schedule.name,
        schedule_execution_data_mode=ScheduleExecutionDataMode.LAUNCH_SCHEDULED_EXECUTION,
        scheduled_execution_datetime_utc=schedule_time_utc,
    )

    if isinstance(schedule_execution_data, ExternalScheduleExecutionErrorData):
        error = schedule_execution_data.error
        tick_holder.update_with_status(ScheduleTickStatus.FAILURE, error=error)
        return None
    elif not schedule_execution_data.should_execute:
        # Update tick to skipped state and return
        tick_holder.update_with_status(ScheduleTickStatus.SKIPPED)
        return None

    run_config = schedule_execution_data.run_config
    schedule_tags = schedule_execution_data.tags

    execution_plan_errors = []
    execution_plan_snapshot = None

    try:
        external_execution_plan = repo_location.get_external_execution_plan(
            external_pipeline, run_config, external_schedule.mode, step_keys_to_execute=None,
        )
        execution_plan_snapshot = external_execution_plan.execution_plan_snapshot
    except DagsterSubprocessError as e:
        execution_plan_errors.extend(e.subprocess_error_infos)
    except Exception as e:  # pylint: disable=broad-except
        execution_plan_errors.append(serializable_error_info_from_exc_info(sys.exc_info()))

    pipeline_tags = external_pipeline.tags or {}
    check_tags(pipeline_tags, "pipeline_tags")
    tags = merge_dicts(pipeline_tags, schedule_tags)

    tags[SCHEDULED_EXECUTION_TIME_TAG] = schedule_time_utc.isoformat()

    # If the run was scheduled correctly but there was an error creating its
    # run config, enter it into the run DB with a FAILURE status
    possibly_invalid_pipeline_run = instance.create_run(
        pipeline_name=external_schedule.pipeline_name,
        run_id=None,
        run_config=run_config,
        mode=external_schedule.mode,
        solids_to_execute=external_pipeline.solids_to_execute,
        step_keys_to_execute=None,
        solid_selection=external_pipeline.solid_selection,
        status=(
            PipelineRunStatus.FAILURE
            if len(execution_plan_errors) > 0
            else PipelineRunStatus.NOT_STARTED
        ),
        root_run_id=None,
        parent_run_id=None,
        tags=tags,
        pipeline_snapshot=external_pipeline.pipeline_snapshot,
        execution_plan_snapshot=execution_plan_snapshot,
        parent_pipeline_snapshot=external_pipeline.parent_pipeline_snapshot,
    )

    if len(execution_plan_errors) > 0:
        for error in execution_plan_errors:
            instance.report_engine_event(
                error.message, possibly_invalid_pipeline_run, EngineEventData.engine_error(error),
            )
        instance.report_run_failed(possibly_invalid_pipeline_run)

    return possibly_invalid_pipeline_run


def create_scheduler_cli_group():
    group = click.Group(name="scheduler")
    group.add_command(scheduler_run_command)
    return group


scheduler_cli = create_scheduler_cli_group()
