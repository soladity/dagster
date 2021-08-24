import warnings
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union, cast

from dagster import check
from dagster.core.definitions.events import AssetKey
from dagster.core.definitions.solid import SolidDefinition
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.execution.plan.utils import build_resources_for_manager

if TYPE_CHECKING:
    from dagster.core.execution.context.system import StepExecutionContext
    from dagster.core.types.dagster_type import DagsterType
    from dagster.core.definitions import PipelineDefinition
    from dagster.core.log_manager import DagsterLogManager
    from dagster.core.system_config.objects import ResolvedRunConfig
    from dagster.core.definitions.resource import Resources
    from dagster.core.execution.plan.plan import ExecutionPlan
    from dagster.core.execution.plan.outputs import StepOutputHandle

RUN_ID_PLACEHOLDER = "__EPHEMERAL_RUN_ID"


class OutputContext:
    """
    The context object that is available to the `handle_output` method of an :py:class:`IOManager`.

    Attributes:
        step_key (Optional[str]): The step_key for the compute step that produced the output.
        name (Optional[str]): The name of the output that produced the output.
        pipeline_name (Optional[str]): The name of the pipeline definition.
        run_id (Optional[str]): The id of the run that produced the output.
        metadata (Optional[Dict[str, Any]]): A dict of the metadata that is assigned to the
            OutputDefinition that produced the output.
        mapping_key (Optional[str]): The key that identifies a unique mapped output. None for regular outputs.
        config (Optional[Any]): The configuration for the output.
        solid_def (Optional[SolidDefinition]): The definition of the solid that produced the output.
        dagster_type (Optional[DagsterType]): The type of this output.
        log (Optional[DagsterLogManager]): The log manager to use for this output.
        version (Optional[str]): (Experimental) The version of the output.
        resource_config (Optional[Dict[str, Any]]): The config associated with the resource that
            initializes the RootInputManager.
        resources (Optional[Resources]): The resources required by the output manager, specified by the
            `required_resource_keys` parameter.
    """

    def __init__(
        self,
        step_key: Optional[str] = None,
        name: Optional[str] = None,
        pipeline_name: Optional[str] = None,
        run_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        mapping_key: Optional[str] = None,
        config: Optional[Any] = None,
        solid_def: Optional["SolidDefinition"] = None,
        dagster_type: Optional["DagsterType"] = None,
        log_manager: Optional["DagsterLogManager"] = None,
        version: Optional[str] = None,
        resource_config: Optional[Dict[str, Any]] = None,
        resources: Optional[Union["Resources", Dict[str, Any]]] = None,
        step_context: Optional["StepExecutionContext"] = None,
    ):
        from dagster.core.definitions.resource import Resources, IContainsGenerator
        from dagster.core.execution.build_resources import build_resources

        self._step_key = step_key
        self._name = name
        self._pipeline_name = pipeline_name
        self._run_id = run_id
        self._metadata = metadata
        self._mapping_key = mapping_key
        self._config = config
        self._solid_def = solid_def
        self._dagster_type = dagster_type
        self._log = log_manager
        self._version = version
        self._resource_config = resource_config
        self._step_context = step_context

        if isinstance(resources, Resources):
            self._resources_cm = None
            self._resources = resources
        else:
            self._resources_cm = build_resources(
                check.opt_dict_param(resources, "resources", key_type=str)
            )
            self._resources = self._resources_cm.__enter__()  # pylint: disable=no-member
            self._resources_contain_cm = isinstance(self._resources, IContainsGenerator)
            self._cm_scope_entered = False

    def __enter__(self):
        if self._resources_cm:
            self._cm_scope_entered = True
        return self

    def __exit__(self, *exc):
        if self._resources_cm:
            self._resources_cm.__exit__(*exc)  # pylint: disable=no-member

    def __del__(self):
        if self._resources_cm and self._resources_contain_cm and not self._cm_scope_entered:
            self._resources_cm.__exit__(None, None, None)  # pylint: disable=no-member

    @property
    def step_key(self) -> str:
        if self._step_key is None:
            raise DagsterInvariantViolationError(
                "Attempting to access step_key, "
                "but it was not provided when constructing the OutputContext"
            )

        return self._step_key

    @property
    def name(self) -> str:
        if self._name is None:
            raise DagsterInvariantViolationError(
                "Attempting to access name, "
                "but it was not provided when constructing the OutputContext"
            )

        return self._name

    @property
    def pipeline_name(self) -> str:
        if self._pipeline_name is None:
            raise DagsterInvariantViolationError(
                "Attempting to access pipeline_name, "
                "but it was not provided when constructing the OutputContext"
            )

        return self._pipeline_name

    @property
    def run_id(self) -> str:
        if self._run_id is None:
            raise DagsterInvariantViolationError(
                "Attempting to access run_id, "
                "but it was not provided when constructing the OutputContext"
            )

        return self._run_id

    @property
    def metadata(self) -> Optional[Dict[str, Any]]:
        return self._metadata

    @property
    def mapping_key(self) -> Optional[str]:
        return self._mapping_key

    @property
    def config(self) -> Any:
        return self._config

    @property
    def solid_def(self) -> "SolidDefinition":
        if self._solid_def is None:
            raise DagsterInvariantViolationError(
                "Attempting to access solid_def, "
                "but it was not provided when constructing the OutputContext"
            )

        return self._solid_def

    @property
    def dagster_type(self) -> "DagsterType":
        if self._dagster_type is None:
            raise DagsterInvariantViolationError(
                "Attempting to access dagster_type, "
                "but it was not provided when constructing the OutputContext"
            )

        return self._dagster_type

    @property
    def log(self) -> "DagsterLogManager":
        if self._log is None:
            raise DagsterInvariantViolationError(
                "Attempting to access log, "
                "but it was not provided when constructing the OutputContext"
            )

        return self._log

    @property
    def version(self) -> Optional[str]:
        return self._version

    @property
    def resource_config(self) -> Optional[Dict[str, Any]]:
        return self._resource_config

    @property
    def resources(self) -> Any:
        if self._resources is None:
            raise DagsterInvariantViolationError(
                "Attempting to access resources, "
                "but it was not provided when constructing the OutputContext"
            )

        if self._resources_cm and self._resources_contain_cm and not self._cm_scope_entered:
            raise DagsterInvariantViolationError(
                "At least one provided resource is a generator, but attempting to access "
                "resources outside of context manager scope. You can use the following syntax to "
                "open a context manager: `with build_output_context(...) as context:`"
            )
        return self._resources

    @property
    def asset_key(self) -> Optional[AssetKey]:
        matching_output_defs = [
            output_def
            for output_def in cast(SolidDefinition, self._solid_def).output_defs
            if output_def.name == self.name
        ]
        check.invariant(len(matching_output_defs) == 1)
        return matching_output_defs[0].get_asset_key(self)

    @property
    def step_context(self) -> "StepExecutionContext":
        if self._step_context is None:
            raise DagsterInvariantViolationError(
                "Attempting to access step_context, "
                "but it was not provided when constructing the OutputContext"
            )

        return self._step_context

    def get_run_scoped_output_identifier(self) -> List[str]:
        """Utility method to get a collection of identifiers that as a whole represent a unique
        step output.

        The unique identifier collection consists of

        - ``run_id``: the id of the run which generates the output.
            Note: This method also handles the re-execution memoization logic. If the step that
            generates the output is skipped in the re-execution, the ``run_id`` will be the id
            of its parent run.
        - ``step_key``: the key for a compute step.
        - ``name``: the name of the output. (default: 'result').

        Returns:
            List[str, ...]: A list of identifiers, i.e. run id, step key, and output name
        """

        warnings.warn(
            "`OutputContext.get_run_scoped_output_identifier` is deprecated. Use "
            "`OutputContext.get_output_identifier` instead."
        )
        # if run_id is None and this is a re-execution, it means we failed to find its source run id
        check.invariant(
            self.run_id is not None,
            "Unable to find the run scoped output identifier: run_id is None on OutputContext.",
        )
        check.invariant(
            self.step_key is not None,
            "Unable to find the run scoped output identifier: step_key is None on OutputContext.",
        )
        check.invariant(
            self.name is not None,
            "Unable to find the run scoped output identifier: name is None on OutputContext.",
        )
        run_id = cast(str, self.run_id)
        step_key = cast(str, self.step_key)
        name = cast(str, self.name)

        if self.mapping_key:
            return [run_id, step_key, name, self.mapping_key]

        return [run_id, step_key, name]

    def get_output_identifier(self) -> List[str]:
        """Utility method to get a collection of identifiers that as a whole represent a unique
        step output.

        If not using memoization, the unique identifier collection consists of

        - ``run_id``: the id of the run which generates the output.
            Note: This method also handles the re-execution memoization logic. If the step that
            generates the output is skipped in the re-execution, the ``run_id`` will be the id
            of its parent run.
        - ``step_key``: the key for a compute step.
        - ``name``: the name of the output. (default: 'result').

        If using memoization, the ``version`` corresponding to the step output is used in place of
        the ``run_id``.

        Returns:
            List[str, ...]: A list of identifiers, i.e. (run_id or version), step_key, and output_name
        """
        version = self.version
        step_key = self.step_key
        name = self.name
        if version is not None:
            check.invariant(
                self.mapping_key is None,
                f"Mapping key and version both provided for output '{name}' of step '{step_key}'. "
                "Dynamic mapping is not supported when using versioning.",
            )
            identifier = ["versioned_outputs", version, step_key, name]
        else:
            run_id = self.run_id
            identifier = [run_id, step_key, name]
            if self.mapping_key:
                identifier.append(self.mapping_key)

        return identifier


