'''
Naming conventions:

For public functions:

execute_*

These represent functions which do purely in-memory compute. They will evaluate expectations
the core transform, and exercise all logging and metrics tracking (outside of outputs), but they
will not invoke *any* outputs (and their APIs don't allow the user to).


'''

# too many lines
# pylint: disable=C0302

from collections import namedtuple
from contextlib import contextmanager
import itertools
import inspect
import uuid

from contextlib2 import ExitStack
import six

from dagster import (
    check,
    config,
)

from .definitions import (
    DEFAULT_OUTPUT,
    ContextCreationExecutionInfo,
    PipelineDefinition,
    Solid,
)

from .execution_context import (
    ExecutionContext,
    ReentrantInfo,
    RuntimeExecutionContext,
)

from .errors import (
    DagsterInvariantViolationError,
    DagsterUserCodeExecutionError,
)

from .evaluator import (
    EvaluationError,
    evaluate_config_value,
    friendly_string_for_error,
)

from .events import construct_event_logger

from .execution_plan.create import (
    create_execution_plan_core,
    create_subplan,
)

from .execution_plan.objects import (
    ExecutionPlan,
    ExecutionPlanInfo,
    ExecutionSubsetInfo,
    StepResult,
    StepTag,
)

from .execution_plan.simple_engine import execute_plan_core


class PipelineExecutionResult(object):
    '''Result of execution of the whole pipeline. Returned eg by :py:function:`execute_pipeline`.

    Attributes:
        pipeline (PipelineDefinition): Pipeline that was executed
        context (ExecutionContext): ExecutionContext of that particular Pipeline run.
        result_list (list[SolidExecutionResult]): List of results for each pipeline solid.
    '''

    def __init__(
        self,
        pipeline,
        context,
        result_list,
    ):
        self.pipeline = check.inst_param(pipeline, 'pipeline', PipelineDefinition)
        self.context = check.inst_param(context, 'context', RuntimeExecutionContext)
        self.result_list = check.list_param(
            result_list,
            'result_list',
            of_type=SolidExecutionResult,
        )
        self.run_id = context.run_id

    @property
    def success(self):
        '''Whether the pipeline execution was successful at all steps'''
        return all([result.success for result in self.result_list])

    def result_for_solid(self, name):
        '''Get a :py:class:`SolidExecutionResult` for a given solid name.

        Returns:
          SolidExecutionResult
        '''
        check.str_param(name, 'name')

        if not self.pipeline.has_solid(name):
            raise DagsterInvariantViolationError(
                'Try to get result for solid {name} in {pipeline}. No such solid.'.format(
                    name=name,
                    pipeline=self.pipeline.display_name,
                )
            )

        for result in self.result_list:
            if result.solid.name == name:
                return result

        raise DagsterInvariantViolationError(
            'Did not find result for solid {name} in pipeline execution result'.format(name=name)
        )


