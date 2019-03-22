/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { PipelineRunStatus, LogLevel } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: PipelineRunLogsUpdateFragment
// ====================================================

export interface PipelineRunLogsUpdateFragment_logs_nodes_LogMessageEvent_step {
  __typename: "ExecutionStep";
  name: string;
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_LogMessageEvent {
  __typename: "LogMessageEvent" | "PipelineStartEvent" | "PipelineSuccessEvent" | "PipelineFailureEvent" | "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent" | "ExecutionStepOutputEvent" | "PipelineProcessStartEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunLogsUpdateFragment_logs_nodes_LogMessageEvent_step | null;
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepFailureEvent_step {
  __typename: "ExecutionStep";
  name: string;
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepFailureEvent_error {
  __typename: "PythonError";
  stack: string[];
  message: string;
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepFailureEvent {
  __typename: "ExecutionStepFailureEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepFailureEvent_step | null;
  error: PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepFailureEvent_error;
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_PipelineProcessStartedEvent_step {
  __typename: "ExecutionStep";
  name: string;
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_PipelineProcessStartedEvent {
  __typename: "PipelineProcessStartedEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunLogsUpdateFragment_logs_nodes_PipelineProcessStartedEvent_step | null;
  processId: number;
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_StepMaterializationEvent_step {
  __typename: "ExecutionStep";
  name: string;
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_StepMaterializationEvent {
  __typename: "StepMaterializationEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunLogsUpdateFragment_logs_nodes_StepMaterializationEvent_step | null;
  fileLocation: string;
  fileName: string;
}

export type PipelineRunLogsUpdateFragment_logs_nodes = PipelineRunLogsUpdateFragment_logs_nodes_LogMessageEvent | PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepFailureEvent | PipelineRunLogsUpdateFragment_logs_nodes_PipelineProcessStartedEvent | PipelineRunLogsUpdateFragment_logs_nodes_StepMaterializationEvent;

export interface PipelineRunLogsUpdateFragment_logs {
  __typename: "LogMessageConnection";
  nodes: PipelineRunLogsUpdateFragment_logs_nodes[];
}

export interface PipelineRunLogsUpdateFragment {
  __typename: "PipelineRun";
  runId: string;
  status: PipelineRunStatus;
  logs: PipelineRunLogsUpdateFragment_logs;
}
