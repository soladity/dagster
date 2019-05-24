from __future__ import absolute_import
from collections import namedtuple

from rx import Observable

from graphql.execution.base import ResolveInfo

from dagster import RunConfig, check

from dagster.core.events import DagsterEventType
from dagster.core.execution.api import ExecutionSelector, create_execution_plan, execute_plan
from dagster.core.execution.config import ReexecutionConfig
from dagster.core.utils import make_new_run_id

from dagster_graphql.schema.runs import from_event_record, from_dagster_event_record

from .fetch_runs import get_validated_config
from .fetch_pipelines import get_dauphin_pipeline_from_selector
from .utils import capture_dauphin_error, UserFacingGraphQLError


@capture_dauphin_error
def start_pipeline_execution(
    graphene_info,
    selector,
    environment_dict,
    mode,
    step_keys_to_execute,
    reexecution_config,
    graphql_execution_metadata,
):

    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(selector, 'selector', ExecutionSelector)
    check.opt_list_param(step_keys_to_execute, 'step_keys_to_execute', of_type=str)
    check.opt_str_param(mode, 'mode')
    check.opt_inst_param(reexecution_config, 'reexecution_config', ReexecutionConfig)
    graphql_execution_metadata = check.opt_dict_param(
        graphql_execution_metadata, 'graphql_execution_metadata'
    )

    run_id = graphql_execution_metadata.get('runId')

    pipeline_run_storage = graphene_info.context.pipeline_runs

    dauphin_pipeline = get_dauphin_pipeline_from_selector(graphene_info, selector)

    validated_config = get_validated_config(
        graphene_info, dauphin_pipeline, environment_dict, mode=mode
    )

    new_run_id = run_id if run_id else make_new_run_id()

    execution_plan = create_execution_plan(
        dauphin_pipeline.get_dagster_pipeline(), validated_config.value, mode=mode
    )

    run = pipeline_run_storage.create_run(
        new_run_id,
        selector,
        environment_dict,
        mode,
        execution_plan,
        reexecution_config,
        step_keys_to_execute,
    )
    pipeline_run_storage.add_run(run)

    if step_keys_to_execute:
        for step_key in step_keys_to_execute:
            if not execution_plan.has_step(step_key):
                raise UserFacingGraphQLError(
                    graphene_info.schema.type_named('InvalidStepError')(invalid_step_key=step_key)
                )

    if reexecution_config and reexecution_config.step_output_handles:
        for step_output_handle in reexecution_config.step_output_handles:
            if not execution_plan.has_step(step_output_handle.step_key):
                raise UserFacingGraphQLError(
                    graphene_info.schema.type_named('InvalidStepError')(
                        invalid_step_key=step_output_handle.step_key
                    )
                )

            step = execution_plan.get_step_by_key(step_output_handle.step_key)

            if not step.has_step_output(step_output_handle.output_name):
                raise UserFacingGraphQLError(
                    graphene_info.schema.type_named('InvalidOutputError')(
                        step_key=step_output_handle.step_key,
                        invalid_output_name=step_output_handle.output_name,
                    )
                )

    graphene_info.context.execution_manager.execute_pipeline(
        graphene_info.context.handle,
        dauphin_pipeline.get_dagster_pipeline(),
        run,
        raise_on_error=graphene_info.context.raise_on_error,
    )

    return graphene_info.schema.type_named('StartPipelineExecutionSuccess')(
        run=graphene_info.schema.type_named('PipelineRun')(run)
    )