class SolidExecutionResult(object):
    '''Execution result for one solid of the pipeline.

    Attributes:
      context (ExecutionContext): ExecutionContext of that particular Pipeline run.
      solid (SolidDefinition): Solid for which this result is
    '''

    def __init__(self, context, solid, input_expectations, transforms, output_expectations):
        self.context = check.inst_param(context, 'context', RuntimeExecutionContext)
        self.solid = check.inst_param(solid, 'solid', Solid)
        self.input_expectations = check.list_param(
            input_expectations,
            'input_expectations',
            StepResult,
        )
        self.output_expectations = check.list_param(
            output_expectations,
            'output_expectations',
            StepResult,
        )
        self.transforms = check.list_param(transforms, 'transforms', StepResult)

    @staticmethod
    def from_results(context, results):
        results = check.list_param(results, 'results', StepResult)
        if results:
            input_expectations = []
            output_expectations = []
            transforms = []

            for result in results:
                if result.tag == StepTag.INPUT_EXPECTATION:
                    input_expectations.append(result)
                elif result.tag == StepTag.OUTPUT_EXPECTATION:
                    output_expectations.append(result)
                elif result.tag == StepTag.TRANSFORM:
                    transforms.append(result)

            return SolidExecutionResult(
                context=context,
                solid=results[0].step.solid,
                input_expectations=input_expectations,
                output_expectations=output_expectations,
                transforms=transforms,
            )
        else:
            check.failed("Cannot create SolidExecutionResult from empty list")

    @property
    def success(self):
        '''Whether the solid execution was successful'''
        return all(
            [
                result.success for result in
                itertools.chain(self.input_expectations, self.output_expectations, self.transforms)
            ]
        )

    @property
    def transformed_values(self):
        '''Return dictionary of transformed results, with keys being output names.
        Returns None if execution result isn't a success.'''
        if self.success and self.transforms:
            return {
                result.success_data.output_name: result.success_data.value
                for result in self.transforms
            }
        else:
            return None

    def transformed_value(self, output_name=DEFAULT_OUTPUT):
        '''Returns transformed value either for DEFAULT_OUTPUT or for the output
        given as output_name. Returns None if execution result isn't a success'''
        check.str_param(output_name, 'output_name')

        if not self.solid.definition.has_output(output_name):
            raise DagsterInvariantViolationError(
                '{output_name} not defined in solid {solid}'.format(
                    output_name=output_name,
                    solid=self.solid.name,
                )
            )

        if self.success:
            for result in self.transforms:
                if result.success_data.output_name == output_name:
                    return result.success_data.value
            raise DagsterInvariantViolationError(
                'Did not find result {output_name} in solid {self.solid.name} execution result'.
                format(output_name=output_name, self=self)
            )
        else:
            return None

    def reraise_user_error(self):
        if not self.success:
            for result in itertools.chain(
                self.input_expectations, self.output_expectations, self.transforms
            ):
                if not result.success:
                    if isinstance(
                        result.failure_data.dagster_error,
                        DagsterUserCodeExecutionError,
                    ):
                        six.reraise(*result.failure_data.dagster_error.original_exc_info)
                    else:
                        raise result.failure_data.dagster_error

    @property
    def dagster_error(self):
        '''Returns exception that happened during this solid's execution, if any'''
        for result in itertools.chain(
            self.input_expectations, self.output_expectations, self.transforms
        ):
            if not result.success:
                return result.failure_data.dagster_error


def create_execution_plan(pipeline, typed_environment):
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    check.inst_param(typed_environment, 'environment', config.Environment)

    with yield_context(pipeline, typed_environment) as context:
        return create_execution_plan_core(ExecutionPlanInfo(context, pipeline, typed_environment))


def get_run_id(reentrant_info):
    check.opt_inst_param(reentrant_info, 'reentrant_info', ReentrantInfo)
    if reentrant_info and reentrant_info.run_id:
        return reentrant_info.run_id
    else:
        return str(uuid.uuid4())


def merge_two_dicts(left, right):
    result = left.copy()
    result.update(right)
    return result


def get_context_stack(user_context_params, reentrant_info):
    check.inst(user_context_params, ExecutionContext)
    check.opt_inst_param(reentrant_info, 'reentrant_info', ReentrantInfo)

    if reentrant_info and reentrant_info.context_stack:
        user_keys = set(user_context_params.context_stack.keys())
        reentrant_keys = set(reentrant_info.context_stack.keys())
        if not user_keys.isdisjoint(reentrant_keys):
            raise DagsterInvariantViolationError(
                (
                    'You have specified re-entrant keys and user-defined keys '
                    'that overlap. User keys: {user_keys}. Reentrant keys: '
                    '{reentrant_keys}.'
                ).format(
                    user_keys=user_keys,
                    reentrant_keys=reentrant_keys,
                )
            )

        return merge_two_dicts(user_context_params.context_stack, reentrant_info.context_stack)
    else:
        return user_context_params.context_stack


ResourceCreationInfo = namedtuple('ResourceCreationInfo', 'config run_id')


def _ensure_gen(thing_or_gen):
    if not inspect.isgenerator(thing_or_gen):

        def _gen_thing():
            yield thing_or_gen

        return _gen_thing()

    return thing_or_gen


@contextmanager
def with_maybe_gen(thing_or_gen):
    gen = _ensure_gen(thing_or_gen)

    try:
        thing = next(gen)
    except StopIteration:
        check.failed('Must yield one item. You did not yield anything.')

    yield thing

    stopped = False

    try:
        next(gen)
    except StopIteration:
        stopped = True

    check.invariant(stopped, 'Must yield one item. Yielded more than one item')


