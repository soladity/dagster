# pylint: disable=no-value-for-parameter
import pandas as pd
from dagster_pandas import DataFrame

from dagster import Path, PresetDefinition, file_relative_path, lambda_solid, pipeline


@lambda_solid
def sum_solid(num_df: DataFrame) -> DataFrame:
    sum_df = num_df.copy()
    sum_df['sum'] = sum_df['num1'] + sum_df['num2']
    return sum_df


@lambda_solid
def sum_sq_solid(sum_df: DataFrame) -> DataFrame:
    sum_sq_df = sum_df.copy()
    sum_sq_df['sum_sq'] = sum_df['sum'] ** 2
    return sum_sq_df


@pipeline(
    preset_defs=[
        PresetDefinition.from_files(
            'test',
            environment_files=[
                file_relative_path(__file__, 'environments/pandas_hello_world_test.yaml')
            ],
        ),
        PresetDefinition.from_files(
            'prod',
            environment_files=[
                file_relative_path(__file__, 'environments/pandas_hello_world_prod.yaml')
            ],
        ),
    ]
)
def pandas_hello_world_pipeline():
    return sum_sq_solid(sum_solid())


@lambda_solid
def read_csv(path: Path) -> DataFrame:
    return pd.read_csv(path)


@pipeline
def pandas_hello_world_pipeline_no_config():
    return sum_sq_solid(sum_solid(read_csv()))
