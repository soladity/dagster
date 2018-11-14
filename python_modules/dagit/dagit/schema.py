import sys
import traceback

import graphene

from graphene.types.generic import GenericScalar

import dagster
import dagster.core.definitions

from dagster import check

from dagster.core.types import DagsterCompositeType

from dagster.core.execution import create_execution_plan


def resolve_pipelines_implementation(_root_obj, info):
    repository = info.context['repository_container'].repository
    pipelines = []
    for pipeline_def in repository.get_all_pipelines():
        pipelines.append(Pipeline(pipeline_def))
    return pipelines


def result_or_error(root_obj, fn, info, *argv):
    error = info.context['repository_container'].error
    if error != None:
        return PythonError(*error)
    try:
        return fn(root_obj, info, *argv)
    except Exception:  # pylint: disable=broad-except
        return PythonError(*sys.exc_info())


def results_or_errors(root_obj, fn, info, *argv):
    error = info.context['repository_container'].error
    if error != None:
        return [PythonError(*error)]
    try:
        return fn(root_obj, info, *argv)
    except Exception:  # pylint: disable=broad-except
        return [PythonError(*sys.exc_info())]


def non_null_list(ttype):
    return graphene.NonNull(graphene.List(graphene.NonNull(ttype)))


class Query(graphene.ObjectType):
    pipeline = graphene.Field(lambda: Pipeline, name=graphene.NonNull(graphene.String))
    pipelineOrError = graphene.Field(
        lambda: PipelineOrError,
        name=graphene.NonNull(graphene.String),
    )

    pipelines = non_null_list(lambda: Pipeline)
    pipelinesOrErrors = non_null_list(lambda: PipelineOrError)

    type = graphene.Field(
        lambda: Type,
        pipelineName=graphene.NonNull(graphene.String),
        typeName=graphene.NonNull(graphene.String),
    )

    types = graphene.NonNull(
        graphene.List(graphene.NonNull(lambda: Type)),
        pipelineName=graphene.NonNull(graphene.String),
    )

    def resolve_pipeline(self, info, name):
        check.str_param(name, 'name')
        repository = info.context['repository_container'].repository
        return Pipeline(repository.get_pipeline(name))

    def resolve_pipelineOrError(self, info, name):
        return result_or_error(self, self.resolve_pipeline, info, name)

    def resolve_pipelines(self, info):
        return resolve_pipelines_implementation(self, info)

    def resolve_pipelinesOrErrors(self, info):
        # self is NoneType here (because array?) for so have to call resolve_pipelines like this
        return results_or_errors(self, resolve_pipelines_implementation, info)

    def resolve_type(self, info, pipelineName, typeName):
        check.str_param(pipelineName, 'pipelineName')
        check.str_param(typeName, 'typeName')
        repository = info.context['repository_container'].repository
        pipeline = repository.get_pipeline(pipelineName)
        return Type.from_dagster_type(pipeline.type_named(typeName))

    def resolve_types(self, info, pipelineName):
        check.str_param(pipelineName, 'pipelineName')
        repository = info.context['repository_container'].repository
        pipeline = repository.get_pipeline(pipelineName)
        return sorted(
            [Type.from_dagster_type(type) for type in pipeline.all_types()],
            key=lambda type: type.name
        )


class Pipeline(graphene.ObjectType):
    name = graphene.NonNull(graphene.String)
    description = graphene.String()
    solids = non_null_list(lambda: Solid)
    contexts = non_null_list(lambda: PipelineContext)
    environment_type = graphene.NonNull(lambda: Type)
    execution_plan = graphene.Field(
        graphene.NonNull(lambda: ExecutionPlan),
        args={
            'config': graphene.Argument(GenericScalar),
        },
    )

    def __init__(self, pipeline):
        super(Pipeline, self).__init__(name=pipeline.name, description=pipeline.description)
        self._pipeline = check.inst_param(pipeline, 'pipeline', dagster.PipelineDefinition)

    def resolve_execution_plan(self, _info, config):
        return ExecutionPlan(self, create_execution_plan(self._pipeline, config))

    def resolve_solids(self, _info):
        return [
            Solid(
                solid,
                self._pipeline.dependency_structure.deps_of_solid_with_input(solid.name),
                self._pipeline.dependency_structure.depended_by_of_solid(solid.name),
            ) for solid in self._pipeline.solids
        ]

    def resolve_contexts(self, _info):
        return [
            PipelineContext(name=name, context=context)
            for name, context in self._pipeline.context_definitions.items()
        ]

    def resolve_environment_type(self, _info):
        return Type.from_dagster_type(self._pipeline.environment_type)


class Error(graphene.Interface):
    message = graphene.String(required=True)
    stack = non_null_list(graphene.String)


