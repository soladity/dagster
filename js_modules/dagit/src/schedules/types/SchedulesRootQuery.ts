// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { ScheduleAttemptStatus, PipelineRunStatus, ScheduleStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: SchedulesRootQuery
// ====================================================

export interface SchedulesRootQuery_scheduler_SchedulerNotDefinedError {
  __typename: "SchedulerNotDefinedError";
  message: string;
}

export interface SchedulesRootQuery_scheduler_Scheduler_runningSchedules_scheduleDefinition {
  __typename: "ScheduleDefinition";
  name: string;
  executionParamsString: string;
  environmentConfigYaml: string;
  cronSchedule: string;
}

export interface SchedulesRootQuery_scheduler_Scheduler_runningSchedules_attempts {
  __typename: "ScheduleAttempt";
  time: string;
  jsonResult: string;
  status: ScheduleAttemptStatus;
}

export interface SchedulesRootQuery_scheduler_Scheduler_runningSchedules_runs_pipeline {
  __typename: "Pipeline" | "UnknownPipeline";
  name: string;
}

export interface SchedulesRootQuery_scheduler_Scheduler_runningSchedules_runs_stats {
  __typename: "PipelineRunStatsSnapshot";
  startTime: number | null;
}

export interface SchedulesRootQuery_scheduler_Scheduler_runningSchedules_runs {
  __typename: "PipelineRun";
  runId: string;
  pipeline: SchedulesRootQuery_scheduler_Scheduler_runningSchedules_runs_pipeline;
  status: PipelineRunStatus;
  stats: SchedulesRootQuery_scheduler_Scheduler_runningSchedules_runs_stats;
}

export interface SchedulesRootQuery_scheduler_Scheduler_runningSchedules {
  __typename: "RunningSchedule";
  id: string;
  scheduleDefinition: SchedulesRootQuery_scheduler_Scheduler_runningSchedules_scheduleDefinition;
  logsPath: string;
  runsCount: number;
  attempts: SchedulesRootQuery_scheduler_Scheduler_runningSchedules_attempts[];
  runs: SchedulesRootQuery_scheduler_Scheduler_runningSchedules_runs[];
  status: ScheduleStatus;
}

export interface SchedulesRootQuery_scheduler_Scheduler {
  __typename: "Scheduler";
  runningSchedules: SchedulesRootQuery_scheduler_Scheduler_runningSchedules[];
}

export interface SchedulesRootQuery_scheduler_PythonError {
  __typename: "PythonError";
  message: string;
}

export type SchedulesRootQuery_scheduler = SchedulesRootQuery_scheduler_SchedulerNotDefinedError | SchedulesRootQuery_scheduler_Scheduler | SchedulesRootQuery_scheduler_PythonError;

export interface SchedulesRootQuery {
  scheduler: SchedulesRootQuery_scheduler;
}

export interface SchedulesRootQueryVariables {
  limit: number;
}