def get_pipeline_run_observable(graphene_info, run_id, after=None):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.str_param(run_id, 'run_id')
    check.opt_str_param(after, 'after')
    pipeline_run_storage = graphene_info.context.pipeline_runs
    run = pipeline_run_storage.get_run_by_id(run_id)

    if not run:

        def _get_error_observable(observer):
            observer.on_next(
                graphene_info.schema.type_named('PipelineRunLogsSubscriptionMissingRunIdFailure')(
                    missingRunId=run_id
                )
            )

        return Observable.create(_get_error_observable)  # pylint: disable=E1101

    def get_observable(pipeline):
        return run.observable_after_cursor(after).map(
            lambda events: graphene_info.schema.type_named('PipelineRunLogsSubscriptionSuccess')(
                runId=run_id,
                messages=[
                    from_event_record(graphene_info, event, pipeline, run.execution_plan)
                    for event in events
                ],
            )
        )

    return get_observable(get_dauphin_pipeline_from_selector(graphene_info, run.selector))


ExecutionParams = namedtuple(
    'ExecutionParams',
    'graphene_info pipeline_name environment_dict mode execution_metadata step_keys',
)


@capture_dauphin_error
def do_execute_plan(
    graphene_info, pipeline_name, environment_dict, mode, execution_metadata, step_keys
):
    check.opt_str_param(mode, 'mode')

    execute_plan_args = ExecutionParams(
        graphene_info=graphene_info,
        pipeline_name=pipeline_name,
        environment_dict=environment_dict,
        mode=mode,
        execution_metadata=execution_metadata,
        step_keys=step_keys,
    )

    return _execute_plan_resolve_config(
        execute_plan_args,
        get_dauphin_pipeline_from_selector(graphene_info, ExecutionSelector(pipeline_name)),
    )


def _execute_plan_resolve_config(execute_plan_args, dauphin_pipeline):
    check.inst_param(execute_plan_args, 'execute_plan_args', ExecutionParams)
    validated_config = get_validated_config(
        execute_plan_args.graphene_info,
        dauphin_pipeline,
        execute_plan_args.environment_dict,
        execute_plan_args.mode,
    )
    return _do_execute_plan(execute_plan_args, dauphin_pipeline, validated_config)


def tags_from_graphql_execution_metadata(graphql_execution_metadata):
    tags = {}
    if graphql_execution_metadata and 'tags' in graphql_execution_metadata:
        for tag in graphql_execution_metadata['tags']:
            tags[tag['key']] = tag['value']
    return tags


def _do_execute_plan(execute_plan_args, dauphin_pipeline, _evaluate_env_config_result):
    check.inst_param(execute_plan_args, 'execute_plan_args', ExecutionParams)

    graphql_execution_metadata = execute_plan_args.execution_metadata
    run_id = graphql_execution_metadata.get('runId') if graphql_execution_metadata else None
    tags = tags_from_graphql_execution_metadata(graphql_execution_metadata)
    execution_plan = create_execution_plan(
        pipeline=dauphin_pipeline.get_dagster_pipeline(),
        environment_dict=execute_plan_args.environment_dict,
        mode=execute_plan_args.mode,
    )

    if execute_plan_args.step_keys:
        for step_key in execute_plan_args.step_keys:
            if not execution_plan.has_step(step_key):
                raise UserFacingGraphQLError(
                    execute_plan_args.graphene_info.schema.type_named('InvalidStepError')(
                        invalid_step_key=step_key
                    )
                )

    event_records = []

    run_config = RunConfig(
        run_id=run_id, mode=execute_plan_args.mode, tags=tags, event_callback=event_records.append
    )

    execute_plan(
        execution_plan=execution_plan,
        environment_dict=execute_plan_args.environment_dict,
        run_config=run_config,
        step_keys_to_execute=execute_plan_args.step_keys,
    )

    return execute_plan_args.graphene_info.schema.type_named('ExecutePlanSuccess')(
        pipeline=dauphin_pipeline,
        has_failures=any(
            er
            for er in event_records
            if er.is_dagster_event and er.dagster_event.event_type == DagsterEventType.STEP_FAILURE
        ),
        step_events=list(
            map(
                lambda er: from_dagster_event_record(
                    execute_plan_args.graphene_info, er, dauphin_pipeline, execution_plan
                ),
                filter(lambda er: er.is_dagster_event, event_records),
            )
        ),
    )
