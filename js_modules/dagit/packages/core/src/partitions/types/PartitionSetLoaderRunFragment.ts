// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RunStatus, StepEventStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: PartitionSetLoaderRunFragment
// ====================================================

export interface PartitionSetLoaderRunFragment_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface PartitionSetLoaderRunFragment_stats_RunStatsSnapshot {
  __typename: "RunStatsSnapshot";
  id: string;
  startTime: number | null;
  endTime: number | null;
  materializations: number;
}

export interface PartitionSetLoaderRunFragment_stats_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface PartitionSetLoaderRunFragment_stats_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: PartitionSetLoaderRunFragment_stats_PythonError_cause | null;
}

export type PartitionSetLoaderRunFragment_stats = PartitionSetLoaderRunFragment_stats_RunStatsSnapshot | PartitionSetLoaderRunFragment_stats_PythonError;

export interface PartitionSetLoaderRunFragment_stepStats_materializations {
  __typename: "Materialization";
}

export interface PartitionSetLoaderRunFragment_stepStats_expectationResults {
  __typename: "ExpectationResult";
  success: boolean;
}

export interface PartitionSetLoaderRunFragment_stepStats {
  __typename: "RunStepStats";
  stepKey: string;
  startTime: number | null;
  endTime: number | null;
  status: StepEventStatus | null;
  materializations: PartitionSetLoaderRunFragment_stepStats_materializations[];
  expectationResults: PartitionSetLoaderRunFragment_stepStats_expectationResults[];
}

export interface PartitionSetLoaderRunFragment {
  __typename: "Run";
  id: string;
  status: RunStatus;
  tags: PartitionSetLoaderRunFragment_tags[];
  runId: string;
  stats: PartitionSetLoaderRunFragment_stats;
  stepStats: PartitionSetLoaderRunFragment_stepStats[];
}
