from collections import namedtuple

from dagster import check
from dagster.core.errors import DagsterInvalidDefinitionError

from .dependency import DependencyDefinition, SolidInvocation
from .solid import ISolidDefinition
from .output import OutputDefinition

_composition_stack = []


def enter_composition(name, source):
    _composition_stack.append(InProgressCompositionContext(name, source))


def exit_composition(output):
    return _composition_stack.pop().complete(output)


def current_context():
    return _composition_stack[-1]


class InProgressCompositionContext:
    '''This context captures invocations of solids within a
    composition function such as @composite_solid or @pipeline
    '''

    def __init__(self, name, source):
        self.name = check.str_param(name, 'name')
        self.source = check.str_param(source, 'source')
        self._invocations = {}

    def has_seen_invocation(self, name):
        return name in self._invocations

    def observe_invocation(self, invocation):
        self._invocations[invocation.solid_name] = invocation

    def complete(self, output):
        return CompleteCompositionContext(self.name, self._invocations, output)


class CompleteCompositionContext(
    namedtuple('_CompositionContext', 'name solid_defs dependencies input_mappings output_mappings')
):
    '''The processed information from capturing solid invocations during a composition function.
    '''

    def __new__(cls, name, invocations, output_mappings):

        dep_dict = {}
        solid_def_dict = {}
        input_mappings = []

        for invocation in invocations.values():
            def_name = invocation.solid_def.name
            if def_name in solid_def_dict and solid_def_dict[def_name] is not invocation.solid_def:
                check.failed('Detected conflicting solid definitions with the same name')
            solid_def_dict[def_name] = invocation.solid_def

            dep_dict[SolidInvocation(invocation.solid_def.name, invocation.solid_name)] = {
                input_name: DependencyDefinition(solid_name, output_name)
                for input_name, (solid_name, output_name) in invocation.input_bindings.items()
            }

            input_mappings += [
                node.input_def.mapping_to(invocation.solid_name, input_name)
                for input_name, node in invocation.input_mappings.items()
            ]

        return super(cls, CompleteCompositionContext).__new__(
            cls, name, list(solid_def_dict.values()), dep_dict, input_mappings, output_mappings
        )


class CallableSolidNode:
    '''An intermediate object in solid composition to allow for binding information such as
    an alias before invoking.
    '''

    def __init__(self, solid_def, solid_name=None):
        self.solid_def = solid_def
        self.solid_name = check.opt_str_param(solid_name, 'solid_name', solid_def.name)

    def __call__(self, *args, **kwargs):
        input_bindings = {}
        input_mappings = {}

        # handle *args
        for idx, output_node in enumerate(args):
            if idx >= len(self.solid_def.input_defs):
                raise DagsterInvalidDefinitionError(
                    'In {source} {name} received too many inputs for solid '
                    'invocation {solid_name}. Only {def_num} defined, received {arg_num}'.format(
                        source=current_context().source,
                        name=current_context().name,
                        solid_name=self.solid_name,
                        def_num=len(self.solid_def.input_defs),
                        arg_num=len(args),
                    )
                )

            input_name = self.solid_def.input_defs[idx].name

            if isinstance(output_node, InvokedSolidOutputHandle):
                input_bindings[input_name] = output_node
            elif isinstance(output_node, InputMappingNode):
                input_mappings[input_name] = output_node
            elif isinstance(output_node, tuple) and all(
                map(lambda item: isinstance(item, InvokedSolidOutputHandle), output_node)
            ):
                raise DagsterInvalidDefinitionError(
                    'In {source} {name} received a tuple of multiple outputs for '
                    'input position {idx} in solid invocation {solid_name}. '
                    'Must pass individual output, available from tuple: {options}'.format(
                        source=current_context().source,
                        name=current_context().name,
                        idx=idx,
                        solid_name=self.solid_name,
                        options=output_node._fields,
                    )
                )
            else:
                raise DagsterInvalidDefinitionError(
                    'In {source} {name} received invalid type {type} for input '
                    '{input_name} at postition {idx} in solid invocation {solid_name}. '
                    'Must pass the output from previous solid invocations or inputs to the '
                    'composition function as inputs when invoking solids during composition.'.format(
                        source=current_context().source,
                        name=current_context().name,
                        type=type(output_node),
                        idx={idx},
                        input_name=input_name,
                        solid_name=self.solid_name,
                    )
                )

        # then **kwargs
        for input_name, output_node in kwargs.items():
            if isinstance(output_node, InvokedSolidOutputHandle):
                input_bindings[input_name] = output_node
            elif isinstance(output_node, InputMappingNode):
                input_mappings[input_name] = output_node
            elif isinstance(output_node, tuple) and all(
                map(lambda item: isinstance(item, InvokedSolidOutputHandle), output_node)
            ):
                raise DagsterInvalidDefinitionError(
                    'In {source} {name} received a tuple of multiple outputs for '
                    'the input {input_name} in solid invocation {solid_name}. '
                    'Must pass individual output, available from tuple: {options}'.format(
                        name=current_context().name,
                        source=current_context().source,
                        input_name=input_name,
                        solid_name=self.solid_name,
                        options=output_node._fields,
                    )
                )
            else:
                raise DagsterInvalidDefinitionError(
                    'In {source} {name} received invalid type {type} for input '
                    '{input_name} in solid invocation {solid_name}. '
                    'Must pass the output from previous solid invocations or inputs to the composition function '
                    'as inputs when invoking solids during composition.'.format(
                        source=current_context().source,
                        name=current_context().name,
                        type=type(output_node),
                        input_name=input_name,
                        solid_name=self.solid_name,
                    )
                )

        if current_context().has_seen_invocation(self.solid_name):
            raise DagsterInvalidDefinitionError(
                '{source} {name} invokd the same solid ({solid_name}) twice without aliasing.'.format(
                    source=current_context().source,
                    name=current_context().name,
                    solid_name=self.solid_name,
                )
            )

        current_context().observe_invocation(
            InvokedSolidNode(self.solid_name, self.solid_def, input_bindings, input_mappings)
        )

        if len(self.solid_def.output_defs) == 0:
            return None

        if len(self.solid_def.output_defs) == 1:
            output_name = self.solid_def.output_defs[0].name
            return InvokedSolidOutputHandle(self.solid_name, output_name)

        outputs = [output_def.name for output_def in self.solid_def.output_defs]
        return namedtuple('_{solid_def}_outputs'.format(solid_def=self.solid_def.name), outputs)(
            **{output: InvokedSolidOutputHandle(self.solid_name, output) for output in outputs}
        )


