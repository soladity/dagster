from dagster.utils import script_relative_path
from .setup import execute_dagster_graphql, define_context, pandas_hello_world_solids_config

CONFIG_VALIDATION_QUERY = '''
query PipelineQuery($config: PipelineConfig, $pipeline: ExecutionSelector!)
{
    isPipelineConfigValid(config: $config, pipeline: $pipeline) {
        __typename
        ... on PipelineConfigValidationValid {
            pipeline { name }
        }
        ... on PipelineConfigValidationInvalid {
            pipeline { name }
            errors {
                __typename
                ... on RuntimeMismatchConfigError {
                    type { name }
                    valueRep
                }
                ... on MissingFieldConfigError {
                    field { name }
                }
                ... on MissingFieldsConfigError {
                    fields { name }
                }
                ... on FieldNotDefinedConfigError {
                    fieldName
                }
                ... on FieldsNotDefinedConfigError {
                    fieldNames
                }
                ... on SelectorTypeConfigError {
                    incomingFields
                }
                message
                reason
                stack {
                    entries {
                        __typename
                        ... on EvaluationStackPathEntry {
                            field {
                                name
                                configType {
                                    name
                                }
                            }
                        }
                        ... on EvaluationStackListItemEntry {
                            listIndex
                        }
                    }
                }
            }
        }
        ... on PipelineNotFoundError {
            pipelineName
        }
    }
}
'''


def field_stack(error_data):
    return [
        entry['field']['name']
        for entry in error_data['stack']['entries']
        if entry['__typename'] == 'EvaluationStackPathEntry'
    ]


def single_error_data(result):
    assert len(result.data['isPipelineConfigValid']['errors']) == 1
    return result.data['isPipelineConfigValid']['errors'][0]


def find_error(result, field_stack_to_find, reason):
    llist = list(find_errors(result, field_stack_to_find, reason))
    assert len(llist) == 1
    return llist[0]


def find_errors(result, field_stack_to_find, reason):
    error_datas = result.data['isPipelineConfigValid']['errors']
    for error_data in error_datas:
        if field_stack_to_find == field_stack(error_data) and error_data['reason'] == reason:
            yield error_data


def execute_config_graphql(pipeline_name, env_config):
    return execute_dagster_graphql(
        define_context(),
        CONFIG_VALIDATION_QUERY,
        {'config': env_config, 'pipeline': {'name': pipeline_name}},
    )


def test_pipeline_not_found():
    result = execute_config_graphql(pipeline_name='nope', env_config={})

    assert not result.errors
    assert result.data
    assert result.data['isPipelineConfigValid']['__typename'] == 'PipelineNotFoundError'
    assert result.data['isPipelineConfigValid']['pipelineName'] == 'nope'


def test_basic_valid_config():
    result = execute_config_graphql(
        pipeline_name='pandas_hello_world', env_config=pandas_hello_world_solids_config()
    )

    assert not result.errors
    assert result.data
    assert result.data['isPipelineConfigValid']['__typename'] == 'PipelineConfigValidationValid'
    assert result.data['isPipelineConfigValid']['pipeline']['name'] == 'pandas_hello_world'


def test_root_field_not_defined():
    result = execute_config_graphql(
        pipeline_name='pandas_hello_world',
        env_config={
            'solids': {
                'sum_solid': {'inputs': {'num': {'csv': {'path': script_relative_path('num.csv')}}}}
            },
            'nope': {},
        },
    )

    assert not result.errors
    assert result.data
    assert result.data['isPipelineConfigValid']['__typename'] == 'PipelineConfigValidationInvalid'
    assert result.data['isPipelineConfigValid']['pipeline']['name'] == 'pandas_hello_world'
    errors = result.data['isPipelineConfigValid']['errors']
    assert len(errors) == 1
    error = errors[0]
    assert error['__typename'] == 'FieldNotDefinedConfigError'
    assert error['fieldName'] == 'nope'
    assert not error['stack']['entries']


