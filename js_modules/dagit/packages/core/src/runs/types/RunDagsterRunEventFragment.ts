// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { LogLevel, DagsterEventType, ErrorSource, ObjectStoreOperationType } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: RunDagsterRunEventFragment
// ====================================================

export interface RunDagsterRunEventFragment_ExecutionStepSkippedEvent {
  __typename: "ExecutionStepSkippedEvent" | "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent" | "ExecutionStepUpForRetryEvent" | "ExecutionStepRestartEvent" | "LogMessageEvent" | "RunStartEvent" | "RunEnqueuedEvent" | "RunDequeuedEvent" | "RunStartingEvent" | "RunCancelingEvent" | "RunCanceledEvent" | "RunSuccessEvent" | "HookCompletedEvent" | "HookSkippedEvent" | "AlertStartEvent" | "AlertSuccessEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  eventType: DagsterEventType | null;
}

export interface RunDagsterRunEventFragment_StepMaterializationEvent_materialization_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface RunDagsterRunEventFragment_StepMaterializationEvent_materialization_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface RunDagsterRunEventFragment_StepMaterializationEvent_materialization_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface RunDagsterRunEventFragment_StepMaterializationEvent_materialization_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface RunDagsterRunEventFragment_StepMaterializationEvent_materialization_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface RunDagsterRunEventFragment_StepMaterializationEvent_materialization_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface RunDagsterRunEventFragment_StepMaterializationEvent_materialization_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface RunDagsterRunEventFragment_StepMaterializationEvent_materialization_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface RunDagsterRunEventFragment_StepMaterializationEvent_materialization_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface RunDagsterRunEventFragment_StepMaterializationEvent_materialization_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface RunDagsterRunEventFragment_StepMaterializationEvent_materialization_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface RunDagsterRunEventFragment_StepMaterializationEvent_materialization_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: RunDagsterRunEventFragment_StepMaterializationEvent_materialization_metadataEntries_EventAssetMetadataEntry_assetKey;
}

export type RunDagsterRunEventFragment_StepMaterializationEvent_materialization_metadataEntries = RunDagsterRunEventFragment_StepMaterializationEvent_materialization_metadataEntries_EventPathMetadataEntry | RunDagsterRunEventFragment_StepMaterializationEvent_materialization_metadataEntries_EventJsonMetadataEntry | RunDagsterRunEventFragment_StepMaterializationEvent_materialization_metadataEntries_EventUrlMetadataEntry | RunDagsterRunEventFragment_StepMaterializationEvent_materialization_metadataEntries_EventTextMetadataEntry | RunDagsterRunEventFragment_StepMaterializationEvent_materialization_metadataEntries_EventMarkdownMetadataEntry | RunDagsterRunEventFragment_StepMaterializationEvent_materialization_metadataEntries_EventPythonArtifactMetadataEntry | RunDagsterRunEventFragment_StepMaterializationEvent_materialization_metadataEntries_EventFloatMetadataEntry | RunDagsterRunEventFragment_StepMaterializationEvent_materialization_metadataEntries_EventIntMetadataEntry | RunDagsterRunEventFragment_StepMaterializationEvent_materialization_metadataEntries_EventPipelineRunMetadataEntry | RunDagsterRunEventFragment_StepMaterializationEvent_materialization_metadataEntries_EventAssetMetadataEntry;

export interface RunDagsterRunEventFragment_StepMaterializationEvent_materialization {
  __typename: "Materialization";
  assetKey: RunDagsterRunEventFragment_StepMaterializationEvent_materialization_assetKey | null;
  label: string;
  description: string | null;
  metadataEntries: RunDagsterRunEventFragment_StepMaterializationEvent_materialization_metadataEntries[];
}

export interface RunDagsterRunEventFragment_StepMaterializationEvent {
  __typename: "StepMaterializationEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  eventType: DagsterEventType | null;
  materialization: RunDagsterRunEventFragment_StepMaterializationEvent_materialization;
}

export interface RunDagsterRunEventFragment_RunFailureEvent_pipelineFailureError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface RunDagsterRunEventFragment_RunFailureEvent_pipelineFailureError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: RunDagsterRunEventFragment_RunFailureEvent_pipelineFailureError_cause | null;
}

export interface RunDagsterRunEventFragment_RunFailureEvent {
  __typename: "RunFailureEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  eventType: DagsterEventType | null;
  pipelineFailureError: RunDagsterRunEventFragment_RunFailureEvent_pipelineFailureError | null;
}

export interface RunDagsterRunEventFragment_ExecutionStepFailureEvent_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface RunDagsterRunEventFragment_ExecutionStepFailureEvent_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: RunDagsterRunEventFragment_ExecutionStepFailureEvent_error_cause | null;
}

export interface RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventAssetMetadataEntry_assetKey;
}

