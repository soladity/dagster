import uuid

import pandas as pd

from graphql import graphql, parse

from dagster import (
    Any,
    Bool,
    DependencyDefinition,
    Dict,
    Enum,
    EnumValue,
    Field,
    InputDefinition,
    Int,
    List,
    Nullable,
    OutputDefinition,
    PipelineContextDefinition,
    PipelineDefinition,
    RepositoryDefinition,
    ResourceDefinition,
    SolidDefinition,
    String,
    check,
    lambda_solid,
    solid,
)

from dagster.core.types.marshal import PickleMarshallingStrategy

from dagster.utils import script_relative_path
from dagster.utils.test import get_temp_file_name

from dagster_pandas import DataFrame

from dagit.app import RepositoryContainer
from dagit.pipeline_execution_manager import SynchronousExecutionManager
from dagit.pipeline_run_storage import PipelineRunStorage
from dagit.schema import create_schema
from dagit.schema.context import DagsterGraphQLContext


PRODUCTION_QUERY = '''
query AppQuery {
  pipelinesOrError {
    ... on Error {
      message
      stack
      __typename
    }
    ... on PipelineConnection {
      nodes {
        ...PipelineFragment
        __typename
      }
    }
    __typename
  }
}

fragment PipelineFragment on Pipeline {
  name
  description
  solids {
    ...SolidFragment
    __typename
  }
  contexts {
    name
    description
    config {
      ...ConfigFieldFragment
      __typename
    }
    __typename
  }
  ...PipelineGraphFragment
  ...ConfigEditorFragment
  __typename
}

fragment SolidFragment on Solid {
  ...SolidTypeSignatureFragment
  name
  definition {
    description
    metadata {
      key
      value
      __typename
    }
    configDefinition {
      ...ConfigFieldFragment
      __typename
    }
    __typename
  }
  inputs {
    definition {
      name
      description
      type {
        ... RuntimeTypeWithTooltipFragment
        __typename
      }
      expectations {
        name
        description
        __typename
      }
      __typename
    }
    dependsOn {
      definition {
        name
        __typename
      }
      solid {
        name
        __typename
      }
      __typename
    }
    __typename
  }
  outputs {
    definition {
      name
      description
      type {
        __typename
      }
      expectations {
        name
        description
        __typename
      }
      expectations {
        name
        description
        __typename
      }
      __typename
    }
    __typename
  }
  __typename
}

fragment RuntimeTypeWithTooltipFragment on RuntimeType {
  name
  description
  __typename
}

fragment SolidTypeSignatureFragment on Solid {
  outputs {
    definition {
      name
      type {
        ... RuntimeTypeWithTooltipFragment
        __typename
      }
      __typename
    }
    __typename
  }
  inputs {
    definition {
      name
      type {
        ... RuntimeTypeWithTooltipFragment
        __typename
      }
      __typename
    }
    __typename
  }
  __typename
}

fragment ConfigFieldFragment on ConfigTypeField {
  configType {
    __typename
    name
    description
    ... on CompositeConfigType {
      fields {
        name
        description
        isOptional
        defaultValue
        configType {
          name
          description
          ... on CompositeConfigType {
            fields {
              name
              description
              isOptional
              defaultValue
              configType {
                name
                description
                __typename
              }
              __typename
            }
            __typename
          }
          __typename
        }
        __typename
      }
      __typename
    }
  }
  __typename
}

fragment PipelineGraphFragment on Pipeline {
  name
  solids {
    ...SolidNodeFragment
    __typename
  }
  __typename
}

fragment SolidNodeFragment on Solid {
  name
  inputs {
    definition {
      name
      type {
        name
        __typename
      }
      __typename
    }
    dependsOn {
      definition {
        name
        __typename
      }
      solid {
        name
        __typename
      }
      __typename
    }
    __typename
  }
  outputs {
    definition {
      name
      type {
        name
        __typename
      }
      expectations {
        name
        description
        __typename
      }
      __typename
    }
    __typename
  }
  __typename
}

fragment ConfigEditorFragment on Pipeline {
  name
  ...ConfigExplorerFragment
  __typename
}

fragment ConfigExplorerFragment on Pipeline {
  contexts {
    name
    description
    config {
      ...ConfigFieldFragment
      __typename
    }
    __typename
  }
  solids {
    definition {
      name
      description
      configDefinition {
        ...ConfigFieldFragment
        __typename
      }
      __typename
    }
    __typename
  }
  __typename
}
'''


def define_scalar_output_pipeline():
    @lambda_solid(output=OutputDefinition(String))
    def return_str():
        return 'foo'

    @lambda_solid(output=OutputDefinition(Int))
    def return_int():
        return 34234

    @lambda_solid(output=OutputDefinition(Bool))
    def return_bool():
        return True

    @lambda_solid(output=OutputDefinition(Any))
    def return_any():
        return 'dkjfkdjfe'

    return PipelineDefinition(
        name='scalar_output_pipeline', solids=[return_str, return_int, return_bool, return_any]
    )


