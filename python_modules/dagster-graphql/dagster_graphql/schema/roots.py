import sys

from dagster import check
from dagster.core.definitions.events import AssetKey
from dagster.core.execution.retries import Retries
from dagster.core.host_representation import (
    RepositorySelector,
    RepresentedPipeline,
    ScheduleSelector,
    TriggerSelector,
)
from dagster.core.instance import DagsterInstance
from dagster.core.launcher import RunLauncher
from dagster.core.storage.compute_log_manager import ComputeIOType
from dagster.core.storage.pipeline_run import PipelineRunStatus, PipelineRunsFilter
from dagster_graphql import dauphin
from dagster_graphql.implementation.execution import (
    ExecutionParams,
    create_and_launch_partition_backfill,
    delete_pipeline_run,
    get_compute_log_observable,
    get_pipeline_run_observable,
    launch_pipeline_execution,
    launch_pipeline_reexecution,
    terminate_pipeline_execution,
    trigger_execution,
)
from dagster_graphql.implementation.external import (
    fetch_repositories,
    fetch_repository,
    get_full_external_pipeline_or_raise,
)
from dagster_graphql.implementation.fetch_assets import get_asset, get_assets
from dagster_graphql.implementation.fetch_partition_sets import (
    get_partition_set,
    get_partition_sets_or_error,
)
from dagster_graphql.implementation.fetch_pipelines import (
    get_pipeline_or_error,
    get_pipeline_snapshot_or_error_from_pipeline_selector,
    get_pipeline_snapshot_or_error_from_snapshot_id,
)
from dagster_graphql.implementation.fetch_runs import (
    get_execution_plan,
    get_run_by_id,
    get_run_group,
    get_run_groups,
    get_run_tags,
    get_runs,
    validate_pipeline_config,
)
from dagster_graphql.implementation.fetch_schedules import (
    get_schedule_definition_or_error,
    get_schedule_definitions_or_error,
    get_schedule_states_or_error,
    get_scheduler_or_error,
)
from dagster_graphql.implementation.run_config_schema import (
    resolve_is_run_config_valid,
    resolve_run_config_schema_or_error,
)
from dagster_graphql.implementation.utils import (
    ExecutionMetadata,
    UserFacingGraphQLError,
    capture_dauphin_error,
    pipeline_selector_from_graphql,
)

from .config_types import to_dauphin_config_type
from .runs import DauphinPipelineRunStatus
from .schedules import (
    DauphinReconcileSchedulerStateMutation,
    DauphinStartScheduleMutation,
    DauphinStopRunningScheduleMutation,
)