export type RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries = RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventPathMetadataEntry | RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventJsonMetadataEntry | RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventUrlMetadataEntry | RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventTextMetadataEntry | RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventMarkdownMetadataEntry | RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventPythonArtifactMetadataEntry | RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventFloatMetadataEntry | RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventIntMetadataEntry | RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventPipelineRunMetadataEntry | RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventAssetMetadataEntry;

export interface RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata {
  __typename: "FailureMetadata";
  metadataEntries: RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries[];
}

export interface RunDagsterRunEventFragment_ExecutionStepFailureEvent {
  __typename: "ExecutionStepFailureEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  eventType: DagsterEventType | null;
  error: RunDagsterRunEventFragment_ExecutionStepFailureEvent_error | null;
  errorSource: ErrorSource | null;
  failureMetadata: RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata | null;
}

export interface RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventAssetMetadataEntry_assetKey;
}

export type RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries = RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventPathMetadataEntry | RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventJsonMetadataEntry | RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventUrlMetadataEntry | RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventTextMetadataEntry | RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventMarkdownMetadataEntry | RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventPythonArtifactMetadataEntry | RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventFloatMetadataEntry | RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventIntMetadataEntry | RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventPipelineRunMetadataEntry | RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventAssetMetadataEntry;

export interface RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck {
  __typename: "TypeCheck";
  label: string;
  description: string | null;
  success: boolean;
  metadataEntries: RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries[];
}

export interface RunDagsterRunEventFragment_ExecutionStepInputEvent {
  __typename: "ExecutionStepInputEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  eventType: DagsterEventType | null;
  inputName: string;
  typeCheck: RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck;
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventAssetMetadataEntry_assetKey;
}

export type RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries = RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventPathMetadataEntry | RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventJsonMetadataEntry | RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventUrlMetadataEntry | RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventTextMetadataEntry | RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventMarkdownMetadataEntry | RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventPythonArtifactMetadataEntry | RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventFloatMetadataEntry | RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventIntMetadataEntry | RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventPipelineRunMetadataEntry | RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventAssetMetadataEntry;

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck {
  __typename: "TypeCheck";
  label: string;
  description: string | null;
  success: boolean;
  metadataEntries: RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries[];
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_EventAssetMetadataEntry_assetKey;
}

export type RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries = RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_EventPathMetadataEntry | RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_EventJsonMetadataEntry | RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_EventUrlMetadataEntry | RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_EventTextMetadataEntry | RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_EventMarkdownMetadataEntry | RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_EventPythonArtifactMetadataEntry | RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_EventFloatMetadataEntry | RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_EventIntMetadataEntry | RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_EventPipelineRunMetadataEntry | RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_EventAssetMetadataEntry;

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent {
  __typename: "ExecutionStepOutputEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  eventType: DagsterEventType | null;
  outputName: string;
  typeCheck: RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck;
  metadataEntries: RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries[];
}

export interface RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventAssetMetadataEntry_assetKey;
}

export type RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries = RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventPathMetadataEntry | RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventJsonMetadataEntry | RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventUrlMetadataEntry | RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventTextMetadataEntry | RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventMarkdownMetadataEntry | RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventPythonArtifactMetadataEntry | RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventFloatMetadataEntry | RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventIntMetadataEntry | RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventPipelineRunMetadataEntry | RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventAssetMetadataEntry;

export interface RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult {
  __typename: "ExpectationResult";
  success: boolean;
  label: string;
  description: string | null;
  metadataEntries: RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries[];
}

export interface RunDagsterRunEventFragment_StepExpectationResultEvent {
  __typename: "StepExpectationResultEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  eventType: DagsterEventType | null;
  expectationResult: RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult;
}

export interface RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventAssetMetadataEntry_assetKey;
}

export type RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries = RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventPathMetadataEntry | RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventJsonMetadataEntry | RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventUrlMetadataEntry | RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventTextMetadataEntry | RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventMarkdownMetadataEntry | RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventPythonArtifactMetadataEntry | RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventFloatMetadataEntry | RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventIntMetadataEntry | RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventPipelineRunMetadataEntry | RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventAssetMetadataEntry;

export interface RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult {
  __typename: "ObjectStoreOperationResult";
  op: ObjectStoreOperationType;
  metadataEntries: RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries[];
}

export interface RunDagsterRunEventFragment_ObjectStoreOperationEvent {
  __typename: "ObjectStoreOperationEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  eventType: DagsterEventType | null;
  operationResult: RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult;
}

export interface RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_EventAssetMetadataEntry_assetKey;
}