def get_output_context(
    execution_plan: "ExecutionPlan",
    pipeline_def: "PipelineDefinition",
    resolved_run_config: "ResolvedRunConfig",
    step_output_handle: "StepOutputHandle",
    run_id: Optional[str],
    log_manager: Optional["DagsterLogManager"],
    step_context: Optional["StepExecutionContext"],
    resources: Optional["Resources"],
    version: Optional[str],
) -> "OutputContext":
    """
    Args:
        run_id (str): The run ID of the run that produced the output, not necessarily the run that
            the context will be used in.
    """

    step = execution_plan.get_step_by_key(step_output_handle.step_key)
    # get config
    solid_config = resolved_run_config.solids[step.solid_handle.to_string()]
    outputs_config = solid_config.outputs

    if outputs_config:
        output_config = outputs_config.get_output_manager_config(step_output_handle.output_name)
    else:
        output_config = None

    step_output = execution_plan.get_step_output(step_output_handle)
    output_def = pipeline_def.get_solid(step_output.solid_handle).output_def_named(step_output.name)

    io_manager_key = output_def.io_manager_key
    resource_config = resolved_run_config.resources[io_manager_key].config

    if step_context:
        check.invariant(
            not resources,
            "Expected either resources or step context to be set, but "
            "received both. If step context is provided, resources for IO manager will be "
            "retrieved off of that.",
        )
        resources = build_resources_for_manager(io_manager_key, step_context)

    return OutputContext(
        step_key=step_output_handle.step_key,
        name=step_output_handle.output_name,
        pipeline_name=pipeline_def.name,
        run_id=run_id,
        metadata=output_def.metadata,
        mapping_key=step_output_handle.mapping_key,
        config=output_config,
        solid_def=pipeline_def.get_solid(step.solid_handle).definition,
        dagster_type=output_def.dagster_type,
        log_manager=log_manager,
        version=version,
        step_context=step_context,
        resource_config=resource_config,
        resources=resources,
    )


