from collections import defaultdict

from dagster import check
from dagster.core.definitions import PipelineDefinition, Solid, SolidHandle
from dagster.core.definitions.events import ObjectStoreOperation
from dagster.core.definitions.utils import DEFAULT_OUTPUT
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.events import DagsterEvent, DagsterEventType
from dagster.core.execution.plan.objects import StepKind


class PipelineExecutionResult(object):
    '''Output of execution of the whole pipeline. Returned eg by :py:func:`execute_pipeline`.
    '''

    def __init__(self, pipeline, run_id, event_list, reconstruct_context):
        self.pipeline = check.inst_param(pipeline, 'pipeline', PipelineDefinition)
        self.run_id = check.str_param(run_id, 'run_id')
        self.event_list = check.list_param(event_list, 'step_event_list', of_type=DagsterEvent)
        self.reconstruct_context = check.callable_param(reconstruct_context, 'reconstruct_context')

        self._events_by_step_key = self._construct_events_by_step_key(event_list)

    def _construct_events_by_step_key(self, event_list):
        events_by_step_key = defaultdict(list)
        for event in event_list:
            events_by_step_key[event.step_key].append(event)

        return dict(events_by_step_key)

    @property
    def success(self):
        '''Whether the pipeline execution was successful at all steps'''
        return all([not event.is_failure for event in self.event_list])

    @property
    def step_event_list(self):
        '''The full list of step events'''
        return [event for event in self.event_list if event.is_step_event]

    @property
    def events_by_step_key(self):
        return self._events_by_step_key

    def result_for_solid(self, name):
        '''Get a :py:class:`SolidExecutionResult` for a given top level solid name.
        '''
        if not self.pipeline.has_solid_named(name):
            raise DagsterInvariantViolationError(
                'Tried to get result for solid {name} in {pipeline}. No such top level solid.'.format(
                    name=name, pipeline=self.pipeline.display_name
                )
            )

        return self.result_for_handle(name)

    @property
    def solid_result_list(self):
        '''Get a list of :py:class:`SolidExecutionResult`, one for each top level solid.
        '''
        return [self.result_for_solid(solid.name) for solid in self.pipeline.solids]

    def result_for_handle(self, handle):
        '''Get a :py:class:`SolidExecutionResult` for a given solid handle string.
        '''
        check.str_param(handle, 'handle')

        solid_def = self.pipeline.get_solid(SolidHandle.from_string(handle))
        if not solid_def:
            raise DagsterInvariantViolationError(
                'Cant not find solid handle {handle} in pipeline.'.format(handle=handle)
            )

        events_by_kind = defaultdict(list)
        for event in self.event_list:
            if event.is_step_event:
                if event.solid_handle.is_or_descends_from(handle):
                    events_by_kind[event.step_kind].append(event)

        return SolidExecutionResult(solid_def, events_by_kind, self.reconstruct_context)


