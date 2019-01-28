

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: PipelineExecutionPipelineFragment
// ====================================================

export interface PipelineExecutionPipelineFragment_environmentType {
  key: string;
}

export interface PipelineExecutionPipelineFragment_configTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  isSelector: boolean;
}

export interface PipelineExecutionPipelineFragment_configTypes_CompositeConfigType_fields_configType_EnumConfigType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  isList: boolean;
  isNullable: boolean;
}

export interface PipelineExecutionPipelineFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType_ofType {
  key: string;
}

export interface PipelineExecutionPipelineFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType {
  __typename: "ListConfigType";
  key: string;
  name: string | null;
  isList: boolean;
  isNullable: boolean;
  ofType: PipelineExecutionPipelineFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType_ofType;
}

export type PipelineExecutionPipelineFragment_configTypes_CompositeConfigType_fields_configType = PipelineExecutionPipelineFragment_configTypes_CompositeConfigType_fields_configType_EnumConfigType | PipelineExecutionPipelineFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType;

export interface PipelineExecutionPipelineFragment_configTypes_CompositeConfigType_fields {
  name: string;
  isOptional: boolean;
  configType: PipelineExecutionPipelineFragment_configTypes_CompositeConfigType_fields_configType;
}

export interface PipelineExecutionPipelineFragment_configTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  isSelector: boolean;
  fields: PipelineExecutionPipelineFragment_configTypes_CompositeConfigType_fields[];
}

export type PipelineExecutionPipelineFragment_configTypes = PipelineExecutionPipelineFragment_configTypes_EnumConfigType | PipelineExecutionPipelineFragment_configTypes_CompositeConfigType;

export interface PipelineExecutionPipelineFragment {
  name: string;
  environmentType: PipelineExecutionPipelineFragment_environmentType;
  configTypes: PipelineExecutionPipelineFragment_configTypes[];
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

export enum StepKind {
  INPUT_EXPECTATION = "INPUT_EXPECTATION",
  INPUT_THUNK = "INPUT_THUNK",
  JOIN = "JOIN",
  MATERIALIZATION_THUNK = "MATERIALIZATION_THUNK",
  OUTPUT_EXPECTATION = "OUTPUT_EXPECTATION",
  SERIALIZE = "SERIALIZE",
  TRANSFORM = "TRANSFORM",
}

/**
 * This type represents the fields necessary to identify a
 *         pipeline or pipeline subset.
 */
export interface ExecutionSelector {
  name: string;
  solidSubset?: string[] | null;
}

//==============================================================
// END Enums and Input Objects
//==============================================================