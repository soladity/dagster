

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: PipelineExecutionPipelineRunFragment
// ====================================================

export interface PipelineExecutionPipelineRunFragment_logs_nodes_LogMessageEvent {
  message: string;
  timestamp: string;
  level: LogLevel;
  __typename: "LogMessageEvent" | "PipelineStartEvent" | "PipelineSuccessEvent" | "PipelineFailureEvent" | "PipelineProcessStartEvent";
}

export interface PipelineExecutionPipelineRunFragment_logs_nodes_ExecutionStepFailureEvent_step {
  name: string;
}

export interface PipelineExecutionPipelineRunFragment_logs_nodes_ExecutionStepFailureEvent_error {
  stack: string[];
  message: string;
}

export interface PipelineExecutionPipelineRunFragment_logs_nodes_ExecutionStepFailureEvent {
  message: string;
  timestamp: string;
  level: LogLevel;
  __typename: "ExecutionStepFailureEvent";
  step: PipelineExecutionPipelineRunFragment_logs_nodes_ExecutionStepFailureEvent_step;
  error: PipelineExecutionPipelineRunFragment_logs_nodes_ExecutionStepFailureEvent_error;
}

export interface PipelineExecutionPipelineRunFragment_logs_nodes_PipelineProcessStartedEvent {
  message: string;
  timestamp: string;
  level: LogLevel;
  __typename: "PipelineProcessStartedEvent";
  processId: number;
}

export interface PipelineExecutionPipelineRunFragment_logs_nodes_ExecutionStepStartEvent_step {
  name: string;
}

export interface PipelineExecutionPipelineRunFragment_logs_nodes_ExecutionStepStartEvent {
  message: string;
  timestamp: string;
  level: LogLevel;
  __typename: "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent";
  step: PipelineExecutionPipelineRunFragment_logs_nodes_ExecutionStepStartEvent_step;
}

export type PipelineExecutionPipelineRunFragment_logs_nodes = PipelineExecutionPipelineRunFragment_logs_nodes_LogMessageEvent | PipelineExecutionPipelineRunFragment_logs_nodes_ExecutionStepFailureEvent | PipelineExecutionPipelineRunFragment_logs_nodes_PipelineProcessStartedEvent | PipelineExecutionPipelineRunFragment_logs_nodes_ExecutionStepStartEvent;

export interface PipelineExecutionPipelineRunFragment_logs {
  nodes: PipelineExecutionPipelineRunFragment_logs_nodes[];
}

export interface PipelineExecutionPipelineRunFragment_executionPlan_steps_solid {
  name: string;
}

export interface PipelineExecutionPipelineRunFragment_executionPlan_steps {
  name: string;
  solid: PipelineExecutionPipelineRunFragment_executionPlan_steps_solid;
  tag: StepTag;
}

export interface PipelineExecutionPipelineRunFragment_executionPlan {
  steps: PipelineExecutionPipelineRunFragment_executionPlan_steps[];
}

export interface PipelineExecutionPipelineRunFragment {
  runId: string;
  status: PipelineRunStatus;
  logs: PipelineExecutionPipelineRunFragment_logs;
  executionPlan: PipelineExecutionPipelineRunFragment_executionPlan;
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

//==============================================================
// START Enums and Input Objects
//==============================================================

export enum EvaluationErrorReason {
  FIELD_NOT_DEFINED = "FIELD_NOT_DEFINED",
  MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD",
  RUNTIME_TYPE_MISMATCH = "RUNTIME_TYPE_MISMATCH",
  SELECTOR_FIELD_ERROR = "SELECTOR_FIELD_ERROR",
}

export enum LogLevel {
  CRITICAL = "CRITICAL",
  DEBUG = "DEBUG",
  ERROR = "ERROR",
  INFO = "INFO",
  WARNING = "WARNING",
}

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
  INPUT_THUNK = "INPUT_THUNK",
  JOIN = "JOIN",
  MATERIALIZATION_THUNK = "MATERIALIZATION_THUNK",
  OUTPUT_EXPECTATION = "OUTPUT_EXPECTATION",
  SERIALIZE = "SERIALIZE",
  TRANSFORM = "TRANSFORM",
}

/**
 * This type represents the fields necessary to identify a
 *         pipeline or pipeline subset.
 */
export interface ExecutionSelector {
  name: string;
  solidSubset?: string[] | null;
}

//==============================================================
// END Enums and Input Objects
//==============================================================