class InvokedSolidNode(
    namedtuple('_InvokedSolidNode', 'solid_name solid_def input_bindings input_mappings')
):
    '''The metadata about a solid invocation saved by the current composition context.
    '''

    def __new__(cls, solid_name, solid_def, input_bindings, input_mappings):
        return super(cls, InvokedSolidNode).__new__(
            cls,
            check.str_param(solid_name, 'solid_name'),
            check.inst_param(solid_def, 'solid_def', ISolidDefinition),
            check.dict_param(
                input_bindings, 'input_bindings', key_type=str, value_type=InvokedSolidOutputHandle
            ),
            check.dict_param(
                input_mappings, 'input_mappings', key_type=str, value_type=InputMappingNode
            ),
        )


class InvokedSolidOutputHandle(namedtuple('_InvokedSolidOutputHandle', 'solid_name output_name')):
    '''The return value for an output when invoking a solid in a composition function.
    '''

    def __new__(cls, solid_name, output_name):
        return super(cls, InvokedSolidOutputHandle).__new__(
            cls,
            check.str_param(solid_name, 'solid_name'),
            check.str_param(output_name, 'output_name'),
        )


class InputMappingNode:
    def __init__(self, input_def):
        self.input_def = input_def


def composite_mapping_from_output(output, output_defs, name):
    # output can be different types
    check.list_param(output_defs, 'output_defs', OutputDefinition)
    check.str_param(name, 'name')

    # single output
    if isinstance(output, InvokedSolidOutputHandle):
        if len(output_defs) == 1:
            return [output_defs[0].mapping_from(output.solid_name, output.output_name)]
        else:
            raise DagsterInvalidDefinitionError(
                'Returned a single output ({solid_name}.{output_name}) in '
                '@composite_solid {name} but {num} outputs are defined. '
                'Return a dict to map defined outputs.'.format(
                    solid_name=output.solid_name,
                    output_name=output.output_name,
                    name=name,
                    num=len(output_defs),
                )
            )

    output_mappings = []
    output_def_dict = {output_def.name: output_def for output_def in output_defs}

    # tuple returned directly
    if isinstance(output, tuple) and all(
        map(lambda item: isinstance(item, InvokedSolidOutputHandle), output)
    ):
        for handle in output:
            if handle.output_name not in output_def_dict:
                raise DagsterInvalidDefinitionError(
                    'Output name mismatch returning output tuple in @composite_solid {name}. '
                    'No matching OutputDefinition named {output_name} for {solid_name}.{output_name}.'
                    'Return a dict to map to the desired OutputDefinition'.format(
                        name=name, output_name=handle.output_name, solid_name=handle.solid_name
                    )
                )
            output_mappings.append(
                output_def_dict[handle.output_name].mapping_from(
                    handle.solid_name, handle.output_name
                )
            )
        return output_mappings

    # mapping dict
    if isinstance(output, dict):
        for name, handle in output.items():
            if name in output_def_dict:
                raise DagsterInvalidDefinitionError(
                    '@composite_solid {name} referenced key {key} which does not match any '
                    'OutputDefinitions. Valid options are: {options}'.format(
                        name=name, key=name, options=list(output_def_dict.keys())
                    )
                )
            if not isinstance(handle, InvokedSolidOutputHandle):
                raise DagsterInvalidDefinitionError(
                    '@composite_solid {name} returned problematic dict entry under '
                    'key {key} of type {type}. Dict values must be outputs of '
                    'invoked solids'.format(name=name, key=name, type=type(handle))
                )

            output_mappings.append(
                output_def_dict[name].mapping_from(handle.solid_name, handle.output_name)
            )
        return output_mappings

    # error
    if output is not None:
        raise DagsterInvalidDefinitionError(
            '@composite_solid {name} returned problematic value '
            'of type {type}. Expected return value from invoked solid or dict mapping '
            'output name to return values from invoked solids'.format(name=name, type=type(output))
        )
