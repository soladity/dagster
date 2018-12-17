from dagster import check

from dagster.utils import camelcase

from .config import (
    Context,
    Environment,
    Execution,
    Expectations,
    Solid,
)

from .configurable import (
    Configurable,
    ConfigurableObjectFromDict,
    ConfigurableSelectorFromDict,
    Field,
)

from .definitions import (
    PipelineContextDefinition,
    PipelineDefinition,
    ResourceDefinition,
    SolidDefinition,
)

from .evaluator import hard_create_config_value

from .types import (
    Bool,
    DagsterTypeAttributes,
    DagsterType,
    NamedDict,
)


class SystemConfigObject(ConfigurableObjectFromDict, DagsterType):
    pass


class SystemConfigSelector(ConfigurableSelectorFromDict, DagsterType):
    pass


def _is_selector_field_optional(dagster_type):
    if len(dagster_type.field_dict) > 1:
        return False
    else:
        _name, field = single_item(dagster_type.field_dict)
        return field.is_optional


def define_maybe_optional_selector_field(dagster_type):
    check.inst_param(dagster_type, 'dagster_type', SystemConfigSelector)
    is_optional = _is_selector_field_optional(dagster_type)

    return Field(
        dagster_type,
        is_optional=is_optional,
        default_value=lambda: hard_create_config_value(dagster_type, None),
    ) if is_optional else Field(dagster_type)


class SpecificResourceConfig(SystemConfigObject):
    def __init__(self, name, config_field):
        super(SpecificResourceConfig, self).__init__(
            name=name,
            fields={
                'config': config_field,
            },
        )


class ResourceDictionaryType(SystemConfigObject):
    def __init__(self, name, resources):
        check.str_param(name, 'name')
        check.dict_param(
            resources,
            'resources',
            key_type=str,
            value_type=ResourceDefinition,
        )

        field_dict = {}

        for resource_name, resource in resources.items():
            if resource.config_field:
                specific_resource_type = SpecificResourceConfig(
                    name + '.' + resource_name,
                    resource.config_field,
                )
                field_dict[resource_name] = Field(specific_resource_type)

        super(ResourceDictionaryType, self).__init__(
            name=name,
            fields=field_dict,
            type_attributes=DagsterTypeAttributes(is_system_config=True),
        )


class SpecificContextConfig(SystemConfigObject):
    def __init__(self, name, config_field, resources):
        check.str_param(name, 'name')
        check.opt_inst_param(config_field, 'config_field', Field)
        check.dict_param(
            resources,
            'resources',
            key_type=str,
            value_type=ResourceDefinition,
        )
        resource_dict_type = ResourceDictionaryType(
            '{name}.Resources'.format(name=name),
            resources,
        )
        super(SpecificContextConfig, self).__init__(
            name=name,
            fields={
                'config': config_field,
                'resources': Field(resource_dict_type),
            } if config_field else {
                'resources': Field(resource_dict_type),
            },
            type_attributes=DagsterTypeAttributes(is_system_config=True),
        )


def single_item(ddict):
    check.dict_param(ddict, 'ddict')
    check.param_invariant(len(ddict) == 1, 'ddict')
    return list(ddict.items())[0]


class ContextConfigType(SystemConfigSelector):
    def __init__(self, pipeline_name, context_definitions):
        check.str_param(pipeline_name, 'pipeline_name')
        check.dict_param(
            context_definitions,
            'context_definitions',
            key_type=str,
            value_type=PipelineContextDefinition,
        )

        full_type_name = '{pipeline_name}.ContextConfig'.format(pipeline_name=pipeline_name)

        field_dict = {}
        if len(context_definitions) == 1:
            context_name, context_definition = single_item(context_definitions)
            field_dict[context_name] = Field(
                create_specific_context_type(
                    pipeline_name,
                    context_name,
                    context_definition,
                ),
            )
        else:
            for context_name, context_definition in context_definitions.items():
                field_dict[context_name] = Field(
                    create_specific_context_type(
                        pipeline_name,
                        context_name,
                        context_definition,
                    ),
                    is_optional=True,
                )

        super(ContextConfigType, self).__init__(
            name=full_type_name,
            fields=field_dict,
            description='A configuration dictionary with typed fields',
            type_attributes=DagsterTypeAttributes(is_system_config=True),
        )

    def construct_from_config_value(self, config_value):
        context_name, context_value = single_item(config_value)
        return Context(
            name=context_name,
            config=context_value.get('config'),
            resources=context_value['resources'],
        )


def create_specific_context_type(pipeline_name, context_name, context_definition):
    specific_context_config_type = SpecificContextConfig(
        '{pipeline_name}.ContextDefinitionConfig.{context_name}'.format(
            pipeline_name=pipeline_name,
            context_name=camelcase(context_name),
        ),
        context_definition.config_field,
        context_definition.resources,
    )
    return specific_context_config_type