class PythonError(graphene.ObjectType):
    class Meta:
        interfaces = (Error, )

    def __init__(self, exc_type, exc_value, exc_tb):
        super(PythonError, self).__init__()
        self.message = traceback.format_exception_only(exc_type, exc_value)[0]
        self.stack = traceback.format_tb(tb=exc_tb)


class PipelineOrError(graphene.Union):
    class Meta:
        types = (Pipeline, PythonError)


class PipelineContext(graphene.ObjectType):
    name = graphene.NonNull(graphene.String)
    description = graphene.String()
    config = graphene.Field(lambda: Config)

    def __init__(self, name, context):
        super(PipelineContext, self).__init__(name=name, description=context.description)
        self._context = check.inst_param(context, 'context', dagster.PipelineContextDefinition)

    def resolve_config(self, _info):
        return Config(self._context.config_def) if self._context.config_def else None


class Solid(graphene.ObjectType):
    name = graphene.NonNull(graphene.String)
    definition = graphene.NonNull(lambda: SolidDefinition)
    inputs = non_null_list(lambda: Input)
    outputs = non_null_list(lambda: Output)

    def __init__(self, solid, depends_on=None, depended_by=None):
        super(Solid, self).__init__(name=solid.name)

        self._solid = check.inst_param(solid, 'solid', dagster.core.definitions.Solid)

        if depends_on:
            self.depends_on = {
                input_handle: output_handle
                for input_handle, output_handle in depends_on.items()
            }
        else:
            self.depends_on = {}

        if depended_by:
            self.depended_by = {
                output_handle: input_handles
                for output_handle, input_handles in depended_by.items()
            }
        else:
            self.depended_by = {}

    def resolve_definition(self, _info):
        return SolidDefinition(self._solid.definition)

    def resolve_inputs(self, _info):
        return [Input(input_handle, self) for input_handle in self._solid.input_handles()]

    def resolve_outputs(self, _info):
        return [Output(output_handle, self) for output_handle in self._solid.output_handles()]


class Input(graphene.ObjectType):
    solid = graphene.NonNull(lambda: Solid)
    definition = graphene.NonNull(lambda: InputDefinition)
    depends_on = graphene.Field(lambda: Output)

    def __init__(self, input_handle, solid):
        super(Input, self).__init__(solid=solid)
        self._solid = check.inst_param(solid, 'solid', Solid)
        self._input_handle = check.inst_param(
            input_handle, 'input_handle', dagster.core.definitions.SolidInputHandle
        )

    def resolve_definition(self, _info):
        return InputDefinition(self._input_handle.input_def, self._solid.resolve_definition({}))

    def resolve_depends_on(self, _info):
        if self._input_handle in self._solid.depends_on:
            return Output(
                self._solid.depends_on[self._input_handle],
                Solid(self._solid.depends_on[self._input_handle].solid),
            )
        else:
            return None


class Output(graphene.ObjectType):
    solid = graphene.NonNull(lambda: Solid)
    definition = graphene.NonNull(lambda: OutputDefinition)
    depended_by = graphene.List(lambda: graphene.NonNull(Input))

    def __init__(self, output_handle, solid):
        super(Output, self).__init__(solid=solid)
        self._solid = check.inst_param(solid, 'solid', Solid)
        self._output_handle = check.inst_param(
            output_handle, 'output_handle', dagster.core.definitions.SolidOutputHandle
        )

    def resolve_definition(self, _info):
        return OutputDefinition(self._output_handle.output_def, self._solid.resolve_definition({}))

    def resolve_depended_by(self, _info):
        return [
            Input(
                input_handle,
                Solid(input_handle.solid),
            ) for input_handle in self._solid.depended_by.get(self._output_handle, [])
        ]


class SolidMetadataItemDefinition(graphene.ObjectType):
    key = graphene.NonNull(graphene.String)
    value = graphene.NonNull(graphene.String)


class SolidDefinition(graphene.ObjectType):
    name = graphene.NonNull(graphene.String)
    description = graphene.String()
    metadata = non_null_list(lambda: SolidMetadataItemDefinition)
    input_definitions = non_null_list(lambda: InputDefinition)
    output_definitions = non_null_list(lambda: OutputDefinition)
    config_definition = graphene.Field(lambda: Config)

    # solids - ?

    def __init__(self, solid_def):
        super(SolidDefinition, self).__init__(
            name=solid_def.name, description=solid_def.description
        )

        self._solid_def = check.inst_param(solid_def, 'solid_def', dagster.SolidDefinition)

    def resolve_metadata(self, _info):
        return [
            SolidMetadataItemDefinition(key=item[0], value=item[1])
            for item in self._solid_def.metadata.items()
        ]

    def resolve_input_definitions(self, _info):
        return [
            InputDefinition(input_definition, self)
            for input_definition in self._solid_def.input_defs
        ]

    def resolve_output_definitions(self, _info):
        return [
            OutputDefinition(output_definition, self)
            for output_definition in self._solid_def.output_defs
        ]

    def resolve_config_definition(self, _info):
        return Config(self._solid_def.config_def) if self._solid_def.config_def else None


