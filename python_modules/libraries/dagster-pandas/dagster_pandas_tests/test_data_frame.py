import pytest
from dagster_pandas.constraints import (
    ColumnTypeConstraint,
    InRangeColumnConstraint,
    NonNullableColumnConstraint,
)
from dagster_pandas.data_frame import _execute_summary_stats, create_dagster_pandas_dataframe_type
from dagster_pandas.validation import PandasColumn
from pandas import DataFrame, read_csv

from dagster import (
    DagsterInvariantViolationError,
    DagsterType,
    EventMetadataEntry,
    InputDefinition,
    Output,
    OutputDefinition,
    check_dagster_type,
    execute_pipeline,
    execute_solid,
    pipeline,
    solid,
)
from dagster.utils import safe_tempfile_path


def test_create_pandas_dataframe_dagster_type():
    TestDataFrame = create_dagster_pandas_dataframe_type(
        name='TestDataFrame',
        columns=[PandasColumn(name='foo', constraints=[ColumnTypeConstraint('int64')])],
    )
    assert isinstance(TestDataFrame, DagsterType)


def test_basic_pipeline_with_pandas_dataframe_dagster_type():
    def compute_event_metadata(dataframe):
        return [
            EventMetadataEntry.text(str(max(dataframe['pid'])), 'max_pid', 'maximum pid'),
        ]

    BasicDF = create_dagster_pandas_dataframe_type(
        name='BasicDF',
        columns=[
            PandasColumn.integer_column('pid', non_nullable=True),
            PandasColumn.string_column('names'),
        ],
        event_metadata_fn=compute_event_metadata,
    )

    @solid(output_defs=[OutputDefinition(name='basic_dataframe', dagster_type=BasicDF)])
    def create_dataframe(_):
        yield Output(
            DataFrame({'pid': [1, 2, 3], 'names': ['foo', 'bar', 'baz']}),
            output_name='basic_dataframe',
        )

    @pipeline
    def basic_pipeline():
        return create_dataframe()

    result = execute_pipeline(basic_pipeline)
    assert result.success
    for event in result.event_list:
        if event.event_type_value == 'STEP_OUTPUT':
            mock_df_output_event_metadata = (
                event.event_specific_data.type_check_data.metadata_entries
            )
            assert len(mock_df_output_event_metadata) == 1
            assert any([entry.label == 'max_pid' for entry in mock_df_output_event_metadata])


def test_create_dagster_pandas_dataframe_type_with_null_event_metadata_fn():
    BasicDF = create_dagster_pandas_dataframe_type(
        name='BasicDF',
        columns=[
            PandasColumn.integer_column('pid', non_nullable=True),
            PandasColumn.string_column('names'),
        ],
        event_metadata_fn=None,
    )
    assert isinstance(BasicDF, DagsterType)
    basic_type_check = check_dagster_type(BasicDF, DataFrame({'pid': [1], 'names': ['foo']}))
    assert basic_type_check.success


def test_bad_dataframe_type_returns_bad_stuff():
    with pytest.raises(DagsterInvariantViolationError):
        BadDFBadSummaryStats = create_dagster_pandas_dataframe_type(
            'BadDF', event_metadata_fn=lambda _: 'ksjdkfsd'
        )
        check_dagster_type(BadDFBadSummaryStats, DataFrame({'num': [1]}))

    with pytest.raises(DagsterInvariantViolationError):
        BadDFBadSummaryStatsListItem = create_dagster_pandas_dataframe_type(
            'BadDF', event_metadata_fn=lambda _: ['ksjdkfsd']
        )
        check_dagster_type(BadDFBadSummaryStatsListItem, DataFrame({'num': [1]}))


def test_dataframe_description_generation_just_type_constraint():
    TestDataFrame = create_dagster_pandas_dataframe_type(
        name='TestDataFrame',
        columns=[PandasColumn(name='foo', constraints=[ColumnTypeConstraint('int64')])],
    )
    assert TestDataFrame.description == "\n### Columns\n**foo**: `int64`\n\n"


def test_dataframe_description_generation_no_type_constraint():
    TestDataFrame = create_dagster_pandas_dataframe_type(
        name='TestDataFrame', columns=[PandasColumn(name='foo')],
    )
    assert TestDataFrame.description == "\n### Columns\n**foo**\n\n"


def test_dataframe_description_generation_multi_constraints():
    TestDataFrame = create_dagster_pandas_dataframe_type(
        name='TestDataFrame',
        columns=[
            PandasColumn(
                name='foo',
                constraints=[
                    ColumnTypeConstraint('int64'),
                    InRangeColumnConstraint(0, 100),
                    NonNullableColumnConstraint(),
                ],
            ),
        ],
    )
    assert (
        TestDataFrame.description
        == "\n### Columns\n**foo**: `int64`\n+ 0 < values < 100\n+ No Null values allowed.\n\n"
    )


def test_execute_summary_stats_null_function():
    assert _execute_summary_stats('foo', DataFrame(), None) == []

    metadata_entries = _execute_summary_stats(
        'foo',
        DataFrame({'bar': [1, 2, 3]}),
        lambda value: [EventMetadataEntry.text('baz', 'qux', 'quux')],
    )
    assert len(metadata_entries) == 1
    assert metadata_entries[0].label == 'qux'
    assert metadata_entries[0].description == 'quux'
    assert metadata_entries[0].entry_data.text == 'baz'


def test_execute_summary_stats_error():
    with pytest.raises(DagsterInvariantViolationError):
        assert _execute_summary_stats('foo', DataFrame({}), lambda value: 'jajaja')

    with pytest.raises(DagsterInvariantViolationError):
        assert _execute_summary_stats(
            'foo',
            DataFrame({}),
            lambda value: [EventMetadataEntry.text('baz', 'qux', 'quux'), 'rofl'],
        )


def test_custom_dagster_dataframe_hydration_ok():
    input_dataframe = DataFrame({'foo': [1, 2, 3]})
    with safe_tempfile_path() as input_csv_fp, safe_tempfile_path() as output_csv_fp:
        input_dataframe.to_csv(input_csv_fp)
        TestDataFrame = create_dagster_pandas_dataframe_type(
            name='TestDataFrame', columns=[PandasColumn.exists('foo'),]
        )

        @solid(
            input_defs=[InputDefinition('test_df', TestDataFrame)],
            output_defs=[OutputDefinition(TestDataFrame)],
        )
        def use_test_dataframe(_, test_df):
            test_df['bar'] = [2, 4, 6]
            return test_df

        solid_result = execute_solid(
            use_test_dataframe,
            environment_dict={
                'solids': {
                    'use_test_dataframe': {
                        'inputs': {'test_df': {'csv': {'path': input_csv_fp}}},
                        'outputs': [{'result': {'csv': {'path': output_csv_fp}}},],
                    }
                }
            },
        )

        assert solid_result.success
        solid_output_df = read_csv(output_csv_fp)
        assert all(solid_output_df['bar'] == [2, 4, 6])
