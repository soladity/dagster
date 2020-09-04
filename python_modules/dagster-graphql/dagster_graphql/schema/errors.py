from __future__ import absolute_import

from dagster_graphql import dauphin

from dagster import check
from dagster.config.errors import (
    EvaluationError,
    FieldNotDefinedErrorData,
    FieldsNotDefinedErrorData,
    MissingFieldErrorData,
    MissingFieldsErrorData,
    RuntimeMismatchErrorData,
    SelectorTypeErrorData,
)
from dagster.config.stack import EvaluationStackListItemEntry, EvaluationStackPathEntry
from dagster.core.host_representation import RepresentedPipeline
from dagster.core.snap import ConfigSchemaSnapshot
from dagster.utils.error import SerializableErrorInfo

from ..implementation.utils import PipelineSelector
from .config_types import DauphinConfigTypeField
from .runs import DauphinStepEvent


class DauphinError(dauphin.Interface):
    class Meta(object):
        name = "Error"

    message = dauphin.String(required=True)


class DauphinPythonError(dauphin.ObjectType):
    class Meta(object):
        name = "PythonError"
        interfaces = (DauphinError,)

    className = dauphin.Field(dauphin.String)
    stack = dauphin.non_null_list(dauphin.String)
    cause = dauphin.Field("PythonError")

    def __init__(self, error_info):
        super(DauphinPythonError, self).__init__()
        check.inst_param(error_info, "error_info", SerializableErrorInfo)
        self.message = error_info.message
        self.stack = error_info.stack
        self.cause = error_info.cause
        self.className = error_info.cls_name


class DauphinSchedulerNotDefinedError(dauphin.ObjectType):
    class Meta(object):
        name = "SchedulerNotDefinedError"
        interfaces = (DauphinError,)

    def __init__(self):
        super(DauphinSchedulerNotDefinedError, self).__init__()
        self.message = "Scheduler is not defined for the currently loaded repository."


class DauphinScheduleNotFoundError(dauphin.ObjectType):
    class Meta(object):
        name = "ScheduleNotFoundError"
        interfaces = (DauphinError,)

    schedule_name = dauphin.NonNull(dauphin.String)

    def __init__(self, schedule_name):
        super(DauphinScheduleNotFoundError, self).__init__()
        self.schedule_name = check.str_param(schedule_name, "schedule_name")
        self.message = (
            "Schedule {schedule_name} is not present in the currently loaded repository."
        ).format(schedule_name=schedule_name)


class DauphinPipelineSnapshotNotFoundError(dauphin.ObjectType):
    class Meta(object):
        name = "PipelineSnapshotNotFoundError"
        interfaces = (DauphinError,)

    snapshot_id = dauphin.NonNull(dauphin.String)

    def __init__(self, snapshot_id):
        super(DauphinPipelineSnapshotNotFoundError, self).__init__()
        self.snapshot_id = check.str_param(snapshot_id, "snapshot_id")
        self.message = (
            "Pipeline snapshot {snapshot_id} is not present in the current instance."
        ).format(snapshot_id=snapshot_id)


class DauphinReloadNotSupported(dauphin.ObjectType):
    class Meta(object):
        name = "ReloadNotSupported"
        interfaces = (DauphinError,)

    def __init__(self, location_name):
        self.message = "Location {location_name} does not support reloading.".format(
            location_name=location_name
        )


class DauphinRepositoryLocationNotFound(dauphin.ObjectType):
    class Meta(object):
        name = "RepositoryLocationNotFound"
        interfaces = (DauphinError,)

    def __init__(self, location_name):
        self.message = "Location {location_name} does not exist.".format(
            location_name=location_name
        )


class DauphinPipelineNotFoundError(dauphin.ObjectType):
    class Meta(object):
        name = "PipelineNotFoundError"
        interfaces = (DauphinError,)

    pipeline_name = dauphin.NonNull(dauphin.String)
    repository_name = dauphin.NonNull(dauphin.String)
    repository_location_name = dauphin.NonNull(dauphin.String)

    def __init__(self, selector):
        super(DauphinPipelineNotFoundError, self).__init__()
        check.inst_param(selector, "selector", PipelineSelector)
        self.pipeline_name = selector.pipeline_name
        self.repository_name = selector.repository_name
        self.repository_location_name = selector.location_name
        self.message = "Could not find Pipeline {selector.location_name}.{selector.repository_name}.{selector.pipeline_name}".format(
            selector=selector
        )


