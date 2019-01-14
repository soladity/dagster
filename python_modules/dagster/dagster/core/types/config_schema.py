from dagster import check
from dagster.utils import single_item

from .builtin_enum import BuiltinEnum
from .config import ConfigType


class InputSchema:
    @property
    def schema_type(self):
        check.not_implemented(
            'Must override schema_type in {klass}'.format(klass=type(self).__name__)
        )

    def construct_from_config_value(self, config_value):
        return config_value


def resolve_config_cls_arg(config_cls):
    if isinstance(config_cls, BuiltinEnum):
        return ConfigType.from_builtin_enum(config_cls)
    else:
        check.type_param(config_cls, 'config_cls')
        check.param_invariant(issubclass(config_cls, ConfigType), 'config_cls')
        return config_cls.inst()


def make_bare_input_schema(config_cls):
    config_type = resolve_config_cls_arg(config_cls)

    class _InputSchema(InputSchema):
        @property
        def schema_type(self):
            return config_type

    return _InputSchema()


class OutputSchema:
    @property
    def schema_type(self):
        check.not_implemented(
            'Must override schema_type in {klass}'.format(klass=type(self).__name__)
        )

    def materialize_runtime_value(self, _config_value, _runtime_value):
        check.not_implemented('Must implement')


def _create_input_schema(config_type, func):
    class _InputSchema(InputSchema):
        @property
        def schema_type(self):
            return config_type

        def construct_from_config_value(self, config_value):
            return func(config_value)

    return _InputSchema()


def input_schema(config_cls):
    config_type = resolve_config_cls_arg(config_cls)
    return lambda func: _create_input_schema(config_type, func)


def input_selector_schema(config_cls):
    config_type = resolve_config_cls_arg(config_cls)
    check.param_invariant(config_type.is_selector, 'config_cls')

    def _wrap(func):
        def _selector(config_value):
            selector_key, selector_value = single_item(config_value)
            return func(selector_key, selector_value)

        return _create_input_schema(config_type, _selector)

    return _wrap


def _create_output_schema(config_type, func):
    class _OutputSchema(OutputSchema):
        @property
        def schema_type(self):
            return config_type

        def materialize_runtime_value(self, config_value, runtime_value):
            return func(config_value, runtime_value)

    return _OutputSchema()


def output_schema(config_cls):
    config_type = resolve_config_cls_arg(config_cls)
    return lambda func: _create_input_schema(config_type, func)


def output_selector_schema(config_cls):
    config_type = resolve_config_cls_arg(config_cls)
    check.param_invariant(config_type.is_selector, 'config_cls')

    def _wrap(func):
        def _selector(config_value, runtime_value):
            selector_key, selector_value = single_item(config_value)
            return func(selector_key, selector_value, runtime_value)

        return _create_output_schema(config_type, _selector)

    return _wrap