class DauphinQuery(dauphin.ObjectType):
    class Meta(object):
        name = "Query"

    version = dauphin.NonNull(dauphin.String)

    repositoriesOrError = dauphin.NonNull("RepositoriesOrError")
    repositoryOrError = dauphin.Field(
        dauphin.NonNull("RepositoryOrError"),
        repositorySelector=dauphin.NonNull("RepositorySelector"),
    )

    pipelineOrError = dauphin.Field(
        dauphin.NonNull("PipelineOrError"), params=dauphin.NonNull("PipelineSelector")
    )

    pipelineSnapshotOrError = dauphin.Field(
        dauphin.NonNull("PipelineSnapshotOrError"),
        snapshotId=dauphin.String(),
        activePipelineSelector=dauphin.Argument("PipelineSelector"),
    )

    scheduler = dauphin.Field(dauphin.NonNull("SchedulerOrError"))

    scheduleDefinitionOrError = dauphin.Field(
        dauphin.NonNull("ScheduleDefinitionOrError"),
        schedule_selector=dauphin.NonNull("ScheduleSelector"),
    )
    scheduleDefinitionsOrError = dauphin.Field(
        dauphin.NonNull("ScheduleDefinitionsOrError"),
        repositorySelector=dauphin.NonNull("RepositorySelector"),
    )
    scheduleStatesOrError = dauphin.Field(
        dauphin.NonNull("ScheduleStatesOrError"),
        repositorySelector=dauphin.Argument("RepositorySelector"),
        withNoScheduleDefinition=dauphin.Boolean(),
    )

    partitionSetsOrError = dauphin.Field(
        dauphin.NonNull("PartitionSetsOrError"),
        repositorySelector=dauphin.NonNull("RepositorySelector"),
        pipelineName=dauphin.NonNull(dauphin.String),
    )
    partitionSetOrError = dauphin.Field(
        dauphin.NonNull("PartitionSetOrError"),
        repositorySelector=dauphin.NonNull("RepositorySelector"),
        partitionSetName=dauphin.String(),
    )

    pipelineRunsOrError = dauphin.Field(
        dauphin.NonNull("PipelineRunsOrError"),
        filter=dauphin.Argument("PipelineRunsFilter"),
        cursor=dauphin.String(),
        limit=dauphin.Int(),
    )

    pipelineRunOrError = dauphin.Field(
        dauphin.NonNull("PipelineRunOrError"), runId=dauphin.NonNull(dauphin.ID)
    )

    pipelineRunTags = dauphin.non_null_list("PipelineTagAndValues")

    runGroupOrError = dauphin.Field(
        dauphin.NonNull("RunGroupOrError"), runId=dauphin.NonNull(dauphin.ID)
    )

    runGroupsOrError = dauphin.Field(
        dauphin.NonNull("RunGroupsOrError"),
        filter=dauphin.Argument("PipelineRunsFilter"),
        cursor=dauphin.String(),
        limit=dauphin.Int(),
    )

    isPipelineConfigValid = dauphin.Field(
        dauphin.NonNull("PipelineConfigValidationResult"),
        args={
            "pipeline": dauphin.Argument(dauphin.NonNull("PipelineSelector")),
            "runConfigData": dauphin.Argument("RunConfigData"),
            "mode": dauphin.Argument(dauphin.NonNull(dauphin.String)),
        },
    )

    executionPlanOrError = dauphin.Field(
        dauphin.NonNull("ExecutionPlanOrError"),
        args={
            "pipeline": dauphin.Argument(dauphin.NonNull("PipelineSelector")),
            "runConfigData": dauphin.Argument("RunConfigData"),
            "mode": dauphin.Argument(dauphin.NonNull(dauphin.String)),
        },
    )

    runConfigSchemaOrError = dauphin.Field(
        dauphin.NonNull("RunConfigSchemaOrError"),
        args={
            "selector": dauphin.Argument(dauphin.NonNull("PipelineSelector")),
            "mode": dauphin.Argument(dauphin.String),
        },
        description="""Fetch an environment schema given an execution selection and a mode.
        See the descripton on RunConfigSchema for more information.""",
    )

    instance = dauphin.NonNull("Instance")
    assetsOrError = dauphin.Field(
        dauphin.NonNull("AssetsOrError"),
        prefixPath=dauphin.Argument(dauphin.List(dauphin.NonNull(dauphin.String))),
    )
    assetOrError = dauphin.Field(
        dauphin.NonNull("AssetOrError"),
        assetKey=dauphin.Argument(dauphin.NonNull("AssetKeyInput")),
    )

    def resolve_repositoriesOrError(self, graphene_info):
        return fetch_repositories(graphene_info)

    def resolve_repositoryOrError(self, graphene_info, **kwargs):
        return fetch_repository(
            graphene_info, RepositorySelector.from_graphql_input(kwargs.get("repositorySelector")),
        )

    def resolve_pipelineSnapshotOrError(self, graphene_info, **kwargs):
        snapshot_id_arg = kwargs.get("snapshotId")
        pipeline_selector_arg = kwargs.get("activePipelineSelector")
        check.invariant(
            not (snapshot_id_arg and pipeline_selector_arg),
            "Must only pass one of snapshotId or activePipelineSelector",
        )
        check.invariant(
            snapshot_id_arg or pipeline_selector_arg,
            "Must set one of snapshotId or activePipelineSelector",
        )

        if pipeline_selector_arg:
            pipeline_selector = pipeline_selector_from_graphql(
                graphene_info.context, kwargs["activePipelineSelector"]
            )
            return get_pipeline_snapshot_or_error_from_pipeline_selector(
                graphene_info, pipeline_selector
            )
        else:
            return get_pipeline_snapshot_or_error_from_snapshot_id(graphene_info, snapshot_id_arg)

    def resolve_version(self, graphene_info):
        return graphene_info.context.version

    def resolve_scheduler(self, graphene_info):
        return get_scheduler_or_error(graphene_info)

    def resolve_scheduleDefinitionOrError(self, graphene_info, schedule_selector):
        return get_schedule_definition_or_error(
            graphene_info, ScheduleSelector.from_graphql_input(schedule_selector)
        )

    def resolve_scheduleDefinitionsOrError(self, graphene_info, **kwargs):
        return get_schedule_definitions_or_error(
            graphene_info, RepositorySelector.from_graphql_input(kwargs.get("repositorySelector"))
        )

    def resolve_scheduleStatesOrError(self, graphene_info, **kwargs):
        return get_schedule_states_or_error(
            graphene_info,
            RepositorySelector.from_graphql_input(kwargs["repositorySelector"])
            if kwargs.get("repositorySelector")
            else None,
            kwargs.get("withNoScheduleDefinition"),
        )

    def resolve_pipelineOrError(self, graphene_info, **kwargs):
        return get_pipeline_or_error(
            graphene_info, pipeline_selector_from_graphql(graphene_info.context, kwargs["params"]),
        )

    def resolve_pipelineRunsOrError(self, graphene_info, **kwargs):
        filters = kwargs.get("filter")
        if filters is not None:
            filters = filters.to_selector()

        return graphene_info.schema.type_named("PipelineRuns")(
            results=get_runs(graphene_info, filters, kwargs.get("cursor"), kwargs.get("limit"))
        )

    def resolve_pipelineRunOrError(self, graphene_info, runId):
        return get_run_by_id(graphene_info, runId)

    def resolve_runGroupsOrError(self, graphene_info, **kwargs):
        filters = kwargs.get("filter")
        if filters is not None:
            filters = filters.to_selector()

        return graphene_info.schema.type_named("RunGroupsOrError")(
            results=get_run_groups(
                graphene_info, filters, kwargs.get("cursor"), kwargs.get("limit")
            )
        )

    def resolve_partitionSetsOrError(self, graphene_info, **kwargs):
        return get_partition_sets_or_error(
            graphene_info,
            RepositorySelector.from_graphql_input(kwargs.get("repositorySelector")),
            kwargs.get("pipelineName"),
        )

    def resolve_partitionSetOrError(self, graphene_info, **kwargs):
        return get_partition_set(
            graphene_info,
            RepositorySelector.from_graphql_input(kwargs.get("repositorySelector")),
            kwargs.get("partitionSetName"),
        )

    def resolve_pipelineRunTags(self, graphene_info):
        return get_run_tags(graphene_info)

    def resolve_runGroupOrError(self, graphene_info, runId):
        return get_run_group(graphene_info, runId)

    def resolve_isPipelineConfigValid(self, graphene_info, pipeline, **kwargs):
        return validate_pipeline_config(
            graphene_info,
            pipeline_selector_from_graphql(graphene_info.context, pipeline),
            kwargs.get("runConfigData"),
            kwargs.get("mode"),
        )

    def resolve_executionPlanOrError(self, graphene_info, pipeline, **kwargs):
        return get_execution_plan(
            graphene_info,
            pipeline_selector_from_graphql(graphene_info.context, pipeline),
            kwargs.get("runConfigData"),
            kwargs.get("mode"),
        )

    def resolve_runConfigSchemaOrError(self, graphene_info, **kwargs):
        return resolve_run_config_schema_or_error(
            graphene_info,
            pipeline_selector_from_graphql(graphene_info.context, kwargs["selector"]),
            kwargs.get("mode"),
        )

    def resolve_instance(self, graphene_info):
        return graphene_info.schema.type_named("Instance")(graphene_info.context.instance)

    def resolve_assetsOrError(self, graphene_info, **kwargs):
        return get_assets(graphene_info, kwargs.get("prefixPath"))

    def resolve_assetOrError(self, graphene_info, **kwargs):
        return get_asset(graphene_info, AssetKey.from_graphql_input(kwargs["assetKey"]))


