import sys
import time

from dagster import check
from dagster.core.engine.engine_base import Engine
from dagster.core.errors import DagsterSubprocessError
from dagster.core.events import DagsterEvent, EngineEventData
from dagster.core.execution.context.system import SystemPipelineExecutionContext
from dagster.core.execution.plan.plan import ExecutionPlan
from dagster.serdes import deserialize_json_to_dagster_namedtuple
from dagster.utils.error import serializable_error_info_from_exc_info

from .config import CeleryConfig, CeleryK8sJobConfig
from .defaults import task_default_priority, task_default_queue
from .tags import (
    DAGSTER_CELERY_QUEUE_TAG,
    DAGSTER_CELERY_RUN_PRIORITY_TAG,
    DAGSTER_CELERY_STEP_PRIORITY_TAG,
    DAGSTER_STEP_PRIORITY_TAG,
)

TICK_SECONDS = 1
DELEGATE_MARKER = 'celery_queue_wait'


class CeleryEngine(Engine):
    @staticmethod
    def execute(pipeline_context, execution_plan):
        return _core_celery_execution_loop(
            pipeline_context, execution_plan, step_execution_fn=_submit_task
        )


class CeleryK8sJobEngine(Engine):
    @staticmethod
    def execute(pipeline_context, execution_plan):
        return _core_celery_execution_loop(
            pipeline_context, execution_plan, step_execution_fn=_submit_task_k8s_job
        )


def _core_celery_execution_loop(pipeline_context, execution_plan, step_execution_fn):
    from .tasks import make_app

    check.inst_param(pipeline_context, 'pipeline_context', SystemPipelineExecutionContext)
    check.inst_param(execution_plan, 'execution_plan', ExecutionPlan)
    check.callable_param(step_execution_fn, 'step_execution_fn')

    check.param_invariant(
        isinstance(pipeline_context.executor_config, (CeleryConfig, CeleryK8sJobConfig)),
        'pipeline_context',
        'Expected executor_config to be Celery config got {}'.format(
            pipeline_context.executor_config
        ),
    )

    celery_config = pipeline_context.executor_config

    storage = pipeline_context.environment_dict.get('storage')

    # https://github.com/dagster-io/dagster/issues/2440
    check.invariant(
        pipeline_context.system_storage_def.is_persistent,
        'Cannot use in-memory storage with Celery, use filesystem (on top of NFS or '
        'similar system that allows files to be available to all nodes), S3, or GCS',
    )

    app = make_app(celery_config)

    priority_for_step = lambda step: (
        -1 * int(step.tags.get(DAGSTER_CELERY_STEP_PRIORITY_TAG, task_default_priority))
        + -1 * _get_run_priority(pipeline_context)
    )
    priority_for_key = lambda step_key: (
        priority_for_step(execution_plan.get_step_by_key(step_key))
    )
    _warn_on_priority_misuse(pipeline_context, execution_plan)

    step_results = {}  # Dict[ExecutionStep, celery.AsyncResult]
    step_errors = {}
    completed_steps = set({})  # Set[step_key]
    active_execution = execution_plan.start(
        retries=pipeline_context.executor_config.retries, sort_key_fn=priority_for_step
    )
    stopping = False

    while (not active_execution.is_complete and not stopping) or step_results:

        results_to_pop = []
        for step_key, result in sorted(step_results.items(), key=lambda x: priority_for_key(x[0])):
            if result.ready():
                try:
                    step_events = result.get()
                except Exception as e:  # pylint: disable=broad-except
                    # We will want to do more to handle the exception here.. maybe subclass Task
                    # Certainly yield an engine or pipeline event
                    step_events = []
                    step_errors[step_key] = serializable_error_info_from_exc_info(sys.exc_info())
                    stopping = True
                for step_event in step_events:
                    event = deserialize_json_to_dagster_namedtuple(step_event)
                    yield event
                    active_execution.handle_event(event)

                results_to_pop.append(step_key)
                completed_steps.add(step_key)

        for step_key in results_to_pop:
            if step_key in step_results:
                del step_results[step_key]
                active_execution.verify_complete(pipeline_context, step_key)

        # process skips from failures or uncovered inputs
        for event in active_execution.skipped_step_events_iterator(pipeline_context):
            yield event

        # don't add any new steps if we are stopping
        if stopping:
            continue

        # This is a slight refinement. If we have n workers idle and schedule m > n steps for
        # execution, the first n steps will be picked up by the idle workers in the order in
        # which they are scheduled (and the following m-n steps will be executed in priority
        # order, provided that it takes longer to execute a step than to schedule it). The test
        # case has m >> n to exhibit this behavior in the absence of this sort step.
        for step in active_execution.get_steps_to_execute():
            try:
                queue = step.tags.get(DAGSTER_CELERY_QUEUE_TAG, task_default_queue)
                yield DagsterEvent.engine_event(
                    pipeline_context,
                    'Submitting celery task for step "{step_key}" to queue "{queue}".'.format(
                        step_key=step.key, queue=queue
                    ),
                    EngineEventData(marker_start=DELEGATE_MARKER),
                    step_key=step.key,
                )

                # Get the Celery priority for this step
                priority = _get_step_priority(pipeline_context, step)

                # Submit the Celery tasks
                step_results[step.key] = step_execution_fn(
                    app, pipeline_context, step, queue, priority
                )

            except Exception:
                yield DagsterEvent.engine_event(
                    pipeline_context,
                    'Encountered error during celery task submission.'.format(),
                    event_specific_data=EngineEventData.engine_error(
                        serializable_error_info_from_exc_info(sys.exc_info()),
                    ),
                )
                raise

        time.sleep(TICK_SECONDS)

    if step_errors:
        raise DagsterSubprocessError(
            'During celery execution errors occurred in workers:\n{error_list}'.format(
                error_list='\n'.join(
                    [
                        '[{step}]: {err}'.format(step=key, err=err.to_string())
                        for key, err in step_errors.items()
                    ]
                )
            ),
            subprocess_error_infos=list(step_errors.values()),
        )


