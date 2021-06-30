// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { InstigationStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: StopSensor
// ====================================================

export interface StopSensor_stopSensor_ReadOnlyError {
  __typename: "ReadOnlyError";
}

export interface StopSensor_stopSensor_StopSensorMutationResult_instigationState {
  __typename: "InstigationState";
  id: string;
  status: InstigationStatus;
}

export interface StopSensor_stopSensor_StopSensorMutationResult {
  __typename: "StopSensorMutationResult";
  instigationState: StopSensor_stopSensor_StopSensorMutationResult_instigationState | null;
}

export interface StopSensor_stopSensor_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export type StopSensor_stopSensor = StopSensor_stopSensor_ReadOnlyError | StopSensor_stopSensor_StopSensorMutationResult | StopSensor_stopSensor_PythonError;

export interface StopSensor {
  stopSensor: StopSensor_stopSensor;
}

export interface StopSensorVariables {
  jobOriginId: string;
}
