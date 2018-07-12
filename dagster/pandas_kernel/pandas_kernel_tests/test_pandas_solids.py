import os

import pandas as pd

from dagster import check
from dagster import config
import dagster.core
from dagster.core import types
from dagster.core.definitions import (SolidDefinition, create_single_materialization_output)
from dagster.core.decorators import solid
from dagster.core.execution import (
    DagsterExecutionContext,
    execute_pipeline_through_solid,
    _read_source,
    materialize_pipeline_iterator,
    output_single_solid,
    _pipeline_solid_in_memory,
    materialize_pipeline,
    execute_pipeline,
    execute_single_solid,
)
import dagster.pandas_kernel as dagster_pd
from dagster.utils.test import (get_temp_file_name, get_temp_file_names, script_relative_path)
from .utils import simple_csv_input


def get_solid_transformed_value(context, solid_inst, environment):
    execution_result = execute_single_solid(
        context,
        solid_inst,
        environment=environment,
    )
    return execution_result.transformed_value


def get_num_csv_environment():
    return config.Environment(
        sources={
            'num_csv': config.Source('CSV', args={'path': script_relative_path('num.csv')}),
        }
    )


def create_test_context():
    return DagsterExecutionContext()


def test_pandas_input():
    csv_input = simple_csv_input('num_csv')
    df = _read_source(
        create_test_context(), csv_input.sources[0], {'path': script_relative_path('num.csv')}
    )

    assert isinstance(df, pd.DataFrame)
    assert df.to_dict('list') == {'num1': [1, 3], 'num2': [2, 4]}


def test_pandas_solid():
    csv_input = simple_csv_input('num_csv')

    def transform(_context, args):
        num_csv = args['num_csv']
        num_csv['sum'] = num_csv['num1'] + num_csv['num2']
        return num_csv

    test_output = {}

    def materialization_fn_inst(context, arg_dict, df):
        assert isinstance(df, pd.DataFrame)
        assert isinstance(context, DagsterExecutionContext)
        assert isinstance(arg_dict, dict)

        test_output['df'] = df

    custom_output_def = create_single_materialization_output(
        materialization_type='CUSTOM',
        materialization_fn=materialization_fn_inst,
        argument_def_dict={},
    )

    single_solid = SolidDefinition(
        name='sum_table',
        inputs=[csv_input],
        transform_fn=transform,
        output=custom_output_def,
    )

    output_single_solid(
        create_test_context(),
        single_solid,
        environment=get_num_csv_environment(),
        materialization_type='CUSTOM',
        arg_dict={},
    )

    assert test_output['df'].to_dict('list') == {'num1': [1, 3], 'num2': [2, 4], 'sum': [3, 7]}


def test_pandas_csv_to_csv():
    csv_input = simple_csv_input('num_csv')

    # just adding a second context arg to test that
    def transform(context, args):
        check.inst_param(context, 'context', dagster.core.execution.DagsterExecutionContext)
        num_csv = args['num_csv']
        num_csv['sum'] = num_csv['num1'] + num_csv['num2']
        return num_csv

    def materialization_fn_inst(context, arg_dict, df):
        assert isinstance(context, DagsterExecutionContext)
        path = check.str_elem(arg_dict, 'path')
        df.to_csv(path, index=False)

    csv_output_def = create_single_materialization_output(
        materialization_type='CSV',
        materialization_fn=materialization_fn_inst,
        argument_def_dict={'path': types.PATH}
    )

    solid_def = SolidDefinition(
        name='sum_table',
        inputs=[csv_input],
        transform_fn=transform,
        output=csv_output_def,
    )

    output_df = execute_transform_in_temp_csv_files(solid_def)

    assert output_df.to_dict('list') == {'num1': [1, 3], 'num2': [2, 4], 'sum': [3, 7]}


