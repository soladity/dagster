import pytest

from dagster import (
    Any,
    Bool,
    Float,
    InputDefinition,
    Int,
    List,
    Nullable,
    OutputDefinition,
    Path,
    PipelineConfigEvaluationError,
    PipelineDefinition,
    String,
    execute_pipeline,
    lambda_solid,
)

from dagster.utils.test import get_temp_file_name


def define_test_all_scalars_pipeline():
    @lambda_solid(inputs=[InputDefinition('num', Int)])
    def take_int(num):
        return num

    @lambda_solid(output=OutputDefinition(Int))
    def produce_int():
        return 2

    @lambda_solid(inputs=[InputDefinition('string', String)])
    def take_string(string):
        return string

    @lambda_solid(output=OutputDefinition(String))
    def produce_string():
        return 'foo'

    @lambda_solid(inputs=[InputDefinition('path', Path)])
    def take_path(path):
        return path

    @lambda_solid(output=OutputDefinition(Path))
    def produce_path():
        return '/path/to/foo'

    @lambda_solid(inputs=[InputDefinition('float_number', Float)])
    def take_float(float_number):
        return float_number

    @lambda_solid(output=OutputDefinition(Float))
    def produce_float():
        return 3.14

    @lambda_solid(inputs=[InputDefinition('bool_value', Bool)])
    def take_bool(bool_value):
        return bool_value

    @lambda_solid(output=OutputDefinition(Bool))
    def produce_bool():
        return True

    @lambda_solid(inputs=[InputDefinition('any_value', Any)])
    def take_any(any_value):
        return any_value

    @lambda_solid(output=OutputDefinition(Any))
    def produce_any():
        return True

    @lambda_solid(inputs=[InputDefinition('string_list', List(String))])
    def take_string_list(string_list):
        return string_list

    @lambda_solid(inputs=[InputDefinition('nullable_string', Nullable(String))])
    def take_nullable_string(nullable_string):
        return nullable_string

    return PipelineDefinition(
        name='test_all_scalars_pipeline',
        solids=[
            produce_any,
            produce_bool,
            produce_float,
            produce_int,
            produce_path,
            produce_string,
            take_any,
            take_bool,
            take_float,
            take_int,
            take_nullable_string,
            take_path,
            take_string,
            take_string_list,
        ],
    )


def single_input_env(solid_name, input_name, input_spec):
    return {'solids': {solid_name: {'inputs': {input_name: input_spec}}}}


def test_int_input_schema_value():
    result = execute_pipeline(
        define_test_all_scalars_pipeline(),
        environment=single_input_env('take_int', 'num', {'value': 2}),
        solid_subset=['take_int'],
    )

    assert result.success
    assert result.result_for_solid('take_int').transformed_value() == 2


def test_int_input_schema_failure():
    with pytest.raises(PipelineConfigEvaluationError) as exc_info:
        execute_pipeline(
            define_test_all_scalars_pipeline(),
            environment=single_input_env('take_int', 'num', {'value': 'dkjdfkdj'}),
            solid_subset=['take_int'],
        )

    assert 'Type failure at path "root:solids:take_int:inputs:num:value" on type "Int"' in str(
        exc_info.value
    )


def single_output_env(solid_name, output_spec):
    return {'solids': {solid_name: {'outputs': [{'result': output_spec}]}}}


def test_int_json_schema_roundtrip():
    with get_temp_file_name() as tmp_file:
        mat_result = execute_pipeline(
            define_test_all_scalars_pipeline(),
            environment=single_output_env('produce_int', {'json': {'path': tmp_file}}),
            solid_subset=['produce_int'],
        )

        assert mat_result.success

        source_result = execute_pipeline(
            define_test_all_scalars_pipeline(),
            environment=single_input_env('take_int', 'num', {'json': {'path': tmp_file}}),
            solid_subset=['take_int'],
        )

        assert source_result.result_for_solid('take_int').transformed_value() == 2


