import pytest
from dagster_examples.intro_tutorial.inputs import (
    execute_with_another_world,
    hello_typed_inputs_pipeline,
)

from dagster import DagsterInvalidConfigError, execute_pipeline
from dagster.utils import check_cli_execute_file_pipeline, script_relative_path


def test_hello_inputs_parameterized_pipeline():
    result = execute_with_another_world()
    assert result.success
    solid_result = result.result_for_solid('add_hello_to_word')
    assert solid_result.output_value() == 'Hello, Mars!'


def test_hello_inputs_parameterized_cli_pipeline():
    check_cli_execute_file_pipeline(
        script_relative_path('../../dagster_examples/intro_tutorial/inputs.py'),
        'hello_inputs_pipeline',
        script_relative_path('../../dagster_examples/intro_tutorial/inputs_env.yaml'),
    )


def test_hello_typed_inputs():
    with pytest.raises(
        DagsterInvalidConfigError,
        match=(
            'Type failure at path '
            '"root:solids:add_hello_to_word_typed:inputs:word:value" on type "String"'
        ),
    ):
        execute_pipeline(
            hello_typed_inputs_pipeline,
            {'solids': {'add_hello_to_word_typed': {'inputs': {'word': {'value': 343}}}}},
        )


def test_hello_typed_bad_structure():
    with pytest.raises(
        DagsterInvalidConfigError,
        match='Value for selector type String.InputHydrationConfig must be a dict',
    ):
        execute_pipeline(
            hello_typed_inputs_pipeline,
            {'solids': {'add_hello_to_word_typed': {'inputs': {'word': {'Foobar Baz'}}}}},
        )


def test_hello_typed():
    result = execute_pipeline(
        hello_typed_inputs_pipeline,
        {'solids': {'add_hello_to_word_typed': {'inputs': {'word': {'value': 'Foobar Baz'}}}}},
    )
    assert result.success
    assert len(result.solid_result_list) == 1
    assert result.result_for_solid('add_hello_to_word_typed').output_value() == 'Hello, Foobar Baz!'
