from collections import OrderedDict
from typing import TYPE_CHECKING, Any, Dict, Iterable, Iterator, List, Optional, Set, Tuple, Union

from dagster import check
from dagster.core.definitions.config import ConfigMapping
from dagster.core.definitions.definition_config_schema import IDefinitionConfigSchema
from dagster.core.definitions.mode import ModeDefinition
from dagster.core.errors import DagsterInvalidDefinitionError
from dagster.core.types.dagster_type import (
    DagsterType,
    DagsterTypeKind,
    construct_dagster_type_dictionary,
)
from toposort import CircularDependencyError, toposort_flatten

from .dependency import (
    DependencyStructure,
    IDependencyDefinition,
    Solid,
    SolidHandle,
    SolidInputHandle,
    SolidInvocation,
)
from .i_solid_definition import NodeDefinition
from .input import FanInInputPointer, InputDefinition, InputMapping, InputPointer
from .output import OutputDefinition, OutputMapping
from .solid_container import create_execution_structure, validate_dependency_dict

if TYPE_CHECKING:
    from .solid import SolidDefinition
    from .resource import ResourceDefinition


def _check_node_defs_arg(graph_name: str, node_defs: List[NodeDefinition]):
    if not isinstance(node_defs, list):
        raise DagsterInvalidDefinitionError(
            '"solids" arg to "{name}" is not a list. Got {val}.'.format(
                name=graph_name, val=repr(node_defs)
            )
        )
    for node_def in node_defs:
        if isinstance(node_def, NodeDefinition):
            continue
        elif callable(node_def):
            raise DagsterInvalidDefinitionError(
                """You have passed a lambda or function {func} into {name} that is
                not a solid. You have likely forgetten to annotate this function with
                an @solid or @lambda_solid decorator.'
                """.format(
                    name=graph_name, func=node_def.__name__
                )
            )
        else:
            raise DagsterInvalidDefinitionError(
                "Invalid item in solid list: {item}".format(item=repr(node_def))
            )

    return node_defs


def _create_adjacency_lists(
    solids: List[Solid],
    dep_structure: DependencyStructure,
) -> Tuple[Dict[str, Set[Solid]], Dict[str, Set[Solid]]]:
    visit_dict = {s.name: False for s in solids}
    forward_edges: Dict[str, Set[Solid]] = {s.name: set() for s in solids}
    backward_edges: Dict[str, Set[Solid]] = {s.name: set() for s in solids}

    def visit(solid_name):
        if visit_dict[solid_name]:
            return

        visit_dict[solid_name] = True

        for output_handle in dep_structure.all_upstream_outputs_from_solid(solid_name):
            forward_node = output_handle.solid.name
            backward_node = solid_name
            if forward_node in forward_edges:
                forward_edges[forward_node].add(backward_node)
                backward_edges[backward_node].add(forward_node)
                visit(forward_node)

    for s in solids:
        visit(s.name)

    return (forward_edges, backward_edges)