def test_basic_invalid_not_defined_field():
    result = execute_config_graphql(
        pipeline_name='pandas_hello_world',
        env_config={
            'solids': {
                'sum_solid': {'inputs': {'num': {'csv': {'path': 'foo.txt', 'extra': 'nope'}}}}
            }
        },
    )

    assert not result.errors
    assert result.data
    assert result.data['isPipelineConfigValid']['__typename'] == 'PipelineConfigValidationInvalid'
    assert result.data['isPipelineConfigValid']['pipeline']['name'] == 'pandas_hello_world'
    assert len(result.data['isPipelineConfigValid']['errors']) == 1
    error_data = result.data['isPipelineConfigValid']['errors'][0]
    assert ['solids', 'sum_solid', 'inputs', 'num', 'csv'] == field_stack(error_data)
    assert error_data['reason'] == 'FIELD_NOT_DEFINED'
    assert error_data['fieldName'] == 'extra'


def test_multiple_not_defined_fields():
    result = execute_config_graphql(
        pipeline_name='pandas_hello_world',
        env_config={
            'solids': {
                'sum_solid': {
                    'inputs': {
                        'num': {
                            'csv': {'path': 'foo.txt', 'extra_one': 'nope', 'extra_two': 'nope'}
                        }
                    }
                }
            }
        },
    )

    assert not result.errors
    assert result.data
    assert result.data['isPipelineConfigValid']['__typename'] == 'PipelineConfigValidationInvalid'
    assert result.data['isPipelineConfigValid']['pipeline']['name'] == 'pandas_hello_world'
    assert len(result.data['isPipelineConfigValid']['errors']) == 1
    error_data = result.data['isPipelineConfigValid']['errors'][0]
    assert ['solids', 'sum_solid', 'inputs', 'num', 'csv'] == field_stack(error_data)
    assert error_data['reason'] == 'FIELDS_NOT_DEFINED'
    assert error_data['fieldNames'] == ['extra_one', 'extra_two']


def test_root_wrong_type():
    result = execute_config_graphql(pipeline_name='pandas_hello_world', env_config=123)
    assert not result.errors
    assert result.data
    assert result.data['isPipelineConfigValid']['__typename'] == 'PipelineConfigValidationInvalid'
    assert result.data['isPipelineConfigValid']['pipeline']['name'] == 'pandas_hello_world'
    errors = result.data['isPipelineConfigValid']['errors']
    assert len(errors) == 1
    error = errors[0]
    assert error['reason'] == 'RUNTIME_TYPE_MISMATCH'
    assert not error['stack']['entries']


def test_basic_invalid_config_type_mismatch():
    result = execute_config_graphql(
        pipeline_name='pandas_hello_world',
        env_config={'solids': {'sum_solid': {'inputs': {'num': {'csv': {'path': 123}}}}}},
    )

    assert not result.errors
    assert result.data
    assert result.data['isPipelineConfigValid']['__typename'] == 'PipelineConfigValidationInvalid'
    assert result.data['isPipelineConfigValid']['pipeline']['name'] == 'pandas_hello_world'
    assert len(result.data['isPipelineConfigValid']['errors']) == 1
    error_data = result.data['isPipelineConfigValid']['errors'][0]
    assert error_data['message']
    assert error_data['stack']
    assert error_data['stack']['entries']
    assert error_data['reason'] == 'RUNTIME_TYPE_MISMATCH'
    assert error_data['valueRep'] == '123'
    assert error_data['type']['name'] == 'Path'

    assert ['solids', 'sum_solid', 'inputs', 'num', 'csv', 'path'] == field_stack(error_data)


def test_basic_invalid_config_missing_field():
    result = execute_config_graphql(
        pipeline_name='pandas_hello_world',
        env_config={'solids': {'sum_solid': {'inputs': {'num': {'csv': {}}}}}},
    )

    assert not result.errors
    assert result.data
    assert result.data['isPipelineConfigValid']['__typename'] == 'PipelineConfigValidationInvalid'
    assert result.data['isPipelineConfigValid']['pipeline']['name'] == 'pandas_hello_world'
    assert len(result.data['isPipelineConfigValid']['errors']) == 1
    error_data = result.data['isPipelineConfigValid']['errors'][0]

    assert ['solids', 'sum_solid', 'inputs', 'num', 'csv'] == field_stack(error_data)
    assert error_data['reason'] == 'MISSING_REQUIRED_FIELD'
    assert error_data['field']['name'] == 'path'


