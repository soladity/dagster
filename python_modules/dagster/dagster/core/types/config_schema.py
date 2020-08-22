from dagster import check
from dagster.config.config_type import ConfigType, ConfigTypeKind
from dagster.core.decorator_utils import (
    split_function_parameters,
    validate_decorated_fn_positionals,
)
from dagster.core.errors import DagsterInvalidDefinitionError
from dagster.utils import ensure_gen, ensure_single_item
from dagster.utils.backcompat import canonicalize_backcompat_args, rename_warning


class DagsterTypeLoader(object):
    @property
    def schema_type(self):
        check.not_implemented(
            "Must override schema_type in {klass}".format(klass=type(self).__name__)
        )

    def construct_from_config_value(self, _context, config_value):
        """
        How to create a runtime value from config data.
        """
        return config_value

    def required_resource_keys(self):
        return frozenset()


class InputHydrationConfig(DagsterTypeLoader):
    def __init__(self):
        rename_warning("DagsterTypeLoader", "InputHydrationConfig", "0.10.0")
        super(InputHydrationConfig, self).__init__()


class DagsterTypeMaterializer(object):
    @property
    def schema_type(self):
        check.not_implemented(
            "Must override schema_type in {klass}".format(klass=type(self).__name__)
        )

    def materialize_runtime_values(self, _context, _config_value, _runtime_value):
        """
        How to materialize a runtime value given configuration.
        """
        check.not_implemented("Must implement")

    def required_resource_keys(self):
        return frozenset()


class OutputMaterializationConfig(DagsterTypeMaterializer):
    def __init__(self):
        rename_warning("DagsterTypeMaterializer", "OutputMaterializationConfig", "0.10.0")
        super(OutputMaterializationConfig, self).__init__()


class DagsterTypeLoaderFromDecorator(DagsterTypeLoader):
    def __init__(self, config_type, func, required_resource_keys):
        self._config_type = check.inst_param(config_type, "config_type", ConfigType)
        self._func = check.callable_param(func, "func")
        self._required_resource_keys = check.opt_set_param(
            required_resource_keys, "required_resource_keys", of_type=str
        )

    @property
    def schema_type(self):
        return self._config_type

    def construct_from_config_value(self, context, config_value):
        return self._func(context, config_value)

    def required_resource_keys(self):
        return frozenset(self._required_resource_keys)


def _create_type_loader_for_decorator(config_type, func, required_resource_keys):
    return DagsterTypeLoaderFromDecorator(config_type, func, required_resource_keys)


def input_hydration_config(config_schema=None, required_resource_keys=None, config_cls=None):
    """Deprecated in favor of dagster_type_loader"""
    rename_warning("dagster_type_loader", "input_hydration_config", "0.10.0")
    config_schema = canonicalize_backcompat_args(
        config_schema, "config_schema", config_cls, "config_cls", "0.10.0",
    )
    return dagster_type_loader(config_schema, required_resource_keys)


def dagster_type_loader(config_schema, required_resource_keys=None):
    """Create an dagster type loader that maps config data to a runtime value.

    The decorated function should take the execution context and parsed config value and return the
    appropriate runtime value.

    Args:
        config_schema (ConfigSchema): The schema for the config that's passed to the decorated
            function.

    Examples:

    .. code-block:: python

        @dagster_type_loader(Permissive())
        def load_dict(_context, value):
            return value
    """
    from dagster.config.field import resolve_to_config_type

    config_type = resolve_to_config_type(config_schema)
    EXPECTED_POSITIONALS = ["context", "*"]

    def wrapper(func):
        fn_positionals, _ = split_function_parameters(func, EXPECTED_POSITIONALS)
        missing_positional = validate_decorated_fn_positionals(fn_positionals, EXPECTED_POSITIONALS)
        if missing_positional:
            raise DagsterInvalidDefinitionError(
                "@dagster_type_loader '{solid_name}' decorated function does not have required positional "
                "parameter '{missing_param}'. Solid functions should only have keyword arguments "
                "that match input names and a first positional parameter named 'context'.".format(
                    solid_name=func.__name__, missing_param=missing_positional
                )
            )
        return _create_type_loader_for_decorator(config_type, func, required_resource_keys)

    return wrapper


