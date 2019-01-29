import json
import subprocess

from dagster.utils import script_relative_path


def test_basic_introspection():
    query = '{ __schema { types { name } } }'

    repo_path = script_relative_path('./repository.yml')

    result = subprocess.check_output(['dagit', '-q', query, '-y', repo_path])

    result_data = json.loads(result.decode())
    assert result_data['data']


def test_basic_pipelines():
    query = '{ pipelines { nodes { name } } }'

    repo_path = script_relative_path('./repository.yml')

    result = subprocess.check_output(['dagit', '-q', query, '-y', repo_path])

    result_data = json.loads(result.decode())
    assert result_data['data']


def test_basic_variables():
    query = 'query FooBar($pipelineName: String!){ pipeline(params:{name: $pipelineName}){ name} }'
    variables = '{"pipelineName": "pandas_hello_world"}'
    repo_path = script_relative_path('./repository.yml')

    result = subprocess.check_output(['dagit', '-q', query, '-v', variables, '-y', repo_path])
    result_data = json.loads(result.decode())
    assert result_data['data']


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


def test_start_execution():
    variables = '''
 {{
     "pipeline" : {{
         "name" : "pandas_hello_world"
    }},
    "config" : {{
        "solids" : {{
            "sum_solid" : {{
                "inputs" : {{
                    "num" : {{
                        "csv" : {{
                            "path" : "{path}"
                        }}
                    }}
                }}
            }}
        }}
    }}
 }}'''.format(
        path=script_relative_path('./num.csv')
    )

    repo_path = script_relative_path('./repository.yml')

    result = subprocess.check_output(
        ['dagit', '-q', START_PIPELINE_EXECUTION_QUERY, '-v', variables, '-y', repo_path]
    )
    result_data = json.loads(result.decode())
    print(result_data)
    assert result_data['data']