def define_pipeline_with_enum_config():
    @solid(
        config_field=Field(
            Enum('TestEnum', [EnumValue(config_value='ENUM_VALUE', description='An enum value.')])
        )
    )
    def takes_an_enum(_info):
        pass

    return PipelineDefinition(name='pipeline_with_enum_config', solids=[takes_an_enum])


def define_repository():
    return RepositoryDefinition(
        name='test',
        pipeline_dict={
            'context_config_pipeline': define_context_config_pipeline,
            'more_complicated_config': define_more_complicated_config,
            'more_complicated_nested_config': define_more_complicated_nested_config,
            'pandas_hello_world': define_pandas_hello_world,
            'pandas_hello_world_two': define_pipeline_two,
            'pipeline_with_list': define_pipeline_with_list,
            'pandas_hello_world_df_input': define_pipeline_with_pandas_df_input,
            'no_config_pipeline': define_no_config_pipeline,
            'scalar_output_pipeline': define_scalar_output_pipeline,
            'pipeline_with_enum_config': define_pipeline_with_enum_config,
        },
    )


def define_context():
    return DagsterGraphQLContext(
        RepositoryContainer(repository=define_repository()),
        PipelineRunStorage(),
        execution_manager=SynchronousExecutionManager(),
    )


def execute_dagster_graphql(context, query, variables=None):
    return graphql(
        create_schema(),
        query,
        context=context,
        variables=variables,
        # executor=GeventObservableExecutor(),
        allow_subscriptions=True,
        return_promise=False,
    )


@lambda_solid(inputs=[InputDefinition('num', DataFrame)], output=OutputDefinition(DataFrame))
def sum_solid(num):
    sum_df = num.copy()
    sum_df['sum'] = sum_df['num1'] + sum_df['num2']
    return sum_df


@lambda_solid(inputs=[InputDefinition('sum_df', DataFrame)], output=OutputDefinition(DataFrame))
def sum_sq_solid(sum_df):
    sum_sq_df = sum_df.copy()
    sum_sq_df['sum_sq'] = sum_df['sum'] ** 2
    return sum_sq_df


PIPELINE_OR_ERROR_SUBSET_QUERY = '''
query PipelineQuery($name: String! $solidSubset: [String!])
{
    pipelineOrError(params: { name: $name, solidSubset: $solidSubset }) {
        __typename
        ... on Pipeline {
            name
            solids {
                name
            }
            configTypes {
                __typename
                name
                ... on CompositeConfigType {
                    fields {
                    name
                    configType {
                        name
                        __typename
                    }
                    __typename
                    }
                    __typename
                }
            }
        }
        ... on SolidNotFoundError {
            solidName
        }
    }
}
'''
PIPELINE_SUBSET_QUERY = '''
query PipelineQuery($name: String! $solidSubset: [String!])
{
    pipeline(params: { name: $name, solidSubset: $solidSubset }) {
        name
        solids {
            name
        }
        configTypes {
          __typename
          name
          ... on CompositeConfigType {
            fields {
              name
              configType {
                name
                __typename
              }
              __typename
            }
            __typename
          }
        }
    }
}
'''


def field_names_of(type_dict, typename):
    return {field_data['name'] for field_data in type_dict[typename]['fields']}


def types_dict_of_result(subset_result, top_key):
    return {
        type_data['name']: type_data for type_data in subset_result.data[top_key]['configTypes']
    }


def test_pandas_hello_world_pipeline_subset():
    do_test_subset(PIPELINE_SUBSET_QUERY, 'pipeline')


def test_pandas_hello_world_pipeline_or_error_subset():
    do_test_subset(PIPELINE_OR_ERROR_SUBSET_QUERY, 'pipelineOrError')


def test_pandas_hello_world_pipeline_or_error_subset_wrong_solid_name():
    result = execute_dagster_graphql(
        define_context(),
        PIPELINE_OR_ERROR_SUBSET_QUERY,
        {'name': 'pandas_hello_world', 'solidSubset': ['nope']},
    )

    if result.errors:
        raise Exception(result.errors)

    assert not result.errors
    assert result.data
    assert result.data['pipelineOrError']['__typename'] == 'SolidNotFoundError'
    assert result.data['pipelineOrError']['solidName'] == 'nope'


def test_enum_query():
    ENUM_QUERY = '''{
  pipeline(params: { name:"pipeline_with_enum_config" }){
    name
    configTypes {
      __typename
      name
      ... on EnumConfigType {
        values
        {
          value
          description
        }
      }
    }
  }
}
'''

    result = execute_dagster_graphql(define_context(), ENUM_QUERY)
    if result.errors:
        raise Exception(result.errors)

    assert not result.errors
    assert result.data

    enum_type_data = None

    for td in result.data['pipeline']['configTypes']:
        if td['name'] == 'TestEnum':
            enum_type_data = td
            break

    assert enum_type_data
    assert enum_type_data['name'] == 'TestEnum'
    assert enum_type_data['values'] == [{'value': 'ENUM_VALUE', 'description': 'An enum value.'}]