@contextmanager
def yield_context(pipeline, environment, reentrant_info=None):
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    check.inst_param(environment, 'environment', config.Environment)
    check.opt_inst_param(reentrant_info, 'reentrant_info', ReentrantInfo)

    context_definition = pipeline.context_definitions[environment.context.name]

    run_id = get_run_id(reentrant_info)

    ec_or_gen = context_definition.context_fn(
        ContextCreationExecutionInfo(
            config=environment.context.config,
            pipeline_def=pipeline,
            run_id=run_id,
        ),
    )

    with with_maybe_gen(ec_or_gen) as execution_context:
        check.inst(execution_context, ExecutionContext)

        with _create_resources(
            pipeline,
            context_definition,
            environment,
            execution_context,
            run_id,
        ) as resources:
            loggers = _create_loggers(reentrant_info, execution_context)

            yield RuntimeExecutionContext(
                run_id=get_run_id(reentrant_info),
                loggers=loggers,
                resources=resources,
                context_stack=get_context_stack(execution_context, reentrant_info),
            )


def _create_loggers(reentrant_info, execution_context):
    if reentrant_info and reentrant_info.event_callback:
        return execution_context.loggers + [construct_event_logger(reentrant_info.event_callback)]
    else:
        return execution_context.loggers


@contextmanager
def _create_resources(pipeline_def, context_def, environment, execution_context, run_id):
    if not context_def.resources:
        yield execution_context.resources
        return

    resources = {}
    check.invariant(
        not execution_context.resources,
        (
            'If resources explicitly specified on context definition, the context '
            'creation function should not return resources as a property of the '
            'ExecutionContext.'
        ),
    )

    # See https://bit.ly/2zIXyqw
    # The "ExitStack" allows one to stack up N context managers and then yield
    # something. We do this so that resources can cleanup after themselves. We
    # can potentially have many resources so we need to use this abstraction.
    with ExitStack() as stack:
        for resource_name in context_def.resources.keys():
            resource_obj_or_gen = get_resource_or_gen(
                context_def,
                resource_name,
                environment,
                run_id,
            )

            resource_obj = stack.enter_context(with_maybe_gen(resource_obj_or_gen))

            resources[resource_name] = resource_obj

        context_name = environment.context.name

        resources_type = pipeline_def.context_definitions[context_name].resources_type
        yield resources_type(**resources)


def get_resource_or_gen(context_definition, resource_name, environment, run_id):
    resource_def = context_definition.resources[resource_name]
    # Need to do default values
    resource_config = environment.context.resources.get(resource_name, {}).get('config')
    return resource_def.resource_fn(ResourceCreationInfo(resource_config, run_id))


def _do_iterate_pipeline(
    pipeline,
    context,
    typed_environment,
    throw_on_error=True,
):
    check.inst(context, RuntimeExecutionContext)
    pipeline_success = True
    with context.value('pipeline', pipeline.display_name):
        context.events.pipeline_start()

        execution_plan = create_execution_plan_core(
            ExecutionPlanInfo(context, pipeline, typed_environment)
        )

        steps = list(execution_plan.topological_steps())

        if not steps:
            context.debug(
                'Pipeline {pipeline} has no nodes and no execution will happen'.format(
                    pipeline=pipeline.display_name
                )
            )
            context.events.pipeline_success()
            return

        context.debug(
            'About to execute the compute node graph in the following order {order}'.format(
                order=[step.key for step in steps]
            )
        )

        check.invariant(len(steps[0].step_inputs) == 0)

        for solid_result in _process_step_results(
            context,
            execute_plan_core(context, execution_plan),
        ):
            if throw_on_error and not solid_result.success:
                solid_result.reraise_user_error()

            if not solid_result.success:
                pipeline_success = False
            yield solid_result

        if pipeline_success:
            context.events.pipeline_success()
        else:
            context.events.pipeline_failure()


def execute_pipeline_iterator(
    pipeline,
    environment=None,
    throw_on_error=True,
    reentrant_info=None,
):
    '''Returns iterator that yields :py:class:`SolidExecutionResult` for each
    solid executed in the pipeline.

    This is intended to allow the caller to do things between each executed
    node. For the 'synchronous' API, see :py:function:`execute_pipeline`.

    Parameters:
      pipeline (PipelineDefinition): pipeline to run
      execution (ExecutionContext): execution context of the run
    '''
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    check.opt_dict_param(environment, 'environment')
    typed_environment = create_typed_environment(pipeline, environment)
    check.bool_param(throw_on_error, 'throw_on_error')
    check.opt_inst_param(reentrant_info, 'reentrant_info', ReentrantInfo)

    with yield_context(pipeline, typed_environment, reentrant_info) as context:
        for solid_result in _do_iterate_pipeline(
            pipeline,
            context,
            typed_environment,
            throw_on_error,
        ):
            yield solid_result


