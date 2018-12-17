import pytest

from dagster import (
    DependencyDefinition,
    DagsterInvariantViolationError,
    execute_pipeline,
    PipelineDefinition,
    solid,
    InputDefinition,
    OutputDefinition,
    types,
)


def test_string_csv_from_inputs():
    called = {}

    @solid(inputs=[InputDefinition('string_input', types.String)])
    def str_as_input(_info, string_input):
        assert string_input == 'foo'
        called['yup'] = True

    pipeline = PipelineDefinition(solids=[str_as_input])

    result = execute_pipeline(
        pipeline,
        {
            'solids': {
                'str_as_input': {
                    'inputs': {
                        'string_input': 'foo',
                    },
                },
            },
        },
    )

    assert result.success
    assert called['yup']


def test_string__missing_inputs():
    called = {}

    @solid(inputs=[InputDefinition('string_input', types.String)])
    def str_as_input(_info, string_input):  # pylint: disable=W0613
        called['yup'] = True

    pipeline = PipelineDefinition(name='missing_inputs', solids=[str_as_input])
    with pytest.raises(DagsterInvariantViolationError) as exc_info:
        execute_pipeline(pipeline)

    assert 'In pipeline missing_inputs solid str_as_input, input string_input' in str(
        exc_info.value
    )

    assert 'yup' not in called


def test_string_csv_missing_input_collision():
    called = {}

    @solid(outputs=[OutputDefinition(types.String)])
    def str_as_output(_info):
        return 'bar'

    @solid(inputs=[InputDefinition('string_input', types.String)])
    def str_as_input(_info, string_input):  # pylint: disable=W0613
        called['yup'] = True

    pipeline = PipelineDefinition(
        name='overlapping',
        solids=[str_as_input, str_as_output],
        dependencies={
            'str_as_input': {
                'string_input': DependencyDefinition('str_as_output'),
            },
        },
    )
    with pytest.raises(DagsterInvariantViolationError) as exc_info:
        execute_pipeline(
            pipeline,
            {
                'solids': {
                    'str_as_input': {
                        'inputs': {
                            'string_input': 'bar',
                        },
                    },
                },
            },
        )

    assert 'In pipeline overlapping solid str_as_input, input string_input' in str(exc_info.value)
    assert 'while also specifying' in str(exc_info.value)

    assert 'yup' not in called