class DauphinStepOutputHandle(dauphin.InputObjectType):
    class Meta(object):
        name = "StepOutputHandle"

    stepKey = dauphin.NonNull(dauphin.String)
    outputName = dauphin.NonNull(dauphin.String)


class DauphinDeletePipelineRunSuccess(dauphin.ObjectType):
    class Meta(object):
        name = "DeletePipelineRunSuccess"

    runId = dauphin.NonNull(dauphin.String)


class DauphinDeletePipelineRunResult(dauphin.Union):
    class Meta(object):
        name = "DeletePipelineRunResult"
        types = ("DeletePipelineRunSuccess", "PythonError", "PipelineRunNotFoundError")


class DauphinDeleteRunMutation(dauphin.Mutation):
    class Meta(object):
        name = "DeletePipelineRun"

    class Arguments(object):
        runId = dauphin.NonNull(dauphin.String)

    Output = dauphin.NonNull("DeletePipelineRunResult")

    def mutate(self, graphene_info, **kwargs):
        run_id = kwargs["runId"]
        return delete_pipeline_run(graphene_info, run_id)


class DauphinTerminatePipelineExecutionSuccess(dauphin.ObjectType):
    class Meta(object):
        name = "TerminatePipelineExecutionSuccess"

    run = dauphin.Field(dauphin.NonNull("PipelineRun"))


