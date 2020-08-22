from collections import namedtuple

from dagster import check
from dagster.builtins import BuiltinEnum
from dagster.config.field_utils import check_user_facing_opt_config_param
from dagster.primitive_mapping import is_supported_config_python_builtin
from dagster.utils.backcompat import rename_warning


def is_callable_valid_config_arg(config):
    return BuiltinEnum.contains(config) or is_supported_config_python_builtin(config)


class ConfigMapping(namedtuple("_ConfigMapping", "config_fn config_schema")):
    """Defines a config mapping for a composite solid.

    By specifying a config mapping function, you can override the configuration for the child
    solids contained within a composite solid.

    Config mappings require the configuration schema to be specified as ``config_schema``, which will
    be exposed as the configuration schema for the composite solid, as well as a configuration mapping
    function, ``config_fn``, which maps the config provided to the composite solid to the config
    that will be provided to the child solids.

    Args:
        config_fn (Callable[[dict], dict]): The function that will be called
            to map the composite config to a config appropriate for the child solids.
        config_schema (ConfigSchema): The schema of the composite config.
    """

    def __new__(cls, config_fn, config_schema=None):
        return super(ConfigMapping, cls).__new__(
            cls,
            config_fn=check.callable_param(config_fn, "config_fn"),
            config_schema=check_user_facing_opt_config_param(config_schema, "config_schema"),
        )

    @property
    def config_field(self):
        rename_warning("config_schema", "config_field", "0.9.0")
        return self.config_schema