export type RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries = RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_EventPathMetadataEntry | RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_EventJsonMetadataEntry | RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_EventUrlMetadataEntry | RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_EventTextMetadataEntry | RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_EventMarkdownMetadataEntry | RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_EventPythonArtifactMetadataEntry | RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_EventFloatMetadataEntry | RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_EventIntMetadataEntry | RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_EventPipelineRunMetadataEntry | RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_EventAssetMetadataEntry;

export interface RunDagsterRunEventFragment_HandledOutputEvent {
  __typename: "HandledOutputEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  eventType: DagsterEventType | null;
  outputName: string;
  managerKey: string;
  metadataEntries: RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries[];
}

export interface RunDagsterRunEventFragment_LoadedInputEvent {
  __typename: "LoadedInputEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  eventType: DagsterEventType | null;
  inputName: string;
  managerKey: string;
  upstreamOutputName: string | null;
  upstreamStepKey: string | null;
}

export interface RunDagsterRunEventFragment_EngineEvent_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface RunDagsterRunEventFragment_EngineEvent_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface RunDagsterRunEventFragment_EngineEvent_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface RunDagsterRunEventFragment_EngineEvent_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface RunDagsterRunEventFragment_EngineEvent_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface RunDagsterRunEventFragment_EngineEvent_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface RunDagsterRunEventFragment_EngineEvent_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface RunDagsterRunEventFragment_EngineEvent_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface RunDagsterRunEventFragment_EngineEvent_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface RunDagsterRunEventFragment_EngineEvent_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface RunDagsterRunEventFragment_EngineEvent_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: RunDagsterRunEventFragment_EngineEvent_metadataEntries_EventAssetMetadataEntry_assetKey;
}

export type RunDagsterRunEventFragment_EngineEvent_metadataEntries = RunDagsterRunEventFragment_EngineEvent_metadataEntries_EventPathMetadataEntry | RunDagsterRunEventFragment_EngineEvent_metadataEntries_EventJsonMetadataEntry | RunDagsterRunEventFragment_EngineEvent_metadataEntries_EventUrlMetadataEntry | RunDagsterRunEventFragment_EngineEvent_metadataEntries_EventTextMetadataEntry | RunDagsterRunEventFragment_EngineEvent_metadataEntries_EventMarkdownMetadataEntry | RunDagsterRunEventFragment_EngineEvent_metadataEntries_EventPythonArtifactMetadataEntry | RunDagsterRunEventFragment_EngineEvent_metadataEntries_EventFloatMetadataEntry | RunDagsterRunEventFragment_EngineEvent_metadataEntries_EventIntMetadataEntry | RunDagsterRunEventFragment_EngineEvent_metadataEntries_EventPipelineRunMetadataEntry | RunDagsterRunEventFragment_EngineEvent_metadataEntries_EventAssetMetadataEntry;

export interface RunDagsterRunEventFragment_EngineEvent_engineError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface RunDagsterRunEventFragment_EngineEvent_engineError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: RunDagsterRunEventFragment_EngineEvent_engineError_cause | null;
}

export interface RunDagsterRunEventFragment_EngineEvent {
  __typename: "EngineEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  eventType: DagsterEventType | null;
  metadataEntries: RunDagsterRunEventFragment_EngineEvent_metadataEntries[];
  engineError: RunDagsterRunEventFragment_EngineEvent_engineError | null;
  markerStart: string | null;
  markerEnd: string | null;
}

export interface RunDagsterRunEventFragment_HookErroredEvent_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface RunDagsterRunEventFragment_HookErroredEvent_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: RunDagsterRunEventFragment_HookErroredEvent_error_cause | null;
}

export interface RunDagsterRunEventFragment_HookErroredEvent {
  __typename: "HookErroredEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  eventType: DagsterEventType | null;
  error: RunDagsterRunEventFragment_HookErroredEvent_error | null;
}

export interface RunDagsterRunEventFragment_LogsCapturedEvent {
  __typename: "LogsCapturedEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  eventType: DagsterEventType | null;
  logKey: string;
  stepKeys: string[] | null;
  pid: number | null;
}

export type RunDagsterRunEventFragment = RunDagsterRunEventFragment_ExecutionStepSkippedEvent | RunDagsterRunEventFragment_StepMaterializationEvent | RunDagsterRunEventFragment_RunFailureEvent | RunDagsterRunEventFragment_ExecutionStepFailureEvent | RunDagsterRunEventFragment_ExecutionStepInputEvent | RunDagsterRunEventFragment_ExecutionStepOutputEvent | RunDagsterRunEventFragment_StepExpectationResultEvent | RunDagsterRunEventFragment_ObjectStoreOperationEvent | RunDagsterRunEventFragment_HandledOutputEvent | RunDagsterRunEventFragment_LoadedInputEvent | RunDagsterRunEventFragment_EngineEvent | RunDagsterRunEventFragment_HookErroredEvent | RunDagsterRunEventFragment_LogsCapturedEvent;
