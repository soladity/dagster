import graphene
from dagster.core.definitions.events import AssetKey

from ...implementation.execution import (
    cancel_partition_backfill,
    create_and_launch_partition_backfill,
    delete_pipeline_run,
    launch_pipeline_execution,
    launch_pipeline_reexecution,
    resume_partition_backfill,
    terminate_pipeline_execution,
    wipe_assets,
)
from ...implementation.external import fetch_workspace, get_full_external_pipeline_or_raise
from ...implementation.utils import (
    ExecutionMetadata,
    ExecutionParams,
    UserFacingGraphQLError,
    capture_error,
    check_read_only,
    pipeline_selector_from_graphql,
)
from ..asset_key import GrapheneAssetKey
from ..backfill import (
    GrapheneCancelBackfillResult,
    GrapheneLaunchBackfillResult,
    GrapheneResumeBackfillResult,
)
from ..errors import (
    GrapheneAssetNotFoundError,
    GrapheneConflictingExecutionParamsError,
    GraphenePipelineRunNotFoundError,
    GraphenePresetNotFoundError,
    GraphenePythonError,
    GrapheneReadOnlyError,
    GrapheneReloadNotSupported,
    GrapheneRepositoryLocationNotFound,
)
from ..external import GrapheneWorkspace, GrapheneWorkspaceLocationEntry
from ..inputs import GrapheneAssetKeyInput, GrapheneExecutionParams, GrapheneLaunchBackfillParams
from ..pipelines.pipeline import GraphenePipelineRun
from ..runs import GrapheneLaunchPipelineExecutionResult, GrapheneLaunchPipelineReexecutionResult
from ..schedules import (
    GrapheneReconcileSchedulerStateMutation,
    GrapheneStartScheduleMutation,
    GrapheneStopRunningScheduleMutation,
)
from ..sensors import GrapheneStartSensorMutation, GrapheneStopSensorMutation
from ..util import non_null_list