def do_test_subset(query, top_key):
    subset_result = execute_dagster_graphql(
        define_context(), query, {'name': 'pandas_hello_world', 'solidSubset': ['sum_sq_solid']}
    )

    if subset_result.errors:
        raise Exception(subset_result.errors)

    assert not subset_result.errors
    assert subset_result.data

    assert [solid_data['name'] for solid_data in subset_result.data[top_key]['solids']] == [
        'sum_sq_solid'
    ]

    subset_types_dict = types_dict_of_result(subset_result, top_key)
    assert field_names_of(subset_types_dict, 'PandasHelloWorld.SumSqSolid.Inputs') == {'sum_df'}
    assert 'PandasHelloWorld.SumSolid.Inputs' not in subset_types_dict

    full_types_dict = types_dict_of_result(
        execute_dagster_graphql(define_context(), query, {'name': 'pandas_hello_world'}), top_key
    )

    assert 'PandasHelloWorld.SumSolid.Inputs' in full_types_dict
    assert 'PandasHelloWorld.SumSqSolid.Inputs' not in full_types_dict

    assert field_names_of(full_types_dict, 'PandasHelloWorld.SumSolid.Inputs') == {'num'}


def define_pandas_hello_world():
    return PipelineDefinition(
        name='pandas_hello_world',
        solids=[sum_solid, sum_sq_solid],
        dependencies={
            'sum_solid': {},
            'sum_sq_solid': {'sum_df': DependencyDefinition(sum_solid.name)},
        },
    )


def define_pipeline_with_pandas_df_input():
    return PipelineDefinition(
        name='pandas_hello_world_df_input',
        solids=[sum_solid, sum_sq_solid],
        dependencies={'sum_sq_solid': {'sum_df': DependencyDefinition(sum_solid.name)}},
    )


def define_no_config_pipeline():
    @lambda_solid
    def return_hello():
        return 'Hello'

    return PipelineDefinition(name='no_config_pipeline', solids=[return_hello])


def define_pipeline_two():
    return PipelineDefinition(
        name='pandas_hello_world_two', solids=[sum_solid], dependencies={'sum_solid': {}}
    )


def define_pipeline_with_list():
    return PipelineDefinition(
        name='pipeline_with_list',
        solids=[
            SolidDefinition(
                name='solid_with_list',
                inputs=[],
                outputs=[],
                transform_fn=lambda *_args: None,
                config_field=Field(List(Int)),
            )
        ],
    )