class DauphinPipelineRunNotFoundError(dauphin.ObjectType):
    class Meta(object):
        name = "PipelineRunNotFoundError"
        interfaces = (DauphinError,)

    run_id = dauphin.NonNull(dauphin.String)

    def __init__(self, run_id):
        super(DauphinPipelineRunNotFoundError, self).__init__()
        self.run_id = check.str_param(run_id, "run_id")
        self.message = "Pipeline run {run_id} could not be found.".format(run_id=run_id)


class DauphinInvalidPipelineRunsFilterError(dauphin.ObjectType):
    class Meta(object):
        name = "InvalidPipelineRunsFilterError"
        interfaces = (DauphinError,)

    def __init__(self, message):
        super(DauphinInvalidPipelineRunsFilterError, self).__init__()
        self.message = check.str_param(message, "message")


class DauphinRunGroupNotFoundError(dauphin.ObjectType):
    class Meta(object):
        name = "RunGroupNotFoundError"
        interfaces = (DauphinError,)

    run_id = dauphin.NonNull(dauphin.String)

    def __init__(self, run_id):
        super(DauphinRunGroupNotFoundError, self).__init__()
        self.run_id = check.str_param(run_id, "run_id")
        self.message = "Run group of run {run_id} could not be found.".format(run_id=run_id)


class DauphinInvalidSubsetError(dauphin.ObjectType):
    class Meta(object):
        name = "InvalidSubsetError"
        interfaces = (DauphinError,)

    pipeline = dauphin.Field(dauphin.NonNull("Pipeline"))

    def __init__(self, message, pipeline):
        super(DauphinInvalidSubsetError, self).__init__()
        self.message = check.str_param(message, "message")
        self.pipeline = pipeline


class DauphinPresetNotFoundError(dauphin.ObjectType):
    class Meta(object):
        name = "PresetNotFoundError"
        interfaces = (DauphinError,)

    preset = dauphin.NonNull(dauphin.String)

    def __init__(self, preset, selector):
        self.preset = check.str_param(preset, "preset")
        self.message = "Preset {preset} not found in pipeline {pipeline}.".format(
            preset=preset, pipeline=selector.pipeline_name
        )


class DauphinConflictingExecutionParamsError(dauphin.ObjectType):
    class Meta(object):
        name = "ConflictingExecutionParamsError"
        interfaces = (DauphinError,)

    def __init__(self, conflicting_param):
        self.message = "Invalid ExecutionParams. Cannot define {conflicting_param} when using a preset.".format(
            conflicting_param=conflicting_param
        )


class DauphinModeNotFoundError(dauphin.ObjectType):
    class Meta(object):
        name = "ModeNotFoundError"
        interfaces = (DauphinError,)

    mode = dauphin.NonNull(dauphin.String)

    def __init__(self, mode, selector):
        self.mode = check.str_param(mode, "mode")
        self.message = "Mode {mode} not found in pipeline {pipeline}.".format(
            mode=mode, pipeline=selector.pipeline_name
        )


class DauphinPipelineConfigValidationValid(dauphin.ObjectType):
    class Meta(object):
        name = "PipelineConfigValidationValid"

    pipeline_name = dauphin.NonNull(dauphin.String)


class DauphinPipelineConfigValidationInvalid(dauphin.ObjectType):
    class Meta(object):
        name = "PipelineConfigValidationInvalid"

    pipeline_name = dauphin.NonNull(dauphin.String)
    errors = dauphin.non_null_list("PipelineConfigValidationError")

    @staticmethod
    def for_validation_errors(represented_pipeline, errors):
        check.inst_param(represented_pipeline, "represented_pipeline", RepresentedPipeline)
        check.list_param(errors, "errors", of_type=EvaluationError)
        return DauphinPipelineConfigValidationInvalid(
            pipeline_name=represented_pipeline.name,
            errors=[
                DauphinPipelineConfigValidationError.from_dagster_error(
                    represented_pipeline.config_schema_snapshot, err
                )
                for err in errors
            ],
        )


