from dagster import (
    PipelineDefinition,
    check,
    types,
)


def scaffold_pipeline_config(pipeline_def, skip_optional=True):
    check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)
    check.bool_param(skip_optional, 'skip_optional')

    env_config_type = pipeline_def.environment_type

    env_dict = {}

    for env_field_name, env_field in env_config_type.field_dict.items():
        if skip_optional and env_field.is_optional:
            continue

        # unfortunately we have to treat this special for now
        if env_field_name == 'context':
            if skip_optional and pipeline_def.environment_type.field_dict['context'].is_optional:
                continue

        env_dict[env_field_name] = scaffold_type(env_field.dagster_type, skip_optional)

    return env_dict


def scaffold_type(config_type, skip_optional=True):
    check.inst_param(config_type, 'config_type', types.DagsterType)
    check.bool_param(skip_optional, 'skip_optional')

    # Right now selectors and composites have the same
    # scaffolding logic, which might not be wise.
    if isinstance(config_type, types.DagsterCompositeTypeBase):
        default_dict = {}
        for field_name, field in config_type.field_dict.items():
            if skip_optional and field.is_optional:
                continue

            default_dict[field_name] = scaffold_type(field.dagster_type, skip_optional)
        return default_dict
    elif config_type is types.PythonDict:
        return {}
    elif config_type is types.Any:
        return 'AnyType'
    elif isinstance(config_type, types.DagsterScalarType):
        defaults = {
            types.String: '',
            types.Path: 'path/to/something',
            types.Int: 0,
            types.Bool: True,
        }

        return defaults[config_type]
    else:
        check.failed('Do not know how to scaffold {type_name}'.format(type_name=config_type.name))
