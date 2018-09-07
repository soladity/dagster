import dagster
from dagster import (
    DependencyDefinition,
    InputDefinition,
    OutputDefinition,
    PipelineDefinition,
    solid,
)
import dagster.pandas as dagster_pd


@solid(
    inputs=[InputDefinition('num', dagster_pd.DataFrame)],
    outputs=[OutputDefinition(dagster_type=dagster_pd.DataFrame)]
)
def sum_solid(_context, _conf, num):
    sum_df = num.copy()
    sum_df['sum'] = sum_df['num1'] + sum_df['num2']
    return sum_df


@solid(
    inputs=[InputDefinition('sum_df', dagster_pd.DataFrame)],
    outputs=[OutputDefinition(dagster_type=dagster_pd.DataFrame)]
)
def sum_sq_solid(_context, _conf, sum_df):
    sum_sq_df = sum_df.copy()
    sum_sq_df['sum_sq'] = sum_df['sum']**2
    return sum_sq_df


@solid(
    inputs=[InputDefinition('sum_sq_solid', dagster_pd.DataFrame)],
    outputs=[OutputDefinition(dagster_type=dagster_pd.DataFrame)]
)
def always_fails_solid(_context, _conf, **_kwargs):
    raise Exception('I am a programmer and I make error')


def define_pipeline():
    return dagster.PipelineDefinition(
        name='pandas_hello_world_fails',
        solids=[
            dagster_pd.load_csv_solid('load_num_csv'),
            sum_solid,
            sum_sq_solid,
            always_fails_solid,
        ],
        dependencies={
            'sum_solid': {
                'num': DependencyDefinition('load_num_csv')
            },
            'sum_sq_solid': {
                'sum_df': DependencyDefinition(sum_solid.name),
            },
            'always_fails_solid': {
                'sum_sq_solid': DependencyDefinition(sum_sq_solid.name),
            }
        }
    )


def define_success_pipeline():
    return PipelineDefinition(
        name='pandas_hello_world',
        solids=[dagster_pd.load_csv_solid('load_num_csv'), sum_solid, sum_sq_solid],
        dependencies={
            'sum_solid': {
                'num': DependencyDefinition('load_num_csv')
            },
            'sum_sq_solid': {
                'sum_df': DependencyDefinition(sum_solid.name),
            },
        },
    )
