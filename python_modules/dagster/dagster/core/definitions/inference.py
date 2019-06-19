import inspect
import sys

import six

from dagster.core.errors import DagsterInvalidDefinitionError, DagsterTypeError

from . import InputDefinition, OutputDefinition

if hasattr(inspect, 'signature'):
    funcsigs = inspect
else:
    import funcsigs


def infer_output_definitions(decorator_name, solid_name, fn):
    signature = funcsigs.signature(fn)
    try:
        return [
            OutputDefinition()
            if signature.return_annotation is funcsigs.Signature.empty
            else OutputDefinition(signature.return_annotation)
        ]
    except DagsterTypeError as type_error:
        six.raise_from(
            DagsterInvalidDefinitionError(
                'Error inferring Dagster type for return type '
                '"{type_annotation}" from {decorator} "{solid}". '
                'Correct the issue or explicitly pass definitions to {decorator}.'.format(
                    decorator=decorator_name,
                    solid=solid_name,
                    type_annotation=signature.return_annotation,
                )
            ),
            type_error,
        )


def _input_param_type(type_annotation):
    if sys.version_info.major >= 3 and type_annotation is not inspect.Parameter.empty:
        return type_annotation
    return None


def infer_input_definitions_for_lambda_solid(solid_name, fn):
    signature = funcsigs.signature(fn)
    params = list(signature.parameters.values())

    return _infer_inputs_from_params(params, '@lambda_solid', solid_name)


def _infer_inputs_from_params(params, decorator_name, solid_name):
    input_defs = []
    for param in params:
        try:
            input_defs.append(InputDefinition(param.name, _input_param_type(param.annotation)))
        except DagsterTypeError as type_error:
            six.raise_from(
                DagsterInvalidDefinitionError(
                    'Error inferring Dagster type for input name {param} typed as '
                    '"{type_annotation}" from {decorator} "{solid}". '
                    'Correct the issue or explicitly pass definitions to {decorator}.'.format(
                        decorator=decorator_name,
                        solid=solid_name,
                        param=param.name,
                        type_annotation=param.annotation,
                    )
                ),
                type_error,
            )

    return input_defs


def infer_input_definitions_for_composite_solid(solid_name, fn):
    signature = funcsigs.signature(fn)
    params = list(signature.parameters.values())

    return _infer_inputs_from_params(params, '@composite_solid', solid_name)


def infer_input_definitions_for_solid(solid_name, fn):
    signature = funcsigs.signature(fn)
    params = list(signature.parameters.values())
    if len(params) == 0:
        raise DagsterInvalidDefinitionError(
            'Must provide at least one parameter for @solid "{solid}"'.format(solid=solid_name)
        )

    if params[0].name not in {'context', '_context', '_'}:
        raise DagsterInvalidDefinitionError(
            'First parameter for @solid "{solid}" must be "context", "_context", or "_"'.format(
                solid=solid_name
            )
        )
    return _infer_inputs_from_params(params[1:], '@solid', solid_name)