class DauphinTerminatePipelineExecutionFailure(dauphin.ObjectType):
    class Meta(object):
        name = "TerminatePipelineExecutionFailure"

    run = dauphin.NonNull("PipelineRun")
    message = dauphin.NonNull(dauphin.String)


class DauphinTerminatePipelineExecutionResult(dauphin.Union):
    class Meta(object):
        name = "TerminatePipelineExecutionResult"
        types = (
            "TerminatePipelineExecutionSuccess",
            "TerminatePipelineExecutionFailure",
            "PipelineRunNotFoundError",
            "PythonError",
        )


@capture_dauphin_error
def create_execution_params_and_launch_pipeline_exec(graphene_info, execution_params_dict):
    # refactored into a helper function here in order to wrap with @capture_dauphin_error,
    # because create_execution_params may raise

    return launch_pipeline_execution(
        graphene_info,
        execution_params=create_execution_params(graphene_info, execution_params_dict),
    )


class DauphinLaunchPipelineExecutionMutation(dauphin.Mutation):
    class Meta(object):
        name = "LaunchPipelineExecutionMutation"
        description = "Launch a pipeline run via the run launcher configured on the instance."

    class Arguments(object):
        executionParams = dauphin.NonNull("ExecutionParams")

    Output = dauphin.NonNull("LaunchPipelineExecutionResult")

    def mutate(self, graphene_info, **kwargs):
        return create_execution_params_and_launch_pipeline_exec(
            graphene_info, kwargs["executionParams"]
        )


class DauphinLaunchPartitionBackfillMutation(dauphin.Mutation):
    class Meta(object):
        name = "LaunchPartitionBackfillMutation"
        description = "Launches a set of partition backfill runs via the run launcher configured on the instance."

    class Arguments(object):
        backfillParams = dauphin.NonNull("PartitionBackfillParams")

    Output = dauphin.NonNull("PartitionBackfillResult")

    def mutate(self, graphene_info, **kwargs):
        return create_and_launch_partition_backfill(graphene_info, kwargs["backfillParams"])


@capture_dauphin_error
def create_execution_params_and_launch_pipeline_reexec(graphene_info, execution_params_dict):
    # refactored into a helper function here in order to wrap with @capture_dauphin_error,
    # because create_execution_params may raise

    return launch_pipeline_reexecution(
        graphene_info,
        execution_params=create_execution_params(graphene_info, execution_params_dict),
    )


class DauphinLaunchPipelineReexecutionMutation(dauphin.Mutation):
    class Meta(object):
        name = "DauphinLaunchPipelineReexecutionMutation"
        description = "Re-launch a pipeline run via the run launcher configured on the instance"

    class Arguments(object):
        executionParams = dauphin.NonNull("ExecutionParams")

    Output = dauphin.NonNull("LaunchPipelineReexecutionResult")

    def mutate(self, graphene_info, **kwargs):
        return create_execution_params_and_launch_pipeline_reexec(
            graphene_info, execution_params_dict=kwargs["executionParams"],
        )


class DauphinTerminatePipelineExecutionMutation(dauphin.Mutation):
    class Meta(object):
        name = "TerminatePipelineExecutionMutation"

    class Arguments(object):
        runId = dauphin.NonNull(dauphin.String)

    Output = dauphin.NonNull("TerminatePipelineExecutionResult")

    def mutate(self, graphene_info, **kwargs):
        return terminate_pipeline_execution(graphene_info, kwargs["runId"])


class DauphinReloadRepositoryLocationMutationResult(dauphin.Union):
    class Meta(object):
        name = "ReloadRepositoryLocationMutationResult"
        types = (
            "RepositoryLocation",
            "ReloadNotSupported",
            "RepositoryLocationNotFound",
            "PythonError",
        )