def define_more_complicated_config():
    return PipelineDefinition(
        name='more_complicated_config',
        solids=[
            SolidDefinition(
                name='a_solid_with_three_field_config',
                inputs=[],
                outputs=[],
                transform_fn=lambda *_args: None,
                config_field=Field(
                    Dict(
                        {
                            'field_one': Field(String),
                            'field_two': Field(String, is_optional=True),
                            'field_three': Field(
                                String, is_optional=True, default_value='some_value'
                            ),
                        }
                    )
                ),
            )
        ],
    )


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
                ... on FieldNotDefinedConfigError {
                    fieldName
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


def pandas_hello_world_solids_config():
    return {
        'solids': {
            'sum_solid': {'inputs': {'num': {'csv': {'path': script_relative_path('num.csv')}}}}
        }
    }


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


def field_stack(error_data):
    return [
        entry['field']['name']
        for entry in error_data['stack']['entries']
        if entry['__typename'] == 'EvaluationStackPathEntry'
    ]


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


def single_error_data(result):
    assert len(result.data['isPipelineConfigValid']['errors']) == 1
    return result.data['isPipelineConfigValid']['errors'][0]


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


def define_more_complicated_nested_config():
    return PipelineDefinition(
        name='more_complicated_nested_config',
        solids=[
            SolidDefinition(
                name='a_solid_with_multilayered_config',
                inputs=[],
                outputs=[],
                transform_fn=lambda *_args: None,
                config_field=Field(
                    Dict(
                        {
                            'field_one': Field(String),
                            'field_two': Field(String, is_optional=True),
                            'field_three': Field(
                                String, is_optional=True, default_value='some_value'
                            ),
                            'nested_field': Field(
                                Dict(
                                    {
                                        'field_four_str': Field(String),
                                        'field_five_int': Field(Int),
                                        'field_six_nullable_int_list': Field(
                                            List(Nullable(Int)), is_optional=True
                                        ),
                                    }
                                )
                            ),
                        }
                    )
                ),
            )
        ],
    )


TYPE_RENDER_QUERY = '''
fragment innerInfo on ConfigType {
  name
  isList
  isNullable
  innerTypes {
    name
  }
  ... on CompositeConfigType {
    fields {
      name
      configType {
       name
      }
      isOptional
    }
  }  
}

{
  pipeline(params: { name: "more_complicated_nested_config" }) { 
    name
    solids {
      name
      definition {
        configDefinition {
          configType {
            ...innerInfo
            innerTypes {
              ...innerInfo
            }
          }
        }
      }
    }
  }
}
'''


def test_type_rendering():
    result = execute_dagster_graphql(define_context(), TYPE_RENDER_QUERY)
    assert not result.errors
    assert result.data


def define_context_config_pipeline():
    return PipelineDefinition(
        name='context_config_pipeline',
        solids=[],
        context_definitions={
            'context_one': PipelineContextDefinition(
                context_fn=lambda *args, **kwargs: None, config_field=Field(String)
            ),
            'context_two': PipelineContextDefinition(
                context_fn=lambda *args, **kwargs: None, config_field=Field(Int)
            ),
            'context_with_resources': PipelineContextDefinition(
                resources={
                    'resource_one': ResourceDefinition(
                        resource_fn=lambda *args, **kwargs: None, config_field=Field(Int)
                    ),
                    'resource_two': ResourceDefinition(resource_fn=lambda *args, **kwargs: None),
                }
            ),
        },
    )


RESOURCE_QUERY = '''
{
  pipeline(params: { name: "context_config_pipeline" }) {
    contexts {
      name
      resources {
        name
        description
        config {
          configType {
            name
            ... on CompositeConfigType {
              fields {
                name
                configType {
                  name
                }
              }
            }
          }
        }
      }
    }
  }
}
'''


def test_context_fetch_resources():
    result = execute_dagster_graphql(define_context(), RESOURCE_QUERY)

    assert not result.errors
    assert result.data
    assert result.data['pipeline']
    assert result.data['pipeline']['contexts']


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


def find_error(result, field_stack_to_find, reason):
    llist = list(find_errors(result, field_stack_to_find, reason))
    assert len(llist) == 1
    return llist[0]


def find_errors(result, field_stack_to_find, reason):
    error_datas = result.data['isPipelineConfigValid']['errors']
    for error_data in error_datas:
        if field_stack_to_find == field_stack(error_data) and error_data['reason'] == reason:
            yield error_data


def test_pipelines():
    result = execute_dagster_graphql(define_context(), '{ pipelines { nodes { name } } }')
    assert not result.errors
    assert result.data

    assert set([p['name'] for p in result.data['pipelines']['nodes']]) == set(
        [p.name for p in define_repository().get_all_pipelines()]
    )


def test_pipelines_or_error():
    result = execute_dagster_graphql(
        define_context(), '{ pipelinesOrError { ... on PipelineConnection { nodes { name } } } } '
    )
    assert not result.errors
    assert result.data

    assert set([p['name'] for p in result.data['pipelinesOrError']['nodes']]) == set(
        [p.name for p in define_repository().get_all_pipelines()]
    )


def test_pipeline_by_name():
    result = execute_dagster_graphql(
        define_context(),
        '''
    {
        pipeline(params: {name: "pandas_hello_world_two"}) {
            name
        }
    }''',
    )

    assert not result.errors
    assert result.data
    assert result.data['pipeline']['name'] == 'pandas_hello_world_two'


def test_pipeline_or_error_by_name():
    result = execute_dagster_graphql(
        define_context(),
        '''
    {
        pipelineOrError(params: { name: "pandas_hello_world_two" }) {
          ... on Pipeline {
             name
           }
        }
    }''',
    )

    assert not result.errors
    assert result.data
    assert result.data['pipelineOrError']['name'] == 'pandas_hello_world_two'


def test_smoke_test_config_type_system():
    result = execute_dagster_graphql(define_context(), ALL_CONFIG_TYPES_QUERY)

    assert not result.errors
    assert result.data


ALL_CONFIG_TYPES_QUERY = '''
fragment configTypeFragment on ConfigType {
  __typename
  key
  name
  description
  isNullable
  isList
  isSelector
  isBuiltin
  isSystemGenerated
  innerTypes {
    key
    name
    description
    ... on CompositeConfigType {
        fields {
            name
            isOptional
            description
        }
    }
    ... on WrappingConfigType {
        ofType { key }
    }
  }
  ... on EnumConfigType {
    values {
      value
      description
    }
  }
  ... on CompositeConfigType {
    fields {
      name
      isOptional
      description
    }
  }
  ... on WrappingConfigType {
    ofType { key }
  }
}

{
 	pipelines {
    nodes {
      name
      configTypes {
        ...configTypeFragment
      }
    }
  } 
}
'''

CONFIG_TYPE_QUERY = '''
query ConfigTypeQuery($pipelineName: String! $configTypeName: String!)
{
    configTypeOrError(
        pipelineName: $pipelineName
        configTypeName: $configTypeName
    ) {
        __typename
        ... on RegularConfigType {
            name
        }
        ... on CompositeConfigType {
            name
            innerTypes { key name }
            fields { name configType { key name } }
        }
        ... on EnumConfigType {
            name
        }
        ... on PipelineNotFoundError {
            pipelineName
        }
        ... on ConfigTypeNotFoundError {
            pipeline { name }
            configTypeName
        }
    }
}
'''


def test_config_type_or_error_query_success():
    result = execute_dagster_graphql(
        define_context(),
        CONFIG_TYPE_QUERY,
        {'pipelineName': 'pandas_hello_world', 'configTypeName': 'PandasHelloWorld.Environment'},
    )

    assert not result.errors
    assert result.data
    assert result.data['configTypeOrError']['__typename'] == 'CompositeConfigType'
    assert result.data['configTypeOrError']['name'] == 'PandasHelloWorld.Environment'


def test_config_type_or_error_pipeline_not_found():
    result = execute_dagster_graphql(
        define_context(),
        CONFIG_TYPE_QUERY,
        {'pipelineName': 'nope', 'configTypeName': 'PandasHelloWorld.Environment'},
    )

    assert not result.errors
    assert result.data
    assert result.data['configTypeOrError']['__typename'] == 'PipelineNotFoundError'
    assert result.data['configTypeOrError']['pipelineName'] == 'nope'


def test_config_type_or_error_type_not_found():
    result = execute_dagster_graphql(
        define_context(),
        CONFIG_TYPE_QUERY,
        {'pipelineName': 'pandas_hello_world', 'configTypeName': 'nope'},
    )

    assert not result.errors
    assert result.data
    assert result.data['configTypeOrError']['__typename'] == 'ConfigTypeNotFoundError'
    assert result.data['configTypeOrError']['pipeline']['name'] == 'pandas_hello_world'
    assert result.data['configTypeOrError']['configTypeName'] == 'nope'


def test_config_type_or_error_nested_complicated():
    result = execute_dagster_graphql(
        define_context(),
        CONFIG_TYPE_QUERY,
        {
            'pipelineName': 'more_complicated_nested_config',
            'configTypeName': (
                'MoreComplicatedNestedConfig.SolidConfig.ASolidWithMultilayeredConfig'
            ),
        },
    )

    assert not result.errors
    assert result.data
    assert result.data['configTypeOrError']['__typename'] == 'CompositeConfigType'
    assert (
        result.data['configTypeOrError']['name']
        == 'MoreComplicatedNestedConfig.SolidConfig.ASolidWithMultilayeredConfig'
    )
    assert len(result.data['configTypeOrError']['innerTypes']) == 6


RUNTIME_TYPE_QUERY = '''
query RuntimeTypeQuery($pipelineName: String! $runtimeTypeName: String!)
{
    runtimeTypeOrError(
        pipelineName: $pipelineName
        runtimeTypeName: $runtimeTypeName
    ) {
        __typename
        ... on RegularRuntimeType {
            name
        }
        ... on PipelineNotFoundError {
            pipelineName
        }
        ... on RuntimeTypeNotFoundError {
            pipeline { name }
            runtimeTypeName
        }
    }
}
'''


def test_runtime_type_query_works():
    result = execute_dagster_graphql(
        define_context(),
        RUNTIME_TYPE_QUERY,
        {'pipelineName': 'pandas_hello_world', 'runtimeTypeName': 'PandasDataFrame'},
    )

    assert not result.errors
    assert result.data
    assert result.data['runtimeTypeOrError']['__typename'] == 'RegularRuntimeType'
    assert result.data['runtimeTypeOrError']['name'] == 'PandasDataFrame'


def test_runtime_type_or_error_pipeline_not_found():
    result = execute_dagster_graphql(
        define_context(), RUNTIME_TYPE_QUERY, {'pipelineName': 'nope', 'runtimeTypeName': 'nope'}
    )

    assert not result.errors
    assert result.data
    assert result.data['runtimeTypeOrError']['__typename'] == 'PipelineNotFoundError'
    assert result.data['runtimeTypeOrError']['pipelineName'] == 'nope'


def test_runtime_type_or_error_type_not_found():
    result = execute_dagster_graphql(
        define_context(),
        RUNTIME_TYPE_QUERY,
        {'pipelineName': 'pandas_hello_world', 'runtimeTypeName': 'nope'},
    )

    assert not result.errors
    assert result.data
    assert result.data['runtimeTypeOrError']['__typename'] == 'RuntimeTypeNotFoundError'
    assert result.data['runtimeTypeOrError']['pipeline']['name'] == 'pandas_hello_world'
    assert result.data['runtimeTypeOrError']['runtimeTypeName'] == 'nope'


def test_smoke_test_runtime_type_system():
    result = execute_dagster_graphql(define_context(), ALL_RUNTIME_TYPES_QUERY)

    assert not result.errors
    assert result.data


ALL_RUNTIME_TYPES_QUERY = '''
fragment schemaTypeFragment on ConfigType {
  key
  name
  ... on CompositeConfigType {
    fields {
      name
      configType {
        key
        name
      }
    }
    innerTypes {
      key
      name
    }
  }
}
fragment runtimeTypeFragment on RuntimeType {
    key
    name
    isNullable
    isList
    description
    inputSchemaType {
        ...schemaTypeFragment
    }
    outputSchemaType {
        ...schemaTypeFragment
    }
    innerTypes {
        key
    }
    ... on WrappingRuntimeType {
        ofType {
            key
        }
    }
}

{
 	pipelines {
    nodes {
      name
      runtimeTypes {
        ...runtimeTypeFragment
      }
    }
  }
}
'''

EXECUTION_PLAN_QUERY = '''
query PipelineQuery($config: PipelineConfig, $pipeline: ExecutionSelector!) {
  executionPlan(config: $config, pipeline: $pipeline) {
    __typename
    ... on ExecutionPlan {
      pipeline { name }
      steps {
        name
        solid {
          name
        }
        kind 
        inputs {
          name
          type {
            name
          }
          dependsOn {
            name
          }
        }
        outputs {
          name
          type {
            name
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


def test_query_execution_plan_errors():
    result = execute_dagster_graphql(
        define_context(),
        EXECUTION_PLAN_QUERY,
        {'config': 2334893, 'pipeline': {'name': 'pandas_hello_world'}},
    )

    assert not result.errors
    assert result.data
    assert result.data['executionPlan']['__typename'] == 'PipelineConfigValidationInvalid'

    result = execute_dagster_graphql(
        define_context(), EXECUTION_PLAN_QUERY, {'config': 2334893, 'pipeline': {'name': 'nope'}}
    )

    assert not result.errors
    assert result.data
    assert result.data['executionPlan']['__typename'] == 'PipelineNotFoundError'
    assert result.data['executionPlan']['pipelineName'] == 'nope'


def test_query_execution_plan_snapshot(snapshot):
    result = execute_dagster_graphql(
        define_context(),
        EXECUTION_PLAN_QUERY,
        {'config': pandas_hello_world_solids_config(), 'pipeline': {'name': 'pandas_hello_world'}},
    )

    assert not result.errors
    assert result.data

    snapshot.assert_match(result.data)


def test_query_execution_plan():
    result = execute_dagster_graphql(
        define_context(),
        EXECUTION_PLAN_QUERY,
        {'config': pandas_hello_world_solids_config(), 'pipeline': {'name': 'pandas_hello_world'}},
    )

    if result.errors:
        raise Exception(result.errors[0])

    assert not result.errors
    assert result.data

    plan_data = result.data['executionPlan']

    names = get_nameset(plan_data['steps'])
    assert len(names) == 3

    assert names == set(
        ['sum_solid.num.input_thunk', 'sum_solid.transform', 'sum_sq_solid.transform']
    )

    assert result.data['executionPlan']['pipeline']['name'] == 'pandas_hello_world'

    cn = get_named_thing(plan_data['steps'], 'sum_solid.transform')

    assert cn['kind'] == 'TRANSFORM'
    assert cn['solid']['name'] == 'sum_solid'

    assert get_nameset(cn['inputs']) == set(['num'])

    sst_input = get_named_thing(cn['inputs'], 'num')
    assert sst_input['type']['name'] == 'PandasDataFrame'

    assert sst_input['dependsOn']['name'] == 'sum_solid.num.input_thunk'

    sst_output = get_named_thing(cn['outputs'], 'result')
    assert sst_output['type']['name'] == 'PandasDataFrame'


def get_nameset(llist):
    return set([item['name'] for item in llist])


def get_named_thing(llist, name):
    for cn in llist:
        if cn['name'] == name:
            return cn

    check.failed('not found')


def test_production_query():
    result = execute_dagster_graphql(define_context(), PRODUCTION_QUERY)

    if result.errors:
        raise Exception(result.errors)

    assert not result.errors
    assert result.data


ALL_TYPES_QUERY = '''
{
  pipelinesOrError {
    __typename
    ... on PipelineConnection {
      nodes {
        runtimeTypes {
          __typename
          name
        }
        configTypes {
          __typename
          name
          ... on CompositeConfigType {
            fields {
              name
              configType {
                name
                __typename
              }
              __typename
            }
            __typename
          }
        }
        __typename
      }
    }
  }
}
'''


def test_production_config_editor_query():
    result = execute_dagster_graphql(define_context(), ALL_TYPES_QUERY)
    if result.errors:
        raise Exception(result.errors)

    assert not result.errors
    assert result.data


def test_basic_start_pipeline_execution():
    result = execute_dagster_graphql(
        define_context(),
        START_PIPELINE_EXECUTION_QUERY,
        variables={
            'pipeline': {'name': 'pandas_hello_world'},
            'config': pandas_hello_world_solids_config(),
        },
    )

    if result.errors:
        raise Exception(result.errors)

    assert not result.errors
    assert result.data

    # just test existence
    assert result.data['startPipelineExecution']['__typename'] == 'StartPipelineExecutionSuccess'
    assert uuid.UUID(result.data['startPipelineExecution']['run']['runId'])
    assert result.data['startPipelineExecution']['run']['pipeline']['name'] == 'pandas_hello_world'


def test_basic_start_pipeline_execution_config_failure():
    result = execute_dagster_graphql(
        define_context(),
        START_PIPELINE_EXECUTION_QUERY,
        variables={
            'pipeline': {'name': 'pandas_hello_world'},
            'config': {'solids': {'sum_solid': {'inputs': {'num': {'csv': {'path': 384938439}}}}}},
        },
    )

    assert not result.errors
    assert result.data
    assert result.data['startPipelineExecution']['__typename'] == 'PipelineConfigValidationInvalid'


def test_basis_start_pipeline_not_found_error():
    result = execute_dagster_graphql(
        define_context(),
        START_PIPELINE_EXECUTION_QUERY,
        variables={
            'pipeline': {'name': 'sjkdfkdjkf'},
            'config': {'solids': {'sum_solid': {'inputs': {'num': {'csv': {'path': 'test.csv'}}}}}},
        },
    )

    if result.errors:
        raise Exception(result.errors)

    assert not result.errors
    assert result.data

    # just test existence
    assert result.data['startPipelineExecution']['__typename'] == 'PipelineNotFoundError'
    assert result.data['startPipelineExecution']['pipelineName'] == 'sjkdfkdjkf'


def test_basic_start_pipeline_execution_and_subscribe():
    context = define_context()

    result = execute_dagster_graphql(
        context,
        START_PIPELINE_EXECUTION_QUERY,
        variables={
            'pipeline': {'name': 'pandas_hello_world'},
            'config': {
                'solids': {
                    'sum_solid': {
                        'inputs': {'num': {'csv': {'path': script_relative_path('num.csv')}}}
                    }
                }
            },
        },
    )

    assert not result.errors
    assert result.data

    # just test existence
    assert result.data['startPipelineExecution']['__typename'] == 'StartPipelineExecutionSuccess'
    run_id = result.data['startPipelineExecution']['run']['runId']
    assert uuid.UUID(run_id)

    subscription = execute_dagster_graphql(
        context, parse(SUBSCRIPTION_QUERY), variables={'runId': run_id}
    )

    messages = []
    subscription.subscribe(messages.append)

    for m in messages:
        assert not m.errors
        assert m.data
        assert m.data['pipelineRunLogs']


SUBSCRIPTION_QUERY = '''
subscription subscribeTest($runId: ID!) {
    pipelineRunLogs(runId: $runId) {
        __typename
    }
}
'''


def test_basic_sync_execution_no_config():
    context = define_context()
    result = execute_dagster_graphql(
        context,
        START_PIPELINE_EXECUTION_QUERY,
        variables={'pipeline': {'name': 'no_config_pipeline'}, 'config': None},
    )

    assert not result.errors
    assert result.data
    logs = result.data['startPipelineExecution']['run']['logs']['nodes']
    assert isinstance(logs, list)
    assert has_event_of_type(logs, 'PipelineStartEvent')
    assert has_event_of_type(logs, 'PipelineSuccessEvent')
    assert not has_event_of_type(logs, 'PipelineFailureEvent')


def test_basic_sync_execution():
    context = define_context()
    result = execute_dagster_graphql(
        context,
        START_PIPELINE_EXECUTION_QUERY,
        variables={
            'config': pandas_hello_world_solids_config(),
            'pipeline': {'name': 'pandas_hello_world'},
        },
    )

    assert not result.errors
    assert result.data

    logs = result.data['startPipelineExecution']['run']['logs']['nodes']
    assert isinstance(logs, list)
    assert has_event_of_type(logs, 'PipelineStartEvent')
    assert has_event_of_type(logs, 'PipelineSuccessEvent')
    assert not has_event_of_type(logs, 'PipelineFailureEvent')

    assert first_event_of_type(logs, 'PipelineStartEvent')['level'] == 'INFO'


def first_event_of_type(logs, message_type):
    for log in logs:
        if log['__typename'] == message_type:
            return log
    return None


def has_event_of_type(logs, message_type):
    return first_event_of_type(logs, message_type) is not None


START_PIPELINE_EXECUTION_QUERY = '''
mutation ($pipeline: ExecutionSelector!, $config: PipelineConfig) {
    startPipelineExecution(pipeline: $pipeline, config: $config) {
        __typename
        ... on StartPipelineExecutionSuccess {
            run {
                runId
                pipeline { name }
                logs {
                    nodes {
                        __typename
                        ... on MessageEvent {
                            message
                            level
                        }
                        ... on ExecutionStepStartEvent {
                            step { kind }
                        }
                    }
                }
            }
        }
        ... on PipelineConfigValidationInvalid {
            pipeline { name }
            errors { message }
        }
        ... on PipelineNotFoundError {
            pipelineName
        }
    }
}
'''


def test_successful_start_subplan():
    marshalling = PickleMarshallingStrategy()

    with get_temp_file_name() as num_df_file:
        with get_temp_file_name() as out_df_file:
            num_df = pd.read_csv(script_relative_path('num.csv'))
            marshalling.marshal_value(num_df, num_df_file)

            result = execute_dagster_graphql(
                define_context(),
                START_EXECUTION_PLAN_QUERY,
                variables={
                    'pipelineName': 'pandas_hello_world',
                    'config': pandas_hello_world_solids_config(),
                    'stepExecutions': [
                        {
                            'stepKey': 'sum_solid.transform',
                            'marshalledInputs': [{'inputName': 'num', 'key': num_df_file}],
                            'marshalledOutputs': [{'outputName': 'result', 'key': out_df_file}],
                        }
                    ],
                    'executionMetadata': {'runId': 'kdjkfjdfd'},
                },
            )

            out_df = marshalling.unmarshal_value(out_df_file)
            assert out_df.to_dict('list') == {'num1': [1, 3], 'num2': [2, 4], 'sum': [3, 7]}
            if result.errors:
                raise Exception(result.errors)


def test_start_subplan_pipeline_not_found():
    result = execute_dagster_graphql(
        define_context(),
        START_EXECUTION_PLAN_QUERY,
        variables={
            'pipelineName': 'nope',
            'config': pandas_hello_world_solids_config(),
            'stepExecutions': [{'stepKey': 'sum_solid.transform'}],
            'executionMetadata': {'runId': 'kdjkfjdfd'},
        },
    )

    if result.errors:
        raise Exception(result.errors)

    assert result.data['startSubplanExecution']['__typename'] == 'PipelineNotFoundError'
    assert result.data['startSubplanExecution']['pipelineName'] == 'nope'


def test_start_subplan_invalid_config():
    result = execute_dagster_graphql(
        define_context(),
        START_EXECUTION_PLAN_QUERY,
        variables={
            'pipelineName': 'pandas_hello_world',
            'config': {'solids': {'sum_solid': {'inputs': {'num': {'csv': {'path': 384938439}}}}}},
            'stepExecutions': [{'stepKey': 'sum_solid.transform'}],
            'executionMetadata': {'runId': 'kdjkfjdfd'},
        },
    )

    assert not result.errors
    assert result.data
    assert result.data['startSubplanExecution']['__typename'] == 'PipelineConfigValidationInvalid'


def test_start_subplan_invalid_step_keys():
    result = execute_dagster_graphql(
        define_context(),
        START_EXECUTION_PLAN_QUERY,
        variables={
            'pipelineName': 'pandas_hello_world',
            'config': pandas_hello_world_solids_config(),
            'stepExecutions': [{'stepKey': 'nope'}],
            'executionMetadata': {'runId': 'kdjkfjdfd'},
        },
    )

    if result.errors:
        raise Exception(result.errors)

    assert result.data
    assert (
        result.data['startSubplanExecution']['__typename']
        == 'StartSubplanExecutionInvalidStepsError'
    )

    assert result.data['startSubplanExecution']['invalidStepKeys'] == ['nope']


def test_start_subplan_invalid_input_name():
    result = execute_dagster_graphql(
        define_context(),
        START_EXECUTION_PLAN_QUERY,
        variables={
            'pipelineName': 'pandas_hello_world',
            'config': pandas_hello_world_solids_config(),
            'stepExecutions': [
                {
                    'stepKey': 'sum_solid.transform',
                    'marshalledInputs': [{'inputName': 'nope', 'key': 'nope'}],
                }
            ],
            'executionMetadata': {'runId': 'kdjkfjdfd'},
        },
    )

    if result.errors:
        raise Exception(result.errors)

    assert result.data
    assert (
        result.data['startSubplanExecution']['__typename']
        == 'StartSubplanExecutionInvalidInputError'
    )

    assert result.data['startSubplanExecution']['step']['key'] == 'sum_solid.transform'
    assert result.data['startSubplanExecution']['invalidInputName'] == 'nope'


def test_start_subplan_invalid_output_name():
    result = execute_dagster_graphql(
        define_context(),
        START_EXECUTION_PLAN_QUERY,
        variables={
            'pipelineName': 'pandas_hello_world',
            'config': pandas_hello_world_solids_config(),
            'stepExecutions': [
                {
                    'stepKey': 'sum_solid.transform',
                    'marshalledOutputs': [{'outputName': 'nope', 'key': 'nope'}],
                }
            ],
            'executionMetadata': {'runId': 'kdjkfjdfd'},
        },
    )

    if result.errors:
        raise Exception(result.errors)

    assert result.data
    assert (
        result.data['startSubplanExecution']['__typename']
        == 'StartSubplanExecutionInvalidOutputError'
    )

    assert result.data['startSubplanExecution']['step']['key'] == 'sum_solid.transform'
    assert result.data['startSubplanExecution']['invalidOutputName'] == 'nope'


START_EXECUTION_PLAN_QUERY = '''
mutation (
    $pipelineName: String!
    $config: PipelineConfig
    $stepExecutions: [StepExecution!]!
    $executionMetadata: ExecutionMetadata!
) {
    startSubplanExecution(
        pipelineName: $pipelineName
        config: $config
        stepExecutions: $stepExecutions
        executionMetadata: $executionMetadata
    ) {
        __typename
        ... on StartSubplanExecutionSuccess {
            pipeline { name }
        }
        ... on PipelineNotFoundError {
            pipelineName
        }
        ... on PipelineConfigValidationInvalid {
            pipeline { name }
            errors { message }
        }
        ... on StartSubplanExecutionInvalidStepsError {
            invalidStepKeys
        }
        ... on StartSubplanExecutionInvalidInputError {
            step { key }
            invalidInputName
        }
        ... on StartSubplanExecutionInvalidOutputError {
            step { key }
            invalidOutputName
        }
    }
}

'''
