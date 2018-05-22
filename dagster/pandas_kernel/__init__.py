from __future__ import (absolute_import, division, print_function, unicode_literals)
from builtins import *  # pylint: disable=W0622,W0401

import pandas as pd

from dagster import check

from dagster.core.definitions import (Solid, has_context_argument)
from dagster.core.execution import DagsterExecutionContext
from dagster.core.errors import DagsterUserCodeExecutionError
from .definitions import (
    create_dagster_pd_csv_input,
    create_dagster_pd_csv_output,
    create_dagster_pd_dependency_input,
    create_dagster_pd_parquet_output,
)


def solid(**kwargs):
    return Solid(**kwargs)


def depends_on(solid_inst):
    check.inst_param(solid_inst, 'solid_inst', Solid)
    return create_dagster_pd_dependency_input(solid_inst)


def _default_passthrough_transform(*args, **kwargs):
    check.invariant(not args, 'There should be no positional args')
    check.invariant(len(kwargs) == 1, 'There should be only one input')
    return list(kwargs.values())[0]


def _post_process_transform(context, df):
    check.inst_param(context, 'context', DagsterExecutionContext)
    check.inst_param(df, 'df', pd.DataFrame)

    context.metric('rows', df.shape[0])


def _dependency_transform_wrapper(transform_fn):
    check.callable_param(transform_fn, 'transform_fn')
    if has_context_argument(transform_fn):

        def wrapper_with_context(context, **kwargs):
            df = transform_fn(context, **kwargs)
            _post_process_transform(context, df)
            return df

        return wrapper_with_context
    else:

        def wrapper_no_context(context, **kwargs):
            df = transform_fn(**kwargs)
            _post_process_transform(context, df)
            return df

        return wrapper_no_context


def dataframe_solid(*args, inputs, transform_fn=None, **kwargs):
    check.invariant(not args, 'must use all keyword args')

    # will add parquet and other standardized formats
    if transform_fn is None:
        check.param_invariant(
            len(inputs) == 1, 'inputs',
            'If you do not specify a transform there must only be one input'
        )
        transform_fn = _default_passthrough_transform

    return Solid(
        inputs=inputs,
        outputs=[csv_output(), parquet_output()],
        transform_fn=_dependency_transform_wrapper(transform_fn),
        **kwargs
    )


def single_path_arg(input_name, path):
    check.str_param(input_name, 'input_name')
    check.str_param(path, 'path')
    return {input_name: {'path': path}}


def csv_input(name, delimiter=',', **read_csv_kwargs):
    return create_dagster_pd_csv_input(name, delimiter, **read_csv_kwargs)


def csv_output():
    return create_dagster_pd_csv_output()


def parquet_output():
    return create_dagster_pd_parquet_output()