class DauphinReloadRepositoryLocationMutation(dauphin.Mutation):
    class Meta(object):
        name = "ReloadRepositoryLocationMutation"

    class Arguments(object):
        repositoryLocationName = dauphin.NonNull(dauphin.String)

    Output = dauphin.NonNull("ReloadRepositoryLocationMutationResult")

    def mutate(self, graphene_info, **kwargs):
        location_name = kwargs["repositoryLocationName"]

        if not graphene_info.context.has_repository_location(
            location_name
        ) and not graphene_info.context.has_repository_location_error(location_name):
            return graphene_info.schema.type_named("RepositoryLocationNotFound")(location_name)

        if not graphene_info.context.is_reload_supported(location_name):
            return graphene_info.schema.type_named("ReloadNotSupported")(location_name)

        graphene_info.context.reload_repository_location(location_name)

        if graphene_info.context.has_repository_location(location_name):
            return graphene_info.schema.type_named("RepositoryLocation")(
                graphene_info.context.get_repository_location(location_name)
            )
        else:
            return graphene_info.schema.type_named("PythonError")(
                graphene_info.context.get_repository_location_error(location_name)
            )


class DauphinExecutionTag(dauphin.InputObjectType):
    class Meta(object):
        name = "ExecutionTag"

    key = dauphin.NonNull(dauphin.String)
    value = dauphin.NonNull(dauphin.String)


class DauphinMarshalledInput(dauphin.InputObjectType):
    class Meta(object):
        name = "MarshalledInput"

    input_name = dauphin.NonNull(dauphin.String)
    key = dauphin.NonNull(dauphin.String)


class DauphinMarshalledOutput(dauphin.InputObjectType):
    class Meta(object):
        name = "MarshalledOutput"

    output_name = dauphin.NonNull(dauphin.String)
    key = dauphin.NonNull(dauphin.String)


class DauphinStepExecution(dauphin.InputObjectType):
    class Meta(object):
        name = "StepExecution"

    stepKey = dauphin.NonNull(dauphin.String)
    marshalledInputs = dauphin.List(dauphin.NonNull(DauphinMarshalledInput))
    marshalledOutputs = dauphin.List(dauphin.NonNull(DauphinMarshalledOutput))


class DauphinExecutionMetadata(dauphin.InputObjectType):
    class Meta(object):
        name = "ExecutionMetadata"

    runId = dauphin.String()
    tags = dauphin.List(dauphin.NonNull(DauphinExecutionTag))
    rootRunId = dauphin.String(
        description="""The ID of the run at the root of the run group. All partial /
        full re-executions should use the first run as the rootRunID so they are
        grouped together."""
    )
    parentRunId = dauphin.String(
        description="""The ID of the run serving as the parent within the run group.
        For the first re-execution, this will be the same as the `rootRunId`. For
        subsequent runs, the root or a previous re-execution could be the parent run."""
    )


def create_execution_params(graphene_info, graphql_execution_params):
    preset_name = graphql_execution_params.get("preset")
    selector = pipeline_selector_from_graphql(
        graphene_info.context, graphql_execution_params["selector"]
    )
    if preset_name:
        if graphql_execution_params.get("runConfigData"):
            raise UserFacingGraphQLError(
                graphene_info.schema.type_named("ConflictingExecutionParamsError")(
                    conflicting_param="runConfigData"
                )
            )

        if graphql_execution_params.get("mode"):
            raise UserFacingGraphQLError(
                graphene_info.schema.type_named("ConflictingExecutionParamsError")(
                    conflicting_param="mode"
                )
            )

        if selector.solid_selection:
            raise UserFacingGraphQLError(
                graphene_info.schema.type_named("ConflictingExecutionParamsError")(
                    conflicting_param="selector.solid_selection"
                )
            )

        external_pipeline = get_full_external_pipeline_or_raise(graphene_info, selector)

        if not external_pipeline.has_preset(preset_name):
            raise UserFacingGraphQLError(
                graphene_info.schema.type_named("PresetNotFoundError")(
                    preset=preset_name, selector=selector
                )
            )

        preset = external_pipeline.get_preset(preset_name)

        return ExecutionParams(
            selector=selector.with_solid_selection(preset.solid_selection),
            run_config=preset.run_config,
            mode=preset.mode,
            execution_metadata=create_execution_metadata(
                graphql_execution_params.get("executionMetadata")
            ),
            step_keys=graphql_execution_params.get("stepKeys"),
        )

    return execution_params_from_graphql(graphene_info.context, graphql_execution_params)


def execution_params_from_graphql(context, graphql_execution_params):
    return ExecutionParams(
        selector=pipeline_selector_from_graphql(context, graphql_execution_params.get("selector")),
        run_config=graphql_execution_params.get("runConfigData") or {},
        mode=graphql_execution_params.get("mode"),
        execution_metadata=create_execution_metadata(
            graphql_execution_params.get("executionMetadata")
        ),
        step_keys=graphql_execution_params.get("stepKeys"),
    )


