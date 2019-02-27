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
    DagsterExecutionStepExecutionError,
    DagsterExecutionStepNotFoundError,
    DagsterInvalidSubplanInputNotFoundError,
    DagsterInvalidSubplanMissingInputError,
    DagsterInvalidSubplanOutputNotFoundError,
)

from dagster.core.execution import ExecutionMetadata, execute_marshalling

from dagster.core.execution_plan.objects import StepKind
from dagster.core.execution_plan.plan_subset import MarshalledOutput
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

    @lambda_solid
    def user_throw_exception():
        raise Exception('whoops')

    pipeline = PipelineDefinition(
        name='basic_external_plan_execution',
        solids=[return_one, add_one, user_throw_exception],
        dependencies={'add_one': {'num': DependencyDefinition('return_one')}},
    )
    return pipeline


def test_basic_pipeline_external_plan_execution():
    pipeline = define_inty_pipeline()

    with get_temp_file_names(2) as temp_files:

        temp_path, write_path = temp_files  # pylint: disable=W0632

        int_type = resolve_to_runtime_type(Int)

        serialize_to_file(int_type.serialization_strategy, 5, temp_path)

        step_events = execute_marshalling(
            pipeline,
            ['add_one.transform'],
            inputs_to_marshal={'add_one.transform': {'num': temp_path}},
            outputs_to_marshal={'add_one.transform': [MarshalledOutput('result', write_path)]},
        )

        assert deserialize_from_file(int_type.serialization_strategy, write_path) == 6

    assert len(step_events) == 2

    thunk_step_output_event = step_events[0]

    assert thunk_step_output_event.kind == StepKind.UNMARSHAL_INPUT

    transform_step_output_event = step_events[1]
    assert transform_step_output_event.kind == StepKind.TRANSFORM
    assert transform_step_output_event.is_successful_output
    assert transform_step_output_event.step_output_data.output_name == 'result'
    assert transform_step_output_event.step_output_data.get_value() == 6


def test_external_execution_marshal_wrong_input_error():
    pipeline = define_inty_pipeline()

    with pytest.raises(DagsterInvalidSubplanInputNotFoundError) as exc_info:
        execute_marshalling(
            pipeline,
            ['add_one.transform'],
            inputs_to_marshal={'add_one.transform': {'nope': 'nope'}},
        )

    assert str(exc_info.value) == 'Input nope on add_one.transform does not exist.'
    assert exc_info.value.pipeline_name == pipeline.name
    assert exc_info.value.step_keys == ['add_one.transform']


def test_external_execution_step_for_input_missing():
    pipeline = define_inty_pipeline()

    with pytest.raises(DagsterExecutionStepNotFoundError) as exc_info:
        execute_marshalling(
            pipeline, ['add_one.transform'], inputs_to_marshal={'nope': {'nope': 'nope'}}
        )

    assert exc_info.value.step_key == 'nope'


def test_external_execution_input_marshal_code_error():
    pipeline = define_inty_pipeline()

    with pytest.raises(IOError):
        execute_marshalling(
            pipeline,
            ['add_one.transform'],
            inputs_to_marshal={'add_one.transform': {'num': 'nope'}},
            throw_on_user_error=True,
        )

    step_events = execute_marshalling(
        pipeline,
        ['add_one.transform'],
        inputs_to_marshal={'add_one.transform': {'num': 'nope'}},
        throw_on_user_error=False,
    )

    assert len(step_events) == 1
    marshal_step_error = step_events[0]
    assert marshal_step_error.is_step_failure
    assert not marshal_step_error.is_successful_output
    assert marshal_step_error.step.kind == StepKind.UNMARSHAL_INPUT
    assert isinstance(marshal_step_error.step_failure_data.dagster_error.user_exception, IOError)


def test_external_execution_step_for_output_missing():
    pipeline = define_inty_pipeline()

    with pytest.raises(DagsterExecutionStepNotFoundError):
        execute_marshalling(
            pipeline,
            ['add_one.transform'],
            inputs_to_marshal={'add_one.transform': {'num': 'nope'}},
            outputs_to_marshal={'nope': [MarshalledOutput('nope', 'nope')]},
        )


def test_external_execution_output_missing():
    pipeline = define_inty_pipeline()

    with pytest.raises(DagsterInvalidSubplanOutputNotFoundError):
        execute_marshalling(
            pipeline,
            ['add_one.transform'],
            outputs_to_marshal={'add_one.transform': [MarshalledOutput('nope', 'nope')]},
        )


def test_external_execution_marshal_output_code_error():
    pipeline = define_inty_pipeline()

    # guaranteed that folder does not exist
    hardcoded_uuid = '83fb4ace-5cab-459d-99b6-2ca9808c54a1'

    outputs_to_marshal = {
        'add_one.transform': [
            MarshalledOutput(
                output_name='result', marshalling_key='{uuid}/{uuid}'.format(uuid=hardcoded_uuid)
            )
        ]
    }

    with pytest.raises(IOError) as exc_info:
        execute_marshalling(
            pipeline,
            ['return_one.transform', 'add_one.transform'],
            outputs_to_marshal=outputs_to_marshal,
            execution_metadata=ExecutionMetadata(),
            throw_on_user_error=True,
        )

    assert 'No such file or directory' in str(exc_info.value)

    step_events = execute_marshalling(
        pipeline,
        ['return_one.transform', 'add_one.transform'],
        outputs_to_marshal=outputs_to_marshal,
        execution_metadata=ExecutionMetadata(),
        throw_on_user_error=False,
    )

    assert len(step_events) == 3

    events_dict = {event.step.key: event for event in step_events}

    assert events_dict['return_one.transform'].is_successful_output is True
    assert events_dict['add_one.transform'].is_successful_output is True
    assert events_dict['add_one.transform.marshal-output.result'].is_successful_output is False


def test_external_execution_output_code_error_throw_on_user_error():
    pipeline = define_inty_pipeline()

    with pytest.raises(Exception) as exc_info:
        execute_marshalling(
            pipeline,
            ['user_throw_exception.transform'],
            execution_metadata=ExecutionMetadata(),
            throw_on_user_error=True,
        )

    assert str(exc_info.value) == 'whoops'


def test_external_execution_output_code_error_no_throw_on_user_error():
    pipeline = define_inty_pipeline()

    step_events = execute_marshalling(
        pipeline,
        ['user_throw_exception.transform'],
        execution_metadata=ExecutionMetadata(),
        throw_on_user_error=False,
    )

    assert len(step_events) == 1
    step_event = step_events[0]
    assert isinstance(
        step_event.step_failure_data.dagster_error, DagsterExecutionStepExecutionError
    )
    assert str(step_event.step_failure_data.dagster_error.user_exception) == 'whoops'


def test_external_execution_unsatisfied_input_error():
    pipeline = define_inty_pipeline()

    with pytest.raises(DagsterInvalidSubplanMissingInputError) as exc_info:
        execute_marshalling(pipeline, ['add_one.transform'], execution_metadata=ExecutionMetadata())

    assert exc_info.value.pipeline_name == 'basic_external_plan_execution'
    assert exc_info.value.step_keys == ['add_one.transform']
    assert exc_info.value.step.key == 'add_one.transform'
    assert exc_info.value.input_name == 'num'

    assert str(exc_info.value) == (
        "You have specified a subset execution on pipeline basic_external_plan_execution with "
        "step_keys ['add_one.transform']. You have failed to provide the required input num for "
        "step add_one.transform."
    )