class DauphinPipelineConfigValidationResult(dauphin.Union):
    class Meta(object):
        name = "PipelineConfigValidationResult"
        types = (
            DauphinInvalidSubsetError,
            DauphinPipelineConfigValidationValid,
            DauphinPipelineConfigValidationInvalid,
            DauphinPipelineNotFoundError,
            DauphinPythonError,
        )


class DauphinPipelineConfigValidationError(dauphin.Interface):
    class Meta(object):
        name = "PipelineConfigValidationError"

    message = dauphin.NonNull(dauphin.String)
    path = dauphin.non_null_list(dauphin.String)
    stack = dauphin.NonNull("EvaluationStack")
    reason = dauphin.NonNull("EvaluationErrorReason")

    @staticmethod
    def from_dagster_error(config_schema_snapshot, error):
        check.inst_param(config_schema_snapshot, "config_schema_snapshot", ConfigSchemaSnapshot)
        check.inst_param(error, "error", EvaluationError)

        if isinstance(error.error_data, RuntimeMismatchErrorData):
            return DauphinRuntimeMismatchConfigError(
                message=error.message,
                path=[],  # TODO: remove
                stack=DauphinEvaluationStack(config_schema_snapshot, error.stack),
                reason=error.reason,
                value_rep=error.error_data.value_rep,
            )
        elif isinstance(error.error_data, MissingFieldErrorData):
            return DauphinMissingFieldConfigError(
                message=error.message,
                path=[],  # TODO: remove
                stack=DauphinEvaluationStack(config_schema_snapshot, error.stack),
                reason=error.reason,
                field=DauphinConfigTypeField(
                    config_schema_snapshot=config_schema_snapshot,
                    field_snap=error.error_data.field_snap,
                ),
            )
        elif isinstance(error.error_data, MissingFieldsErrorData):
            return DauphinMissingFieldsConfigError(
                message=error.message,
                path=[],  # TODO: remove
                stack=DauphinEvaluationStack(config_schema_snapshot, error.stack),
                reason=error.reason,
                fields=[
                    DauphinConfigTypeField(
                        config_schema_snapshot=config_schema_snapshot, field_snap=field_snap,
                    )
                    for field_snap in error.error_data.field_snaps
                ],
            )

        elif isinstance(error.error_data, FieldNotDefinedErrorData):
            return DauphinFieldNotDefinedConfigError(
                message=error.message,
                path=[],  # TODO: remove
                stack=DauphinEvaluationStack(config_schema_snapshot, error.stack),
                reason=error.reason,
                field_name=error.error_data.field_name,
            )
        elif isinstance(error.error_data, FieldsNotDefinedErrorData):
            return DauphinFieldsNotDefinedConfigError(
                message=error.message,
                path=[],  # TODO: remove
                stack=DauphinEvaluationStack(config_schema_snapshot, error.stack),
                reason=error.reason,
                field_names=error.error_data.field_names,
            )
        elif isinstance(error.error_data, SelectorTypeErrorData):
            return DauphinSelectorTypeConfigError(
                message=error.message,
                path=[],  # TODO: remove
                stack=DauphinEvaluationStack(config_schema_snapshot, error.stack),
                reason=error.reason,
                incoming_fields=error.error_data.incoming_fields,
            )
        else:
            check.failed(
                "Error type not supported {error_data}".format(error_data=repr(error.error_data))
            )


class DauphinRuntimeMismatchConfigError(dauphin.ObjectType):
    class Meta(object):
        name = "RuntimeMismatchConfigError"
        interfaces = (DauphinPipelineConfigValidationError,)

    value_rep = dauphin.Field(dauphin.String)


class DauphinMissingFieldConfigError(dauphin.ObjectType):
    class Meta(object):
        name = "MissingFieldConfigError"
        interfaces = (DauphinPipelineConfigValidationError,)

    field = dauphin.NonNull("ConfigTypeField")


class DauphinMissingFieldsConfigError(dauphin.ObjectType):
    class Meta(object):
        name = "MissingFieldsConfigError"
        interfaces = (DauphinPipelineConfigValidationError,)

    fields = dauphin.non_null_list("ConfigTypeField")


class DauphinFieldNotDefinedConfigError(dauphin.ObjectType):
    class Meta(object):
        name = "FieldNotDefinedConfigError"
        interfaces = (DauphinPipelineConfigValidationError,)

    field_name = dauphin.NonNull(dauphin.String)