def execute_transform_in_temp_csv_files(solid_inst):
    with get_temp_file_name() as temp_file_name:
        result = output_single_solid(
            create_test_context(),
            solid_inst,
            environment=get_num_csv_environment(),
            materialization_type='CSV',
            arg_dict={'path': temp_file_name},
        )

        assert result.success

        output_df = pd.read_csv(temp_file_name)
    return output_df


def create_sum_table():
    def transform(_context, args):
        num_csv = args['num_csv']
        check.inst_param(num_csv, 'num_csv', pd.DataFrame)
        num_csv['sum'] = num_csv['num1'] + num_csv['num2']
        return num_csv

    return dagster_pd.dataframe_solid(
        name='sum_table',
        inputs=[simple_csv_input('num_csv')],
        transform_fn=transform,
    )


@solid(
    inputs=[dagster_pd.dataframe_input('num_csv')],
    output=dagster_pd.dataframe_output(),
)
def sum_table(num_csv):
    check.inst_param(num_csv, 'num_csv', pd.DataFrame)
    num_csv['sum'] = num_csv['num1'] + num_csv['num2']
    return num_csv


@solid(
    inputs=[dagster_pd.dataframe_dependency(solid=sum_table, name='sum_df')],
    output=dagster_pd.dataframe_output(),
)
def sum_sq_table(sum_df):
    sum_df['sum_squared'] = sum_df['sum'] * sum_df['sum']
    return sum_df


@solid(
    inputs=[dagster_pd.dataframe_dependency(name='sum_table_renamed', solid=sum_table)],
    output=dagster_pd.dataframe_output(),
)
def sum_sq_table_renamed_input(sum_table_renamed):
    sum_table_renamed['sum_squared'] = sum_table_renamed['sum'] * sum_table_renamed['sum']
    return sum_table_renamed


def create_sum_sq_table(sum_table_solid):
    def transform(_context, args):
        sum_df = args['sum_table']
        sum_df['sum_squared'] = sum_df['sum'] * sum_df['sum']
        return sum_df

    return dagster_pd.dataframe_solid(
        name='mult_table',
        inputs=[dagster_pd.dataframe_dependency(sum_table_solid)],
        transform_fn=transform
    )


def test_pandas_csv_to_csv_better_api():
    output_df = execute_transform_in_temp_csv_files(create_sum_table())
    assert output_df.to_dict('list') == {'num1': [1, 3], 'num2': [2, 4], 'sum': [3, 7]}


def test_pandas_csv_to_csv_decorator_api():
    output_df = execute_transform_in_temp_csv_files(sum_table)
    assert output_df.to_dict('list') == {'num1': [1, 3], 'num2': [2, 4], 'sum': [3, 7]}


def test_pandas_csv_in_memory():
    df = get_solid_transformed_value(
        create_test_context(),
        create_sum_table(),
        get_num_csv_environment(),
    )
    assert isinstance(df, pd.DataFrame)
    assert df.to_dict('list') == {'num1': [1, 3], 'num2': [2, 4], 'sum': [3, 7]}


def test_two_step_pipeline_in_memory():
    sum_table_solid = create_sum_table()
    mult_table_solid = create_sum_sq_table(sum_table_solid)
    context = create_test_context()
    df = get_solid_transformed_value(context, sum_table_solid, get_num_csv_environment())
    mult_df = _pipeline_solid_in_memory(context, mult_table_solid, {'sum_table': df})
    assert mult_df.to_dict('list') == {
        'num1': [1, 3],
        'num2': [2, 4],
        'sum': [3, 7],
        'sum_squared': [9, 49]
    }


def test_two_step_pipeline_in_memory_decorator_style():
    context = create_test_context()
    df = get_solid_transformed_value(context, sum_table, get_num_csv_environment())
    mult_df = _pipeline_solid_in_memory(context, sum_sq_table, {'sum_df': df})
    assert mult_df.to_dict('list') == {
        'num1': [1, 3],
        'num2': [2, 4],
        'sum': [3, 7],
        'sum_squared': [9, 49]
    }


