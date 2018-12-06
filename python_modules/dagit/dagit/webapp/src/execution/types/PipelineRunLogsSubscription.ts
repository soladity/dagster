

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL subscription operation: PipelineRunLogsSubscription
// ====================================================

export interface PipelineRunLogsSubscription_pipelineRunLogs_LogMessageEvent_run {
  runId: string;
}

export interface PipelineRunLogsSubscription_pipelineRunLogs_LogMessageEvent {
  run: PipelineRunLogsSubscription_pipelineRunLogs_LogMessageEvent_run;
  __typename: "LogMessageEvent" | "PipelineStartEvent" | "PipelineSuccessEvent" | "PipelineFailureEvent";
  message: string;
  timestamp: any;
}

export interface PipelineRunLogsSubscription_pipelineRunLogs_ExecutionStepStartEvent_run {
  runId: string;
}

export interface PipelineRunLogsSubscription_pipelineRunLogs_ExecutionStepStartEvent_step {
  name: string;
}

export interface PipelineRunLogsSubscription_pipelineRunLogs_ExecutionStepStartEvent {
  run: PipelineRunLogsSubscription_pipelineRunLogs_ExecutionStepStartEvent_run;
  __typename: "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent" | "ExecutionStepFailureEvent";
  message: string;
  timestamp: any;
  step: PipelineRunLogsSubscription_pipelineRunLogs_ExecutionStepStartEvent_step;
}

export type PipelineRunLogsSubscription_pipelineRunLogs = PipelineRunLogsSubscription_pipelineRunLogs_LogMessageEvent | PipelineRunLogsSubscription_pipelineRunLogs_ExecutionStepStartEvent;

export interface PipelineRunLogsSubscription {
  pipelineRunLogs: PipelineRunLogsSubscription_pipelineRunLogs;
}

export interface PipelineRunLogsSubscriptionVariables {
  runId: string;
  after?: any | null;
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

//==============================================================
// START Enums and Input Objects
//==============================================================

/**
 * An enumeration.
 */
export enum PipelineRunStatus {
  FAILURE = "FAILURE",
  NOT_STARTED = "NOT_STARTED",
  STARTED = "STARTED",
  SUCCESS = "SUCCESS",
}

export enum StepTag {
  INPUT_EXPECTATION = "INPUT_EXPECTATION",
  JOIN = "JOIN",
  OUTPUT_EXPECTATION = "OUTPUT_EXPECTATION",
  SERIALIZE = "SERIALIZE",
  TRANSFORM = "TRANSFORM",
}

/**
 * 
 */
export interface PipelineExecutionParams {
  pipelineName: string;
  config?: any | null;
}

//==============================================================
// END Enums and Input Objects
//==============================================================