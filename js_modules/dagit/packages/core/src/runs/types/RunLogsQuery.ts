// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { PipelineRunStatus, LogLevel, DagsterEventType, ErrorSource, ObjectStoreOperationType } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: RunLogsQuery
// ====================================================

export interface RunLogsQuery_pipelineRunOrError_PipelineRunNotFoundError {
  __typename: "PipelineRunNotFoundError" | "PythonError";
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepSkippedEvent {
  __typename: "ExecutionStepSkippedEvent" | "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent" | "ExecutionStepUpForRetryEvent" | "ExecutionStepRestartEvent" | "LogMessageEvent" | "PipelineStartEvent" | "PipelineEnqueuedEvent" | "PipelineDequeuedEvent" | "PipelineStartingEvent" | "PipelineCancelingEvent" | "PipelineCanceledEvent" | "PipelineSuccessEvent" | "HookCompletedEvent" | "HookSkippedEvent" | "AlertStartEvent" | "AlertSuccessEvent";
  runId: string;
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  eventType: DagsterEventType | null;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_StepMaterializationEvent_materialization_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_StepMaterializationEvent_materialization_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_StepMaterializationEvent_materialization_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_StepMaterializationEvent_materialization_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_StepMaterializationEvent_materialization_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_StepMaterializationEvent_materialization_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_StepMaterializationEvent_materialization_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_StepMaterializationEvent_materialization_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_StepMaterializationEvent_materialization_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_StepMaterializationEvent_materialization_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_StepMaterializationEvent_materialization_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_StepMaterializationEvent_materialization_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: RunLogsQuery_pipelineRunOrError_PipelineRun_events_StepMaterializationEvent_materialization_metadataEntries_EventAssetMetadataEntry_assetKey;
}

export type RunLogsQuery_pipelineRunOrError_PipelineRun_events_StepMaterializationEvent_materialization_metadataEntries = RunLogsQuery_pipelineRunOrError_PipelineRun_events_StepMaterializationEvent_materialization_metadataEntries_EventPathMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_StepMaterializationEvent_materialization_metadataEntries_EventJsonMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_StepMaterializationEvent_materialization_metadataEntries_EventUrlMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_StepMaterializationEvent_materialization_metadataEntries_EventTextMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_StepMaterializationEvent_materialization_metadataEntries_EventMarkdownMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_StepMaterializationEvent_materialization_metadataEntries_EventPythonArtifactMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_StepMaterializationEvent_materialization_metadataEntries_EventFloatMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_StepMaterializationEvent_materialization_metadataEntries_EventIntMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_StepMaterializationEvent_materialization_metadataEntries_EventPipelineRunMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_StepMaterializationEvent_materialization_metadataEntries_EventAssetMetadataEntry;

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_StepMaterializationEvent_materialization {
  __typename: "Materialization";
  assetKey: RunLogsQuery_pipelineRunOrError_PipelineRun_events_StepMaterializationEvent_materialization_assetKey | null;
  label: string;
  description: string | null;
  metadataEntries: RunLogsQuery_pipelineRunOrError_PipelineRun_events_StepMaterializationEvent_materialization_metadataEntries[];
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_StepMaterializationEvent {
  __typename: "StepMaterializationEvent";
  runId: string;
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  eventType: DagsterEventType | null;
  materialization: RunLogsQuery_pipelineRunOrError_PipelineRun_events_StepMaterializationEvent_materialization;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_PipelineFailureEvent_pipelineFailureError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_PipelineFailureEvent_pipelineFailureError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: RunLogsQuery_pipelineRunOrError_PipelineRun_events_PipelineFailureEvent_pipelineFailureError_cause | null;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_PipelineFailureEvent {
  __typename: "PipelineFailureEvent";
  runId: string;
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  eventType: DagsterEventType | null;
  pipelineFailureError: RunLogsQuery_pipelineRunOrError_PipelineRun_events_PipelineFailureEvent_pipelineFailureError | null;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepFailureEvent_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepFailureEvent_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepFailureEvent_error_cause | null;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventAssetMetadataEntry_assetKey;
}

export type RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries = RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventPathMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventJsonMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventUrlMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventTextMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventMarkdownMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventPythonArtifactMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventFloatMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventIntMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventPipelineRunMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventAssetMetadataEntry;

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepFailureEvent_failureMetadata {
  __typename: "FailureMetadata";
  metadataEntries: RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries[];
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepFailureEvent {
  __typename: "ExecutionStepFailureEvent";
  runId: string;
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  eventType: DagsterEventType | null;
  error: RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepFailureEvent_error;
  errorSource: ErrorSource | null;
  failureMetadata: RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepFailureEvent_failureMetadata | null;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepInputEvent_typeCheck_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepInputEvent_typeCheck_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepInputEvent_typeCheck_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepInputEvent_typeCheck_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepInputEvent_typeCheck_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepInputEvent_typeCheck_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepInputEvent_typeCheck_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepInputEvent_typeCheck_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepInputEvent_typeCheck_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepInputEvent_typeCheck_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepInputEvent_typeCheck_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepInputEvent_typeCheck_metadataEntries_EventAssetMetadataEntry_assetKey;
}

export type RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepInputEvent_typeCheck_metadataEntries = RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepInputEvent_typeCheck_metadataEntries_EventPathMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepInputEvent_typeCheck_metadataEntries_EventJsonMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepInputEvent_typeCheck_metadataEntries_EventUrlMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepInputEvent_typeCheck_metadataEntries_EventTextMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepInputEvent_typeCheck_metadataEntries_EventMarkdownMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepInputEvent_typeCheck_metadataEntries_EventPythonArtifactMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepInputEvent_typeCheck_metadataEntries_EventFloatMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepInputEvent_typeCheck_metadataEntries_EventIntMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepInputEvent_typeCheck_metadataEntries_EventPipelineRunMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepInputEvent_typeCheck_metadataEntries_EventAssetMetadataEntry;

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepInputEvent_typeCheck {
  __typename: "TypeCheck";
  label: string;
  description: string | null;
  success: boolean;
  metadataEntries: RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepInputEvent_typeCheck_metadataEntries[];
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepInputEvent {
  __typename: "ExecutionStepInputEvent";
  runId: string;
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  eventType: DagsterEventType | null;
  inputName: string;
  typeCheck: RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepInputEvent_typeCheck;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventAssetMetadataEntry_assetKey;
}

export type RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepOutputEvent_typeCheck_metadataEntries = RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventPathMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventJsonMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventUrlMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventTextMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventMarkdownMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventPythonArtifactMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventFloatMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventIntMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventPipelineRunMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventAssetMetadataEntry;

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepOutputEvent_typeCheck {
  __typename: "TypeCheck";
  label: string;
  description: string | null;
  success: boolean;
  metadataEntries: RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepOutputEvent_typeCheck_metadataEntries[];
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepOutputEvent_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepOutputEvent_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepOutputEvent_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepOutputEvent_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepOutputEvent_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepOutputEvent_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepOutputEvent_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepOutputEvent_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepOutputEvent_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepOutputEvent_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepOutputEvent_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepOutputEvent_metadataEntries_EventAssetMetadataEntry_assetKey;
}

export type RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepOutputEvent_metadataEntries = RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepOutputEvent_metadataEntries_EventPathMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepOutputEvent_metadataEntries_EventJsonMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepOutputEvent_metadataEntries_EventUrlMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepOutputEvent_metadataEntries_EventTextMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepOutputEvent_metadataEntries_EventMarkdownMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepOutputEvent_metadataEntries_EventPythonArtifactMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepOutputEvent_metadataEntries_EventFloatMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepOutputEvent_metadataEntries_EventIntMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepOutputEvent_metadataEntries_EventPipelineRunMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepOutputEvent_metadataEntries_EventAssetMetadataEntry;

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepOutputEvent {
  __typename: "ExecutionStepOutputEvent";
  runId: string;
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  eventType: DagsterEventType | null;
  outputName: string;
  typeCheck: RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepOutputEvent_typeCheck;
  metadataEntries: RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepOutputEvent_metadataEntries[];
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_StepExpectationResultEvent_expectationResult_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_StepExpectationResultEvent_expectationResult_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_StepExpectationResultEvent_expectationResult_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_StepExpectationResultEvent_expectationResult_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_StepExpectationResultEvent_expectationResult_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_StepExpectationResultEvent_expectationResult_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_StepExpectationResultEvent_expectationResult_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_StepExpectationResultEvent_expectationResult_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_StepExpectationResultEvent_expectationResult_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_StepExpectationResultEvent_expectationResult_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_StepExpectationResultEvent_expectationResult_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: RunLogsQuery_pipelineRunOrError_PipelineRun_events_StepExpectationResultEvent_expectationResult_metadataEntries_EventAssetMetadataEntry_assetKey;
}

export type RunLogsQuery_pipelineRunOrError_PipelineRun_events_StepExpectationResultEvent_expectationResult_metadataEntries = RunLogsQuery_pipelineRunOrError_PipelineRun_events_StepExpectationResultEvent_expectationResult_metadataEntries_EventPathMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_StepExpectationResultEvent_expectationResult_metadataEntries_EventJsonMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_StepExpectationResultEvent_expectationResult_metadataEntries_EventUrlMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_StepExpectationResultEvent_expectationResult_metadataEntries_EventTextMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_StepExpectationResultEvent_expectationResult_metadataEntries_EventMarkdownMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_StepExpectationResultEvent_expectationResult_metadataEntries_EventPythonArtifactMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_StepExpectationResultEvent_expectationResult_metadataEntries_EventFloatMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_StepExpectationResultEvent_expectationResult_metadataEntries_EventIntMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_StepExpectationResultEvent_expectationResult_metadataEntries_EventPipelineRunMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_StepExpectationResultEvent_expectationResult_metadataEntries_EventAssetMetadataEntry;

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_StepExpectationResultEvent_expectationResult {
  __typename: "ExpectationResult";
  success: boolean;
  label: string;
  description: string | null;
  metadataEntries: RunLogsQuery_pipelineRunOrError_PipelineRun_events_StepExpectationResultEvent_expectationResult_metadataEntries[];
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_StepExpectationResultEvent {
  __typename: "StepExpectationResultEvent";
  runId: string;
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  eventType: DagsterEventType | null;
  expectationResult: RunLogsQuery_pipelineRunOrError_PipelineRun_events_StepExpectationResultEvent_expectationResult;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ObjectStoreOperationEvent_operationResult_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ObjectStoreOperationEvent_operationResult_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ObjectStoreOperationEvent_operationResult_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ObjectStoreOperationEvent_operationResult_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ObjectStoreOperationEvent_operationResult_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ObjectStoreOperationEvent_operationResult_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ObjectStoreOperationEvent_operationResult_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ObjectStoreOperationEvent_operationResult_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ObjectStoreOperationEvent_operationResult_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ObjectStoreOperationEvent_operationResult_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ObjectStoreOperationEvent_operationResult_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: RunLogsQuery_pipelineRunOrError_PipelineRun_events_ObjectStoreOperationEvent_operationResult_metadataEntries_EventAssetMetadataEntry_assetKey;
}

export type RunLogsQuery_pipelineRunOrError_PipelineRun_events_ObjectStoreOperationEvent_operationResult_metadataEntries = RunLogsQuery_pipelineRunOrError_PipelineRun_events_ObjectStoreOperationEvent_operationResult_metadataEntries_EventPathMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_ObjectStoreOperationEvent_operationResult_metadataEntries_EventJsonMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_ObjectStoreOperationEvent_operationResult_metadataEntries_EventUrlMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_ObjectStoreOperationEvent_operationResult_metadataEntries_EventTextMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_ObjectStoreOperationEvent_operationResult_metadataEntries_EventMarkdownMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_ObjectStoreOperationEvent_operationResult_metadataEntries_EventPythonArtifactMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_ObjectStoreOperationEvent_operationResult_metadataEntries_EventFloatMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_ObjectStoreOperationEvent_operationResult_metadataEntries_EventIntMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_ObjectStoreOperationEvent_operationResult_metadataEntries_EventPipelineRunMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_ObjectStoreOperationEvent_operationResult_metadataEntries_EventAssetMetadataEntry;

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ObjectStoreOperationEvent_operationResult {
  __typename: "ObjectStoreOperationResult";
  op: ObjectStoreOperationType;
  metadataEntries: RunLogsQuery_pipelineRunOrError_PipelineRun_events_ObjectStoreOperationEvent_operationResult_metadataEntries[];
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_ObjectStoreOperationEvent {
  __typename: "ObjectStoreOperationEvent";
  runId: string;
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  eventType: DagsterEventType | null;
  operationResult: RunLogsQuery_pipelineRunOrError_PipelineRun_events_ObjectStoreOperationEvent_operationResult;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_HandledOutputEvent_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_HandledOutputEvent_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_HandledOutputEvent_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_HandledOutputEvent_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_HandledOutputEvent_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_HandledOutputEvent_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_HandledOutputEvent_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_HandledOutputEvent_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_HandledOutputEvent_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_HandledOutputEvent_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_HandledOutputEvent_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: RunLogsQuery_pipelineRunOrError_PipelineRun_events_HandledOutputEvent_metadataEntries_EventAssetMetadataEntry_assetKey;
}

export type RunLogsQuery_pipelineRunOrError_PipelineRun_events_HandledOutputEvent_metadataEntries = RunLogsQuery_pipelineRunOrError_PipelineRun_events_HandledOutputEvent_metadataEntries_EventPathMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_HandledOutputEvent_metadataEntries_EventJsonMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_HandledOutputEvent_metadataEntries_EventUrlMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_HandledOutputEvent_metadataEntries_EventTextMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_HandledOutputEvent_metadataEntries_EventMarkdownMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_HandledOutputEvent_metadataEntries_EventPythonArtifactMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_HandledOutputEvent_metadataEntries_EventFloatMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_HandledOutputEvent_metadataEntries_EventIntMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_HandledOutputEvent_metadataEntries_EventPipelineRunMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_HandledOutputEvent_metadataEntries_EventAssetMetadataEntry;

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_HandledOutputEvent {
  __typename: "HandledOutputEvent";
  runId: string;
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  eventType: DagsterEventType | null;
  outputName: string;
  managerKey: string;
  metadataEntries: RunLogsQuery_pipelineRunOrError_PipelineRun_events_HandledOutputEvent_metadataEntries[];
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_LoadedInputEvent {
  __typename: "LoadedInputEvent";
  runId: string;
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

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_EngineEvent_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_EngineEvent_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_EngineEvent_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_EngineEvent_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_EngineEvent_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_EngineEvent_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_EngineEvent_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_EngineEvent_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_EngineEvent_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_EngineEvent_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_EngineEvent_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: RunLogsQuery_pipelineRunOrError_PipelineRun_events_EngineEvent_metadataEntries_EventAssetMetadataEntry_assetKey;
}

export type RunLogsQuery_pipelineRunOrError_PipelineRun_events_EngineEvent_metadataEntries = RunLogsQuery_pipelineRunOrError_PipelineRun_events_EngineEvent_metadataEntries_EventPathMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_EngineEvent_metadataEntries_EventJsonMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_EngineEvent_metadataEntries_EventUrlMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_EngineEvent_metadataEntries_EventTextMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_EngineEvent_metadataEntries_EventMarkdownMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_EngineEvent_metadataEntries_EventPythonArtifactMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_EngineEvent_metadataEntries_EventFloatMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_EngineEvent_metadataEntries_EventIntMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_EngineEvent_metadataEntries_EventPipelineRunMetadataEntry | RunLogsQuery_pipelineRunOrError_PipelineRun_events_EngineEvent_metadataEntries_EventAssetMetadataEntry;

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_EngineEvent_engineError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_EngineEvent_engineError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: RunLogsQuery_pipelineRunOrError_PipelineRun_events_EngineEvent_engineError_cause | null;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_EngineEvent {
  __typename: "EngineEvent";
  runId: string;
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  eventType: DagsterEventType | null;
  metadataEntries: RunLogsQuery_pipelineRunOrError_PipelineRun_events_EngineEvent_metadataEntries[];
  engineError: RunLogsQuery_pipelineRunOrError_PipelineRun_events_EngineEvent_engineError | null;
  markerStart: string | null;
  markerEnd: string | null;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_HookErroredEvent_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_HookErroredEvent_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: RunLogsQuery_pipelineRunOrError_PipelineRun_events_HookErroredEvent_error_cause | null;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_HookErroredEvent {
  __typename: "HookErroredEvent";
  runId: string;
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  eventType: DagsterEventType | null;
  error: RunLogsQuery_pipelineRunOrError_PipelineRun_events_HookErroredEvent_error;
}

export interface RunLogsQuery_pipelineRunOrError_PipelineRun_events_LogsCapturedEvent {
  __typename: "LogsCapturedEvent";
  runId: string;
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  eventType: DagsterEventType | null;
  logKey: string;
  stepKeys: string[] | null;
  pid: number | null;
}

export type RunLogsQuery_pipelineRunOrError_PipelineRun_events = RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepSkippedEvent | RunLogsQuery_pipelineRunOrError_PipelineRun_events_StepMaterializationEvent | RunLogsQuery_pipelineRunOrError_PipelineRun_events_PipelineFailureEvent | RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepFailureEvent | RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepInputEvent | RunLogsQuery_pipelineRunOrError_PipelineRun_events_ExecutionStepOutputEvent | RunLogsQuery_pipelineRunOrError_PipelineRun_events_StepExpectationResultEvent | RunLogsQuery_pipelineRunOrError_PipelineRun_events_ObjectStoreOperationEvent | RunLogsQuery_pipelineRunOrError_PipelineRun_events_HandledOutputEvent | RunLogsQuery_pipelineRunOrError_PipelineRun_events_LoadedInputEvent | RunLogsQuery_pipelineRunOrError_PipelineRun_events_EngineEvent | RunLogsQuery_pipelineRunOrError_PipelineRun_events_HookErroredEvent | RunLogsQuery_pipelineRunOrError_PipelineRun_events_LogsCapturedEvent;

export interface RunLogsQuery_pipelineRunOrError_PipelineRun {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  status: PipelineRunStatus;
  canTerminate: boolean;
  events: RunLogsQuery_pipelineRunOrError_PipelineRun_events[];
}

export type RunLogsQuery_pipelineRunOrError = RunLogsQuery_pipelineRunOrError_PipelineRunNotFoundError | RunLogsQuery_pipelineRunOrError_PipelineRun;

export interface RunLogsQuery {
  pipelineRunOrError: RunLogsQuery_pipelineRunOrError;
}

export interface RunLogsQueryVariables {
  runId: string;
  after?: any | null;
}
