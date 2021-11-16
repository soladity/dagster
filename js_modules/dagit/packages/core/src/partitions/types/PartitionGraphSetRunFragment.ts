/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RunStatus, StepEventStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: PartitionGraphSetRunFragment
// ====================================================

export interface PartitionGraphSetRunFragment_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface PartitionGraphSetRunFragment_stats_RunStatsSnapshot {
  __typename: "RunStatsSnapshot";
  id: string;
  startTime: number | null;
  endTime: number | null;
  materializations: number;
}

export interface PartitionGraphSetRunFragment_stats_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface PartitionGraphSetRunFragment_stats_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: PartitionGraphSetRunFragment_stats_PythonError_cause | null;
}

export type PartitionGraphSetRunFragment_stats = PartitionGraphSetRunFragment_stats_RunStatsSnapshot | PartitionGraphSetRunFragment_stats_PythonError;

export interface PartitionGraphSetRunFragment_stepStats_materializations {
  __typename: "Materialization";
}

export interface PartitionGraphSetRunFragment_stepStats_expectationResults {
  __typename: "ExpectationResult";
  success: boolean;
}

export interface PartitionGraphSetRunFragment_stepStats {
  __typename: "RunStepStats";
  stepKey: string;
  startTime: number | null;
  endTime: number | null;
  status: StepEventStatus | null;
  materializations: PartitionGraphSetRunFragment_stepStats_materializations[];
  expectationResults: PartitionGraphSetRunFragment_stepStats_expectationResults[];
}

export interface PartitionGraphSetRunFragment {
  __typename: "Run";
  id: string;
  status: RunStatus;
  tags: PartitionGraphSetRunFragment_tags[];
  runId: string;
  stats: PartitionGraphSetRunFragment_stats;
  stepStats: PartitionGraphSetRunFragment_stepStats[];
}
