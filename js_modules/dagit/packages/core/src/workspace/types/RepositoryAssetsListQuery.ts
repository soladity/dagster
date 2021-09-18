// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositorySelector } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: RepositoryAssetsListQuery
// ====================================================

export interface RepositoryAssetsListQuery_repositoryOrError_PythonError {
  __typename: "PythonError";
}

export interface RepositoryAssetsListQuery_repositoryOrError_Repository_assetNodes_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface RepositoryAssetsListQuery_repositoryOrError_Repository_assetNodes {
  __typename: "AssetNode";
  id: string;
  assetKey: RepositoryAssetsListQuery_repositoryOrError_Repository_assetNodes_assetKey;
  opName: string | null;
  description: string | null;
  jobName: string | null;
}

export interface RepositoryAssetsListQuery_repositoryOrError_Repository {
  __typename: "Repository";
  id: string;
  assetNodes: RepositoryAssetsListQuery_repositoryOrError_Repository_assetNodes[];
}

export interface RepositoryAssetsListQuery_repositoryOrError_RepositoryNotFoundError {
  __typename: "RepositoryNotFoundError";
  message: string;
}

export type RepositoryAssetsListQuery_repositoryOrError = RepositoryAssetsListQuery_repositoryOrError_PythonError | RepositoryAssetsListQuery_repositoryOrError_Repository | RepositoryAssetsListQuery_repositoryOrError_RepositoryNotFoundError;

export interface RepositoryAssetsListQuery {
  repositoryOrError: RepositoryAssetsListQuery_repositoryOrError;
}

export interface RepositoryAssetsListQueryVariables {
  repositorySelector: RepositorySelector;
}
