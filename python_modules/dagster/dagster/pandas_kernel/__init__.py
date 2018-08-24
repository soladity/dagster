from __future__ import (absolute_import, division, print_function, unicode_literals)
from builtins import *  # pylint: disable=W0622,W0401

import pandas as pd

from dagster import (
    ArgumentDefinition,
    ConfigDefinition,
    ExecutionContext,
    InputDefinition,
    OutputDefinition,
    Result,
    SolidDefinition,
    check,
    types,
)


def _create_dataframe_type():
    return types.PythonObjectType(
        name='PandasDataFrame',
        python_type=pd.DataFrame,
        description=
        '''Two-dimensional size-mutable, potentially heterogeneous tabular data structure with labeled axes (rows and columns).
        See http://pandas.pydata.org/
        ''',
    )


DataFrame = _create_dataframe_type()


def load_csv_solid(name):
    check.str_param(name, 'name')

    def _t_fn(_context, _inputs, config_dict):
        yield Result(pd.read_csv(config_dict['path']))

    return SolidDefinition(
        name=name,
        inputs=[],
        outputs=[OutputDefinition(dagster_type=DataFrame)],
        transform_fn=_t_fn,
        config_def=ConfigDefinition({
            'path': ArgumentDefinition(types.Path),
        }),
    )


def to_csv_solid(name):
    def _t_fn(_context, inputs, config_dict):
        inputs['df'].to_csv(config_dict['path'], index=False)

    return SolidDefinition(
        name=name,
        inputs=[InputDefinition('df', DataFrame)],
        outputs=[],
        config_def=ConfigDefinition({
            'path': ArgumentDefinition(types.Path)
        }),
        transform_fn=_t_fn,
    )


def to_parquet_solid(name):
    def _t_fn(_context, inputs, config_dict):
        inputs['df'].to_parquet(config_dict['path'])

    return SolidDefinition(
        name=name,
        inputs=[InputDefinition('df', DataFrame)],
        outputs=[],
        config_def=ConfigDefinition({
            'path': ArgumentDefinition(types.Path)
        }),
        transform_fn=_t_fn,
    )
