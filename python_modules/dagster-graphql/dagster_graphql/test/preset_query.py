from .utils import execute_dagster_graphql, get_legacy_pipeline_selector

PRESETS_QUERY = '''
query PresetsQuery($selector: PipelineSelector!) {
  pipelineOrError(params: $selector) {
    ... on Pipeline {
      name
      presets {
        __typename
        name
        solidSubset
        environmentConfigYaml
        mode
      }
    }
  }
}
'''


def execute_preset_query(pipeline_name, context):
    selector = get_legacy_pipeline_selector(context, pipeline_name)
    return execute_dagster_graphql(context, PRESETS_QUERY, variables={'selector': selector})
