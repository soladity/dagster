// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { SensorSelector, InstigationType, InstigationStatus, PipelineRunStatus, InstigationTickStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: SensorRootQuery
// ====================================================

export interface SensorRootQuery_sensorOrError_SensorNotFoundError {
  __typename: "SensorNotFoundError" | "ReadOnlyError" | "PythonError";
}

export interface SensorRootQuery_sensorOrError_Sensor_nextTick {
  __typename: "FutureInstigationTick";
  timestamp: number;
}

export interface SensorRootQuery_sensorOrError_Sensor_sensorState_repositoryOrigin_repositoryLocationMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface SensorRootQuery_sensorOrError_Sensor_sensorState_repositoryOrigin {
  __typename: "RepositoryOrigin";
  id: string;
  repositoryLocationName: string;
  repositoryName: string;
  repositoryLocationMetadata: SensorRootQuery_sensorOrError_Sensor_sensorState_repositoryOrigin_repositoryLocationMetadata[];
}

export interface SensorRootQuery_sensorOrError_Sensor_sensorState_typeSpecificData_SensorData {
  __typename: "SensorData";
  lastRunKey: string | null;
}

export interface SensorRootQuery_sensorOrError_Sensor_sensorState_typeSpecificData_ScheduleData {
  __typename: "ScheduleData";
  cronSchedule: string;
}

export type SensorRootQuery_sensorOrError_Sensor_sensorState_typeSpecificData = SensorRootQuery_sensorOrError_Sensor_sensorState_typeSpecificData_SensorData | SensorRootQuery_sensorOrError_Sensor_sensorState_typeSpecificData_ScheduleData;

export interface SensorRootQuery_sensorOrError_Sensor_sensorState_runs {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  status: PipelineRunStatus;
}

export interface SensorRootQuery_sensorOrError_Sensor_sensorState_ticks_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface SensorRootQuery_sensorOrError_Sensor_sensorState_ticks_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: SensorRootQuery_sensorOrError_Sensor_sensorState_ticks_error_cause | null;
}

export interface SensorRootQuery_sensorOrError_Sensor_sensorState_ticks {
  __typename: "InstigationTick";
  id: string;
  status: InstigationTickStatus;
  timestamp: number;
  skipReason: string | null;
  runIds: string[];
  error: SensorRootQuery_sensorOrError_Sensor_sensorState_ticks_error | null;
}

export interface SensorRootQuery_sensorOrError_Sensor_sensorState {
  __typename: "InstigationState";
  id: string;
  name: string;
  instigationType: InstigationType;
  status: InstigationStatus;
  repositoryOrigin: SensorRootQuery_sensorOrError_Sensor_sensorState_repositoryOrigin;
  typeSpecificData: SensorRootQuery_sensorOrError_Sensor_sensorState_typeSpecificData | null;
  runs: SensorRootQuery_sensorOrError_Sensor_sensorState_runs[];
  ticks: SensorRootQuery_sensorOrError_Sensor_sensorState_ticks[];
  runningCount: number;
}

export interface SensorRootQuery_sensorOrError_Sensor {
  __typename: "Sensor";
  id: string;
  jobOriginId: string;
  name: string;
  pipelineName: string | null;
  solidSelection: (string | null)[] | null;
  mode: string | null;
  description: string | null;
  minIntervalSeconds: number;
  nextTick: SensorRootQuery_sensorOrError_Sensor_nextTick | null;
  sensorState: SensorRootQuery_sensorOrError_Sensor_sensorState;
}

export type SensorRootQuery_sensorOrError = SensorRootQuery_sensorOrError_SensorNotFoundError | SensorRootQuery_sensorOrError_Sensor;

export interface SensorRootQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface SensorRootQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: SensorRootQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors_cause | null;
}

export interface SensorRootQuery_instance_daemonHealth_allDaemonStatuses {
  __typename: "DaemonStatus";
  id: string;
  daemonType: string;
  required: boolean;
  healthy: boolean | null;
  lastHeartbeatErrors: SensorRootQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors[];
  lastHeartbeatTime: number | null;
}

export interface SensorRootQuery_instance_daemonHealth_daemonStatus {
  __typename: "DaemonStatus";
  id: string;
  healthy: boolean | null;
}

export interface SensorRootQuery_instance_daemonHealth {
  __typename: "DaemonHealth";
  id: string;
  allDaemonStatuses: SensorRootQuery_instance_daemonHealth_allDaemonStatuses[];
  daemonStatus: SensorRootQuery_instance_daemonHealth_daemonStatus;
}

export interface SensorRootQuery_instance {
  __typename: "Instance";
  daemonHealth: SensorRootQuery_instance_daemonHealth;
}

export interface SensorRootQuery {
  sensorOrError: SensorRootQuery_sensorOrError;
  instance: SensorRootQuery_instance;
}

export interface SensorRootQueryVariables {
  sensorSelector: SensorSelector;
}
