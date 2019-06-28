# pylint: disable=W0613

import pytest

import pandas as pd

from dagster import (
    DagsterTypeCheckError,
    DependencyDefinition,
    InputDefinition,
    OutputDefinition,
    PipelineDefinition,
    execute_pipeline,
    lambda_solid,
)

import dagster_pandas as dagster_pd

from dagster.core.utility_solids import define_stub_solid


def test_wrong_output_value():
    csv_input = InputDefinition('num_csv', dagster_pd.DataFrame)

    @lambda_solid(
        name="test_wrong_output", inputs=[csv_input], output=OutputDefinition(dagster_pd.DataFrame)
    )
    def df_solid(num_csv):
        return 'not a dataframe'

    pass_solid = define_stub_solid('pass_solid', pd.DataFrame())

    pipeline = PipelineDefinition(
        solid_defs=[pass_solid, df_solid],
        dependencies={'test_wrong_output': {'num_csv': DependencyDefinition('pass_solid')}},
    )

    with pytest.raises(DagsterTypeCheckError):
        execute_pipeline(pipeline)


def test_wrong_input_value():
    @lambda_solid(name="test_wrong_input", inputs=[InputDefinition('foo', dagster_pd.DataFrame)])
    def df_solid(foo):
        return foo

    pass_solid = define_stub_solid('pass_solid', 'not a dataframe')

    pipeline = PipelineDefinition(
        solid_defs=[pass_solid, df_solid],
        dependencies={'test_wrong_input': {'foo': DependencyDefinition('pass_solid')}},
    )

    with pytest.raises(DagsterTypeCheckError):
        execute_pipeline(pipeline)
