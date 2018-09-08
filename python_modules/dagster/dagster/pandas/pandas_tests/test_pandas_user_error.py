# pylint: disable=W0613

import pytest

import pandas as pd

import dagster.pandas as dagster_pd
from dagster import (
    DependencyDefinition,
    InputDefinition,
    OutputDefinition,
    PipelineDefinition,
    SolidDefinition,
    config,
    execute_pipeline,
    lambda_solid,
)
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.utility_solids import define_stub_solid


def _dataframe_solid(name, inputs, transform_fn):
    return SolidDefinition.single_output_transform(
        name=name,
        inputs=inputs,
        transform_fn=transform_fn,
        output=OutputDefinition(dagster_type=dagster_pd.DataFrame),
    )


def test_wrong_output_value():
    csv_input = InputDefinition('num_csv', dagster_pd.DataFrame)

    @lambda_solid(
        name="test_wrong_output",
        inputs=[csv_input],
        output=OutputDefinition(dagster_type=dagster_pd.DataFrame),
    )
    def df_solid(num_csv):
        return 'not a dataframe'

    pass_solid = define_stub_solid('pass_solid', pd.DataFrame())

    pipeline = PipelineDefinition(
        solids=[pass_solid, df_solid],
        dependencies={'test_wrong_output': {
            'num_csv': DependencyDefinition('pass_solid'),
        }}
    )

    with pytest.raises(DagsterInvariantViolationError):
        execute_pipeline(
            pipeline,
            environment=config.Environment(),
        )


def test_wrong_input_value():
    @lambda_solid(
        name="test_wrong_input",
        inputs=[InputDefinition('foo', dagster_pd.DataFrame)],
    )
    def df_solid(foo):
        return foo

    pass_solid = define_stub_solid('pass_solid', 'not a dataframe')

    pipeline = PipelineDefinition(
        solids=[pass_solid, df_solid],
        dependencies={'test_wrong_input': {
            'foo': DependencyDefinition('pass_solid'),
        }}
    )

    with pytest.raises(DagsterInvariantViolationError):
        execute_pipeline(
            pipeline,
            environment=config.Environment(),
        )