def test_two_input_solid():
    def transform(_context, args):
        num_csv1 = args['num_csv1']
        num_csv2 = args['num_csv2']
        check.inst_param(num_csv1, 'num_csv1', pd.DataFrame)
        check.inst_param(num_csv2, 'num_csv2', pd.DataFrame)
        num_csv1['sum'] = num_csv1['num1'] + num_csv2['num2']
        return num_csv1

    two_input_solid = dagster_pd.dataframe_solid(
        name='two_input_solid',
        inputs=[simple_csv_input('num_csv1'),
                simple_csv_input('num_csv2')],
        transform_fn=transform,
    )

    environment = config.Environment(
        sources={
            'num_csv1': config.Source('CSV', {'path': script_relative_path('num.csv')}),
            'num_csv2': config.Source('CSV', {'path': script_relative_path('num.csv')}),
        }
    )

    df = get_solid_transformed_value(create_test_context(), two_input_solid, environment)
    assert isinstance(df, pd.DataFrame)
    assert df.to_dict('list') == {'num1': [1, 3], 'num2': [2, 4], 'sum': [3, 7]}


def test_no_transform_solid():
    num_table = dagster_pd.dataframe_solid(
        name='num_table',
        inputs=[simple_csv_input('num_csv')],
    )
    context = create_test_context()
    df = get_solid_transformed_value(context, num_table, get_num_csv_environment())
    assert df.to_dict('list') == {'num1': [1, 3], 'num2': [2, 4]}


def create_diamond_pipeline():
    return dagster.core.pipeline(solids=list(create_diamond_dag()))


def create_diamond_dag():
    num_table_solid = dagster_pd.dataframe_solid(
        name='num_table',
        inputs=[simple_csv_input('num_csv')],
    )

    def sum_transform(_context, args):
        num_df = args['num_table']
        sum_df = num_df.copy()
        sum_df['sum'] = num_df['num1'] + num_df['num2']
        return sum_df

    sum_table_solid = dagster_pd.dataframe_solid(
        name='sum_table',
        inputs=[dagster_pd.dataframe_dependency(num_table_solid)],
        transform_fn=sum_transform,
    )

    def mult_transform(_context, args):
        num_table = args['num_table']
        mult_table = num_table.copy()
        mult_table['mult'] = num_table['num1'] * num_table['num2']
        return mult_table

    mult_table_solid = dagster_pd.dataframe_solid(
        name='mult_table',
        inputs=[dagster_pd.dataframe_dependency(num_table_solid)],
        transform_fn=mult_transform,
    )

    def sum_mult_transform(_context, args):
        sum_df = args['sum_table']
        mult_df = args['mult_table']
        sum_mult_table = sum_df.copy()
        sum_mult_table['mult'] = mult_df['mult']
        sum_mult_table['sum_mult'] = sum_df['sum'] * mult_df['mult']
        return sum_mult_table

    sum_mult_table_solid = dagster_pd.dataframe_solid(
        name='sum_mult_table',
        inputs=[
            dagster_pd.dataframe_dependency(sum_table_solid),
            dagster_pd.dataframe_dependency(mult_table_solid)
        ],
        transform_fn=sum_mult_transform,
    )

    return (num_table_solid, sum_table_solid, mult_table_solid, sum_mult_table_solid)


def test_diamond_dag_run():
    num_table_solid, sum_table_solid, mult_table_solid, sum_mult_table_solid = create_diamond_dag()

    context = create_test_context()

    num_table_df = get_solid_transformed_value(context, num_table_solid, get_num_csv_environment())
    assert num_table_df.to_dict('list') == {'num1': [1, 3], 'num2': [2, 4]}

    sum_df = _pipeline_solid_in_memory(context, sum_table_solid, {'num_table': num_table_df})

    assert sum_df.to_dict('list') == {'num1': [1, 3], 'num2': [2, 4], 'sum': [3, 7]}

    mult_df = _pipeline_solid_in_memory(context, mult_table_solid, {'num_table': num_table_df})

    assert mult_df.to_dict('list') == {'num1': [1, 3], 'num2': [2, 4], 'mult': [2, 12]}

    sum_mult_df = _pipeline_solid_in_memory(
        context, sum_mult_table_solid, {
            'sum_table': sum_df,
            'mult_table': mult_df
        }
    )

    assert sum_mult_df.to_dict('list') == {
        'num1': [1, 3],
        'num2': [2, 4],
        'sum': [3, 7],
        'mult': [2, 12],
        'sum_mult': [6, 84],
    }