def create_execution_params(graphene_info, graphql_execution_params):
    preset_name = graphql_execution_params.get("preset")
    selector = pipeline_selector_from_graphql(graphql_execution_params["selector"])
    if preset_name:
        if graphql_execution_params.get("runConfigData"):
            raise UserFacingGraphQLError(
                GrapheneConflictingExecutionParamsError(conflicting_param="runConfigData")
            )

        if graphql_execution_params.get("mode"):
            raise UserFacingGraphQLError(
                GrapheneConflictingExecutionParamsError(conflicting_param="mode")
            )

        if selector.solid_selection:
            raise UserFacingGraphQLError(
                GrapheneConflictingExecutionParamsError(
                    conflicting_param="selector.solid_selection"
                )
            )

        external_pipeline = get_full_external_pipeline_or_raise(graphene_info, selector)

        if not external_pipeline.has_preset(preset_name):
            raise UserFacingGraphQLError(
                GraphenePresetNotFoundError(preset=preset_name, selector=selector)
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

    return execution_params_from_graphql(graphql_execution_params)


def execution_params_from_graphql(graphql_execution_params):
    return ExecutionParams(
        selector=pipeline_selector_from_graphql(graphql_execution_params.get("selector")),
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


class GrapheneDeletePipelineRunSuccess(graphene.ObjectType):
    runId = graphene.NonNull(graphene.String)

    class Meta:
        name = "DeletePipelineRunSuccess"


class GrapheneDeletePipelineRunResult(graphene.Union):
    class Meta:
        types = (
            GrapheneDeletePipelineRunSuccess,
            GrapheneReadOnlyError,
            GraphenePythonError,
            GraphenePipelineRunNotFoundError,
        )
        name = "DeletePipelineRunResult"


class GrapheneDeleteRunMutation(graphene.Mutation):
    Output = graphene.NonNull(GrapheneDeletePipelineRunResult)

    class Arguments:
        runId = graphene.NonNull(graphene.String)

    class Meta:
        name = "DeleteRunMutation"

    @capture_error
    @check_read_only
    def mutate(self, graphene_info, **kwargs):
        run_id = kwargs["runId"]
        return delete_pipeline_run(graphene_info, run_id)


class GrapheneTerminatePipelineExecutionSuccess(graphene.ObjectType):
    run = graphene.Field(graphene.NonNull(GraphenePipelineRun))

    class Meta:
        name = "TerminatePipelineExecutionSuccess"


class GrapheneTerminatePipelineExecutionFailure(graphene.ObjectType):
    run = graphene.NonNull(GraphenePipelineRun)
    message = graphene.NonNull(graphene.String)

    class Meta:
        name = "TerminatePipelineExecutionFailure"


class GrapheneTerminatePipelineExecutionResult(graphene.Union):
    class Meta:
        types = (
            GrapheneTerminatePipelineExecutionSuccess,
            GrapheneTerminatePipelineExecutionFailure,
            GraphenePipelineRunNotFoundError,
            GrapheneReadOnlyError,
            GraphenePythonError,
        )
        name = "TerminatePipelineExecutionResult"


@capture_error
def create_execution_params_and_launch_pipeline_exec(graphene_info, execution_params_dict):
    # refactored into a helper function here in order to wrap with @capture_error,
    # because create_execution_params may raise
    return launch_pipeline_execution(
        graphene_info,
        execution_params=create_execution_params(graphene_info, execution_params_dict),
    )


class GrapheneLaunchPipelineExecutionMutation(graphene.Mutation):

    Output = graphene.NonNull(GrapheneLaunchPipelineExecutionResult)

    class Arguments:
        executionParams = graphene.NonNull(GrapheneExecutionParams)

    class Meta:
        description = "Launch a pipeline run via the run launcher configured on the instance."
        name = "LaunchPipelineExecutionMutation"

    @capture_error
    @check_read_only
    def mutate(self, graphene_info, **kwargs):
        return create_execution_params_and_launch_pipeline_exec(
            graphene_info, kwargs["executionParams"]
        )


class GrapheneLaunchBackfillMutation(graphene.Mutation):
    Output = graphene.NonNull(GrapheneLaunchBackfillResult)

    class Arguments:
        backfillParams = graphene.NonNull(GrapheneLaunchBackfillParams)

    class Meta:
        description = "Launches a set of partition backfill runs via the run launcher configured on the instance."
        name = "LaunchBackfillMutation"

    @capture_error
    @check_read_only
    def mutate(self, graphene_info, **kwargs):
        return create_and_launch_partition_backfill(graphene_info, kwargs["backfillParams"])


class GrapheneCancelBackfillMutation(graphene.Mutation):
    Output = graphene.NonNull(GrapheneCancelBackfillResult)

    class Arguments:
        backfillId = graphene.NonNull(graphene.String)

    class Meta:
        description = "Marks a partition backfill as canceled."
        name = "CancelBackfillMutation"

    @capture_error
    @check_read_only
    def mutate(self, graphene_info, **kwargs):
        return cancel_partition_backfill(graphene_info, kwargs["backfillId"])


class GrapheneResumeBackfillMutation(graphene.Mutation):
    Output = graphene.NonNull(GrapheneResumeBackfillResult)

    class Arguments:
        backfillId = graphene.NonNull(graphene.String)

    class Meta:
        description = "Retries a set of partition backfill runs via the run launcher configured on the instance."
        name = "ResumeBackfillMutation"

    @capture_error
    @check_read_only
    def mutate(self, graphene_info, **kwargs):
        return resume_partition_backfill(graphene_info, kwargs["backfillId"])


@capture_error
def create_execution_params_and_launch_pipeline_reexec(graphene_info, execution_params_dict):
    # refactored into a helper function here in order to wrap with @capture_error,
    # because create_execution_params may raise
    return launch_pipeline_reexecution(
        graphene_info,
        execution_params=create_execution_params(graphene_info, execution_params_dict),
    )


class GrapheneLaunchPipelineReexecutionMutation(graphene.Mutation):
    Output = graphene.NonNull(GrapheneLaunchPipelineReexecutionResult)

    class Arguments:
        executionParams = graphene.NonNull(GrapheneExecutionParams)

    class Meta:
        description = "Re-launch a pipeline run via the run launcher configured on the instance"
        name = "LaunchPipelineReexecutionMutation"

    @capture_error
    @check_read_only
    def mutate(self, graphene_info, **kwargs):
        return create_execution_params_and_launch_pipeline_reexec(
            graphene_info,
            execution_params_dict=kwargs["executionParams"],
        )


class GrapheneTerminatePipelinePolicy(graphene.Enum):
    # Default behavior: Only mark as canceled if the termination is successful, and after all
    # resources peforming the execution have been shut down.
    SAFE_TERMINATE = "SAFE_TERMINATE"

    # Immediately mark the pipelie as canceled, whether or not the termination was successful.
    # No guarantee that the execution has actually stopped.
    MARK_AS_CANCELED_IMMEDIATELY = "MARK_AS_CANCELED_IMMEDIATELY"

    class Meta:
        name = "TerminatePipelinePolicy"


class GrapheneTerminatePipelineExecutionMutation(graphene.Mutation):
    Output = graphene.NonNull(GrapheneTerminatePipelineExecutionResult)

    class Arguments:
        runId = graphene.NonNull(graphene.String)
        terminatePolicy = graphene.Argument(GrapheneTerminatePipelinePolicy)

    class Meta:
        name = "TerminatePipelineExecutionMutation"

    @capture_error
    @check_read_only
    def mutate(self, graphene_info, **kwargs):
        return terminate_pipeline_execution(
            graphene_info,
            kwargs["runId"],
            kwargs.get("terminatePolicy", GrapheneTerminatePipelinePolicy.SAFE_TERMINATE),
        )


class GrapheneReloadRepositoryLocationMutationResult(graphene.Union):
    class Meta:
        types = (
            GrapheneWorkspaceLocationEntry,
            GrapheneReloadNotSupported,
            GrapheneRepositoryLocationNotFound,
            GrapheneReadOnlyError,
            GraphenePythonError,
        )
        name = "ReloadRepositoryLocationMutationResult"


class GrapheneReloadRepositoryLocationMutation(graphene.Mutation):
    Output = graphene.NonNull(GrapheneReloadRepositoryLocationMutationResult)

    class Arguments:
        repositoryLocationName = graphene.NonNull(graphene.String)

    class Meta:
        name = "ReloadRepositoryLocationMutation"

    @capture_error
    @check_read_only
    def mutate(self, graphene_info, **kwargs):
        location_name = kwargs["repositoryLocationName"]

        if not graphene_info.context.has_repository_location(
            location_name
        ) and not graphene_info.context.has_repository_location_error(location_name):
            return GrapheneRepositoryLocationNotFound(location_name)

        if not graphene_info.context.is_reload_supported(location_name):
            return GrapheneReloadNotSupported(location_name)

        # The current workspace context is a WorkspaceRequestContext, which contains a reference to the
        # repository locations that were present in the root IWorkspaceProcessContext the start of the
        # request. Reloading a repository location modifies the IWorkspaceProcessContext, rendeirng
        # our current WorkspaceRequestContext outdated. Therefore, `reload_repository_location` returns
        # an updated WorkspaceRequestContext for us to use.
        new_context = graphene_info.context.reload_repository_location(location_name)
        return GrapheneWorkspaceLocationEntry(new_context.workspace_snapshot[location_name])


class GrapheneReloadWorkspaceMutationResult(graphene.Union):
    class Meta:
        types = (
            GrapheneWorkspace,
            GrapheneReadOnlyError,
            GraphenePythonError,
        )
        name = "ReloadWorkspaceMutationResult"


class GrapheneReloadWorkspaceMutation(graphene.Mutation):
    Output = graphene.NonNull(GrapheneReloadWorkspaceMutationResult)

    class Meta:
        name = "ReloadWorkspaceMutation"

    @capture_error
    @check_read_only
    def mutate(self, graphene_info, **_kwargs):
        new_context = graphene_info.context.reload_workspace()
        return fetch_workspace(new_context)


class GrapheneAssetWipeSuccess(graphene.ObjectType):
    assetKeys = non_null_list(GrapheneAssetKey)

    class Meta:
        name = "AssetWipeSuccess"


class GrapheneAssetWipeMutationResult(graphene.Union):
    class Meta:
        types = (
            GrapheneAssetNotFoundError,
            GrapheneReadOnlyError,
            GraphenePythonError,
            GrapheneAssetWipeSuccess,
        )
        name = "AssetWipeMutationResult"


class GrapheneAssetWipeMutation(graphene.Mutation):
    Output = graphene.NonNull(GrapheneAssetWipeMutationResult)

    class Arguments:
        assetKeys = graphene.Argument(non_null_list(GrapheneAssetKeyInput))

    class Meta:
        name = "AssetWipeMutation"

    @capture_error
    @check_read_only
    def mutate(self, graphene_info, **kwargs):
        return wipe_assets(
            graphene_info,
            [AssetKey.from_graphql_input(asset_key) for asset_key in kwargs["assetKeys"]],
        )


class GrapheneMutation(graphene.ObjectType):
    launch_pipeline_execution = GrapheneLaunchPipelineExecutionMutation.Field()
    launch_pipeline_reexecution = GrapheneLaunchPipelineReexecutionMutation.Field()
    reconcile_scheduler_state = GrapheneReconcileSchedulerStateMutation.Field()
    start_schedule = GrapheneStartScheduleMutation.Field()
    stop_running_schedule = GrapheneStopRunningScheduleMutation.Field()
    start_sensor = GrapheneStartSensorMutation.Field()
    stop_sensor = GrapheneStopSensorMutation.Field()
    terminate_pipeline_execution = GrapheneTerminatePipelineExecutionMutation.Field()
    delete_pipeline_run = GrapheneDeleteRunMutation.Field()
    reload_repository_location = GrapheneReloadRepositoryLocationMutation.Field()
    reload_workspace = GrapheneReloadWorkspaceMutation.Field()
    wipe_assets = GrapheneAssetWipeMutation.Field()
    launch_partition_backfill = GrapheneLaunchBackfillMutation.Field()
    resume_partition_backfill = GrapheneResumeBackfillMutation.Field()
    cancel_partition_backfill = GrapheneCancelBackfillMutation.Field()

    class Meta:
        name = "Mutation"