class GraphDefinition(NodeDefinition):
    def __init__(
        self,
        name: str,
        description: Optional[str],
        node_defs: List[NodeDefinition],
        dependencies: Optional[Dict[Union[str, SolidInvocation], Dict[str, IDependencyDefinition]]],
        input_mappings: Optional[List[InputMapping]],
        output_mappings: Optional[List[OutputMapping]],
        config_mapping: Optional[ConfigMapping],
        **kwargs,
    ):
        self._node_defs = _check_node_defs_arg(name, node_defs)
        # TODO: backcompat for now
        self._solid_defs = self._node_defs
        self._dagster_type_dict = construct_dagster_type_dictionary(self._node_defs)
        self._dependencies = validate_dependency_dict(dependencies)
        self._dependency_structure, self._solid_dict = create_execution_structure(
            node_defs, self._dependencies, graph_definition=self
        )

        # List[InputMapping]
        self._input_mappings, input_defs = _validate_in_mappings(
            check.opt_list_param(input_mappings, "input_mappings"),
            self._solid_dict,
            self._dependency_structure,
            name,
            class_name=type(self).__name__,
        )
        # List[OutputMapping]
        self._output_mappings = _validate_out_mappings(
            check.opt_list_param(output_mappings, "output_mappings"),
            self._solid_dict,
            self._dependency_structure,
            name,
            class_name=type(self).__name__,
        )

        self._config_mapping = check.opt_inst_param(config_mapping, "config_mapping", ConfigMapping)

        super(GraphDefinition, self).__init__(
            name=name,
            description=description,
            input_defs=input_defs,
            output_defs=[output_mapping.definition for output_mapping in self._output_mappings],
            **kwargs,
        )

        # must happen after base class construction as properties are assumed to be there
        # eager computation to detect cycles
        self.solids_in_topological_order = self._solids_in_topological_order()

    def _solids_in_topological_order(self):

        _forward_edges, backward_edges = _create_adjacency_lists(
            self.solids, self.dependency_structure
        )

        try:
            order = toposort_flatten(backward_edges)
        except CircularDependencyError as err:
            raise DagsterInvalidDefinitionError(str(err)) from err

        return [self.solid_named(solid_name) for solid_name in order]

    @property
    def solids(self) -> List[Solid]:
        """List[Solid]: Top-level solids in the graph."""
        return list(set(self._solid_dict.values()))

    @property
    def node_defs(self) -> List[NodeDefinition]:
        """List[NodeDefinition]: List of nodes in the graph."""
        return self._node_defs

    def has_solid_named(self, name: str) -> bool:
        """Return whether or not there is a top level solid with this name in the graph.

        Args:
            name (str): Name of solid

        Returns:
            bool: True if the solid is in the graph.
        """
        check.str_param(name, "name")
        return name in self._solid_dict

    def solid_named(self, name: str) -> Solid:
        """Return the top level solid named "name". Throws if it does not exist.

        Args:
            name (str): Name of solid

        Returns:
            Solid:
        """
        check.str_param(name, "name")
        check.invariant(
            name in self._solid_dict,
            "{graph_name} has no solid named {name}.".format(graph_name=self._name, name=name),
        )

        return self._solid_dict[name]

    def get_solid(self, handle: SolidHandle) -> Solid:
        """Return the solid contained anywhere within the graph via its handle.

        Args:
            handle (SolidHandle): The solid's handle

        Returns:
            Solid:

        """
        check.inst_param(handle, "handle", SolidHandle)
        current = handle
        lineage = []
        while current:
            lineage.append(current.name)
            current = current.parent

        name = lineage.pop()
        solid = self.solid_named(name)
        while lineage:
            name = lineage.pop()
            solid = solid.definition.solid_named(name)

        return solid

    def iterate_node_defs(self) -> Iterator[NodeDefinition]:
        yield self
        for outer_node_def in self._node_defs:
            yield from outer_node_def.iterate_node_defs()

    def iterate_solid_defs(self) -> Iterator["SolidDefinition"]:
        for outer_node_def in self._node_defs:
            yield from outer_node_def.iterate_solid_defs()

    @property
    def input_mappings(self) -> List[InputMapping]:
        return self._input_mappings

    @property
    def output_mappings(self) -> List[OutputMapping]:
        return self._output_mappings

    @property
    def config_mapping(self) -> Optional[ConfigMapping]:
        return self._config_mapping

    @property
    def has_config_mapping(self) -> bool:
        return self._config_mapping is not None

    def all_dagster_types(self) -> Iterable[DagsterType]:
        return self._dagster_type_dict.values()

    def get_input_mapping(self, input_name: str) -> InputMapping:
        check.str_param(input_name, "input_name")
        for mapping in self._input_mappings:
            if mapping.definition.name == input_name:
                return mapping
        check.failed(f"Could not find input mapping {input_name}")

    def input_mapping_for_pointer(
        self, pointer: Union[InputPointer, FanInInputPointer]
    ) -> Optional[InputMapping]:
        check.inst_param(pointer, "pointer", (InputPointer, FanInInputPointer))

        for mapping in self._input_mappings:
            if mapping.maps_to == pointer:
                return mapping
        return None

    def get_output_mapping(self, output_name: str) -> OutputMapping:
        check.str_param(output_name, "output_name")
        for mapping in self._output_mappings:
            if mapping.definition.name == output_name:
                return mapping
        check.failed(f"Could not find output mapping {output_name}")

    def resolve_output_to_origin(
        self, output_name: str, handle: SolidHandle
    ) -> Tuple[OutputDefinition, SolidHandle]:
        check.str_param(output_name, "output_name")
        check.inst_param(handle, "handle", SolidHandle)

        mapping = self.get_output_mapping(output_name)
        check.invariant(mapping, "Can only resolve outputs for valid output names")
        mapped_solid = self.solid_named(mapping.maps_from.solid_name)
        return mapped_solid.definition.resolve_output_to_origin(
            mapping.maps_from.output_name,
            SolidHandle(mapped_solid.name, handle),
        )

    def default_value_for_input(self, input_name: str) -> Any:
        check.str_param(input_name, "input_name")

        # base case
        if self.input_def_named(input_name).has_default_value:
            return self.input_def_named(input_name).default_value

        mapping = self.get_input_mapping(input_name)
        check.invariant(mapping, "Can only resolve inputs for valid input names")
        mapped_solid = self.solid_named(mapping.maps_to.solid_name)

        return mapped_solid.definition.default_value_for_input(mapping.maps_to.input_name)

    def input_has_default(self, input_name: str) -> bool:
        check.str_param(input_name, "input_name")

        # base case
        if self.input_def_named(input_name).has_default_value:
            return True

        mapping = self.get_input_mapping(input_name)
        check.invariant(mapping, "Can only resolve inputs for valid input names")
        mapped_solid = self.solid_named(mapping.maps_to.solid_name)

        return mapped_solid.definition.input_has_default(mapping.maps_to.input_name)

    @property
    def dependencies(self) -> Dict[Union[str, SolidInvocation], Dict[str, IDependencyDefinition]]:
        return self._dependencies

    @property
    def dependency_structure(self) -> DependencyStructure:
        return self._dependency_structure

    @property
    def config_schema(self) -> Optional[IDefinitionConfigSchema]:
        return self.config_mapping.config_schema if self.config_mapping is not None else None

    def input_supports_dynamic_output_dep(self, input_name: str) -> bool:
        mapping = self.get_input_mapping(input_name)
        internal_dynamic_handle = self.dependency_structure.get_upstream_dynamic_handle_for_solid(
            mapping.maps_to.solid_name
        )
        if internal_dynamic_handle:
            return False

        return True

    def copy_for_configured(
        self,
        name: str,
        description: Optional[str],
        config_schema: Any,
        config_or_config_fn: Any,
    ):
        check.not_implemented("@graph does not yet implement configured")

    def to_job(
        self,
        resource_defs: Dict[str, "ResourceDefinition"],
    ):
        """
        For experimenting with "job" flows
        """
        from .pipeline import PipelineDefinition

        return PipelineDefinition(
            solid_defs=self._solid_defs,
            name=self.name,
            description=self.description,
            dependencies=self._dependencies,
            input_mappings=self._input_mappings,
            output_mappings=self._output_mappings,
            config_mapping=self._config_mapping,
            mode_defs=[ModeDefinition(resource_defs=resource_defs)],
        )