def _process_step_results(context, step_results):
    solid = None
    current_step_results = []
    for step_result in step_results:
        check.inst_param(step_result, 'step_result', StepResult)

        step = step_result.step

        if solid and solid is not step.solid:
            yield SolidExecutionResult.from_results(context, current_step_results)
            current_step_results = []

        if not step_result.success:
            current_step_results.append(step_result)
            yield SolidExecutionResult.from_results(context, current_step_results)
            current_step_results = []
            return

        solid = step.solid
        current_step_results.append(step_result)

    if solid and current_step_results:
        yield SolidExecutionResult.from_results(context, current_step_results)


class PipelineConfigEvaluationError(Exception):
    def __init__(self, pipeline, errors, config_value, *args, **kwargs):
        self.pipeline = check.inst_param(pipeline, 'pipeline', PipelineDefinition)
        self.errors = check.list_param(errors, 'errors', of_type=EvaluationError)
        self.config_value = config_value

        error_msg = 'Pipeline "{pipeline}" config errors:'.format(pipeline=pipeline.name)

        error_messages = []

        for i_error, error in enumerate(self.errors):
            error_message = friendly_string_for_error(error)
            error_messages.append(error_message)
            error_msg += '\n    Error {i_error}: {error_message}'.format(
                i_error=i_error + 1,
                error_message=error_message,
            )

        self.message = error_msg
        self.error_messages = error_messages

        super(PipelineConfigEvaluationError, self).__init__(error_msg, *args, **kwargs)


def execute_plan(pipeline, execution_plan, environment=None, subset_info=None, reentrant_info=None):
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    check.inst_param(execution_plan, 'execution_plan', ExecutionPlan)
    check.opt_dict_param(environment, 'environment')
    check.opt_inst_param(subset_info, 'subset_info', ExecutionSubsetInfo)
    check.opt_inst_param(reentrant_info, 'reentrant_info', ReentrantInfo)

    typed_environment = create_typed_environment(pipeline, environment)

    with yield_context(pipeline, typed_environment, reentrant_info) as context:
        plan_to_execute = create_subplan(
            ExecutionPlanInfo(context=context, pipeline=pipeline, environment=typed_environment),
            execution_plan,
            subset_info,
        ) if subset_info else execution_plan
        return list(execute_plan_core(context, plan_to_execute))


def execute_pipeline(
    pipeline,
    environment=None,
    throw_on_error=True,
    reentrant_info=None,
):
    '''
    "Synchronous" version of :py:function:`execute_pipeline_iterator`.

    Note: throw_on_error is very useful in testing contexts when not testing for error conditions

    Parameters:
      pipeline (PipelineDefinition): Pipeline to run
      environment (config.Environment | dict): The enviroment that parameterizes this run
      throw_on_error (bool):
        throw_on_error makes the function throw when an error is encoutered rather than returning
        the py:class:`SolidExecutionResult` in an error-state.


    Returns:
      PipelineExecutionResult
    '''

    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    check.opt_dict_param(environment, 'environment')
    check.bool_param(throw_on_error, 'throw_on_error')
    check.opt_inst_param(reentrant_info, 'reentrant_info', ReentrantInfo)

    typed_environment = create_typed_environment(pipeline, environment)

    return execute_reentrant_pipeline(pipeline, typed_environment, throw_on_error, reentrant_info)


def execute_reentrant_pipeline(
    pipeline,
    typed_environment,
    throw_on_error,
    reentrant_info,
):
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    check.inst_param(typed_environment, 'typed_environment', config.Environment)
    check.opt_inst_param(reentrant_info, 'reentrant_info', ReentrantInfo)

    with yield_context(pipeline, typed_environment, reentrant_info) as context:
        return PipelineExecutionResult(
            pipeline,
            context,
            list(_do_iterate_pipeline(pipeline, context, typed_environment, throw_on_error)),
        )


def create_typed_environment(pipeline, environment=None):
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    check.opt_dict_param(environment, 'environment')

    pipeline_env_type = pipeline.environment_type
    result = evaluate_config_value(pipeline_env_type, environment)

    if not result.success:
        raise PipelineConfigEvaluationError(pipeline, result.errors, environment)

    return result.value
