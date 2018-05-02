from solidic.types import SolidString

from solidic.definitions import (
    Solid, SolidInputDefinition, SolidOutputTypeDefinition, SolidExecutionContext,
    SolidExpectationDefinition, SolidExpectationResult
)

from solidic.execution import (execute_solid, SolidExecutionResult, SolidExecutionFailureReason)


def create_test_context():
    return SolidExecutionContext()


def test_execute_solid_no_args():
    some_input = SolidInputDefinition(
        name='some_input',
        input_fn=lambda arg_dict: [{'data_key': 'data_value'}],
        argument_def_dict={}
    )

    def tranform_fn_inst(some_input):
        some_input[0]['data_key'] = 'new_value'
        return some_input

    test_output = {}

    def output_fn_inst(data, _output_arg_dict):
        test_output['thedata'] = data

    custom_output = SolidOutputTypeDefinition(
        name='CUSTOM',
        output_fn=output_fn_inst,
        argument_def_dict={},
    )

    single_solid = Solid(
        name='some_node',
        inputs=[some_input],
        transform_fn=tranform_fn_inst,
        output_type_defs=[custom_output],
    )

    execute_solid(
        create_test_context(),
        single_solid,
        input_arg_dicts={'some_input': {}},
        output_type='CUSTOM',
        output_arg_dict={}
    )

    assert test_output['thedata'] == [{'data_key': 'new_value'}]


def create_single_dict_input(expectations=None):
    return SolidInputDefinition(
        name='some_input',
        input_fn=lambda arg_dict: [{'key': arg_dict['str_arg']}],
        argument_def_dict={'str_arg': SolidString},
        expectations=expectations or [],
    )


def create_noop_output(test_output, expectations=None):
    def set_test_output(output, _arg_dict):
        test_output['thedata'] = output

    return SolidOutputTypeDefinition(
        name='CUSTOM',
        output_fn=set_test_output,
        argument_def_dict={},
        expectations=expectations or [],
    )


def test_execute_solid_with_args():
    test_output = {}

    single_solid = Solid(
        name='some_node',
        inputs=[create_single_dict_input()],
        transform_fn=lambda some_input: some_input,
        output_type_defs=[create_noop_output(test_output)],
    )

    execute_solid(
        create_test_context(),
        single_solid,
        input_arg_dicts={'some_input': {
            'str_arg': 'an_input_arg'
        }},
        output_type='CUSTOM',
        output_arg_dict={},
    )

    assert test_output['thedata'][0]['key'] == 'an_input_arg'


def test_execute_solid_with_failed_input_expectation():
    test_output = {}

    # input_def=[create_single_dict_input(expectations=[failing_expect])

    def failing_expectation_fn(_some_input):
        return SolidExpectationResult(success=False)

    failing_expect = SolidExpectationDefinition(
        name='failing', expectation_fn=failing_expectation_fn
    )

    single_solid = Solid(
        name='some_node',
        inputs=[create_single_dict_input(expectations=[failing_expect])],
        transform_fn=lambda some_input: some_input,
        output_type_defs=[create_noop_output(test_output)],
    )

    solid_executation_result = execute_solid(
        create_test_context(),
        single_solid,
        input_arg_dicts={'some_input': {
            'str_arg': 'an_input_arg'
        }},
        output_type='CUSTOM',
        output_arg_dict={},
    )

    assert isinstance(solid_executation_result, SolidExecutionResult)
    assert solid_executation_result.success is False
    assert solid_executation_result.reason == SolidExecutionFailureReason.EXPECTATION_FAILURE