def create_execution_metadata(graphql_execution_metadata):
    return (
        ExecutionMetadata(
            run_id=graphql_execution_metadata.get("runId"),
            tags={t["key"]: t["value"] for t in graphql_execution_metadata.get("tags", [])},
            root_run_id=graphql_execution_metadata.get("rootRunId"),
            parent_run_id=graphql_execution_metadata.get("parentRunId"),
        )
        if graphql_execution_metadata
        else ExecutionMetadata(run_id=None, tags={})
    )


class DauphinRetriesPreviousAttempts(dauphin.InputObjectType):
    class Meta(object):
        name = "RetriesPreviousAttempts"

    key = dauphin.String()
    count = dauphin.Int()


class DauphinRetries(dauphin.InputObjectType):
    class Meta(object):
        name = "Retries"

    mode = dauphin.Field(dauphin.String)
    retries_previous_attempts = dauphin.List(DauphinRetriesPreviousAttempts)


def create_retries_params(retries_config):
    return Retries.from_graphql_input(retries_config)


class DauphinTriggerExecution(dauphin.Mutation):
    class Meta(object):
        name = "TriggerExecution"

    class Arguments(object):
        trigger_selector = dauphin.NonNull("TriggerSelector")

    Output = dauphin.NonNull("TriggerMutationResult")

    def mutate(self, graphene_info, trigger_selector):
        return trigger_execution(
            graphene_info, TriggerSelector.from_graphql_input(trigger_selector)
        )


class DauphinMutation(dauphin.ObjectType):
    class Meta(object):
        name = "Mutation"

    launch_pipeline_execution = DauphinLaunchPipelineExecutionMutation.Field()
    launch_pipeline_reexecution = DauphinLaunchPipelineReexecutionMutation.Field()
    reconcile_scheduler_state = DauphinReconcileSchedulerStateMutation.Field()
    start_schedule = DauphinStartScheduleMutation.Field()
    stop_running_schedule = DauphinStopRunningScheduleMutation.Field()
    terminate_pipeline_execution = DauphinTerminatePipelineExecutionMutation.Field()
    delete_pipeline_run = DauphinDeleteRunMutation.Field()
    reload_repository_location = DauphinReloadRepositoryLocationMutation.Field()
    launch_partition_backfill = DauphinLaunchPartitionBackfillMutation.Field()
    trigger_execution = DauphinTriggerExecution.Field()


DauphinComputeIOType = dauphin.Enum.from_enum(ComputeIOType)


class DauphinSubscription(dauphin.ObjectType):
    class Meta(object):
        name = "Subscription"

    pipelineRunLogs = dauphin.Field(
        dauphin.NonNull("PipelineRunLogsSubscriptionPayload"),
        runId=dauphin.Argument(dauphin.NonNull(dauphin.ID)),
        after=dauphin.Argument("Cursor"),
    )

    computeLogs = dauphin.Field(
        dauphin.NonNull("ComputeLogFile"),
        runId=dauphin.Argument(dauphin.NonNull(dauphin.ID)),
        stepKey=dauphin.Argument(dauphin.NonNull(dauphin.String)),
        ioType=dauphin.Argument(dauphin.NonNull("ComputeIOType")),
        cursor=dauphin.Argument(dauphin.String),
    )

    def resolve_pipelineRunLogs(self, graphene_info, runId, after=None):
        return get_pipeline_run_observable(graphene_info, runId, after)

    def resolve_computeLogs(self, graphene_info, runId, stepKey, ioType, cursor=None):
        check.str_param(ioType, "ioType")  # need to resolve to enum
        return get_compute_log_observable(
            graphene_info, runId, stepKey, ComputeIOType(ioType), cursor
        )


class DauphinRunConfigData(dauphin.GenericScalar, dauphin.Scalar):
    class Meta(object):
        name = "RunConfigData"
        description = """This type is used when passing in a configuration object
        for pipeline configuration. This is any-typed in the GraphQL type system,
        but must conform to the constraints of the dagster config type system"""