def test_pandas_in_memory_diamond_pipeline():
    context = create_test_context()
    pipeline = create_diamond_pipeline()
    result = execute_pipeline_through_solid(
        context, pipeline, environment=get_num_csv_environment(), solid_name='sum_mult_table'
    )

    assert result.transformed_value.to_dict('list') == {
        'num1': [1, 3],
        'num2': [2, 4],
        'sum': [3, 7],
        'mult': [2, 12],
        'sum_mult': [6, 84],
    }


def test_pandas_output_csv_pipeline():
    context = create_test_context()

    with get_temp_file_name() as temp_file_name:
        pipeline = create_diamond_pipeline()
        environment = get_num_csv_environment()

        for _result in materialize_pipeline_iterator(
            context,
            pipeline=pipeline,
            environment=environment,
            materializations=[
                config.Materialization(
                    solid='sum_mult_table',
                    materialization_type='CSV',
                    args={'path': temp_file_name},
                )
            ],
        ):
            pass

        assert os.path.exists(temp_file_name)
        output_df = pd.read_csv(temp_file_name)
        assert output_df.to_dict('list') == {
            'num1': [1, 3],
            'num2': [2, 4],
            'sum': [3, 7],
            'mult': [2, 12],
            'sum_mult': [6, 84],
        }


def _result_named(results, name):
    for result in results:
        if result.name == name:
            return result

    check.failed('could not find name')


def test_pandas_output_intermediate_csv_files():
    context = create_test_context()
    pipeline = create_diamond_pipeline()

    with get_temp_file_names(2) as temp_tuple:
        sum_file, mult_file = temp_tuple  # pylint: disable=E0632

        environment = get_num_csv_environment()

        subgraph_one_result = materialize_pipeline(
            context,
            pipeline,
            environment=environment,
            materializations=[
                config.Materialization(
                    solid='sum_table',
                    materialization_type='CSV',
                    args={'path': sum_file},
                ),
                config.Materialization(
                    solid='mult_table',
                    materialization_type='CSV',
                    args={'path': mult_file},
                ),
            ],
        )

        assert len(subgraph_one_result.result_list) == 3

        expected_sum = {
            'num1': [1, 3],
            'num2': [2, 4],
            'sum': [3, 7],
        }

        assert pd.read_csv(sum_file).to_dict('list') == expected_sum
        sum_table_result = subgraph_one_result.result_named('sum_table')
        assert sum_table_result.transformed_value.to_dict('list') == expected_sum

        expected_mult = {
            'num1': [1, 3],
            'num2': [2, 4],
            'mult': [2, 12],
        }
        assert pd.read_csv(mult_file).to_dict('list') == expected_mult
        mult_table_result = subgraph_one_result.result_named('mult_table')
        assert mult_table_result.transformed_value.to_dict('list') == expected_mult

        pipeline_result = execute_pipeline(
            context,
            pipeline,
            environment=config.Environment(
                sources={
                    'sum_table': config.Source('CSV', {'path': sum_file}),
                    'mult_table': config.Source('CSV', {'path': mult_file}),
                }
            ),
            from_solids=['sum_mult_table'],
            through_solids=['sum_mult_table'],
        )

        assert pipeline_result.success

        subgraph_two_result_list = pipeline_result.result_list

        assert len(subgraph_two_result_list) == 1
        output_df = subgraph_two_result_list[0].transformed_value
        assert output_df.to_dict('list') == {
            'num1': [1, 3],
            'num2': [2, 4],
            'sum': [3, 7],
            'mult': [2, 12],
            'sum_mult': [6, 84],
        }


