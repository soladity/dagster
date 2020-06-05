import yaml
from dagster_graphql import dauphin
from dagster_graphql.implementation.fetch_schedules import (
    get_dagster_schedule_def,
    start_schedule,
    stop_schedule,
)
from dagster_graphql.schema.errors import (
    DauphinPythonError,
    DauphinScheduleNotFoundError,
    DauphinSchedulerNotDefinedError,
)

from dagster import check
from dagster.core.definitions import ScheduleDefinition, ScheduleExecutionContext
from dagster.core.errors import ScheduleExecutionError, user_code_error_boundary
from dagster.core.host_representation import ExternalSchedule
from dagster.core.scheduler import Schedule, ScheduleTickStatus
from dagster.core.scheduler.scheduler import ScheduleTickStatsSnapshot
from dagster.core.storage.pipeline_run import PipelineRunsFilter


class DauphinScheduleStatus(dauphin.Enum):
    class Meta(object):
        name = 'ScheduleStatus'

    RUNNING = 'RUNNING'
    STOPPED = 'STOPPED'
    ENDED = 'ENDED'


class DauphinSchedulerOrError(dauphin.Union):
    class Meta(object):
        name = 'SchedulerOrError'
        types = ('Scheduler', DauphinSchedulerNotDefinedError, 'PythonError')


class DauphinScheduleOrError(dauphin.Union):
    class Meta(object):
        name = 'ScheduleOrError'
        types = ('RunningSchedule', DauphinScheduleNotFoundError, 'PythonError')


class DauphinScheduleDefinition(dauphin.ObjectType):
    class Meta(object):
        name = 'ScheduleDefinition'

    name = dauphin.NonNull(dauphin.String)
    cron_schedule = dauphin.NonNull(dauphin.String)

    pipeline_name = dauphin.NonNull(dauphin.String)
    solid_subset = dauphin.List(dauphin.String)
    mode = dauphin.NonNull(dauphin.String)
    run_config_yaml = dauphin.Field(dauphin.String)
    partition_set = dauphin.Field('PartitionSet')

    def resolve_run_config_yaml(self, graphene_info):
        schedule_def = self._schedule_def
        schedule_context = ScheduleExecutionContext(graphene_info.context.instance)
        try:
            with user_code_error_boundary(
                ScheduleExecutionError,
                lambda: 'Error occurred during the execution of environment_dict_fn for schedule '
                '{schedule_name}'.format(schedule_name=schedule_def.name),
            ):
                environment_config = schedule_def.get_environment_dict(schedule_context)
        except ScheduleExecutionError:
            return None

        run_config_yaml = yaml.dump(environment_config, default_flow_style=False)
        return run_config_yaml if run_config_yaml else ''

    def resolve_partition_set(self, graphene_info):
        if self._external_schedule.partition_set_name is None:
            return None

        external_partition_set = (
            graphene_info.context.get_repository_location(
                self._external_schedule.handle.location_name
            )
            .get_repository(self._external_schedule.handle.repository_name)
            .get_partition_set(self._external_schedule.partition_set_name)
        )

        return graphene_info.schema.type_named('PartitionSet')(
            external_partition_set=external_partition_set,
            partion_set_def=self._schedule_def.get_partition_set(),
        )

    def __init__(self, schedule_def, external_schedule):
        self._schedule_def = check.inst_param(schedule_def, 'schedule_def', ScheduleDefinition)
        self._external_schedule = check.inst_param(
            external_schedule, 'external_schedule', ExternalSchedule
        )

        super(DauphinScheduleDefinition, self).__init__(
            name=external_schedule.name,
            cron_schedule=external_schedule.cron_schedule,
            pipeline_name=external_schedule.pipeline_name,
            solid_subset=external_schedule.solid_subset,
            mode=external_schedule.mode,
        )


DauphinScheduleTickStatus = dauphin.Enum.from_enum(ScheduleTickStatus)


class DauphinScheduleTick(dauphin.ObjectType):
    class Meta(object):
        name = 'ScheduleTick'

    tick_id = dauphin.NonNull(dauphin.String)
    status = dauphin.NonNull('ScheduleTickStatus')
    timestamp = dauphin.NonNull(dauphin.Float)
    tick_specific_data = dauphin.Field('ScheduleTickSpecificData')


class DauphinScheduleTickSuccessData(dauphin.ObjectType):
    class Meta(object):
        name = 'ScheduleTickSuccessData'

    run = dauphin.Field('PipelineRun')


class DauphinScheduleTickFailureData(dauphin.ObjectType):
    class Meta(object):
        name = 'ScheduleTickFailureData'

    error = dauphin.NonNull('PythonError')


class DauphinScheduleTickSpecificData(dauphin.Union):
    class Meta(object):
        name = 'ScheduleTickSpecificData'
        types = (
            DauphinScheduleTickSuccessData,
            DauphinScheduleTickFailureData,
        )


def tick_specific_data_from_dagster_tick(graphene_info, tick):
    if tick.status == ScheduleTickStatus.SUCCESS:
        run_id = tick.run_id
        run = None
        if graphene_info.context.instance.has_run(run_id):
            run = graphene_info.schema.type_named('PipelineRun')(
                graphene_info.context.instance.get_run_by_id(run_id)
            )
        return graphene_info.schema.type_named('ScheduleTickSuccessData')(run=run)
    elif tick.status == ScheduleTickStatus.FAILURE:
        error = tick.error
        return graphene_info.schema.type_named('ScheduleTickFailureData')(error=error)