def _submit_task(app, pipeline_context, step, queue, priority):
    from .tasks import create_task

    task = create_task(app)

    task_signature = task.si(
        instance_ref_dict=pipeline_context.instance.get_ref().to_dict(),
        handle_dict=pipeline_context.execution_target_handle.to_dict(),
        run_id=pipeline_context.pipeline_run.run_id,
        step_keys=[step.key],
        retries_dict=pipeline_context.executor_config.retries.for_inner_plan().to_config(),
    )
    return task_signature.apply_async(
        priority=priority, queue=queue, routing_key='{queue}.execute_plan'.format(queue=queue),
    )


def _submit_task_k8s_job(app, pipeline_context, step, queue, priority):
    from .tasks import create_k8s_job_task

    task = create_k8s_job_task(app)

    task_signature = task.si(
        instance_ref_dict=pipeline_context.instance.get_ref().to_dict(),
        step_keys=[step.key],
        environment_dict=pipeline_context.pipeline_run.environment_dict,
        mode=pipeline_context.pipeline_run.mode,
        pipeline_name=pipeline_context.pipeline_run.pipeline_name,
        run_id=pipeline_context.pipeline_run.run_id,
        job_config_dict=pipeline_context.executor_config.job_config.to_dict(),
        job_namespace=pipeline_context.executor_config.job_namespace,
        load_incluster_config=pipeline_context.executor_config.load_incluster_config,
        kubeconfig_file=pipeline_context.executor_config.kubeconfig_file,
    )

    return task_signature.apply_async(
        priority=priority,
        queue=queue,
        routing_key='{queue}.execute_step_k8s_job'.format(queue=queue),
    )


def _get_step_priority(context, step):
    '''Step priority is (currently) set as the overall pipeline run priority plus the individual
    step priority.
    '''
    run_priority = _get_run_priority(context)
    step_priority = int(step.tags.get(DAGSTER_CELERY_STEP_PRIORITY_TAG, task_default_priority))
    priority = run_priority + step_priority
    return priority


def _get_run_priority(context):
    if not context.has_tag(DAGSTER_CELERY_RUN_PRIORITY_TAG):
        return 0
    try:
        return int(context.get_tag(DAGSTER_CELERY_RUN_PRIORITY_TAG))
    except ValueError:
        return 0


def _warn_on_priority_misuse(context, execution_plan):
    bad_keys = []
    for key in execution_plan.step_keys_to_execute:
        step = execution_plan.get_step_by_key(key)
        if (
            step.tags.get(DAGSTER_STEP_PRIORITY_TAG) is not None
            and step.tags.get(DAGSTER_CELERY_STEP_PRIORITY_TAG) is None
        ):
            bad_keys.append(key)

    if bad_keys:
        context.log.warn(
            'The following steps do not have "dagster-celery/priority" set but do '
            'have "dagster/priority" set which is not applicable for the celery engine: [{}]. '
            'Consider using a function to set both keys.'.format(', '.join(bad_keys))
        )
