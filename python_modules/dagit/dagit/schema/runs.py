from __future__ import absolute_import
import graphene

from dagster import check
from dagster.core.events import (
    EventRecord,
    EventType,
)
from dagit import pipeline_run_storage
import dagit.schema.pipelines
import dagit.schema.errors
from dagit.schema import generic, execution
from .utils import non_null_list
from dagster.utils.error import SerializableErrorInfo
PipelineRunStatus = graphene.Enum.from_enum(pipeline_run_storage.PipelineRunStatus)

from dagster.utils.logging import (
    CRITICAL,
    DEBUG,
    ERROR,
    INFO,
    WARNING,
    check_valid_level_param,
)


class PipelineRun(graphene.ObjectType):
    runId = graphene.NonNull(graphene.String)
    status = graphene.NonNull(PipelineRunStatus)
    pipeline = graphene.NonNull(lambda: dagit.schema.pipelines.Pipeline)
    logs = graphene.NonNull(lambda: LogMessageConnection)
    executionPlan = graphene.NonNull(lambda: execution.ExecutionPlan)

    def __init__(self, pipeline_run):
        from dagit.schema import model
        super(PipelineRun, self).__init__(runId=pipeline_run.run_id, status=pipeline_run.status)
        self._pipeline_run = check.inst_param(
            pipeline_run, 'pipeline_run', pipeline_run_storage.PipelineRun
        )

    def resolve_pipeline(self, info):
        from dagit.schema import model
        return model.get_pipeline_or_raise(info.context, self._pipeline_run.pipeline_name)

    def resolve_logs(self, info):
        return LogMessageConnection(self._pipeline_run)

    def resolve_executionPlan(self, info):
        pipeline = self.resolve_pipeline(info)
        return execution.ExecutionPlan(pipeline, self._pipeline_run.execution_plan)


class LogLevel(graphene.Enum):
    CRITICAL = 'CRITICAL'
    ERROR = 'ERROR'
    INFO = 'INFO'
    WARNING = 'WARNING'
    DEBUG = 'DEBUG'

    @staticmethod
    def from_level(level):
        check_valid_level_param(level)
        if level == CRITICAL:
            return LogLevel.CRITICAL
        elif level == ERROR:
            return LogLevel.ERROR
        elif level == INFO:
            return LogLevel.INFO
        elif level == WARNING:
            return LogLevel.WARNING
        elif level == DEBUG:
            return LogLevel.DEBUG
        else:
            check.failed('unknown log level')


class MessageEvent(graphene.Interface):
    run = graphene.NonNull(lambda: PipelineRun)
    message = graphene.NonNull(graphene.String)
    timestamp = graphene.NonNull(graphene.String)
    level = graphene.NonNull(LogLevel)


class LogMessageConnection(graphene.ObjectType):
    nodes = non_null_list(lambda: PipelineRunEvent)
    pageInfo = graphene.NonNull(lambda: generic.PageInfo)

    def __init__(self, pipeline_run):
        self._pipeline_run = check.inst_param(
            pipeline_run, 'pipeline_run', pipeline_run_storage.PipelineRun
        )
        self._logs = self._pipeline_run.all_logs()

    def resolve_nodes(self, info):
        from dagit.schema import model
        pipeline = model.get_pipeline_or_raise(info.context, self._pipeline_run.pipeline_name)
        return [
            PipelineRunEvent.from_dagster_event(info.context, log, pipeline) for log in self._logs
        ]

    def resolve_pageInfo(self, info):
        count = len(self._logs)
        lastCursor = None
        if count > 0:
            lastCursor = str(count - 1)
        return generic.PageInfo(
            lastCursor=lastCursor,
            hasNextPage=None,
            hasPreviousPage=None,
            count=count,
            totalCount=count,
        )


class LogMessageEvent(graphene.ObjectType):
    class Meta:
        interfaces = (MessageEvent, )


class PipelineEvent(graphene.Interface):
    pipeline = graphene.NonNull(lambda: dagit.schema.pipelines.Pipeline)


class PipelineStartEvent(graphene.ObjectType):
    class Meta:
        interfaces = (MessageEvent, PipelineEvent)


class PipelineSuccessEvent(graphene.ObjectType):
    class Meta:
        interfaces = (MessageEvent, PipelineEvent)


class PipelineFailureEvent(graphene.ObjectType):
    class Meta:
        interfaces = (MessageEvent, PipelineEvent)


class ExecutionStepEvent(graphene.Interface):
    step = graphene.NonNull(lambda: dagit.schema.execution.ExecutionStep)


class ExecutionStepStartEvent(graphene.ObjectType):
    class Meta:
        interfaces = (MessageEvent, ExecutionStepEvent)


class ExecutionStepSuccessEvent(graphene.ObjectType):
    class Meta:
        interfaces = (MessageEvent, ExecutionStepEvent)


class ExecutionStepFailureEvent(graphene.ObjectType):
    class Meta:
        interfaces = (MessageEvent, ExecutionStepEvent)

    error = graphene.NonNull(lambda: dagit.schema.errors.PythonError)


# Should be a union of all possible events
class PipelineRunEvent(graphene.Union):
    class Meta:
        types = (
            LogMessageEvent,
            PipelineStartEvent,
            PipelineSuccessEvent,
            PipelineFailureEvent,
            ExecutionStepStartEvent,
            ExecutionStepSuccessEvent,
            ExecutionStepFailureEvent,
        )

    @staticmethod
    def from_dagster_event(context, event, pipeline):
        check.inst_param(event, 'event', EventRecord)
        check.inst_param(pipeline, 'pipeline', dagit.schema.pipelines.Pipeline)
        pipeline_run = context.pipeline_runs.get_run_by_id(event.run_id)
        run = PipelineRun(pipeline_run)

        basic_params = {
            'run': run,
            'message': event.original_message,
            'timestamp': int(event.timestamp * 1000),
            'level': LogLevel.from_level(event.level),
        }

        if event.event_type == EventType.PIPELINE_START:
            return PipelineStartEvent(pipeline=pipeline, **basic_params)
        elif event.event_type == EventType.PIPELINE_SUCCESS:
            return PipelineSuccessEvent(pipeline=pipeline, **basic_params)
        elif event.event_type == EventType.PIPELINE_FAILURE:
            return PipelineFailureEvent(pipeline=pipeline, **basic_params)
        elif event.event_type == EventType.EXECUTION_PLAN_STEP_START:
            return ExecutionStepStartEvent(
                step=dagit.schema.execution.ExecutionStep(
                    pipeline_run.execution_plan.get_step_by_key(event.step_key)
                ),
                **basic_params
            )
        elif event.event_type == EventType.EXECUTION_PLAN_STEP_SUCCESS:
            return ExecutionStepSuccessEvent(
                step=dagit.schema.execution.ExecutionStep(
                    pipeline_run.execution_plan.get_step_by_key(event.step_key)
                ),
                **basic_params
            )
        elif event.event_type == EventType.EXECUTION_PLAN_STEP_FAILURE:
            check.inst(event.error_info, SerializableErrorInfo)
            failure_event = ExecutionStepFailureEvent(
                step=dagit.schema.execution.ExecutionStep(
                    pipeline_run.execution_plan.get_step_by_key(event.step_key)
                ),
                error=dagit.schema.errors.PythonError(event.error_info),
                **basic_params
            )
            return failure_event
        else:
            return LogMessageEvent(**basic_params)
