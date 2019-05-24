START_PIPELINE_EXECUTION_QUERY = '''
mutation (
    $executionParams: ExecutionParams!
    $reexecutionConfig: ReexecutionConfig
) {
    startPipelineExecution(
        executionParams: $executionParams
        reexecutionConfig: $reexecutionConfig
    ) {
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
                        ... on ExecutionStepOutputEvent {
                            step { key kind }
                            outputName
                            intermediateMaterialization {
                                path
                                description
                            }
                        }
                        ... on StepExpectationResultEvent {
                            expectationResult {
                                success
                                name
                                resultMetadataJsonString
                            }
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


START_PIPELINE_EXECUTION_SNAPSHOT_QUERY = '''
mutation (
    $executionParams: ExecutionParams!
    $reexecutionConfig: ReexecutionConfig
) {
    startPipelineExecution(
        executionParams: $executionParams
        reexecutionConfig: $reexecutionConfig
    ) {
        __typename
        ... on StartPipelineExecutionSuccess {
            run {
                pipeline { name }
                logs {
                    nodes {
                        __typename
                        ... on MessageEvent {
                            level
                        }
                        ... on ExecutionStepStartEvent {
                            step { kind }
                        }
                        ... on ExecutionStepOutputEvent {
                            step { key kind }
                            outputName
                            intermediateMaterialization {
                                description
                            }
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
        ... on InvalidStepError {
            invalidStepKey
        }
        ... on InvalidOutputError {
            stepKey
            invalidOutputName
        }
    }
}
'''

SUBSCRIPTION_QUERY = '''
subscription subscribeTest($runId: ID!) {
    pipelineRunLogs(runId: $runId) {
        __typename
        ... on PipelineRunLogsSubscriptionSuccess {
            runId,
            messages {
                __typename
                ... on ExecutionStepOutputEvent {
                    valueRepr
                }
                ... on MessageEvent {
                    message
                    step { key solidHandleID }
                    level
                }
                ... on ExecutionStepFailureEvent {
                    error {
                        message
                        stack
                    }
                    level
                }
                ... on StepMaterializationEvent {
                    materialization {
                        path
                        description
                    }
                }
                ... on StepExpectationResultEvent {
                    expectationResult {
                        success
                        name
                        message
                        resultMetadataJsonString
                    }
                }
            }
        }
        ... on PipelineRunLogsSubscriptionMissingRunIdFailure {
            missingRunId
        }
    }
}
'''