class DauphinFieldsNotDefinedConfigError(dauphin.ObjectType):
    class Meta(object):
        name = "FieldsNotDefinedConfigError"
        interfaces = (DauphinPipelineConfigValidationError,)

    field_names = dauphin.non_null_list(dauphin.String)


class DauphinSelectorTypeConfigError(dauphin.ObjectType):
    class Meta(object):
        name = "SelectorTypeConfigError"
        interfaces = (DauphinPipelineConfigValidationError,)

    incoming_fields = dauphin.non_null_list(dauphin.String)


class DauphinEvaluationErrorReason(dauphin.Enum):
    class Meta(object):
        name = "EvaluationErrorReason"

    RUNTIME_TYPE_MISMATCH = "RUNTIME_TYPE_MISMATCH"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    MISSING_REQUIRED_FIELDS = "MISSING_REQUIRED_FIELDS"
    FIELD_NOT_DEFINED = "FIELD_NOT_DEFINED"
    FIELDS_NOT_DEFINED = "FIELDS_NOT_DEFINED"
    SELECTOR_FIELD_ERROR = "SELECTOR_FIELD_ERROR"


class DauphinEvaluationStackListItemEntry(dauphin.ObjectType):
    class Meta(object):
        name = "EvaluationStackListItemEntry"

    def __init__(self, list_index):
        super(DauphinEvaluationStackListItemEntry, self).__init__()
        self._list_index = list_index

    list_index = dauphin.NonNull(dauphin.Int)

    def resolve_list_index(self, _info):
        return self._list_index


class DauphinEvaluationStackPathEntry(dauphin.ObjectType):
    class Meta(object):
        name = "EvaluationStackPathEntry"

    def __init__(self, field_name):
        self._field_name = check.str_param(field_name, "field_name")
        super(DauphinEvaluationStackPathEntry, self).__init__()

    field_name = dauphin.NonNull(dauphin.String)

    def resolve_field_name(self, _info):
        return self._field_name


class DauphinEvaluationStackEntry(dauphin.Union):
    class Meta(object):
        name = "EvaluationStackEntry"
        types = (DauphinEvaluationStackListItemEntry, DauphinEvaluationStackPathEntry)

    @staticmethod
    def from_native_entry(entry):
        if isinstance(entry, EvaluationStackPathEntry):
            return DauphinEvaluationStackPathEntry(field_name=entry.field_name)
        elif isinstance(entry, EvaluationStackListItemEntry):
            return DauphinEvaluationStackListItemEntry(list_index=entry.list_index)
        else:
            check.failed("Unsupported stack entry type {entry}".format(entry=entry))


class DauphinEvaluationStack(dauphin.ObjectType):
    def __init__(self, config_schema_snapshot, stack):
        self._config_schema_snapshot = check.inst_param(
            config_schema_snapshot, "config_schema_snapshot", ConfigSchemaSnapshot
        )
        self._stack = stack
        super(DauphinEvaluationStack, self).__init__()

    class Meta(object):
        name = "EvaluationStack"

    entries = dauphin.non_null_list("EvaluationStackEntry")

    def resolve_entries(self, _):
        return map(DauphinEvaluationStackEntry.from_native_entry, self._stack.entries)


class DauphinExecutionPlanOrError(dauphin.Union):
    class Meta(object):
        name = "ExecutionPlanOrError"
        types = (
            "ExecutionPlan",
            DauphinPipelineConfigValidationInvalid,
            DauphinPipelineNotFoundError,
            DauphinInvalidSubsetError,
            DauphinPythonError,
        )


class DauphinExecuteRunInProcessSuccess(dauphin.ObjectType):
    class Meta(object):
        name = "ExecuteRunInProcessSuccess"

    run = dauphin.Field(dauphin.NonNull("PipelineRun"))


class DauphinLaunchPipelineRunSuccess(dauphin.ObjectType):
    class Meta(object):
        name = "LaunchPipelineRunSuccess"

    run = dauphin.Field(dauphin.NonNull("PipelineRun"))


class DauphinInvalidStepError(dauphin.ObjectType):
    class Meta(object):
        name = "InvalidStepError"

    invalid_step_key = dauphin.NonNull(dauphin.String)