class SolidExecutionResult(object):
    '''Execution result for one solid of the pipeline.
    '''

    def __init__(self, solid, step_events_by_kind, reconstruct_context):
        self.solid = check.inst_param(solid, 'solid', Solid)
        self.step_events_by_kind = check.dict_param(
            step_events_by_kind, 'step_events_by_kind', key_type=StepKind, value_type=list
        )
        self.reconstruct_context = check.callable_param(reconstruct_context, 'reconstruct_context')

    @property
    def compute_input_event_dict(self):
        '''input_events_during_compute keyed by input name'''
        return {se.event_specific_data.input_name: se for se in self.input_events_during_compute}

    @property
    def input_events_during_compute(self):
        '''All events of type STEP_INPUT'''
        return self._compute_steps_of_type(DagsterEventType.STEP_INPUT)

    @property
    def compute_output_event_dict(self):
        '''output_events_during_compute keyed by output name'''
        return {se.event_specific_data.output_name: se for se in self.output_events_during_compute}

    def get_output_event_for_compute(self, output_name='result'):
        '''The STEP_OUTPUT events for the given output name'''
        return self.compute_output_event_dict[output_name]

    @property
    def output_events_during_compute(self):
        '''All events of type STEP_OUTPUT'''
        return self._compute_steps_of_type(DagsterEventType.STEP_OUTPUT)

    @property
    def compute_step_events(self):
        '''All events that happen during the solid compute function'''
        return self.step_events_by_kind.get(StepKind.COMPUTE, [])

    @property
    def materializations_during_compute(self):
        '''The Materializations objects yielded by the solid'''
        return [
            mat_event.event_specific_data.materialization
            for mat_event in self.materialization_events_during_compute
        ]

    @property
    def materialization_events_during_compute(self):
        '''All events of type STEP_MATERIALIZATION'''
        return self._compute_steps_of_type(DagsterEventType.STEP_MATERIALIZATION)

    @property
    def expectation_events_during_compute(self):
        '''All events of type STEP_EXPECTATION_RESULT'''
        return self._compute_steps_of_type(DagsterEventType.STEP_EXPECTATION_RESULT)

    def _compute_steps_of_type(self, dagster_event_type):
        return list(
            filter(lambda se: se.event_type == dagster_event_type, self.compute_step_events)
        )

    @property
    def expectation_results_during_compute(self):
        '''The ExpectationResult objects yielded by the solid'''
        return [
            expt_event.event_specific_data.expectation_result
            for expt_event in self.expectation_events_during_compute
        ]

    def get_step_success_event(self):
        '''The STEP_SUCCESS event, throws if not present'''
        for step_event in self.compute_step_events:
            if step_event.event_type == DagsterEventType.STEP_SUCCESS:
                return step_event

        check.failed('Step success not found for solid {}'.format(self.solid.name))

    @property
    def compute_step_failure_event(self):
        '''The STEP_FAILURE event, throws if it did not fail'''
        if self.success:
            raise DagsterInvariantViolationError(
                'Cannot call compute_step_failure_event if successful'
            )

        step_failure_events = self._compute_steps_of_type(DagsterEventType.STEP_FAILURE)
        check.invariant(len(step_failure_events) == 1)
        return step_failure_events[0]

    @property
    def success(self):
        '''Whether the solid execution was successful'''
        any_success = False
        for step_event in self.compute_step_events:
            if step_event.event_type == DagsterEventType.STEP_FAILURE:
                return False
            if step_event.event_type == DagsterEventType.STEP_SUCCESS:
                any_success = True

        return any_success

    @property
    def skipped(self):
        '''Whether the solid execution was skipped'''
        return all(
            [
                step_event.event_type == DagsterEventType.STEP_SKIPPED
                for step_event in self.compute_step_events
            ]
        )

    @property
    def output_values(self):
        '''Return dictionary of computed results, with keys being output names.
        Returns None if execution result isn't a success.

        Reconstructs the pipeline context to materialize values.
        '''
        if self.success and self.compute_step_events:
            with self.reconstruct_context() as context:
                values = {
                    compute_step_event.step_output_data.output_name: self._get_value(
                        context, compute_step_event.step_output_data
                    )
                    for compute_step_event in self.compute_step_events
                    if compute_step_event.is_successful_output
                }
            return values
        else:
            return None

    def output_value(self, output_name=DEFAULT_OUTPUT):
        '''Returns computed value either for DEFAULT_OUTPUT or for the output
        given as output_name. Returns None if execution result isn't a success.

        Reconstructs the pipeline context to materialize value.
        '''
        check.str_param(output_name, 'output_name')

        if not self.solid.definition.has_output(output_name):
            raise DagsterInvariantViolationError(
                '{output_name} not defined in solid {solid}'.format(
                    output_name=output_name, solid=self.solid.name
                )
            )

        if self.success:
            for compute_step_event in self.compute_step_events:
                if (
                    compute_step_event.is_successful_output
                    and compute_step_event.step_output_data.output_name == output_name
                ):
                    with self.reconstruct_context() as context:
                        value = self._get_value(context, compute_step_event.step_output_data)
                    return value

            raise DagsterInvariantViolationError(
                (
                    'Did not find result {output_name} in solid {self.solid.name} '
                    'execution result'
                ).format(output_name=output_name, self=self)
            )
        else:
            return None

    def _get_value(self, context, step_output_data):
        value = context.intermediates_manager.get_intermediate(
            context=context,
            runtime_type=self.solid.output_def_named(step_output_data.output_name).runtime_type,
            step_output_handle=step_output_data.step_output_handle,
        )
        if isinstance(value, ObjectStoreOperation):
            return value.obj

        return value

    @property
    def failure_data(self):
        '''Returns the failing step's data that happened during this solid's execution, if any'''
        for step_event in self.compute_step_events:
            if step_event.event_type == DagsterEventType.STEP_FAILURE:
                return step_event.step_failure_data