class DauphinExecutionParams(dauphin.InputObjectType):
    class Meta(object):
        name = "ExecutionParams"

    selector = dauphin.NonNull(
        "PipelineSelector",
        description="""Defines the pipeline and solid subset that should be executed.
        All subsequent executions in the same run group (for example, a single-step
        re-execution) are scoped to the original run's pipeline selector and solid
        subset.""",
    )
    runConfigData = dauphin.Field("RunConfigData")
    mode = dauphin.Field(dauphin.String)
    executionMetadata = dauphin.Field(
        "ExecutionMetadata",
        description="""Defines run tags and parent / root relationships.\n\nNote: To
        'restart from failure', provide a `parentRunId` and pass the
        'dagster/is_resume_retry' tag. Dagster's automatic step key selection will
        override any stepKeys provided.""",
    )
    stepKeys = dauphin.Field(
        dauphin.List(dauphin.NonNull(dauphin.String)),
        description="""Defines step keys to execute within the execution plan defined
        by the pipeline `selector`. To execute the entire execution plan, you can omit
        this parameter, provide an empty array, or provide every step name.""",
    )
    preset = dauphin.Field(dauphin.String)


class DauphinRepositorySelector(dauphin.InputObjectType):
    class Meta(object):
        name = "RepositorySelector"
        description = """This type represents the fields necessary to identify a repository."""

    repositoryName = dauphin.NonNull(dauphin.String)
    repositoryLocationName = dauphin.NonNull(dauphin.String)


class DauphinPipelineSelector(dauphin.InputObjectType):
    class Meta(object):
        name = "PipelineSelector"
        description = """This type represents the fields necessary to identify a
        pipeline or pipeline subset."""

    pipelineName = dauphin.NonNull(dauphin.String)
    repositoryName = dauphin.NonNull(dauphin.String)
    repositoryLocationName = dauphin.NonNull(dauphin.String)
    solidSelection = dauphin.List(dauphin.NonNull(dauphin.String))


class DauphinScheduleSelector(dauphin.InputObjectType):
    class Meta(object):
        name = "ScheduleSelector"
        description = """This type represents the fields necessary to identify a schedule."""

    repositoryName = dauphin.NonNull(dauphin.String)
    repositoryLocationName = dauphin.NonNull(dauphin.String)
    scheduleName = dauphin.NonNull(dauphin.String)


class DauphinPartitionSetSelector(dauphin.InputObjectType):
    class Meta(object):
        name = "PartitionSetSelector"
        description = """This type represents the fields necessary to identify a
        pipeline or pipeline subset."""

    partitionSetName = dauphin.NonNull(dauphin.String)
    repositorySelector = dauphin.NonNull("RepositorySelector")


class DauphinTriggerSelector(dauphin.InputObjectType):
    class Meta(object):
        name = "TriggerSelector"
        description = """
            This type represents the fields necessary to identify a triggered execution target.
        """

    repositoryName = dauphin.NonNull(dauphin.String)
    repositoryLocationName = dauphin.NonNull(dauphin.String)
    jobName = dauphin.NonNull(dauphin.String)


class DauphinPartitionBackfillParams(dauphin.InputObjectType):
    class Meta(object):
        name = "PartitionBackfillParams"

    selector = dauphin.NonNull("PartitionSetSelector")
    partitionNames = dauphin.non_null_list(dauphin.String)
    reexecutionSteps = dauphin.List(dauphin.NonNull(dauphin.String))
    fromFailure = dauphin.Boolean()
    tags = dauphin.List(dauphin.NonNull(DauphinExecutionTag))


class DauphinPipelineRunsFilter(dauphin.InputObjectType):
    class Meta(object):
        name = "PipelineRunsFilter"
        description = """This type represents a filter on pipeline runs.
        Currently, you may only pass one of the filter options."""

    # Currently you may choose one of the following
    run_id = dauphin.Field(dauphin.String)
    pipeline_name = dauphin.Field(dauphin.String)
    tags = dauphin.List(dauphin.NonNull(DauphinExecutionTag))
    status = dauphin.Field(DauphinPipelineRunStatus)
    snapshot_id = dauphin.Field(dauphin.String)

    def to_selector(self):
        if self.status:
            status = PipelineRunStatus[self.status]
        else:
            status = None

        if self.tags:
            # We are wrapping self.tags in a list because dauphin.List is not marked as iterable
            tags = {tag["key"]: tag["value"] for tag in list(self.tags)}
        else:
            tags = None

        run_ids = [self.run_id] if self.run_id else []
        return PipelineRunsFilter(
            run_ids=run_ids,
            pipeline_name=self.pipeline_name,
            tags=tags,
            status=status,
            snapshot_id=self.snapshot_id,
        )


