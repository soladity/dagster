// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { PipelineRunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: PipelineRunLogsSubscriptionStatusFragment
// ====================================================

export interface PipelineRunLogsSubscriptionStatusFragment {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  status: PipelineRunStatus;
  canTerminate: boolean;
}