def test_int_pickle_schema_roundtrip():
    with get_temp_file_name() as tmp_file:
        mat_result = execute_pipeline(
            define_test_all_scalars_pipeline(),
            environment=single_output_env('produce_int', {'pickle': {'path': tmp_file}}),
            solid_subset=['produce_int'],
        )

        assert mat_result.success

        source_result = execute_pipeline(
            define_test_all_scalars_pipeline(),
            environment=single_input_env('take_int', 'num', {'pickle': {'path': tmp_file}}),
            solid_subset=['take_int'],
        )

        assert source_result.result_for_solid('take_int').transformed_value() == 2


def test_string_input_schema_value():
    result = execute_pipeline(
        define_test_all_scalars_pipeline(),
        environment=single_input_env('take_string', 'string', {'value': 'dkjkfd'}),
        solid_subset=['take_string'],
    )

    assert result.success
    assert result.result_for_solid('take_string').transformed_value() == 'dkjkfd'


def test_string_input_schema_failure():
    with pytest.raises(PipelineConfigEvaluationError) as exc_info:
        execute_pipeline(
            define_test_all_scalars_pipeline(),
            environment=single_input_env('take_string', 'string', {'value': 3343}),
            solid_subset=['take_string'],
        )

    assert (
        'Type failure at path "root:solids:take_string:inputs:string:value" on type "String"'
        in str(exc_info.value)
    )


def test_float_input_schema_value():
    result = execute_pipeline(
        define_test_all_scalars_pipeline(),
        environment=single_input_env('take_float', 'float_number', {'value': 3.34}),
        solid_subset=['take_float'],
    )

    assert result.success
    assert result.result_for_solid('take_float').transformed_value() == 3.34


def test_float_input_schema_failure():
    with pytest.raises(PipelineConfigEvaluationError) as exc_info:
        execute_pipeline(
            define_test_all_scalars_pipeline(),
            environment=single_input_env('take_float', 'float_number', {'value': '3343'}),
            solid_subset=['take_float'],
        )

    assert (
        'Type failure at path "root:solids:take_float:inputs:float_number:value" on type "Float"'
        in str(exc_info.value)
    )


def test_bool_input_schema_value():
    result = execute_pipeline(
        define_test_all_scalars_pipeline(),
        environment=single_input_env('take_bool', 'bool_value', {'value': True}),
        solid_subset=['take_bool'],
    )

    assert result.success
    assert result.result_for_solid('take_bool').transformed_value() is True


def test_bool_input_schema_failure():
    with pytest.raises(PipelineConfigEvaluationError) as exc_info:
        execute_pipeline(
            define_test_all_scalars_pipeline(),
            environment=single_input_env('take_bool', 'bool_value', {'value': '3343'}),
            solid_subset=['take_bool'],
        )

    assert (
        'Type failure at path "root:solids:take_bool:inputs:bool_value:value" on type "Bool".'
        in str(exc_info.value)
    )


def test_any_input_schema_value():
    result = execute_pipeline(
        define_test_all_scalars_pipeline(),
        environment=single_input_env('take_any', 'any_value', {'value': 'ff'}),
        solid_subset=['take_any'],
    )

    assert result.success
    assert result.result_for_solid('take_any').transformed_value() == 'ff'

    result = execute_pipeline(
        define_test_all_scalars_pipeline(),
        environment=single_input_env('take_any', 'any_value', {'value': 3843}),
        solid_subset=['take_any'],
    )

    assert result.success
    assert result.result_for_solid('take_any').transformed_value() == 3843


def test_none_string_input_schema_failure():
    with pytest.raises(PipelineConfigEvaluationError) as exc_info:
        execute_pipeline(
            define_test_all_scalars_pipeline(),
            environment=single_input_env('take_string', 'string', None),
            solid_subset=['take_string'],
        )

    assert (
        'Error 1: You specified no fields at path "root:solids:take_string:inputs:string"'
        in str(exc_info.value)
    )


