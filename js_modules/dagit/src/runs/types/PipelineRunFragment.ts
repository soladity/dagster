// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { PipelineRunStatus, LogLevel, StepKind } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: PipelineRunFragment
// ====================================================

export interface PipelineRunFragment_pipeline_solids {
  __typename: "Solid";
  name: string;
}

export interface PipelineRunFragment_pipeline {
  __typename: "Pipeline";
  name: string;
  solids: PipelineRunFragment_pipeline_solids[];
}

export interface PipelineRunFragment_logs_pageInfo {
  __typename: "PageInfo";
  lastCursor: any | null;
}

export interface PipelineRunFragment_logs_nodes_LogMessageEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface PipelineRunFragment_logs_nodes_LogMessageEvent {
  __typename: "LogMessageEvent" | "PipelineStartEvent" | "PipelineSuccessEvent" | "PipelineFailureEvent" | "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent" | "ExecutionStepOutputEvent" | "ExecutionStepSkippedEvent" | "PipelineProcessStartEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunFragment_logs_nodes_LogMessageEvent_step | null;
}

export interface PipelineRunFragment_logs_nodes_PipelineInitFailureEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface PipelineRunFragment_logs_nodes_PipelineInitFailureEvent_error {
  __typename: "PythonError";
  stack: string[];
  message: string;
}

export interface PipelineRunFragment_logs_nodes_PipelineInitFailureEvent {
  __typename: "PipelineInitFailureEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunFragment_logs_nodes_PipelineInitFailureEvent_step | null;
  error: PipelineRunFragment_logs_nodes_PipelineInitFailureEvent_error;
}

export interface PipelineRunFragment_logs_nodes_ExecutionStepFailureEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface PipelineRunFragment_logs_nodes_ExecutionStepFailureEvent_error {
  __typename: "PythonError";
  stack: string[];
  message: string;
}

export interface PipelineRunFragment_logs_nodes_ExecutionStepFailureEvent {
  __typename: "ExecutionStepFailureEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunFragment_logs_nodes_ExecutionStepFailureEvent_step | null;
  error: PipelineRunFragment_logs_nodes_ExecutionStepFailureEvent_error;
}

export interface PipelineRunFragment_logs_nodes_PipelineProcessStartedEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface PipelineRunFragment_logs_nodes_PipelineProcessStartedEvent {
  __typename: "PipelineProcessStartedEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunFragment_logs_nodes_PipelineProcessStartedEvent_step | null;
  processId: number;
}

export interface PipelineRunFragment_logs_nodes_StepMaterializationEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface PipelineRunFragment_logs_nodes_StepMaterializationEvent_materialization {
  __typename: "Materialization";
  path: string | null;
  description: string | null;
}

export interface PipelineRunFragment_logs_nodes_StepMaterializationEvent {
  __typename: "StepMaterializationEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunFragment_logs_nodes_StepMaterializationEvent_step | null;
  materialization: PipelineRunFragment_logs_nodes_StepMaterializationEvent_materialization;
}

export interface PipelineRunFragment_logs_nodes_StepExpectationResultEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface PipelineRunFragment_logs_nodes_StepExpectationResultEvent_expectationResult {
  __typename: "ExpectationResult";
  success: boolean;
  name: string | null;
  resultMetadataJsonString: string | null;
}

export interface PipelineRunFragment_logs_nodes_StepExpectationResultEvent {
  __typename: "StepExpectationResultEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunFragment_logs_nodes_StepExpectationResultEvent_step | null;
  expectationResult: PipelineRunFragment_logs_nodes_StepExpectationResultEvent_expectationResult;
}

export type PipelineRunFragment_logs_nodes = PipelineRunFragment_logs_nodes_LogMessageEvent | PipelineRunFragment_logs_nodes_PipelineInitFailureEvent | PipelineRunFragment_logs_nodes_ExecutionStepFailureEvent | PipelineRunFragment_logs_nodes_PipelineProcessStartedEvent | PipelineRunFragment_logs_nodes_StepMaterializationEvent | PipelineRunFragment_logs_nodes_StepExpectationResultEvent;

export interface PipelineRunFragment_logs {
  __typename: "LogMessageConnection";
  pageInfo: PipelineRunFragment_logs_pageInfo;
  nodes: PipelineRunFragment_logs_nodes[];
}

export interface PipelineRunFragment_executionPlan_steps_inputs_dependsOn_outputs_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  name: string | null;
}

export interface PipelineRunFragment_executionPlan_steps_inputs_dependsOn_outputs {
  __typename: "ExecutionStepOutput";
  name: string;
  type: PipelineRunFragment_executionPlan_steps_inputs_dependsOn_outputs_type;
}

export interface PipelineRunFragment_executionPlan_steps_inputs_dependsOn {
  __typename: "ExecutionStep";
  key: string;
  outputs: PipelineRunFragment_executionPlan_steps_inputs_dependsOn_outputs[];
}

export interface PipelineRunFragment_executionPlan_steps_inputs {
  __typename: "ExecutionStepInput";
  dependsOn: PipelineRunFragment_executionPlan_steps_inputs_dependsOn;
}

export interface PipelineRunFragment_executionPlan_steps {
  __typename: "ExecutionStep";
  key: string;
  kind: StepKind;
  inputs: PipelineRunFragment_executionPlan_steps_inputs[];
}

export interface PipelineRunFragment_executionPlan {
  __typename: "ExecutionPlan";
  steps: PipelineRunFragment_executionPlan_steps[];
  artifactsPersisted: boolean;
}

export interface PipelineRunFragment {
  __typename: "PipelineRun";
  runId: string;
  status: PipelineRunStatus;
  pipeline: PipelineRunFragment_pipeline;
  logs: PipelineRunFragment_logs;
  environmentConfigYaml: string;
  mode: string;
  executionPlan: PipelineRunFragment_executionPlan;
}
