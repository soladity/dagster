# TODO need to enrich error handling as we enrich the ultimate union type for executePlan
QUERY_TEMPLATE = ''' '
mutation(
  $config: PipelineConfig = {config},
  $pipelineName: String = "{pipeline_name}",
  $runId: String = "{run_id}",
  $mode: String = "{mode}",
  $stepKeys: [String!] = {step_keys}
) {{
  executePlan(
    config: $config,
    mode: $mode,
    executionMetadata: {{
      runId: $runId
    }},
    pipelineName: $pipelineName,
    stepKeys: $stepKeys,
  ) {{
    __typename
    ... on PipelineConfigValidationInvalid {{
      pipeline {{
        name
      }}
      errors {{
        __typename
        message
        path
        reason
      }}
    }}
    ... on PipelineNotFoundError {{
        message
        pipelineName
    }}
    ... on ExecutePlanSuccess {{
      pipeline {{
        name
      }}
      hasFailures
      stepEvents {{
        step {{
          key
          kind
          solidHandleID
        }}
        __typename
        ... on ExecutionStepOutputEvent {{
          outputName
          valueRepr
        }}
        ... on ExecutionStepFailureEvent {{
          error {{
              message
          }}
        }}
      }}
    }}
  }}
}}
'
'''.strip(
    '\n'
)