class DauphinScheduleTickStatsSnapshot(dauphin.ObjectType):
    class Meta(object):
        name = 'ScheduleTickStatsSnapshot'

    ticks_started = dauphin.NonNull(dauphin.Int)
    ticks_succeeded = dauphin.NonNull(dauphin.Int)
    ticks_skipped = dauphin.NonNull(dauphin.Int)
    ticks_failed = dauphin.NonNull(dauphin.Int)

    def __init__(self, stats):
        super(DauphinScheduleTickStatsSnapshot, self).__init__(
            ticks_started=stats.ticks_started,
            ticks_succeeded=stats.ticks_succeeded,
            ticks_skipped=stats.ticks_skipped,
            ticks_failed=stats.ticks_failed,
        )
        self._stats = check.inst_param(stats, 'stats', ScheduleTickStatsSnapshot)


class DauphinRunningSchedule(dauphin.ObjectType):
    class Meta(object):
        name = 'RunningSchedule'

    schedule_definition = dauphin.NonNull('ScheduleDefinition')
    python_path = dauphin.Field(dauphin.String)
    repository_path = dauphin.Field(dauphin.String)
    status = dauphin.NonNull('ScheduleStatus')
    runs = dauphin.Field(dauphin.non_null_list('PipelineRun'), limit=dauphin.Int())
    runs_count = dauphin.NonNull(dauphin.Int)
    ticks = dauphin.Field(dauphin.non_null_list('ScheduleTick'), limit=dauphin.Int())
    ticks_count = dauphin.NonNull(dauphin.Int)
    stats = dauphin.NonNull('ScheduleTickStatsSnapshot')
    logs_path = dauphin.NonNull(dauphin.String)
    running_job_count = dauphin.NonNull(dauphin.Int)

    def __init__(self, graphene_info, schedule):
        self._schedule = check.inst_param(schedule, 'schedule', Schedule)
        external_repository = graphene_info.context.legacy_external_repository
        external_schedule = external_repository.get_external_schedule(schedule.name)
        super(DauphinRunningSchedule, self).__init__(
            schedule_definition=graphene_info.schema.type_named('ScheduleDefinition')(
                schedule_def=get_dagster_schedule_def(graphene_info, schedule.name),
                external_schedule=external_schedule,
            ),
            status=schedule.status,
            python_path=schedule.python_path,
            repository_path=schedule.repository_path,
        )

    def resolve_running_job_count(self, graphene_info):
        external_repository = graphene_info.context.legacy_external_repository
        running_job_count = graphene_info.context.instance.running_job_count(
            external_repository.name, self._schedule.name
        )
        return running_job_count

    def resolve_stats(self, graphene_info):
        external_repository = graphene_info.context.legacy_external_repository
        stats = graphene_info.context.instance.get_schedule_tick_stats_by_schedule(
            external_repository.name, self._schedule.name
        )
        return graphene_info.schema.type_named('ScheduleTickStatsSnapshot')(stats)

    def resolve_ticks(self, graphene_info, limit=None):
        external_repository = graphene_info.context.legacy_external_repository

        # TODO: Add cursor limit argument to get_schedule_ticks_by_schedule
        # https://github.com/dagster-io/dagster/issues/2291
        ticks = graphene_info.context.instance.get_schedule_ticks_by_schedule(
            external_repository.name, self._schedule.name
        )

        if not limit:
            tick_subset = ticks
        else:
            tick_subset = ticks[:limit]

        return [
            graphene_info.schema.type_named('ScheduleTick')(
                tick_id=tick.tick_id,
                status=tick.status,
                timestamp=tick.timestamp,
                tick_specific_data=tick_specific_data_from_dagster_tick(graphene_info, tick),
            )
            for tick in tick_subset
        ]

    def resolve_ticks_count(self, graphene_info):
        external_repository = graphene_info.context.legacy_external_repository
        ticks = graphene_info.context.instance.get_schedule_ticks_by_schedule(
            external_repository.name, self._schedule.name
        )
        return len(ticks)

    def resolve_runs(self, graphene_info, **kwargs):
        return [
            graphene_info.schema.type_named('PipelineRun')(r)
            for r in graphene_info.context.instance.get_runs(
                filters=PipelineRunsFilter.for_schedule(self._schedule), limit=kwargs.get('limit'),
            )
        ]

    def resolve_runs_count(self, graphene_info):
        return graphene_info.context.instance.get_runs_count(
            filters=PipelineRunsFilter.for_schedule(self._schedule)
        )


class DauphinScheduler(dauphin.ObjectType):
    class Meta(object):
        name = 'Scheduler'

    runningSchedules = dauphin.non_null_list('RunningSchedule')


class DauphinRunningScheduleResult(dauphin.ObjectType):
    class Meta(object):
        name = 'RunningScheduleResult'

    schedule = dauphin.NonNull('RunningSchedule')


class DauphinScheduleMutationResult(dauphin.Union):
    class Meta(object):
        name = 'ScheduleMutationResult'
        types = (DauphinPythonError, DauphinRunningScheduleResult)


class DauphinStartScheduleMutation(dauphin.Mutation):
    class Meta(object):
        name = 'StartScheduleMutation'

    class Arguments(object):
        schedule_name = dauphin.NonNull(dauphin.String)

    Output = dauphin.NonNull('ScheduleMutationResult')

    def mutate(self, graphene_info, schedule_name):
        return start_schedule(graphene_info, schedule_name)


class DauphinStopRunningScheduleMutation(dauphin.Mutation):
    class Meta(object):
        name = 'StopRunningScheduleMutation'

    class Arguments(object):
        schedule_name = dauphin.NonNull(dauphin.String)

    Output = dauphin.NonNull('ScheduleMutationResult')

    def mutate(self, graphene_info, schedule_name):
        return stop_schedule(graphene_info, schedule_name)
