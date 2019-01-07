

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: ConfigCodeEditorContainerQuery
// ====================================================

export interface ConfigCodeEditorContainerQuery_pipelineOrError_PythonError {
  __typename: "PythonError" | "PipelineNotFoundError";
}

export interface ConfigCodeEditorContainerQuery_pipelineOrError_Pipeline_types_RegularType {
  __typename: "RegularType";
  name: string;
}

export interface ConfigCodeEditorContainerQuery_pipelineOrError_Pipeline_types_CompositeType_fields_type {
  name: string;
}

export interface ConfigCodeEditorContainerQuery_pipelineOrError_Pipeline_types_CompositeType_fields {
  name: string;
  type: ConfigCodeEditorContainerQuery_pipelineOrError_Pipeline_types_CompositeType_fields_type;
}

export interface ConfigCodeEditorContainerQuery_pipelineOrError_Pipeline_types_CompositeType {
  __typename: "CompositeType";
  name: string;
  fields: ConfigCodeEditorContainerQuery_pipelineOrError_Pipeline_types_CompositeType_fields[];
}

export type ConfigCodeEditorContainerQuery_pipelineOrError_Pipeline_types = ConfigCodeEditorContainerQuery_pipelineOrError_Pipeline_types_RegularType | ConfigCodeEditorContainerQuery_pipelineOrError_Pipeline_types_CompositeType;

export interface ConfigCodeEditorContainerQuery_pipelineOrError_Pipeline {
  __typename: "Pipeline";
  types: ConfigCodeEditorContainerQuery_pipelineOrError_Pipeline_types[];
}

export type ConfigCodeEditorContainerQuery_pipelineOrError = ConfigCodeEditorContainerQuery_pipelineOrError_PythonError | ConfigCodeEditorContainerQuery_pipelineOrError_Pipeline;

export interface ConfigCodeEditorContainerQuery {
  pipelineOrError: ConfigCodeEditorContainerQuery_pipelineOrError;
}

export interface ConfigCodeEditorContainerQueryVariables {
  pipelineName: string;
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

//==============================================================
// START Enums and Input Objects
//==============================================================

export enum EvaluationErrorReason {
  FIELD_NOT_DEFINED = "FIELD_NOT_DEFINED",
  MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD",
  RUNTIME_TYPE_MISMATCH = "RUNTIME_TYPE_MISMATCH",
  SELECTOR_FIELD_ERROR = "SELECTOR_FIELD_ERROR",
}

export enum LogLevel {
  CRITICAL = "CRITICAL",
  DEBUG = "DEBUG",
  ERROR = "ERROR",
  INFO = "INFO",
  WARNING = "WARNING",
}

/**
 * An enumeration.
 */
export enum PipelineRunStatus {
  FAILURE = "FAILURE",
  NOT_STARTED = "NOT_STARTED",
  STARTED = "STARTED",
  SUCCESS = "SUCCESS",
}

export enum StepTag {
  INPUT_EXPECTATION = "INPUT_EXPECTATION",
  INPUT_THUNK = "INPUT_THUNK",
  JOIN = "JOIN",
  MATERIALIZATION_THUNK = "MATERIALIZATION_THUNK",
  OUTPUT_EXPECTATION = "OUTPUT_EXPECTATION",
  SERIALIZE = "SERIALIZE",
  TRANSFORM = "TRANSFORM",
}

/**
 * 
 */
export interface PipelineExecutionParams {
  pipelineName: string;
  config?: any | null;
}

//==============================================================
// END Enums and Input Objects
//==============================================================