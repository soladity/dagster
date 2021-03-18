// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { AssetKeyInput, PipelineRunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: AssetQuery
// ====================================================

export interface AssetQuery_assetOrError_AssetNotFoundError {
  __typename: "AssetNotFoundError";
}

export interface AssetQuery_assetOrError_Asset_key {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetQuery_assetOrError_Asset_assetMaterializations_runOrError_PipelineRunNotFoundError {
  __typename: "PipelineRunNotFoundError" | "PythonError";
}

export interface AssetQuery_assetOrError_Asset_assetMaterializations_runOrError_PipelineRun {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  mode: string;
  status: PipelineRunStatus;
  pipelineName: string;
  pipelineSnapshotId: string | null;
}

export type AssetQuery_assetOrError_Asset_assetMaterializations_runOrError = AssetQuery_assetOrError_Asset_assetMaterializations_runOrError_PipelineRunNotFoundError | AssetQuery_assetOrError_Asset_assetMaterializations_runOrError_PipelineRun;

export interface AssetQuery_assetOrError_Asset_assetMaterializations_materializationEvent_stepStats {
  __typename: "PipelineRunStepStats";
  endTime: number | null;
  startTime: number | null;
}

export interface AssetQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface AssetQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface AssetQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface AssetQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface AssetQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface AssetQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface AssetQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number;
}

export interface AssetQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number;
}

export type AssetQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization_metadataEntries = AssetQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventPathMetadataEntry | AssetQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventJsonMetadataEntry | AssetQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventUrlMetadataEntry | AssetQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventTextMetadataEntry | AssetQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventMarkdownMetadataEntry | AssetQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventPythonArtifactMetadataEntry | AssetQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventFloatMetadataEntry | AssetQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventIntMetadataEntry;

export interface AssetQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization {
  __typename: "Materialization";
  label: string;
  description: string | null;
  metadataEntries: AssetQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization_metadataEntries[];
}

export interface AssetQuery_assetOrError_Asset_assetMaterializations_materializationEvent_assetLineage_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetQuery_assetOrError_Asset_assetMaterializations_materializationEvent_assetLineage {
  __typename: "AssetLineageInfo";
  assetKey: AssetQuery_assetOrError_Asset_assetMaterializations_materializationEvent_assetLineage_assetKey;
  partitions: string[];
}

export interface AssetQuery_assetOrError_Asset_assetMaterializations_materializationEvent {
  __typename: "StepMaterializationEvent";
  runId: string;
  timestamp: string;
  stepKey: string | null;
  stepStats: AssetQuery_assetOrError_Asset_assetMaterializations_materializationEvent_stepStats;
  materialization: AssetQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization;
  assetLineage: AssetQuery_assetOrError_Asset_assetMaterializations_materializationEvent_assetLineage[];
}

export interface AssetQuery_assetOrError_Asset_assetMaterializations {
  __typename: "AssetMaterialization";
  partition: string | null;
  runOrError: AssetQuery_assetOrError_Asset_assetMaterializations_runOrError;
  materializationEvent: AssetQuery_assetOrError_Asset_assetMaterializations_materializationEvent;
}

export interface AssetQuery_assetOrError_Asset {
  __typename: "Asset";
  key: AssetQuery_assetOrError_Asset_key;
  assetMaterializations: AssetQuery_assetOrError_Asset_assetMaterializations[];
}

export type AssetQuery_assetOrError = AssetQuery_assetOrError_AssetNotFoundError | AssetQuery_assetOrError_Asset;

export interface AssetQuery {
  assetOrError: AssetQuery_assetOrError;
}

export interface AssetQueryVariables {
  assetKey: AssetKeyInput;
}