def _validate_in_mappings(
    input_mappings: List[InputMapping],
    solid_dict: Dict[str, Solid],
    dependency_structure: DependencyStructure,
    name: str,
    class_name: str,
) -> Tuple[List[InputMapping], Iterable[InputDefinition]]:
    from .composition import MappedInputPlaceholder

    input_def_dict: Dict[str, InputDefinition] = OrderedDict()
    mapping_keys = set()

    for mapping in input_mappings:
        # handle incorrect objects passed in as mappings
        if not isinstance(mapping, InputMapping):
            if isinstance(mapping, InputDefinition):
                raise DagsterInvalidDefinitionError(
                    "In {class_name} '{name}' you passed an InputDefinition "
                    "named '{input_name}' directly in to input_mappings. Return "
                    "an InputMapping by calling mapping_to on the InputDefinition.".format(
                        name=name, input_name=mapping.name, class_name=class_name
                    )
                )
            else:
                raise DagsterInvalidDefinitionError(
                    "In {class_name} '{name}' received unexpected type '{type}' in input_mappings. "
                    "Provide an OutputMapping using InputDefinition(...).mapping_to(...)".format(
                        type=type(mapping), name=name, class_name=class_name
                    )
                )

        if input_def_dict.get(mapping.definition.name):
            if input_def_dict[mapping.definition.name] != mapping.definition:
                raise DagsterInvalidDefinitionError(
                    "In {class_name} {name} multiple input mappings with same "
                    "definition name but different definitions".format(
                        name=name, class_name=class_name
                    ),
                )
        else:
            input_def_dict[mapping.definition.name] = mapping.definition

        target_solid = solid_dict.get(mapping.maps_to.solid_name)
        if target_solid is None:
            raise DagsterInvalidDefinitionError(
                "In {class_name} '{name}' input mapping references solid "
                "'{solid_name}' which it does not contain.".format(
                    name=name, solid_name=mapping.maps_to.solid_name, class_name=class_name
                )
            )
        if not target_solid.has_input(mapping.maps_to.input_name):
            raise DagsterInvalidDefinitionError(
                "In {class_name} '{name}' input mapping to solid '{mapping.maps_to.solid_name}' "
                "which contains no input named '{mapping.maps_to.input_name}'".format(
                    name=name, mapping=mapping, class_name=class_name
                )
            )

        target_input = target_solid.input_def_named(mapping.maps_to.input_name)
        solid_input_handle = SolidInputHandle(target_solid, target_input)

        if mapping.maps_to_fan_in:
            if not dependency_structure.has_fan_in_deps(solid_input_handle):
                raise DagsterInvalidDefinitionError(
                    'In {class_name} "{name}" input mapping target '
                    '"{mapping.maps_to.solid_name}.{mapping.maps_to.input_name}" (index {mapping.maps_to.fan_in_index} of fan-in) '
                    "is not a MultiDependencyDefinition.".format(
                        name=name, mapping=mapping, class_name=class_name
                    )
                )
            inner_deps = dependency_structure.get_fan_in_deps(solid_input_handle)
            if (mapping.maps_to.fan_in_index >= len(inner_deps)) or (
                inner_deps[mapping.maps_to.fan_in_index] is not MappedInputPlaceholder
            ):
                raise DagsterInvalidDefinitionError(
                    'In {class_name} "{name}" input mapping target '
                    '"{mapping.maps_to.solid_name}.{mapping.maps_to.input_name}" index {mapping.maps_to.fan_in_index} in '
                    "the MultiDependencyDefinition is not a MappedInputPlaceholder".format(
                        name=name, mapping=mapping, class_name=class_name
                    )
                )
            mapping_keys.add(
                "{mapping.maps_to.solid_name}.{mapping.maps_to.input_name}.{mapping.maps_to.fan_in_index}".format(
                    mapping=mapping
                )
            )
            target_type = target_input.dagster_type.get_inner_type_for_fan_in()
            fan_in_msg = " (index {} of fan-in)".format(mapping.maps_to.fan_in_index)
        else:
            if dependency_structure.has_deps(solid_input_handle):
                raise DagsterInvalidDefinitionError(
                    'In {class_name} "{name}" input mapping target '
                    '"{mapping.maps_to.solid_name}.{mapping.maps_to.input_name}" '
                    "is already satisfied by solid output".format(
                        name=name, mapping=mapping, class_name=class_name
                    )
                )

            mapping_keys.add(
                "{mapping.maps_to.solid_name}.{mapping.maps_to.input_name}".format(mapping=mapping)
            )
            target_type = target_input.dagster_type
            fan_in_msg = ""

        if target_type != mapping.definition.dagster_type:
            raise DagsterInvalidDefinitionError(
                "In {class_name} '{name}' input "
                "'{mapping.definition.name}' of type {mapping.definition.dagster_type.display_name} maps to "
                "{mapping.maps_to.solid_name}.{mapping.maps_to.input_name}{fan_in_msg} of different type "
                "{target_type.display_name}. InputMapping source and "
                "destination must have the same type.".format(
                    mapping=mapping,
                    name=name,
                    target_type=target_type,
                    class_name=class_name,
                    fan_in_msg=fan_in_msg,
                )
            )

    for input_handle in dependency_structure.input_handles():
        if dependency_structure.has_fan_in_deps(input_handle):
            for idx, dep in enumerate(dependency_structure.get_fan_in_deps(input_handle)):
                if dep is MappedInputPlaceholder:
                    mapping_str = (
                        "{input_handle.solid_name}.{input_handle.input_name}.{idx}".format(
                            input_handle=input_handle, idx=idx
                        )
                    )
                    if mapping_str not in mapping_keys:
                        raise DagsterInvalidDefinitionError(
                            "Unsatisfied MappedInputPlaceholder at index {idx} in "
                            "MultiDependencyDefinition for '{input_handle.solid_name}.{input_handle.input_name}'".format(
                                input_handle=input_handle, idx=idx
                            )
                        )

    return input_mappings, input_def_dict.values()