class InputDefinition(graphene.ObjectType):
    solid_definition = graphene.NonNull(lambda: SolidDefinition)
    name = graphene.NonNull(graphene.String)
    description = graphene.String()
    type = graphene.NonNull(lambda: Type)
    expectations = non_null_list(lambda: Expectation)

    # inputs - ?

    def __init__(self, input_definition, solid_def):
        super(InputDefinition, self).__init__(
            name=input_definition.name,
            description=input_definition.description,
            solid_definition=solid_def,
        )
        self._input_definition = check.inst_param(
            input_definition, 'input_definition', dagster.InputDefinition
        )

    def resolve_type(self, _info):
        return Type.from_dagster_type(dagster_type=self._input_definition.dagster_type)

    def resolve_expectations(self, _info):
        if self._input_definition.expectations:
            return [Expectation(expectation for expectation in self._input_definition.expectations)]
        else:
            return []


class OutputDefinition(graphene.ObjectType):
    solid_definition = graphene.NonNull(lambda: SolidDefinition)
    name = graphene.NonNull(graphene.String)
    description = graphene.String()
    type = graphene.NonNull(lambda: Type)
    expectations = non_null_list(lambda: Expectation)

    # outputs - ?

    def __init__(self, output_definition, solid_def):
        super(OutputDefinition, self).__init__(
            name=output_definition.name,
            description=output_definition.description,
            solid_definition=solid_def,
        )
        self._output_definition = check.inst_param(
            output_definition, 'output_definition', dagster.OutputDefinition
        )

    def resolve_type(self, _info):
        return Type.from_dagster_type(dagster_type=self._output_definition.dagster_type)

    def resolve_expectations(self, _info):
        if self._output_definition.expectations:
            return [
                Expectation(expectation) for expectation in self._output_definition.expectations
            ]
        else:
            return []


class Expectation(graphene.ObjectType):
    name = graphene.NonNull(graphene.String)
    description = graphene.String()

    def __init__(self, expectation):
        check.inst_param(expectation, 'expectation', dagster.ExpectationDefinition)
        super(Expectation, self).__init__(
            name=expectation.name, description=expectation.description
        )


class Config(graphene.ObjectType):
    type = graphene.NonNull(lambda: Type)

    def __init__(self, config_def):
        super(Config, self).__init__()
        self._config_def = check.opt_inst_param(config_def, 'config_def', dagster.ConfigDefinition)

    def resolve_type(self, _info):
        return Type.from_dagster_type(dagster_type=self._config_def.config_type)


class TypeAttributes(graphene.ObjectType):
    is_builtin = graphene.NonNull(
        graphene.Boolean,
        description='''
True if the system defines it and it is the same type across pipelines.
Examples include "Int" and "String."''',
    )
    is_system_config = graphene.NonNull(
        graphene.Boolean,
        description='''
Dagster generates types for base elements of the config system (e.g. the solids and
context field of the base environment). These types are always present
and are typically not relevant to an end user. This flag allows tool authors to
filter out those types by default.
''',
    )


class Type(graphene.Interface):
    name = graphene.NonNull(graphene.String)
    description = graphene.String()
    type_attributes = graphene.NonNull(TypeAttributes)

    @classmethod
    def from_dagster_type(cls, dagster_type):
        if isinstance(dagster_type, DagsterCompositeType):
            return CompositeType(dagster_type)
        else:
            return RegularType(dagster_type)


class RegularType(graphene.ObjectType):
    class Meta:
        interfaces = [
            Type,
        ]

    def __init__(self, dagster_type):
        super(RegularType, self).__init__(
            name=dagster_type.name,
            description=dagster_type.description,
        )
        self._dagster_type = dagster_type

    def resolve_type_attributes(self, _info):
        return self._dagster_type.type_attributes


class CompositeType(graphene.ObjectType):
    fields = non_null_list(lambda: TypeField)

    class Meta:
        interfaces = [
            Type,
        ]

    def __init__(self, dagster_type):
        super(CompositeType, self).__init__(
            name=dagster_type.name,
            description=dagster_type.description,
        )
        self._dagster_type = dagster_type

    def resolve_type_attributes(self, _info):
        return self._dagster_type.type_attributes

    def resolve_fields(self, _info):
        return [TypeField(name=k, field=v) for k, v in self._dagster_type.field_dict.items()]