class DauphinPipelineTagAndValues(dauphin.ObjectType):
    class Meta(object):
        name = "PipelineTagAndValues"
        description = """A run tag and the free-form values that have been associated
        with it so far."""

    key = dauphin.NonNull(dauphin.String)
    values = dauphin.non_null_list(dauphin.String)

    def __init__(self, key, values):
        super(DauphinPipelineTagAndValues, self).__init__(key=key, values=values)


class DauphinRunConfigSchema(dauphin.ObjectType):
    def __init__(self, represented_pipeline, mode):
        self._represented_pipeline = check.inst_param(
            represented_pipeline, "represented_pipeline", RepresentedPipeline
        )
        self._mode = check.str_param(mode, "mode")

    class Meta(object):
        name = "RunConfigSchema"
        description = """The run config schema represents the all the config type
        information given a certain execution selection and mode of execution of that
        selection. All config interactions (e.g. checking config validity, fetching
        all config types, fetching in a particular config type) should be done
        through this type """

    rootConfigType = dauphin.Field(
        dauphin.NonNull("ConfigType"),
        description="""Fetch the root environment type. Concretely this is the type that
        is in scope at the root of configuration document for a particular execution selection.
        It is the type that is in scope initially with a blank config editor.""",
    )
    allConfigTypes = dauphin.Field(
        dauphin.non_null_list("ConfigType"),
        description="""Fetch all the named config types that are in the schema. Useful
        for things like a type browser UI, or for fetching all the types are in the
        scope of a document so that the index can be built for the autocompleting editor.
    """,
    )

    isRunConfigValid = dauphin.Field(
        dauphin.NonNull("PipelineConfigValidationResult"),
        args={"runConfigData": dauphin.Argument("RunConfigData")},
        description="""Parse a particular environment config result. The return value
        either indicates that the validation succeeded by returning
        `PipelineConfigValidationValid` or that there are configuration errors
        by returning `PipelineConfigValidationInvalid' which containers a list errors
        so that can be rendered for the user""",
    )

    def resolve_allConfigTypes(self, _graphene_info):
        return sorted(
            list(
                map(
                    lambda key: to_dauphin_config_type(
                        self._represented_pipeline.config_schema_snapshot, key
                    ),
                    self._represented_pipeline.config_schema_snapshot.all_config_keys,
                )
            ),
            key=lambda ct: ct.key,
        )

    def resolve_rootConfigType(self, _graphene_info):
        return to_dauphin_config_type(
            self._represented_pipeline.config_schema_snapshot,
            self._represented_pipeline.get_mode_def_snap(self._mode).root_config_key,
        )

    def resolve_isRunConfigValid(self, graphene_info, **kwargs):
        return resolve_is_run_config_valid(
            graphene_info, self._represented_pipeline, self._mode, kwargs.get("runConfigData", {}),
        )


class DauphinRunConfigSchemaOrError(dauphin.Union):
    class Meta(object):
        name = "RunConfigSchemaOrError"
        types = (
            "RunConfigSchema",
            "PipelineNotFoundError",
            "InvalidSubsetError",
            "ModeNotFoundError",
            "PythonError",
        )


class DauphinRunLauncher(dauphin.ObjectType):
    class Meta(object):
        name = "RunLauncher"

    name = dauphin.NonNull(dauphin.String)

    def __init__(self, run_launcher):
        self._run_launcher = check.inst_param(run_launcher, "run_launcher", RunLauncher)

    def resolve_name(self, _graphene_info):
        return self._run_launcher.__class__.__name__


class DauphinInstance(dauphin.ObjectType):
    class Meta(object):
        name = "Instance"

    info = dauphin.NonNull(dauphin.String)
    runLauncher = dauphin.Field("RunLauncher")
    assetsSupported = dauphin.NonNull(dauphin.Boolean)
    executablePath = dauphin.NonNull(dauphin.String)

    def __init__(self, instance):
        self._instance = check.inst_param(instance, "instance", DagsterInstance)

    def resolve_info(self, _graphene_info):
        return self._instance.info_str()

    def resolve_runLauncher(self, _graphene_info):
        return (
            DauphinRunLauncher(self._instance.run_launcher) if self._instance.run_launcher else None
        )

    def resolve_assetsSupported(self, _graphene_info):
        return self._instance.is_asset_aware

    def resolve_executablePath(self, _graphene_info):
        return sys.executable


class DauphinAssetKeyInput(dauphin.InputObjectType):
    class Meta(object):
        name = "AssetKeyInput"

    path = dauphin.non_null_list(dauphin.String)
