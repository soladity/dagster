// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { InstigationTickStatus } from "../../types/globalTypes";

// ====================================================
// GraphQL fragment: TickTagFragment
// ====================================================

export interface TickTagFragment_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface TickTagFragment_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: TickTagFragment_error_cause | null;
}

export interface TickTagFragment {
  __typename: "InstigationTick";
  id: string;
  status: InstigationTickStatus;
  timestamp: number;
  skipReason: string | null;
  runIds: string[];
  error: TickTagFragment_error | null;
}