def csv_materialization(solid_name, path):
    return config.Materialization(
        solid=solid_name,
        materialization_type='CSV',
        args={'path': path},
    )


def parquet_materialization(solid_name, path):
    return config.Materialization(
        solid=solid_name,
        materialization_type='PARQUET',
        args={'path': path},
    )


def test_pandas_output_intermediate_parquet_files():
    context = create_test_context()
    pipeline = create_diamond_pipeline()

    with get_temp_file_names(2) as temp_tuple:
        # false positive on pylint error
        sum_file, mult_file = temp_tuple  # pylint: disable=E0632
        pipeline_result = materialize_pipeline(
            context,
            pipeline,
            environment=get_num_csv_environment(),
            materializations=[
                parquet_materialization('sum_table', sum_file),
                parquet_materialization('mult_table', mult_file),
            ],
        )

        assert pipeline_result.success

        expected_sum = {
            'num1': [1, 3],
            'num2': [2, 4],
            'sum': [3, 7],
        }

        assert pd.read_parquet(sum_file).to_dict('list') == expected_sum


def test_pandas_multiple_inputs():

    context = create_test_context()

    environment = config.Environment(
        sources={
            'num_csv1': config.Source('CSV', {'path': script_relative_path('num.csv')}),
            'num_csv2': config.Source('CSV', {'path': script_relative_path('num.csv')}),
        }
    )

    def transform_fn(_context, args):
        return args['num_csv1'] + args['num_csv2']

    double_sum = dagster_pd.dataframe_solid(
        name='double_sum',
        inputs=[simple_csv_input('num_csv1'),
                simple_csv_input('num_csv2')],
        transform_fn=transform_fn
    )
    pipeline = dagster.core.pipeline(solids=[double_sum])

    output_df = execute_pipeline_through_solid(
        context,
        pipeline,
        environment=environment,
        solid_name='double_sum',
    ).transformed_value

    assert not output_df.empty

    assert output_df.to_dict('list') == {
        'num1': [2, 6],
        'num2': [4, 8],
    }


def test_pandas_multiple_outputs():
    context = create_test_context()

    with get_temp_file_names(2) as temp_tuple:
        # false positive on pylint error
        csv_file, parquet_file = temp_tuple  # pylint: disable=E0632
        pipeline = create_diamond_pipeline()

        for _result in materialize_pipeline_iterator(
            context,
            pipeline=pipeline,
            environment=get_num_csv_environment(),
            materializations=[
                csv_materialization('sum_mult_table', csv_file),
                parquet_materialization('sum_mult_table', parquet_file),
            ],
        ):
            pass

        assert os.path.exists(csv_file)
        output_csv_df = pd.read_csv(csv_file)
        assert output_csv_df.to_dict('list') == {
            'num1': [1, 3],
            'num2': [2, 4],
            'sum': [3, 7],
            'mult': [2, 12],
            'sum_mult': [6, 84],
        }

        assert os.path.exists(parquet_file)
        output_parquet_df = pd.read_parquet(parquet_file)
        assert output_parquet_df.to_dict('list') == {
            'num1': [1, 3],
            'num2': [2, 4],
            'sum': [3, 7],
            'mult': [2, 12],
            'sum_mult': [6, 84],
        }


def test_rename_input():
    result = execute_pipeline(
        create_test_context(),
        dagster.pipeline(solids=[sum_table, sum_sq_table_renamed_input]),
        environment=get_num_csv_environment(),
    )

    assert result.success

    assert result.result_named('sum_sq_table_renamed_input').transformed_value.to_dict('list') == {
        'num1': [1, 3],
        'num2': [2, 4],
        'sum': [3, 7],
        'sum_squared': [9, 49],
    }