def test_value_none_string_input_schema_failure():
    with pytest.raises(PipelineConfigEvaluationError) as exc_info:
        execute_pipeline(
            define_test_all_scalars_pipeline(),
            environment=single_input_env('take_string', 'string', {'value': None}),
            solid_subset=['take_string'],
        )

    assert (
        'Type failure at path "root:solids:take_string:inputs:string:value" on type "String"'
        in str(exc_info.value)
    )


def test_string_json_schema_roundtrip():
    with get_temp_file_name() as tmp_file:
        mat_result = execute_pipeline(
            define_test_all_scalars_pipeline(),
            environment=single_output_env('produce_string', {'json': {'path': tmp_file}}),
            solid_subset=['produce_string'],
        )

        assert mat_result.success

        source_result = execute_pipeline(
            define_test_all_scalars_pipeline(),
            environment=single_input_env('take_string', 'string', {'json': {'path': tmp_file}}),
            solid_subset=['take_string'],
        )

        assert source_result.result_for_solid('take_string').transformed_value() == 'foo'


def test_string_pickle_schema_roundtrip():
    with get_temp_file_name() as tmp_file:
        mat_result = execute_pipeline(
            define_test_all_scalars_pipeline(),
            environment=single_output_env('produce_string', {'pickle': {'path': tmp_file}}),
            solid_subset=['produce_string'],
        )

        assert mat_result.success

        source_result = execute_pipeline(
            define_test_all_scalars_pipeline(),
            environment=single_input_env('take_string', 'string', {'pickle': {'path': tmp_file}}),
            solid_subset=['take_string'],
        )

        assert source_result.result_for_solid('take_string').transformed_value() == 'foo'


def test_path_input_schema_value():
    result = execute_pipeline(
        define_test_all_scalars_pipeline(),
        environment=single_input_env('take_path', 'path', '/a/path'),
        solid_subset=['take_path'],
    )

    assert result.success
    assert result.result_for_solid('take_path').transformed_value() == '/a/path'


def test_path_input_schema_failure():
    with pytest.raises(PipelineConfigEvaluationError) as exc_info:
        execute_pipeline(
            define_test_all_scalars_pipeline(),
            environment=single_input_env('take_path', 'path', {'value': 3343}),
            solid_subset=['take_path'],
        )

    assert 'Type failure at path "root:solids:take_path:inputs:path" on type "Path"' in str(
        exc_info.value
    )


def test_string_list_input():
    result = execute_pipeline(
        define_test_all_scalars_pipeline(),
        environment=single_input_env('take_string_list', 'string_list', [{'value': 'foobar'}]),
        solid_subset=['take_string_list'],
    )

    assert result.success

    assert result.result_for_solid('take_string_list').transformed_value() == ['foobar']


def test_nullable_string_input_with_value():
    result = execute_pipeline(
        define_test_all_scalars_pipeline(),
        environment=single_input_env(
            'take_nullable_string', 'nullable_string', {'value': 'foobar'}
        ),
        solid_subset=['take_nullable_string'],
    )

    assert result.success

    assert result.result_for_solid('take_nullable_string').transformed_value() == 'foobar'


def test_nullable_string_input_with_none_value():
    # Perhaps a confusing test case. Nullable makes the entire enclosing structure nullable,
    # rather than the "value" value embedded within it
    with pytest.raises(PipelineConfigEvaluationError) as exc_info:
        execute_pipeline(
            define_test_all_scalars_pipeline(),
            environment=single_input_env(
                'take_nullable_string', 'nullable_string', {'value': None}
            ),
            solid_subset=['take_nullable_string'],
        )

    assert (
        'Type failure at path "root:solids:take_nullable_string:inputs:nullable_string:value" '
        'on type "String"'
    ) in str(exc_info.value)


def test_nullable_string_input_without_value():
    result = execute_pipeline(
        define_test_all_scalars_pipeline(),
        environment=single_input_env('take_nullable_string', 'nullable_string', None),
        solid_subset=['take_nullable_string'],
    )

    assert result.success

    assert result.result_for_solid('take_nullable_string').transformed_value() is None