class DauphinInvalidOutputError(dauphin.ObjectType):
    class Meta(object):
        name = "InvalidOutputError"

    step_key = dauphin.NonNull(dauphin.String)
    invalid_output_name = dauphin.NonNull(dauphin.String)


class DauphinPipelineRunConflict(dauphin.ObjectType):
    class Meta(object):
        name = "PipelineRunConflict"
        interfaces = (DauphinError,)


create_execution_params_error_types = (
    DauphinPresetNotFoundError,
    DauphinConflictingExecutionParamsError,
)

pipeline_execution_error_types = (
    DauphinInvalidStepError,
    DauphinInvalidOutputError,
    DauphinPipelineConfigValidationInvalid,
    DauphinPipelineNotFoundError,
    DauphinPipelineRunConflict,
    DauphinPythonError,
) + create_execution_params_error_types


launch_pipeline_run_result_types = (DauphinLaunchPipelineRunSuccess,)


class DauphinExecuteRunInProcessResult(dauphin.Union):
    class Meta(object):
        name = "ExecuteRunInProcessResult"
        types = (
            (DauphinExecuteRunInProcessSuccess,)
            + pipeline_execution_error_types
            + (DauphinPipelineRunNotFoundError,)
        )


class DauphinLaunchPipelineExecutionResult(dauphin.Union):
    class Meta(object):
        name = "LaunchPipelineExecutionResult"
        types = launch_pipeline_run_result_types + pipeline_execution_error_types


class DauphinExecutePlanSuccess(dauphin.ObjectType):
    class Meta(object):
        name = "ExecutePlanSuccess"

    pipeline = dauphin.Field(dauphin.NonNull("Pipeline"))
    has_failures = dauphin.Field(dauphin.NonNull(dauphin.Boolean))
    step_events = dauphin.non_null_list(DauphinStepEvent)
    raw_event_records = dauphin.non_null_list(dauphin.String)


class DauphinExecutePlanResult(dauphin.Union):
    class Meta(object):
        name = "ExecutePlanResult"
        types = (
            DauphinExecutePlanSuccess,
            DauphinPipelineConfigValidationInvalid,
            DauphinPipelineNotFoundError,
            DauphinInvalidStepError,
            DauphinPythonError,
        )


class DauphinLaunchPipelineReexecutionResult(dauphin.Union):
    class Meta(object):
        name = "LaunchPipelineReexecutionResult"
        types = launch_pipeline_run_result_types + pipeline_execution_error_types


class DauphinConfigTypeNotFoundError(dauphin.ObjectType):
    class Meta(object):
        name = "ConfigTypeNotFoundError"
        interfaces = (DauphinError,)

    pipeline = dauphin.NonNull("Pipeline")
    config_type_name = dauphin.NonNull(dauphin.String)


class DauphinDagsterTypeNotFoundError(dauphin.ObjectType):
    class Meta(object):
        name = "DagsterTypeNotFoundError"
        interfaces = (DauphinError,)

    dagster_type_name = dauphin.NonNull(dauphin.String)


class DauphinConfigTypeOrError(dauphin.Union):
    class Meta(object):
        name = "ConfigTypeOrError"
        types = (
            "EnumConfigType",
            "CompositeConfigType",
            "RegularConfigType",
            DauphinPipelineNotFoundError,
            DauphinConfigTypeNotFoundError,
            DauphinPythonError,
        )


class DauphinDagsterTypeOrError(dauphin.Union):
    class Meta(object):
        name = "DagsterTypeOrError"
        types = (
            "RegularDagsterType",
            DauphinPipelineNotFoundError,
            DauphinDagsterTypeNotFoundError,
            DauphinPythonError,
        )


class DauphinPipelineRunOrError(dauphin.Union):
    class Meta(object):
        name = "PipelineRunOrError"
        types = ("PipelineRun", DauphinPipelineRunNotFoundError, DauphinPythonError)


class DauphinPipelineRuns(dauphin.ObjectType):
    class Meta(object):
        name = "PipelineRuns"

    results = dauphin.non_null_list("PipelineRun")


class DauphinPipelineRunsOrError(dauphin.Union):
    class Meta(object):
        name = "PipelineRunsOrError"
        types = (DauphinPipelineRuns, DauphinInvalidPipelineRunsFilterError, DauphinPythonError)


