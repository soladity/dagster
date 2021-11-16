/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: PipelineTableFragment
// ====================================================

export interface PipelineTableFragment_modes {
  __typename: "Mode";
  id: string;
  name: string;
}

export interface PipelineTableFragment_runs {
  __typename: "Run";
  id: string;
  mode: string;
  runId: string;
  status: RunStatus;
}

export interface PipelineTableFragment_schedules {
  __typename: "Schedule";
  id: string;
  name: string;
  mode: string;
}

export interface PipelineTableFragment_sensors_targets {
  __typename: "Target";
  mode: string;
  pipelineName: string;
}

export interface PipelineTableFragment_sensors {
  __typename: "Sensor";
  id: string;
  name: string;
  targets: PipelineTableFragment_sensors_targets[] | null;
}

export interface PipelineTableFragment {
  __typename: "Pipeline";
  id: string;
  description: string | null;
  isJob: boolean;
  name: string;
  modes: PipelineTableFragment_modes[];
  runs: PipelineTableFragment_runs[];
  schedules: PipelineTableFragment_schedules[];
  sensors: PipelineTableFragment_sensors[];
}