def input_selector_schema(config_cls, required_resource_keys=None):
    """
    Deprecated in favor of dagster_type_loader.

    A decorator for annotating a function that can take the selected properties
    from a ``config_value`` in to an instance of a custom type.

    Args:
        config_cls (Selector)
    """
    rename_warning("dagster_type_loader", "input_selector_schema", "0.10.0")
    from dagster.config.field import resolve_to_config_type

    config_type = resolve_to_config_type(config_cls)
    check.param_invariant(config_type.kind == ConfigTypeKind.SELECTOR, "config_cls")

    def _wrap(func):
        def _selector(context, config_value):
            selector_key, selector_value = ensure_single_item(config_value)
            return func(context, selector_key, selector_value)

        return _create_type_loader_for_decorator(config_type, _selector, required_resource_keys)

    return _wrap


class DagsterTypeMaterializerForDecorator(DagsterTypeMaterializer):
    def __init__(self, config_type, func, required_resource_keys):
        self._config_type = check.inst_param(config_type, "config_type", ConfigType)
        self._func = check.callable_param(func, "func")
        self._required_resource_keys = check.opt_set_param(
            required_resource_keys, "required_resource_keys", of_type=str
        )

    @property
    def schema_type(self):
        return self._config_type

    def materialize_runtime_values(self, context, config_value, runtime_value):
        return ensure_gen(self._func(context, config_value, runtime_value))

    def required_resource_keys(self):
        return frozenset(self._required_resource_keys)


def _create_output_materializer_for_decorator(config_type, func, required_resource_keys):
    return DagsterTypeMaterializerForDecorator(config_type, func, required_resource_keys)


def output_materialization_config(config_schema=None, required_resource_keys=None, config_cls=None):
    """Deprecated in favor of dagster_type_materializer"""
    rename_warning("dagster_type_materializer", "output_materialization_config", "0.10.0")
    config_schema = canonicalize_backcompat_args(
        config_schema, "config_schema", config_cls, "config_cls", "0.10.0",
    )
    return dagster_type_materializer(config_schema, required_resource_keys)


def dagster_type_materializer(config_schema, required_resource_keys=None):
    """Create an output materialization hydration config that configurably materializes a runtime
    value.

    The decorated function should take the execution context, the parsed config value, and the
    runtime value and the parsed config data, should materialize the runtime value, and should
    return an appropriate :py:class:`AssetMaterialization`.

    Args:
        config_schema (Any): The type of the config data expected by the decorated function.

    Examples:

    .. code-block:: python

        # Takes a list of dicts such as might be read in using csv.DictReader, as well as a config
        value, and writes
        @dagster_type_materializer(Path)
        def materialize_df(_context, path, value):
            with open(path, 'w') as fd:
                writer = csv.DictWriter(fd, fieldnames=value[0].keys())
                writer.writeheader()
                writer.writerows(rowdicts=value)

            return AssetMaterialization.file(path)

    """
    from dagster.config.field import resolve_to_config_type

    config_type = resolve_to_config_type(config_schema)
    return lambda func: _create_output_materializer_for_decorator(
        config_type, func, required_resource_keys
    )


def output_selector_schema(config_cls, required_resource_keys=None):
    """
    Deprecated in favor of dagster_type_materializer.

    A decorator for a annotating a function that can take the selected properties
    of a ``config_value`` and an instance of a custom type and materialize it.

    Args:
        config_cls (Selector):
    """
    rename_warning("dagster_type_materializer", "output_selector_schema", "0.10.0")
    from dagster.config.field import resolve_to_config_type

    config_type = resolve_to_config_type(config_cls)
    check.param_invariant(config_type.kind == ConfigTypeKind.SELECTOR, "config_cls")

    def _wrap(func):
        def _selector(context, config_value, runtime_value):
            selector_key, selector_value = ensure_single_item(config_value)
            return func(context, selector_key, selector_value, runtime_value)

        return _create_output_materializer_for_decorator(
            config_type, _selector, required_resource_keys
        )

    return _wrap
