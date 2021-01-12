// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { ObjectStoreOperationType } from "./globalTypes";

// ====================================================
// GraphQL fragment: RunMetadataProviderMessageFragment
// ====================================================

export interface RunMetadataProviderMessageFragment_ExecutionStepFailureEvent {
  __typename: "ExecutionStepFailureEvent" | "ExecutionStepInputEvent" | "ExecutionStepOutputEvent" | "ExecutionStepSkippedEvent" | "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent" | "ExecutionStepUpForRetryEvent" | "ExecutionStepRestartEvent" | "LogMessageEvent" | "PipelineFailureEvent" | "PipelineInitFailureEvent" | "PipelineStartEvent" | "PipelineEnqueuedEvent" | "PipelineDequeuedEvent" | "PipelineStartingEvent" | "PipelineCancelingEvent" | "PipelineCanceledEvent" | "PipelineSuccessEvent" | "HandledOutputEvent" | "LoadedInputEvent" | "StepExpectationResultEvent" | "StepMaterializationEvent" | "HookCompletedEvent" | "HookSkippedEvent" | "HookErroredEvent";
  message: string;
  timestamp: string;
  stepKey: string | null;
}

export interface RunMetadataProviderMessageFragment_EngineEvent {
  __typename: "EngineEvent";
  message: string;
  timestamp: string;
  stepKey: string | null;
  markerStart: string | null;
  markerEnd: string | null;
}

export interface RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number;
}

export interface RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number;
}

export type RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries = RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventPathMetadataEntry | RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventJsonMetadataEntry | RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventUrlMetadataEntry | RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventTextMetadataEntry | RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventMarkdownMetadataEntry | RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventPythonArtifactMetadataEntry | RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventFloatMetadataEntry | RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventIntMetadataEntry;

export interface RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult {
  __typename: "ObjectStoreOperationResult";
  op: ObjectStoreOperationType;
  metadataEntries: RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries[];
}

export interface RunMetadataProviderMessageFragment_ObjectStoreOperationEvent {
  __typename: "ObjectStoreOperationEvent";
  message: string;
  timestamp: string;
  stepKey: string | null;
  operationResult: RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult;
}

export type RunMetadataProviderMessageFragment = RunMetadataProviderMessageFragment_ExecutionStepFailureEvent | RunMetadataProviderMessageFragment_EngineEvent | RunMetadataProviderMessageFragment_ObjectStoreOperationEvent;