class TypeField(graphene.ObjectType):
    name = graphene.NonNull(graphene.String)
    description = graphene.String()
    type = graphene.NonNull(lambda: Type)
    default_value = graphene.String()
    is_optional = graphene.NonNull(graphene.Boolean)

    def __init__(self, name, field):
        super(TypeField, self).__init__(
            name=name,
            description=field.description,
            default_value=str(field.default_value) if field.default_provided else None,
            is_optional=field.is_optional
        )
        self._field = field

    def resolve_type(self, _info):
        return Type.from_dagster_type(dagster_type=self._field.dagster_type)


class ExecutionPlan(graphene.ObjectType):
    steps = non_null_list(lambda: ExecutionStep)
    pipeline = graphene.NonNull(lambda: Pipeline)

    def __init__(self, pipeline, execution_plan):
        super(ExecutionPlan, self).__init__()
        self.execution_plan = check.inst_param(
            execution_plan,
            'execution_plan',
            dagster.core.execution_plan.ExecutionPlan,
        )
        self.pipeline = check.inst_param(pipeline, 'pipeline', Pipeline)

    def resolve_steps(self, _info):
        return [ExecutionStep(cn) for cn in self.execution_plan.topological_steps()]


class ExecutionStepOutput(graphene.ObjectType):
    name = graphene.NonNull(graphene.String)
    type = graphene.Field(graphene.NonNull(lambda: Type))

    def __init__(self, execution_step_output):
        super(ExecutionStepOutput, self).__init__()
        self.execution_step_output = check.inst_param(
            execution_step_output,
            'execution_step_output',
            dagster.core.execution_plan.StepOutput,
        )

    def resolve_name(self, _info):
        return self.execution_step_output.name

    def resolve_type(self, _info):
        return Type.from_dagster_type(dagster_type=self.execution_step_output.dagster_type)


class ExecutionStepInput(graphene.ObjectType):
    name = graphene.NonNull(graphene.String)
    type = graphene.Field(graphene.NonNull(lambda: Type))
    dependsOn = graphene.Field(graphene.NonNull(lambda: ExecutionStep))

    def __init__(self, execution_step_input):
        super(ExecutionStepInput, self).__init__()
        self.execution_step_input = check.inst_param(
            execution_step_input,
            'execution_step_input',
            dagster.core.execution_plan.StepInput,
        )

    def resolve_name(self, _info):
        return self.execution_step_input.name

    def resolve_type(self, _info):
        return Type.from_dagster_type(dagster_type=self.execution_step_input.dagster_type)

    def resolve_dependsOn(self, _info):
        return ExecutionStep(self.execution_step_input.prev_output_handle.step)


class StepTag(graphene.Enum):
    TRANSFORM = 'TRANSFORM'
    INPUT_EXPECTATION = 'INPUT_EXPECTATION'
    OUTPUT_EXPECTATION = 'OUTPUT_EXPECTATION'
    JOIN = 'JOIN'
    SERIALIZE = 'SERIALIZE'

    @property
    def description(self):
        # self ends up being the internal class "EnumMeta" in graphene
        # so we can't do a dictionary lookup which is awesome
        if self == StepTag.TRANSFORM:
            return 'This is the user-defined transform step'
        elif self == StepTag.INPUT_EXPECTATION:
            return 'Expectation defined on an input'
        elif self == StepTag.OUTPUT_EXPECTATION:
            return 'Expectation defined on an output'
        elif self == StepTag.JOIN:
            return '''Sometimes we fan out compute on identical values
(e.g. multiple expectations in parallel). We synthesizie these in a join step to consolidate to
a single output that the next computation can depend on.
'''
        elif self == StepTag.SERIALIZE:
            return '''This is a special system-defined step to serialize
an intermediate value if the pipeline is configured to do that.'''
        else:
            return 'Unknown enum {value}'.format(value=self)


class ExecutionStep(graphene.ObjectType):
    name = graphene.NonNull(graphene.String)
    inputs = non_null_list(lambda: ExecutionStepInput)
    outputs = non_null_list(lambda: ExecutionStepOutput)
    solid = graphene.NonNull(lambda: Solid)
    tag = graphene.NonNull(lambda: StepTag)

    def __init__(self, execution_step):
        super(ExecutionStep, self).__init__()
        self.execution_step = check.inst_param(
            execution_step,
            'execution_step',
            dagster.core.execution_plan.ExecutionStep,
        )

    def resolve_inputs(self, _info):
        return [ExecutionStepInput(inp) for inp in self.execution_step.step_inputs]

    def resolve_outputs(self, _info):
        return [ExecutionStepOutput(out) for out in self.execution_step.step_outputs]

    def resolve_name(self, _info):
        return self.execution_step.friendly_name

    def resolve_solid(self, _info):
        return Solid(self.execution_step.solid)

    def resolve_tag(self, _info):
        return self.execution_step.tag


def create_schema():
    return graphene.Schema(query=Query, types=[RegularType, CompositeType])
