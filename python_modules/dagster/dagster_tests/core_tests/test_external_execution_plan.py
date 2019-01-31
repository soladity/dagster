import pytest

from dagster import (
    DependencyDefinition,
    InputDefinition,
    Int,
    OutputDefinition,
    PipelineDefinition,
    lambda_solid,
)
from dagster.core.errors import (
    DagsterExecutionStepNotFoundError,
    DagsterInvalidSubplanExecutionError,
    DagsterMarshalOutputError,
    DagsterMarshalOutputNotFoundError,
    DagsterUnmarshalInputError,
    DagsterUnmarshalInputNotFoundError,
)
from dagster.core.execution import (
    execute_externalized_plan,
    create_execution_plan,
    ExecutionMetadata,
)
from dagster.core.execution_plan.objects import StepKind
from dagster.core.types.runtime import resolve_to_runtime_type

from dagster.core.types.marshal import serialize_to_file, deserialize_from_file

from dagster.utils.test import get_temp_file_names


def define_inty_pipeline():
    @lambda_solid
    def return_one():
        return 1

    @lambda_solid(inputs=[InputDefinition('num', Int)], output=OutputDefinition(Int))
    def add_one(num):
        return num + 1

    pipeline = PipelineDefinition(
        name='basic_external_plan_execution',
        solids=[return_one, add_one],
        dependencies={'add_one': {'num': DependencyDefinition('return_one')}},
    )
    return pipeline


def test_basic_pipeline_external_plan_execution():
    pipeline = define_inty_pipeline()

    with get_temp_file_names(2) as temp_files:

        temp_path, write_path = temp_files  # pylint: disable=W0632

        int_type = resolve_to_runtime_type(Int)

        serialize_to_file(int_type.serialization_strategy, 5, temp_path)

        execution_plan = create_execution_plan(pipeline)

        results = execute_externalized_plan(
            pipeline,
            execution_plan,
            ['add_one.transform'],
            inputs_to_marshal={'add_one.transform': {'num': temp_path}},
            outputs_to_marshal={'add_one.transform': [{'output': 'result', 'path': write_path}]},
            execution_metadata=ExecutionMetadata(),
        )

        assert deserialize_from_file(int_type.serialization_strategy, write_path) == 6

    assert len(results) == 2

    thunk_step_result = results[0]

    assert thunk_step_result.kind == StepKind.VALUE_THUNK

    transform_step_result = results[1]
    assert transform_step_result.kind == StepKind.TRANSFORM
    assert transform_step_result.success
    assert transform_step_result.success_data.output_name == 'result'
    assert transform_step_result.success_data.value == 6


def test_external_execution_marshal_wrong_input_error():
    pipeline = define_inty_pipeline()

    execution_plan = create_execution_plan(pipeline)

    with pytest.raises(DagsterUnmarshalInputNotFoundError) as exc_info:
        execute_externalized_plan(
            pipeline,
            execution_plan,
            ['add_one.transform'],
            inputs_to_marshal={'add_one.transform': {'nope': 'nope'}},
            execution_metadata=ExecutionMetadata(),
        )

    assert str(exc_info.value) == 'Input nope does not exist in execution step add_one.transform'
    assert exc_info.value.input_name == 'nope'
    assert exc_info.value.step_key == 'add_one.transform'


def test_external_execution_step_for_input_missing():
    pipeline = define_inty_pipeline()

    execution_plan = create_execution_plan(pipeline)

    with pytest.raises(DagsterExecutionStepNotFoundError) as exc_info:
        execute_externalized_plan(
            pipeline,
            execution_plan,
            ['add_one.transform'],
            inputs_to_marshal={'nope': {'nope': 'nope'}},
            execution_metadata=ExecutionMetadata(),
        )

    assert exc_info.value.step_key == 'nope'


def test_external_execution_input_marshal_code_error():
    pipeline = define_inty_pipeline()

    execution_plan = create_execution_plan(pipeline)

    with pytest.raises(DagsterUnmarshalInputError) as exc_info:
        execute_externalized_plan(
            pipeline,
            execution_plan,
            ['add_one.transform'],
            inputs_to_marshal={'add_one.transform': {'num': 'nope'}},
            execution_metadata=ExecutionMetadata(),
        )

    assert (
        str(exc_info.value) == 'Error during the marshalling of input num in step add_one.transform'
    )
    assert exc_info.value.input_name == 'num'
    assert exc_info.value.step_key == 'add_one.transform'


def test_external_execution_step_for_output_missing():
    pipeline = define_inty_pipeline()

    execution_plan = create_execution_plan(pipeline)

    with pytest.raises(DagsterExecutionStepNotFoundError):
        execute_externalized_plan(
            pipeline,
            execution_plan,
            ['add_one.transform'],
            outputs_to_marshal={'nope': [{'output': 'nope', 'path': 'nope'}]},
            execution_metadata=ExecutionMetadata(),
        )


def test_external_execution_output_missing():
    pipeline = define_inty_pipeline()

    execution_plan = create_execution_plan(pipeline)

    with pytest.raises(DagsterMarshalOutputNotFoundError):
        execute_externalized_plan(
            pipeline,
            execution_plan,
            ['add_one.transform'],
            outputs_to_marshal={'add_one.transform': [{'output': 'nope', 'path': 'nope'}]},
            execution_metadata=ExecutionMetadata(),
        )


def test_external_execution_output_code_error():
    pipeline = define_inty_pipeline()

    execution_plan = create_execution_plan(pipeline)

    with pytest.raises(DagsterMarshalOutputError) as exc_info:
        execute_externalized_plan(
            pipeline,
            execution_plan,
            ['return_one.transform', 'add_one.transform'],
            outputs_to_marshal={'add_one.transform': [{'output': 'result', 'path': 23434}]},
            execution_metadata=ExecutionMetadata(),
        )

    assert (
        str(exc_info.value)
        == 'Error during the marshalling of output result in step add_one.transform'
    )
    assert exc_info.value.output_name == 'result'
    assert exc_info.value.step_key == 'add_one.transform'


def test_external_execution_unsatsified_input_error():
    pipeline = define_inty_pipeline()

    execution_plan = create_execution_plan(pipeline)

    with pytest.raises(DagsterInvalidSubplanExecutionError) as exc_info:
        execute_externalized_plan(
            pipeline, execution_plan, ['add_one.transform'], execution_metadata=ExecutionMetadata()
        )

    assert exc_info.value.pipeline_name == 'basic_external_plan_execution'
    assert exc_info.value.step_keys == ['add_one.transform']
    assert exc_info.value.step_key == 'add_one.transform'
    assert exc_info.value.input_name == 'num'

    assert str(exc_info.value) == (
        "You have specified a subset execution on pipeline basic_external_plan_execution with "
        "step_keys ['add_one.transform']. You have failed to provide the required input num for "
        "step add_one.transform."
    )