def test_context_config_works():
    result = execute_config_graphql(
        pipeline_name='context_config_pipeline',
        env_config={'context': {'context_one': {'config': 'kj23k4j3'}}},
    )

    assert not result.errors
    assert result.data
    assert result.data['isPipelineConfigValid']['__typename'] == 'PipelineConfigValidationValid'
    assert result.data['isPipelineConfigValid']['pipeline']['name'] == 'context_config_pipeline'

    result = execute_config_graphql(
        pipeline_name='context_config_pipeline',
        env_config={'context': {'context_two': {'config': 38934}}},
    )

    assert not result.errors
    assert result.data
    assert result.data['isPipelineConfigValid']['__typename'] == 'PipelineConfigValidationValid'
    assert result.data['isPipelineConfigValid']['pipeline']['name'] == 'context_config_pipeline'


def test_context_config_selector_error():
    result = execute_config_graphql(
        pipeline_name='context_config_pipeline', env_config={'context': {}}
    )

    assert not result.errors
    assert result.data
    assert result.data['isPipelineConfigValid']['__typename'] == 'PipelineConfigValidationInvalid'
    error_data = single_error_data(result)
    assert error_data['reason'] == 'SELECTOR_FIELD_ERROR'
    assert error_data['incomingFields'] == []


def test_context_config_wrong_selector():
    result = execute_config_graphql(
        pipeline_name='context_config_pipeline', env_config={'context': {'not_defined': {}}}
    )

    assert not result.errors
    assert result.data
    assert result.data['isPipelineConfigValid']['__typename'] == 'PipelineConfigValidationInvalid'
    error_data = single_error_data(result)
    assert error_data['reason'] == 'FIELD_NOT_DEFINED'
    assert error_data['fieldName'] == 'not_defined'


def test_context_config_multiple_selectors():
    result = execute_config_graphql(
        pipeline_name='context_config_pipeline',
        env_config={
            'context': {'context_one': {'config': 'kdjfd'}, 'context_two': {'config': 123}}
        },
    )

    assert not result.errors
    assert result.data
    assert result.data['isPipelineConfigValid']['__typename'] == 'PipelineConfigValidationInvalid'
    error_data = single_error_data(result)
    assert error_data['reason'] == 'SELECTOR_FIELD_ERROR'
    assert error_data['incomingFields'] == ['context_one', 'context_two']


def test_more_complicated_works():
    result = execute_config_graphql(
        pipeline_name='more_complicated_nested_config',
        env_config={
            'solids': {
                'a_solid_with_multilayered_config': {
                    'config': {
                        'field_one': 'foo.txt',
                        'field_two': 'yup',
                        'field_three': 'mmmhmmm',
                        'nested_field': {'field_four_str': 'yaya', 'field_five_int': 234},
                    }
                }
            }
        },
    )

    assert not result.errors
    assert result.data
    valid_data = result.data['isPipelineConfigValid']
    assert valid_data['__typename'] == 'PipelineConfigValidationValid'
    assert valid_data['pipeline']['name'] == 'more_complicated_nested_config'


def test_multiple_missing_fields():

    result = execute_config_graphql(
        pipeline_name='more_complicated_nested_config',
        env_config={'solids': {'a_solid_with_multilayered_config': {'config': {}}}},
    )

    assert not result.errors
    assert result.data
    valid_data = result.data['isPipelineConfigValid']

    assert valid_data['__typename'] == 'PipelineConfigValidationInvalid'
    assert valid_data['pipeline']['name'] == 'more_complicated_nested_config'
    assert len(valid_data['errors']) == 1
    error_data = valid_data['errors'][0]
    missing_names = {field_data['name'] for field_data in error_data['fields']}
    assert missing_names == {'nested_field', 'field_one'}
    assert field_stack(error_data) == ['solids', 'a_solid_with_multilayered_config', 'config']