class SolidConfigType(SystemConfigObject):
    def __init__(self, name, config_field, inputs_field):
        check.str_param(name, 'name')
        check.opt_inst_param(config_field, 'config_field', Field)
        check.opt_inst_param(inputs_field, 'inputs_field', Field)
        fields = {}
        if config_field:
            fields['config'] = config_field
        if inputs_field:
            fields['inputs'] = inputs_field

        super(SolidConfigType, self).__init__(
            name=name,
            fields=fields,
            type_attributes=DagsterTypeAttributes(is_system_config=True),
        )

    def construct_from_config_value(self, config_value):
        # TODO we need better rules around optional and default evaluation
        # making this permissive for now
        return Solid(
            config=config_value.get('config'),
            inputs=config_value.get('inputs', {}),
        )


class EnvironmentConfigType(SystemConfigObject):
    def __init__(self, pipeline_def):
        check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)

        pipeline_name = camelcase(pipeline_def.name)

        context_field = define_maybe_optional_selector_field(
            ContextConfigType(pipeline_name, pipeline_def.context_definitions),
        )

        solids_field = Field(
            SolidDictionaryType(
                '{pipeline_name}.SolidsConfigDictionary'.format(pipeline_name=pipeline_name),
                pipeline_def,
            )
        )

        expectations_field = Field(
            ExpectationsConfigType(
                '{pipeline_name}.ExpectationsConfig'.format(pipeline_name=pipeline_name)
            )
        )

        execution_field = Field(
            ExecutionConfigType(
                '{pipeline_name}.ExecutionConfig'.format(pipeline_name=pipeline_name)
            )
        )

        super(EnvironmentConfigType, self).__init__(
            name='{pipeline_name}.Environment'.format(pipeline_name=pipeline_name),
            fields={
                'context': context_field,
                'solids': solids_field,
                'expectations': expectations_field,
                'execution': execution_field,
            },
            type_attributes=DagsterTypeAttributes(is_system_config=True),
        )

    def construct_from_config_value(self, config_value):
        return Environment(**config_value)


class ExpectationsConfigType(SystemConfigObject):
    def __init__(self, name):
        super(ExpectationsConfigType, self).__init__(
            name=name,
            fields={'evaluate': Field(Bool, is_optional=True, default_value=True)},
            type_attributes=DagsterTypeAttributes(is_system_config=True),
        )

    def construct_from_config_value(self, config_value):
        return Expectations(**config_value)


def solid_has_configurable_inputs(solid_definition):
    check.inst_param(solid_definition, 'solid_definition', SolidDefinition)
    return any(map(lambda inp: inp.dagster_type.is_configurable, solid_definition.input_defs))


def get_inputs_field(pipeline_def, solid):
    if not solid_has_configurable_inputs(solid.definition):
        return None

    inputs_field_fields = {}
    for inp in [inp for inp in solid.definition.input_defs if inp.dagster_type.is_configurable]:
        inputs_field_fields[inp.name] = Field(inp.dagster_type, is_optional=True)

    return Field(
        NamedDict(
            '{pipeline_name}.{solid_name}.Inputs'.format(
                pipeline_name=camelcase(pipeline_def.name),
                solid_name=camelcase(solid.name),
            ),
            inputs_field_fields,
        ),
        is_optional=True,
    )


class SolidDictionaryType(SystemConfigObject):
    def __init__(self, name, pipeline_def):
        check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)

        field_dict = {}
        for solid in pipeline_def.solids:
            if solid.definition.config_field or solid_has_configurable_inputs(solid.definition):
                solid_config_type = SolidConfigType(
                    '{pipeline_name}.SolidConfig.{solid_name}'.format(
                        pipeline_name=camelcase(pipeline_def.name),
                        solid_name=camelcase(solid.name),
                    ),
                    solid.definition.config_field,
                    get_inputs_field(pipeline_def, solid),
                )

                field_dict[solid.name] = Field(solid_config_type)

        super(SolidDictionaryType, self).__init__(
            name=name,
            fields=field_dict,
            type_attributes=DagsterTypeAttributes(is_system_config=True),
        )


class ExecutionConfigType(SystemConfigObject):
    def __init__(self, name):
        check.str_param(name, 'name')
        super(ExecutionConfigType, self).__init__(
            name=name,
            fields={
                'serialize_intermediates': Field(Bool, is_optional=True, default_value=False),
            },
            type_attributes=DagsterTypeAttributes(is_system_config=True),
        )

    def construct_from_config_value(self, config_value):
        return Execution(**config_value)
