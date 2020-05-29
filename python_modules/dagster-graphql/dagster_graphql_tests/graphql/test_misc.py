import csv
from collections import OrderedDict

from dagster_graphql.test.utils import execute_dagster_graphql, get_legacy_pipeline_selector

from dagster import (
    DependencyDefinition,
    InputDefinition,
    Materialization,
    OutputDefinition,
    PipelineDefinition,
    PythonObjectDagsterType,
    RepositoryDefinition,
    SolidDefinition,
    input_hydration_config,
    output_materialization_config,
)

from .production_query import PRODUCTION_QUERY


@input_hydration_config(str)
def df_input_schema(_context, path):
    with open(path, 'r') as fd:
        return [OrderedDict(sorted(x.items(), key=lambda x: x[0])) for x in csv.DictReader(fd)]


@output_materialization_config(str)
def df_output_schema(_context, path, value):
    with open(path, 'w') as fd:
        writer = csv.DictWriter(fd, fieldnames=value[0].keys())
        writer.writeheader()
        writer.writerows(rowdicts=value)

    return Materialization.file(path)


PoorMansDataFrame = PythonObjectDagsterType(
    python_type=list,
    name='PoorMansDataFrame',
    input_hydration_config=df_input_schema,
    output_materialization_config=df_output_schema,
)


def test_enum_query(graphql_context):
    selector = get_legacy_pipeline_selector(graphql_context, "pipeline_with_enum_config")

    ENUM_QUERY = '''
    query EnumQuery($selector: PipelineSelector!) {
      runConfigSchemaOrError(selector: $selector) {
        ... on RunConfigSchema {
          allConfigTypes {
            __typename
            key
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
    }
    '''

    result = execute_dagster_graphql(graphql_context, ENUM_QUERY, {'selector': selector,},)

    assert not result.errors
    assert result.data

    enum_type_data = None

    for td in result.data['runConfigSchemaOrError']['allConfigTypes']:
        if td['key'] == 'TestEnum':
            enum_type_data = td
            break

    assert enum_type_data
    assert enum_type_data['key'] == 'TestEnum'
    assert enum_type_data['values'] == [
        {'value': 'ENUM_VALUE_ONE', 'description': 'An enum value.'},
        {'value': 'ENUM_VALUE_TWO', 'description': 'An enum value.'},
        {'value': 'ENUM_VALUE_THREE', 'description': 'An enum value.'},
    ]


TYPE_RENDER_QUERY = '''
fragment innerInfo on ConfigType {
  key
  recursiveConfigTypes {
    key
  }
  ... on CompositeConfigType {
    fields {
      name
      configType {
        key
      }
      isOptional
    }
  }
}

query TypeRenderQuery($selector: PipelineSelector!) {
  pipelineOrError(params: $selector) {
    __typename
    ... on Pipeline {
      name
      solids {
        name
        definition {
          ... on SolidDefinition {
            configField {
              configType {
                ...innerInfo
                recursiveConfigTypes {
                  ...innerInfo
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


def test_type_rendering(graphql_context):
    selector = get_legacy_pipeline_selector(graphql_context, "more_complicated_nested_config")
    result = execute_dagster_graphql(graphql_context, TYPE_RENDER_QUERY, {'selector': selector})
    assert not result.errors
    assert result.data


def define_circular_dependency_pipeline():
    return PipelineDefinition(
        name='circular_dependency_pipeline',
        solid_defs=[
            SolidDefinition(
                name='csolid',
                input_defs=[InputDefinition('num', PoorMansDataFrame)],
                output_defs=[OutputDefinition(PoorMansDataFrame)],
                compute_fn=lambda *_args: None,
            )
        ],
        dependencies={'csolid': {'num': DependencyDefinition('csolid')}},
    )


def define_test_repository():
    return RepositoryDefinition(
        name='test', pipeline_dict={'pipeline': define_circular_dependency_pipeline}
    )


def test_pipeline_or_error_by_name(graphql_context):
    selector = get_legacy_pipeline_selector(graphql_context, "csv_hello_world_two")
    result = execute_dagster_graphql(
        graphql_context,
        '''
    query NamedPipelineQuery($selector: PipelineSelector!) {
        pipelineOrError(params: $selector) {
            ... on Pipeline {
                name
            }
        }
    }''',
        {'selector': selector},
    )

    assert not result.errors
    assert result.data
    assert result.data['pipelineOrError']['name'] == 'csv_hello_world_two'


def test_pipeline_or_error_by_name_not_found(graphql_context):
    selector = get_legacy_pipeline_selector(graphql_context, "foobar")
    result = execute_dagster_graphql(
        graphql_context,
        '''
        query NamedPipelineQuery($selector: PipelineSelector!) {
            pipelineOrError(params: $selector) {
                __typename
                ... on Pipeline {
                    name
                }
            }
        }''',
        {'selector': selector},
    )

    assert not result.errors
    assert result.data
    assert result.data['pipelineOrError']['__typename'] == 'PipelineNotFoundError'


def test_production_query(graphql_context):
    result = execute_dagster_graphql(graphql_context, PRODUCTION_QUERY)

    assert not result.errors
    assert result.data