def test_more_complicated_multiple_errors():
    result = execute_config_graphql(
        pipeline_name='more_complicated_nested_config',
        env_config={
            'solids': {
                'a_solid_with_multilayered_config': {
                    'config': {
                        # 'field_one': 'foo.txt', # missing
                        'field_two': 'yup',
                        'field_three': 'mmmhmmm',
                        'extra_one': 'kjsdkfjd',  # extra
                        'nested_field': {
                            'field_four_str': 23434,  # runtime type
                            'field_five_int': 234,
                            'extra_two': 'ksjdkfjd',  # another extra
                        },
                    }
                }
            }
        },
    )

    assert not result.errors
    assert result.data
    valid_data = result.data['isPipelineConfigValid']

    assert valid_data['__typename'] == 'PipelineConfigValidationInvalid'
    assert valid_data['pipeline']['name'] == 'more_complicated_nested_config'
    assert len(valid_data['errors']) == 4

    missing_error_one = find_error(
        result, ['solids', 'a_solid_with_multilayered_config', 'config'], 'MISSING_REQUIRED_FIELD'
    )
    assert ['solids', 'a_solid_with_multilayered_config', 'config'] == field_stack(
        missing_error_one
    )
    assert missing_error_one['reason'] == 'MISSING_REQUIRED_FIELD'
    assert missing_error_one['field']['name'] == 'field_one'

    not_defined_one = find_error(
        result, ['solids', 'a_solid_with_multilayered_config', 'config'], 'FIELD_NOT_DEFINED'
    )
    assert ['solids', 'a_solid_with_multilayered_config', 'config'] == field_stack(not_defined_one)
    assert not_defined_one['reason'] == 'FIELD_NOT_DEFINED'
    assert not_defined_one['fieldName'] == 'extra_one'

    runtime_type_error = find_error(
        result,
        ['solids', 'a_solid_with_multilayered_config', 'config', 'nested_field', 'field_four_str'],
        'RUNTIME_TYPE_MISMATCH',
    )
    assert [
        'solids',
        'a_solid_with_multilayered_config',
        'config',
        'nested_field',
        'field_four_str',
    ] == field_stack(runtime_type_error)
    assert runtime_type_error['reason'] == 'RUNTIME_TYPE_MISMATCH'
    assert runtime_type_error['valueRep'] == '23434'
    assert runtime_type_error['type']['name'] == 'String'

    not_defined_two = find_error(
        result,
        ['solids', 'a_solid_with_multilayered_config', 'config', 'nested_field'],
        'FIELD_NOT_DEFINED',
    )

    assert ['solids', 'a_solid_with_multilayered_config', 'config', 'nested_field'] == field_stack(
        not_defined_two
    )
    assert not_defined_two['reason'] == 'FIELD_NOT_DEFINED'
    assert not_defined_two['fieldName'] == 'extra_two'

    # TODO: two more errors


def test_config_list():
    result = execute_config_graphql(
        pipeline_name='pipeline_with_list',
        env_config={'solids': {'solid_with_list': {'config': [1, 2]}}},
    )

    assert not result.errors
    assert result.data
    valid_data = result.data['isPipelineConfigValid']
    assert valid_data['__typename'] == 'PipelineConfigValidationValid'
    assert valid_data['pipeline']['name'] == 'pipeline_with_list'


def test_config_list_invalid():
    result = execute_config_graphql(
        pipeline_name='pipeline_with_list',
        env_config={'solids': {'solid_with_list': {'config': 'foo'}}},
    )

    assert not result.errors
    assert result.data
    valid_data = result.data['isPipelineConfigValid']
    assert valid_data['__typename'] == 'PipelineConfigValidationInvalid'
    assert valid_data['pipeline']['name'] == 'pipeline_with_list'
    assert len(valid_data['errors']) == 1
    assert ['solids', 'solid_with_list', 'config'] == field_stack(valid_data['errors'][0])


def test_config_list_item_invalid():
    result = execute_config_graphql(
        pipeline_name='pipeline_with_list',
        env_config={'solids': {'solid_with_list': {'config': [1, 'foo']}}},
    )

    assert not result.errors
    assert result.data
    valid_data = result.data['isPipelineConfigValid']
    assert valid_data['__typename'] == 'PipelineConfigValidationInvalid'
    assert valid_data['pipeline']['name'] == 'pipeline_with_list'
    assert len(valid_data['errors']) == 1
    entries = valid_data['errors'][0]['stack']['entries']
    assert len(entries) == 4
    assert ['solids', 'solid_with_list', 'config'] == field_stack(valid_data['errors'][0])

    last_entry = entries[3]
    assert last_entry['__typename'] == 'EvaluationStackListItemEntry'
    assert last_entry['listIndex'] == 1
