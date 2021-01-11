from functools import update_wrapper

from dagster import check
from dagster.core.definitions.config import is_callable_valid_config_arg
from dagster.core.definitions.definition_config_schema import (
    convert_user_facing_definition_config_schema,
)
from dagster.core.definitions.resource import ResourceDefinition
from dagster.core.storage.output_manager import IOutputManagerDefinition, OutputManager
from dagster.core.storage.root_input_manager import IInputManagerDefinition


class IOManagerDefinition(ResourceDefinition, IInputManagerDefinition, IOutputManagerDefinition):
    """Definition of an output manager resource.

    An OutputManagerDefinition is a :py:class:`ResourceDefinition` whose resource_fn returns an
    :py:class:`IOManager`.
    """

    def __init__(
        self,
        resource_fn=None,
        config_schema=None,
        description=None,
        required_resource_keys=None,
        version=None,
        input_config_schema=None,
        output_config_schema=None,
    ):
        self._input_config_schema = input_config_schema
        self._output_config_schema = output_config_schema
        super(IOManagerDefinition, self).__init__(
            resource_fn=resource_fn,
            config_schema=config_schema,
            description=description,
            required_resource_keys=required_resource_keys,
            version=version,
        )

    @property
    def input_config_schema(self):
        return self._input_config_schema

    @property
    def output_config_schema(self):
        return self._output_config_schema

    def copy_for_configured(self, name, description, config_schema, _):
        check.invariant(name is None, "ResourceDefintions do not have names")
        return IOManagerDefinition(
            config_schema=config_schema,
            description=description or self.description,
            resource_fn=self.resource_fn,
            required_resource_keys=self.required_resource_keys,
            input_config_schema=self.input_config_schema,
            output_config_schema=self.output_config_schema,
        )


class IOManager(OutputManager):
    """
    Base class for user-provided IO managers.

    Extend this class to handle how objects are loaded and stored. Users should implement
    ``handle_output`` to store an object and ``load_input`` to retrieve an object.
    """


def io_manager(
    config_schema=None,
    description=None,
    output_config_schema=None,
    input_config_schema=None,
    required_resource_keys=None,
    version=None,
):
    """
    Define an IO manager.

    The decorated function should accept an :py:class:`InitResourceContext and return an
    py:class:`IOManager`.

    Args:
        config_schema (Optional[ConfigSchema]): The schema for the resource config. Configuration
            data available in `init_context.resource_config`.
        description(Optional[str]): A human-readable description of the resource.
        output_config_schema (Optional[ConfigSchema]): The schema for per-output config.
        input_config_schema (Optional[ConfigSchema]): The schema for per-input config.
        required_resource_keys (Optional[Set[str]]): Keys for the resources required by the object
            manager.
        version (Optional[str]): (Experimental) The version of a resource function. Two wrapped
            resource functions should only have the same version if they produce the same resource
            definition when provided with the same inputs.

    **Examples:**

    .. code-block:: python

        class MyIOManager(IOManager):
            def handle_output(self, context, obj):
                write_csv("some/path")

            def load_input(self, context):
                return read_csv("some/path")

        @io_manager
        def my_io_manager(init_context):
            return MyIOManager()

        @solid(output_defs=[OutputDefinition(io_manager_key="my_io_manager_key")])
        def my_solid(_):
            return do_stuff()

        @pipeline(
            mode_defs=[ModeDefinition(resource_defs={"my_io_manager_key": my_io_manager})]
        )
        def my_pipeline():
            my_solid()

        execute_pipeline(my_pipeline)
    """
    if callable(config_schema) and not is_callable_valid_config_arg(config_schema):
        return _IOManagerDecoratorCallable()(config_schema)

    def _wrap(resource_fn):
        return _IOManagerDecoratorCallable(
            config_schema=config_schema,
            description=description,
            required_resource_keys=required_resource_keys,
            version=version,
            output_config_schema=output_config_schema,
            input_config_schema=input_config_schema,
        )(resource_fn)

    return _wrap


class _IOManagerDecoratorCallable:
    def __init__(
        self,
        config_schema=None,
        description=None,
        required_resource_keys=None,
        version=None,
        output_config_schema=None,
        input_config_schema=None,
    ):
        self.config_schema = convert_user_facing_definition_config_schema(config_schema)
        self.description = check.opt_str_param(description, "description")
        self.required_resource_keys = check.opt_set_param(
            required_resource_keys, "required_resource_keys", of_type=str
        )
        self.version = check.opt_str_param(version, "version")
        self.output_config_schema = convert_user_facing_definition_config_schema(
            output_config_schema
        )
        self.input_config_schema = convert_user_facing_definition_config_schema(input_config_schema)

    def __call__(self, fn):
        check.callable_param(fn, "fn")

        io_manager_def = IOManagerDefinition(
            resource_fn=fn,
            config_schema=self.config_schema,
            description=self.description,
            required_resource_keys=self.required_resource_keys,
            version=self.version,
            output_config_schema=self.output_config_schema,
            input_config_schema=self.input_config_schema,
        )

        update_wrapper(io_manager_def, wrapped=fn)

        return io_manager_def
