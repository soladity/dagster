// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositorySelector, PipelineRunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: RepositoryPipelinesListQuery
// ====================================================

export interface RepositoryPipelinesListQuery_repositoryOrError_PythonError {
  __typename: "PythonError";
}

export interface RepositoryPipelinesListQuery_repositoryOrError_Repository_pipelines_runs {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  status: PipelineRunStatus;
}

export interface RepositoryPipelinesListQuery_repositoryOrError_Repository_pipelines_schedules {
  __typename: "Schedule";
  id: string;
  name: string;
}

export interface RepositoryPipelinesListQuery_repositoryOrError_Repository_pipelines_sensors {
  __typename: "Sensor";
  id: string;
  name: string;
}

export interface RepositoryPipelinesListQuery_repositoryOrError_Repository_pipelines {
  __typename: "Pipeline";
  id: string;
  description: string | null;
  name: string;
  runs: RepositoryPipelinesListQuery_repositoryOrError_Repository_pipelines_runs[];
  schedules: RepositoryPipelinesListQuery_repositoryOrError_Repository_pipelines_schedules[];
  sensors: RepositoryPipelinesListQuery_repositoryOrError_Repository_pipelines_sensors[];
}

export interface RepositoryPipelinesListQuery_repositoryOrError_Repository {
  __typename: "Repository";
  id: string;
  pipelines: RepositoryPipelinesListQuery_repositoryOrError_Repository_pipelines[];
}

export interface RepositoryPipelinesListQuery_repositoryOrError_RepositoryNotFoundError {
  __typename: "RepositoryNotFoundError";
  message: string;
}

export type RepositoryPipelinesListQuery_repositoryOrError = RepositoryPipelinesListQuery_repositoryOrError_PythonError | RepositoryPipelinesListQuery_repositoryOrError_Repository | RepositoryPipelinesListQuery_repositoryOrError_RepositoryNotFoundError;

export interface RepositoryPipelinesListQuery {
  repositoryOrError: RepositoryPipelinesListQuery_repositoryOrError;
}

export interface RepositoryPipelinesListQueryVariables {
  repositorySelector: RepositorySelector;
}
