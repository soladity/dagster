/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RunsFilter, RunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: PartitionRunListForStepQuery
// ====================================================

export interface PartitionRunListForStepQuery_pipelineRunsOrError_Runs_results_repositoryOrigin {
  __typename: "RepositoryOrigin";
  id: string;
  repositoryName: string;
  repositoryLocationName: string;
}

export interface PartitionRunListForStepQuery_pipelineRunsOrError_Runs_results_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface PartitionRunListForStepQuery_pipelineRunsOrError_Runs_results_stats_RunStatsSnapshot {
  __typename: "RunStatsSnapshot";
  id: string;
  enqueuedTime: number | null;
  launchTime: number | null;
  startTime: number | null;
  endTime: number | null;
}

export interface PartitionRunListForStepQuery_pipelineRunsOrError_Runs_results_stats_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface PartitionRunListForStepQuery_pipelineRunsOrError_Runs_results_stats_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: PartitionRunListForStepQuery_pipelineRunsOrError_Runs_results_stats_PythonError_cause | null;
}

export type PartitionRunListForStepQuery_pipelineRunsOrError_Runs_results_stats = PartitionRunListForStepQuery_pipelineRunsOrError_Runs_results_stats_RunStatsSnapshot | PartitionRunListForStepQuery_pipelineRunsOrError_Runs_results_stats_PythonError;

export interface PartitionRunListForStepQuery_pipelineRunsOrError_Runs_results {
  __typename: "Run";
  id: string;
  runId: string;
  status: RunStatus;
  stepKeysToExecute: string[] | null;
  canTerminate: boolean;
  mode: string;
  rootRunId: string | null;
  parentRunId: string | null;
  pipelineSnapshotId: string | null;
  pipelineName: string;
  repositoryOrigin: PartitionRunListForStepQuery_pipelineRunsOrError_Runs_results_repositoryOrigin | null;
  solidSelection: string[] | null;
  tags: PartitionRunListForStepQuery_pipelineRunsOrError_Runs_results_tags[];
  stats: PartitionRunListForStepQuery_pipelineRunsOrError_Runs_results_stats;
}

export interface PartitionRunListForStepQuery_pipelineRunsOrError_Runs {
  __typename: "Runs";
  results: PartitionRunListForStepQuery_pipelineRunsOrError_Runs_results[];
}

export interface PartitionRunListForStepQuery_pipelineRunsOrError_InvalidPipelineRunsFilterError {
  __typename: "InvalidPipelineRunsFilterError";
  message: string;
}

export interface PartitionRunListForStepQuery_pipelineRunsOrError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface PartitionRunListForStepQuery_pipelineRunsOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: PartitionRunListForStepQuery_pipelineRunsOrError_PythonError_cause | null;
}

export type PartitionRunListForStepQuery_pipelineRunsOrError = PartitionRunListForStepQuery_pipelineRunsOrError_Runs | PartitionRunListForStepQuery_pipelineRunsOrError_InvalidPipelineRunsFilterError | PartitionRunListForStepQuery_pipelineRunsOrError_PythonError;

export interface PartitionRunListForStepQuery {
  pipelineRunsOrError: PartitionRunListForStepQuery_pipelineRunsOrError;
}

export interface PartitionRunListForStepQueryVariables {
  filter: RunsFilter;
}
