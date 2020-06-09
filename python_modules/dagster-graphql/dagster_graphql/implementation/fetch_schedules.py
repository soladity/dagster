from graphql.execution.base import ResolveInfo

from dagster import check
from dagster.core.definitions.schedule import ScheduleExecutionContext
from dagster.core.errors import ScheduleExecutionError, user_code_error_boundary
from dagster.core.storage.tags import check_tags
from dagster.utils import merge_dicts

from .utils import (
    ExecutionMetadata,
    ExecutionParams,
    UserFacingGraphQLError,
    capture_dauphin_error,
    legacy_pipeline_selector,
)


@capture_dauphin_error
def start_schedule(graphene_info, schedule_name):
    external_repository = graphene_info.context.legacy_external_repository
    instance = graphene_info.context.instance
    schedule = instance.start_schedule_and_update_storage_state(
        external_repository.get_external_schedule(schedule_name)
    )
    return graphene_info.schema.type_named('RunningScheduleResult')(
        schedule=graphene_info.schema.type_named('RunningSchedule')(
            graphene_info, schedule=schedule
        )
    )


@capture_dauphin_error
def stop_schedule(graphene_info, schedule_name):
    external_repository = graphene_info.context.legacy_external_repository
    instance = graphene_info.context.instance
    schedule = instance.stop_schedule_and_update_storage_state(
        external_repository.get_external_schedule(schedule_name).get_reconstruction_id()
    )
    return graphene_info.schema.type_named('RunningScheduleResult')(
        schedule=graphene_info.schema.type_named('RunningSchedule')(
            graphene_info, schedule=schedule
        )
    )


@capture_dauphin_error
def get_scheduler_or_error(graphene_info):
    instance = graphene_info.context.instance

    if not instance.scheduler:
        raise UserFacingGraphQLError(graphene_info.schema.type_named('SchedulerNotDefinedError')())

    runningSchedules = [
        graphene_info.schema.type_named('RunningSchedule')(graphene_info, schedule=s)
        for s in instance.all_stored_schedule_state()
    ]

    return graphene_info.schema.type_named('Scheduler')(runningSchedules=runningSchedules)


@capture_dauphin_error
def get_schedule_or_error(graphene_info, schedule_name):
    external_repository = graphene_info.context.legacy_external_repository
    instance = graphene_info.context.instance

    schedule = instance.get_schedule_state(
        external_repository.get_external_schedule(schedule_name).get_reconstruction_id()
    )
    if not schedule:
        raise UserFacingGraphQLError(
            graphene_info.schema.type_named('ScheduleNotFoundError')(schedule_name=schedule_name)
        )

    return graphene_info.schema.type_named('RunningSchedule')(graphene_info, schedule=schedule)


def execution_params_for_schedule(graphene_info, schedule_def, pipeline_def):
    schedule_context = ScheduleExecutionContext(graphene_info.context.instance)

    # Get environment_dict
    with user_code_error_boundary(
        ScheduleExecutionError,
        lambda: 'Error occurred during the execution of environment_dict_fn for schedule '
        '{schedule_name}'.format(schedule_name=schedule_def.name),
    ):
        environment_dict = schedule_def.get_environment_dict(schedule_context)

    # Get tags
    with user_code_error_boundary(
        ScheduleExecutionError,
        lambda: 'Error occurred during the execution of tags_fn for schedule '
        '{schedule_name}'.format(schedule_name=schedule_def.name),
    ):
        schedule_tags = schedule_def.get_tags(schedule_context)

    pipeline_tags = pipeline_def.tags or {}
    check_tags(pipeline_tags, 'pipeline_tags')
    tags = merge_dicts(pipeline_tags, schedule_tags)

    mode = schedule_def.mode

    return ExecutionParams(
        selector=legacy_pipeline_selector(
            graphene_info.context, schedule_def.pipeline_name, schedule_def.solid_selection
        ),
        environment_dict=environment_dict,
        mode=mode,
        execution_metadata=ExecutionMetadata(tags=tags, run_id=None),
        step_keys=None,
    )


def get_dagster_schedule_def(graphene_info, schedule_name):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.str_param(schedule_name, 'schedule_name')

    # TODO: Serialize schedule as ExternalScheduleData and add to ExternalRepositoryData
    repository = graphene_info.context.legacy_get_repository_definition()
    schedule_definition = repository.get_schedule_def(schedule_name)
    return schedule_definition


def get_dagster_schedule(graphene_info, schedule_name):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.str_param(schedule_name, 'schedule_name')

    external_repository = graphene_info.context.legacy_external_repository

    instance = graphene_info.context.instance
    if not instance.scheduler:
        raise UserFacingGraphQLError(graphene_info.schema.type_named('SchedulerNotDefinedError')())

    schedule = instance.get_schedule_state(
        external_repository.get_external_schedule(schedule_name).get_reconstruction_id()
    )
    if not schedule:
        raise UserFacingGraphQLError(
            graphene_info.schema.type_named('ScheduleNotFoundError')(schedule_name=schedule_name)
        )

    return schedule
