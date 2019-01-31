/* tslint:disable */
// This file was automatically generated and should not be edited.

import { PipelineRunStatus, LogLevel, StepKind } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: PipelineExecutionRootQuery
// ====================================================

export interface PipelineExecutionRootQuery_pipeline_runs_logs_nodes_LogMessageEvent {
  __typename: "LogMessageEvent" | "PipelineStartEvent" | "PipelineSuccessEvent" | "PipelineFailureEvent" | "PipelineProcessStartEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
}

export interface PipelineExecutionRootQuery_pipeline_runs_logs_nodes_ExecutionStepFailureEvent_step {
  __typename: "ExecutionStep";
  name: string;
}

export interface PipelineExecutionRootQuery_pipeline_runs_logs_nodes_ExecutionStepFailureEvent_error {
  __typename: "PythonError";
  stack: string[];
  message: string;
}

export interface PipelineExecutionRootQuery_pipeline_runs_logs_nodes_ExecutionStepFailureEvent {
  __typename: "ExecutionStepFailureEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineExecutionRootQuery_pipeline_runs_logs_nodes_ExecutionStepFailureEvent_step;
  error: PipelineExecutionRootQuery_pipeline_runs_logs_nodes_ExecutionStepFailureEvent_error;
}

export interface PipelineExecutionRootQuery_pipeline_runs_logs_nodes_PipelineProcessStartedEvent {
  __typename: "PipelineProcessStartedEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  processId: number;
}

export interface PipelineExecutionRootQuery_pipeline_runs_logs_nodes_ExecutionStepStartEvent_step {
  __typename: "ExecutionStep";
  name: string;
}

export interface PipelineExecutionRootQuery_pipeline_runs_logs_nodes_ExecutionStepStartEvent {
  __typename: "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineExecutionRootQuery_pipeline_runs_logs_nodes_ExecutionStepStartEvent_step;
}

export type PipelineExecutionRootQuery_pipeline_runs_logs_nodes = PipelineExecutionRootQuery_pipeline_runs_logs_nodes_LogMessageEvent | PipelineExecutionRootQuery_pipeline_runs_logs_nodes_ExecutionStepFailureEvent | PipelineExecutionRootQuery_pipeline_runs_logs_nodes_PipelineProcessStartedEvent | PipelineExecutionRootQuery_pipeline_runs_logs_nodes_ExecutionStepStartEvent;

export interface PipelineExecutionRootQuery_pipeline_runs_logs_pageInfo {
  __typename: "PageInfo";
  lastCursor: any | null;
}

export interface PipelineExecutionRootQuery_pipeline_runs_logs {
  __typename: "LogMessageConnection";
  nodes: PipelineExecutionRootQuery_pipeline_runs_logs_nodes[];
  pageInfo: PipelineExecutionRootQuery_pipeline_runs_logs_pageInfo;
}

export interface PipelineExecutionRootQuery_pipeline_runs_executionPlan_steps_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineExecutionRootQuery_pipeline_runs_executionPlan_steps {
  __typename: "ExecutionStep";
  name: string;
  solid: PipelineExecutionRootQuery_pipeline_runs_executionPlan_steps_solid;
  kind: StepKind;
}

export interface PipelineExecutionRootQuery_pipeline_runs_executionPlan {
  __typename: "ExecutionPlan";
  steps: PipelineExecutionRootQuery_pipeline_runs_executionPlan_steps[];
}

export interface PipelineExecutionRootQuery_pipeline_runs {
  __typename: "PipelineRun";
  runId: string;
  status: PipelineRunStatus;
  logs: PipelineExecutionRootQuery_pipeline_runs_logs;
  executionPlan: PipelineExecutionRootQuery_pipeline_runs_executionPlan;
}

export interface PipelineExecutionRootQuery_pipeline_environmentType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionRootQuery_pipeline_configTypes_RegularConfigType {
  __typename: "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  isSelector: boolean;
}

export interface PipelineExecutionRootQuery_pipeline_configTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface PipelineExecutionRootQuery_pipeline_configTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  name: string | null;
  isSelector: boolean;
  values: PipelineExecutionRootQuery_pipeline_configTypes_EnumConfigType_values[];
}

export interface PipelineExecutionRootQuery_pipeline_configTypes_CompositeConfigType_fields_configType_EnumConfigType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  isList: boolean;
  isNullable: boolean;
}

export interface PipelineExecutionRootQuery_pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_ofType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionRootQuery_pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType {
  __typename: "ListConfigType";
  key: string;
  name: string | null;
  isList: boolean;
  isNullable: boolean;
  ofType: PipelineExecutionRootQuery_pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_ofType;
}

export type PipelineExecutionRootQuery_pipeline_configTypes_CompositeConfigType_fields_configType = PipelineExecutionRootQuery_pipeline_configTypes_CompositeConfigType_fields_configType_EnumConfigType | PipelineExecutionRootQuery_pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType;

export interface PipelineExecutionRootQuery_pipeline_configTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  isOptional: boolean;
  configType: PipelineExecutionRootQuery_pipeline_configTypes_CompositeConfigType_fields_configType;
}

export interface PipelineExecutionRootQuery_pipeline_configTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  isSelector: boolean;
  fields: PipelineExecutionRootQuery_pipeline_configTypes_CompositeConfigType_fields[];
}

export type PipelineExecutionRootQuery_pipeline_configTypes = PipelineExecutionRootQuery_pipeline_configTypes_RegularConfigType | PipelineExecutionRootQuery_pipeline_configTypes_EnumConfigType | PipelineExecutionRootQuery_pipeline_configTypes_CompositeConfigType;

export interface PipelineExecutionRootQuery_pipeline {
  __typename: "Pipeline";
  name: string;
  runs: PipelineExecutionRootQuery_pipeline_runs[];
  environmentType: PipelineExecutionRootQuery_pipeline_environmentType;
  configTypes: PipelineExecutionRootQuery_pipeline_configTypes[];
}

export interface PipelineExecutionRootQuery {
  pipeline: PipelineExecutionRootQuery_pipeline;
}

export interface PipelineExecutionRootQueryVariables {
  name: string;
  solidSubset?: string[] | null;
}