def step_output_version(
    pipeline_def: "PipelineDefinition",
    execution_plan: "ExecutionPlan",
    resolved_run_config: "ResolvedRunConfig",
    step_output_handle: "StepOutputHandle",
) -> Optional[str]:
    from dagster.core.execution.resolve_versions import resolve_step_output_versions

    step_output_versions = resolve_step_output_versions(
        pipeline_def, execution_plan, resolved_run_config
    )
    return (
        step_output_versions[step_output_handle]
        if step_output_handle in step_output_versions
        else None
    )


def build_output_context(
    step_key: Optional[str] = None,
    name: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    run_id: Optional[str] = None,
    mapping_key: Optional[str] = None,
    config: Optional[Any] = None,
    dagster_type: Optional["DagsterType"] = None,
    version: Optional[str] = None,
    resource_config: Optional[Dict[str, Any]] = None,
    resources: Optional[Dict[str, Any]] = None,
    solid_def: Optional[SolidDefinition] = None,
) -> "OutputContext":
    """Builds output context from provided parameters.

    ``build_output_context`` can be used as either a function, or a context manager. If resources
    that are also context managers are provided, then ``build_output_context`` must be used as a
    context manager.

    Args:
        step_key (Optional[str]): The step_key for the compute step that produced the output.
        name (Optional[str]): The name of the output that produced the output.
        metadata (Optional[Dict[str, Any]]): A dict of the metadata that is assigned to the
            OutputDefinition that produced the output.
        mapping_key (Optional[str]): The key that identifies a unique mapped output. None for regular outputs.
        config (Optional[Any]): The configuration for the output.
        dagster_type (Optional[DagsterType]): The type of this output.
        version (Optional[str]): (Experimental) The version of the output.
        resource_config (Optional[Dict[str, Any]]): The resource config to make available from the
            input context. This usually corresponds to the config provided to the resource that
            loads the output manager.
        resources (Optional[Resources]): The resources to make available from the context.
            For a given key, you can provide either an actual instance of an object, or a resource
            definition.
        solid_def (Optional[SolidDefinition]): The definition of the solid that produced the output.

    Examples:

        .. code-block:: python

            build_output_context()

            with build_output_context(resources={"foo": context_manager_resource}) as context:
                do_something

    """
    from dagster.core.types.dagster_type import DagsterType
    from dagster.core.execution.context_creation_pipeline import initialize_console_manager

    step_key = check.opt_str_param(step_key, "step_key")
    name = check.opt_str_param(name, "name")
    metadata = check.opt_dict_param(metadata, "metadata", key_type=str)
    run_id = check.opt_str_param(run_id, "run_id", default=RUN_ID_PLACEHOLDER)
    mapping_key = check.opt_str_param(mapping_key, "mapping_key")
    dagster_type = check.opt_inst_param(dagster_type, "dagster_type", DagsterType)
    version = check.opt_str_param(version, "version")
    resource_config = check.opt_dict_param(resource_config, "resource_config", key_type=str)
    resources = check.opt_dict_param(resources, "resources", key_type=str)
    solid_def = check.opt_inst_param(solid_def, "solid_def", SolidDefinition)

    return OutputContext(
        step_key=step_key,
        name=name,
        pipeline_name=None,
        run_id=run_id,
        metadata=metadata,
        mapping_key=mapping_key,
        config=config,
        solid_def=solid_def,
        dagster_type=dagster_type,
        log_manager=initialize_console_manager(None),
        version=version,
        resource_config=resource_config,
        resources=resources,
        step_context=None,
    )
