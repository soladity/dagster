from __future__ import absolute_import

from dagster import check
from dagster.core.execution_plan.objects import ExecutionStep, ExecutionPlan, StepInput, StepOutput

from dagit.schema import dauphin
from .runtime_types import to_dauphin_runtime_type


class DauphinExecutionPlan(dauphin.ObjectType):
    class Meta:
        name = 'ExecutionPlan'

    steps = dauphin.non_null_list('ExecutionStep')
    pipeline = dauphin.NonNull('Pipeline')

    def __init__(self, pipeline, execution_plan):
        super(DauphinExecutionPlan, self).__init__(pipeline=pipeline)
        self.execution_plan = check.inst_param(execution_plan, 'execution_plan', ExecutionPlan)

    def resolve_steps(self, _info):
        return [DauphinExecutionStep(step) for step in self.execution_plan.topological_steps()]


class DauphinExecutionStepOutput(dauphin.ObjectType):
    class Meta:
        name = 'ExecutionStepOutput'

    name = dauphin.NonNull(dauphin.String)
    type = dauphin.Field(dauphin.NonNull('RuntimeType'))

    def __init__(self, step_output):
        super(DauphinExecutionStepOutput, self).__init__()
        self._step_output = check.inst_param(step_output, 'step_output', StepOutput)

    def resolve_name(self, _info):
        return self._step_output.name

    def resolve_type(self, _info):
        return to_dauphin_runtime_type(self._step_output.runtime_type)


class DauphinExecutionStepInput(dauphin.ObjectType):
    class Meta:
        name = 'ExecutionStepInput'

    name = dauphin.NonNull(dauphin.String)
    type = dauphin.Field(dauphin.NonNull('RuntimeType'))
    dependsOn = dauphin.Field(dauphin.NonNull('ExecutionStep'))

    def __init__(self, step_input):
        super(DauphinExecutionStepInput, self).__init__()
        self._step_input = check.inst_param(step_input, 'step_input', StepInput)

    def resolve_name(self, _info):
        return self._step_input.name

    def resolve_type(self, _info):
        return to_dauphin_runtime_type(self._step_input.runtime_type)

    def resolve_dependsOn(self, info):
        return info.schema.type_named('ExecutionStep')(self._step_input.prev_output_handle.step)


class DauphinStepKind(dauphin.Enum):
    class Meta:
        name = 'StepKind'

    TRANSFORM = 'TRANSFORM'
    INPUT_EXPECTATION = 'INPUT_EXPECTATION'
    OUTPUT_EXPECTATION = 'OUTPUT_EXPECTATION'
    JOIN = 'JOIN'
    SERIALIZE = 'SERIALIZE'
    INPUT_THUNK = 'INPUT_THUNK'
    MATERIALIZATION_THUNK = 'MATERIALIZATION_THUNK'

    @property
    def description(self):
        # self ends up being the internal class "EnumMeta" in dauphin
        # so we can't do a dictionary lookup which is awesome
        if self == DauphinStepKind.TRANSFORM:
            return 'This is the user-defined transform step'
        elif self == DauphinStepKind.INPUT_EXPECTATION:
            return 'Expectation defined on an input'
        elif self == DauphinStepKind.OUTPUT_EXPECTATION:
            return 'Expectation defined on an output'
        elif self == DauphinStepKind.JOIN:
            return (
                'Sometimes we fan out compute on identical values (e.g. multiple expectations '
                'in parallel). We synthesize these in a join step to consolidate to a single '
                'output that the next computation can depend on.'
            )
        elif self == DauphinStepKind.SERIALIZE:
            return (
                'This is a special system-defined step to serialize an intermediate value if '
                'the pipeline is configured to do that.'
            )

        elif self == DauphinStepKind.INPUT_THUNK:
            return 'Special system-defined step to represent an input specified in the environment'
        elif self == DauphinStepKind.MATERIALIZATION_THUNK:
            return (
                'Special system-defined step to represent an output materialization specified in '
                'the environment'
            )
        else:
            return 'Unknown enum {value}'.format(value=self)


class DauphinExecutionStep(dauphin.ObjectType):
    class Meta:
        name = 'ExecutionStep'

    name = dauphin.Field(dauphin.NonNull(dauphin.String), deprecation_reason='Use key')
    key = dauphin.NonNull(dauphin.String)
    inputs = dauphin.non_null_list('ExecutionStepInput')
    outputs = dauphin.non_null_list('ExecutionStepOutput')
    solid = dauphin.NonNull('Solid')
    kind = dauphin.NonNull('StepKind')

    def __init__(self, execution_step):
        super(DauphinExecutionStep, self).__init__()
        self.execution_step = check.inst_param(execution_step, 'execution_step', ExecutionStep)

    def resolve_inputs(self, info):
        return [
            info.schema.type_named('ExecutionStepInput')(inp)
            for inp in self.execution_step.step_inputs
        ]

    def resolve_outputs(self, info):
        return [
            info.schema.type_named('ExecutionStepOutput')(out)
            for out in self.execution_step.step_outputs
        ]

    def resolve_key(self, _info):
        return self.execution_step.key

    def resolve_name(self, _info):
        return self.execution_step.key

    def resolve_solid(self, info):
        return info.schema.type_named('Solid')(self.execution_step.solid)

    def resolve_kind(self, _info):
        return self.execution_step.kind
