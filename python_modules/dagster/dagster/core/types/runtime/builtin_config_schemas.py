import pickle

from dagster import check, seven
from dagster.core.types.config.config_type import (
    ConfigAnyInstance,
    ConfigBoolInstance,
    ConfigFloatInstance,
    ConfigIntInstance,
    ConfigPathInstance,
    ConfigStringInstance,
    ConfigTypeAttributes,
)
from dagster.core.types.config.field import Field
from dagster.core.types.config.field_utils import NamedSelector
from dagster.core.types.wrapping.wrapping import Dict

from .config_schema import input_selector_schema, make_bare_input_schema, output_selector_schema


def define_builtin_scalar_input_schema(scalar_name, config_scalar_type):
    check.str_param(scalar_name, 'scalar_name')

    @input_selector_schema(
        NamedSelector(
            scalar_name + '.InputHydrationConfig',
            {
                'value': Field(config_scalar_type),
                'json': define_path_dict_field(),
                'pickle': define_path_dict_field(),
            },
            type_attributes=ConfigTypeAttributes(is_system_config=True),
        )
    )
    def _builtin_input_schema(_context, file_type, file_options):
        if file_type == 'value':
            return file_options
        elif file_type == 'json':
            with open(file_options['path'], 'r') as ff:
                value_dict = seven.json.load(ff)
                return value_dict['value']
        elif file_type == 'pickle':
            with open(file_options['path'], 'rb') as ff:
                return pickle.load(ff)
        else:
            check.failed('Unsupported key {key}'.format(key=file_type))

    return _builtin_input_schema


def define_path_dict_field():
    return Field(Dict({'path': Field(ConfigPathInstance)}))


def define_builtin_scalar_output_schema(scalar_name):
    check.str_param(scalar_name, 'scalar_name')

    schema_cls = NamedSelector(
        scalar_name + '.MaterializationSchema',
        {'json': define_path_dict_field(), 'pickle': define_path_dict_field()},
        type_attributes=ConfigTypeAttributes(is_system_config=True),
    )

    @output_selector_schema(schema_cls)
    def _builtin_output_schema(_context, file_type, file_options, runtime_value):
        from dagster.core.events import Materialization

        if file_type == 'json':
            json_file_path = file_options['path']
            json_value = seven.json.dumps({'value': runtime_value})
            with open(json_file_path, 'w') as ff:
                ff.write(json_value)
            return Materialization.file(json_file_path)
        elif file_type == 'pickle':
            pickle_file_path = file_options['path']
            with open(pickle_file_path, 'wb') as ff:
                pickle.dump(runtime_value, ff)
            return Materialization.file(pickle_file_path)
        else:
            check.failed('Unsupported file type: {file_type}'.format(file_type=file_type))

    return _builtin_output_schema


class BuiltinSchemas(object):
    ANY_INPUT = define_builtin_scalar_input_schema('Any', ConfigAnyInstance)
    ANY_OUTPUT = define_builtin_scalar_output_schema('Any')

    BOOL_INPUT = define_builtin_scalar_input_schema('Bool', ConfigBoolInstance)
    BOOL_OUTPUT = define_builtin_scalar_output_schema('Bool')

    FLOAT_INPUT = define_builtin_scalar_input_schema('Float', ConfigFloatInstance)
    FLOAT_OUTPUT = define_builtin_scalar_output_schema('Float')

    INT_INPUT = define_builtin_scalar_input_schema('Int', ConfigIntInstance)
    INT_OUTPUT = define_builtin_scalar_output_schema('Int')

    PATH_INPUT = make_bare_input_schema(ConfigPathInstance)
    PATH_OUTPUT = define_builtin_scalar_output_schema('Path')

    STRING_INPUT = define_builtin_scalar_input_schema('String', ConfigStringInstance)
    STRING_OUTPUT = define_builtin_scalar_output_schema('String')