def _validate_out_mappings(
    output_mappings: List[OutputMapping],
    solid_dict: Dict[str, Solid],
    dependency_structure: DependencyStructure,
    name: str,
    class_name: str,
) -> List[OutputMapping]:
    for mapping in output_mappings:
        if isinstance(mapping, OutputMapping):

            target_solid = solid_dict.get(mapping.maps_from.solid_name)
            if target_solid is None:
                raise DagsterInvalidDefinitionError(
                    "In {class_name} '{name}' output mapping references solid "
                    "'{solid_name}' which it does not contain.".format(
                        name=name, solid_name=mapping.maps_from.solid_name, class_name=class_name
                    )
                )
            if not target_solid.has_output(mapping.maps_from.output_name):
                raise DagsterInvalidDefinitionError(
                    "In {class_name} {name} output mapping from solid '{mapping.maps_from.solid_name}' "
                    "which contains no output named '{mapping.maps_from.output_name}'".format(
                        name=name, mapping=mapping, class_name=class_name
                    )
                )

            target_output = target_solid.output_def_named(mapping.maps_from.output_name)

            if mapping.definition.dagster_type.kind != DagsterTypeKind.ANY and (
                target_output.dagster_type != mapping.definition.dagster_type
            ):
                raise DagsterInvalidDefinitionError(
                    "In {class_name} '{name}' output "
                    "'{mapping.definition.name}' of type {mapping.definition.dagster_type.display_name} "
                    "maps from {mapping.maps_from.solid_name}.{mapping.maps_from.output_name} of different type "
                    "{target_output.dagster_type.display_name}. OutputMapping source "
                    "and destination must have the same type.".format(
                        class_name=class_name,
                        mapping=mapping,
                        name=name,
                        target_output=target_output,
                    )
                )

            if target_output.is_dynamic and not mapping.definition.is_dynamic:
                raise DagsterInvalidDefinitionError(
                    f'In {class_name} "{name}" can not map from {target_output.__class__.__name__} '
                    f'"{target_output.name}" to {mapping.definition.__class__.__name__} '
                    f'"{mapping.definition.name}". Definition types must align.'
                )

            dynamic_handle = dependency_structure.get_upstream_dynamic_handle_for_solid(
                target_solid.name
            )
            if dynamic_handle and not mapping.definition.is_dynamic:
                raise DagsterInvalidDefinitionError(
                    f'In {class_name} "{name}" output "{mapping.definition.name}" mapping from '
                    f'solid "{mapping.maps_from.solid_name}" must be a DynamicOutputDefinition since it is '
                    f'downstream of dynamic output "{dynamic_handle.describe()}".'
                )

        elif isinstance(mapping, OutputDefinition):
            raise DagsterInvalidDefinitionError(
                "You passed an OutputDefinition named '{output_name}' directly "
                "in to output_mappings. Return an OutputMapping by calling "
                "mapping_from on the OutputDefinition.".format(output_name=mapping.name)
            )
        else:
            raise DagsterInvalidDefinitionError(
                "Received unexpected type '{type}' in output_mappings. "
                "Provide an OutputMapping using OutputDefinition(...).mapping_from(...)".format(
                    type=type(mapping)
                )
            )
    return output_mappings
