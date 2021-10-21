// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: RunDetailsTestQuery
// ====================================================

export interface RunDetailsTestQuery_pipelineRunOrError_RunNotFoundError {
  __typename: "RunNotFoundError" | "PythonError";
}

export interface RunDetailsTestQuery_pipelineRunOrError_Run_stats_PythonError {
  __typename: "PythonError";
}

export interface RunDetailsTestQuery_pipelineRunOrError_Run_stats_RunStatsSnapshot {
  __typename: "RunStatsSnapshot";
  id: string;
  endTime: number | null;
  startTime: number | null;
}

export type RunDetailsTestQuery_pipelineRunOrError_Run_stats = RunDetailsTestQuery_pipelineRunOrError_Run_stats_PythonError | RunDetailsTestQuery_pipelineRunOrError_Run_stats_RunStatsSnapshot;

export interface RunDetailsTestQuery_pipelineRunOrError_Run {
  __typename: "Run";
  id: string;
  stats: RunDetailsTestQuery_pipelineRunOrError_Run_stats;
  status: RunStatus;
}

export type RunDetailsTestQuery_pipelineRunOrError = RunDetailsTestQuery_pipelineRunOrError_RunNotFoundError | RunDetailsTestQuery_pipelineRunOrError_Run;

export interface RunDetailsTestQuery {
  pipelineRunOrError: RunDetailsTestQuery_pipelineRunOrError;
}