class DauphinRunGroupOrError(dauphin.Union):
    class Meta(object):
        name = "RunGroupOrError"
        types = ("RunGroup", DauphinRunGroupNotFoundError, DauphinPythonError)


class DauphinRunGroupsOrError(dauphin.ObjectType):
    class Meta(object):
        name = "RunGroupsOrError"
        types = ("RunGroups", DauphinPythonError)

    results = dauphin.non_null_list("RunGroup")


class DauphinScheduleDefinitionNotFoundError(dauphin.ObjectType):
    class Meta(object):
        name = "ScheduleDefinitionNotFoundError"
        interfaces = (DauphinError,)

    schedule_name = dauphin.NonNull(dauphin.String)

    def __init__(self, schedule_name):
        super(DauphinScheduleDefinitionNotFoundError, self).__init__()
        self.schedule_name = check.str_param(schedule_name, "schedule_name")
        self.message = "Schedule {schedule_name} could not be found.".format(
            schedule_name=self.schedule_name
        )


class DauphinScheduleStateNotFoundError(dauphin.ObjectType):
    class Meta(object):
        name = "ScheduleStateNotFoundError"
        interfaces = (DauphinError,)

    schedule_origin_id = dauphin.NonNull(dauphin.String)

    def __init__(self, schedule_origin_id):
        super(DauphinScheduleStateNotFoundError, self).__init__()
        self.schedule_origin_id = check.str_param(schedule_origin_id, "schedule_origin_id")
        self.message = "State for schedule {schedule_origin_id} could not be found.".format(
            schedule_origin_id=self.schedule_origin_id
        )


class DauphinPartitionSetNotFoundError(dauphin.ObjectType):
    class Meta(object):
        name = "PartitionSetNotFoundError"
        interfaces = (DauphinError,)

    partition_set_name = dauphin.NonNull(dauphin.String)

    def __init__(self, partition_set_name):
        super(DauphinPartitionSetNotFoundError, self).__init__()
        self.partition_set_name = check.str_param(partition_set_name, "partition_set_name")
        self.message = "Partition set {partition_set_name} could not be found.".format(
            partition_set_name=self.partition_set_name
        )


class DauphinPartitionBackfillSuccess(dauphin.ObjectType):
    class Meta(object):
        name = "PartitionBackfillSuccess"

    backfill_id = dauphin.NonNull(dauphin.String)
    launched_run_ids = dauphin.non_null_list(dauphin.String)


class DauphinPartitionBackfillResult(dauphin.Union):
    class Meta(object):
        name = "PartitionBackfillResult"
        types = (
            DauphinPartitionBackfillSuccess,
            DauphinPartitionSetNotFoundError,
        ) + pipeline_execution_error_types


class DauphinTriggerExecutionSuccess(dauphin.ObjectType):
    class Meta(object):
        name = "TriggerExecutionSuccess"

    launched_run_ids = dauphin.non_null_list(dauphin.String)


class DauphinTriggerMutationResult(dauphin.Union):
    class Meta(object):
        name = "TriggerMutationResult"
        types = (DauphinTriggerExecutionSuccess,) + pipeline_execution_error_types


class DauphinRepositoriesOrError(dauphin.Union):
    class Meta(object):
        name = "RepositoriesOrError"
        types = ("RepositoryConnection", DauphinPythonError)


class DauphinRepositoryNotFoundError(dauphin.ObjectType):
    class Meta(object):
        name = "RepositoryNotFoundError"
        interfaces = (DauphinError,)

    repository_name = dauphin.NonNull(dauphin.String)
    repository_location_name = dauphin.NonNull(dauphin.String)

    def __init__(self, repository_location_name, repository_name):
        super(DauphinRepositoryNotFoundError, self).__init__()
        self.repository_name = check.str_param(repository_name, "repository_name")
        self.repository_location_name = check.str_param(
            repository_location_name, "repository_location_name"
        )
        self.message = "Could not find Repository {repository_location_name}.{repository_name}".format(
            repository_name=repository_name, repository_location_name=repository_location_name
        )


class DauphinRepositoryOrError(dauphin.Union):
    class Meta(object):
        name = "RepositoryOrError"
        types = (DauphinPythonError, "Repository", DauphinRepositoryNotFoundError)
