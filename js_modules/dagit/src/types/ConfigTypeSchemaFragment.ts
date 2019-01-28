

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: ConfigTypeSchemaFragment
// ====================================================

export interface ConfigTypeSchemaFragment_EnumConfigType_innerTypes_EnumConfigType_innerTypes {
  key: string;
}

export interface ConfigTypeSchemaFragment_EnumConfigType_innerTypes_EnumConfigType {
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: ConfigTypeSchemaFragment_EnumConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface ConfigTypeSchemaFragment_EnumConfigType_innerTypes_CompositeConfigType_innerTypes {
  key: string;
}

export interface ConfigTypeSchemaFragment_EnumConfigType_innerTypes_CompositeConfigType_fields_configType {
  key: string;
}

export interface ConfigTypeSchemaFragment_EnumConfigType_innerTypes_CompositeConfigType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: ConfigTypeSchemaFragment_EnumConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface ConfigTypeSchemaFragment_EnumConfigType_innerTypes_CompositeConfigType {
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: ConfigTypeSchemaFragment_EnumConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: ConfigTypeSchemaFragment_EnumConfigType_innerTypes_CompositeConfigType_fields[];
}

export type ConfigTypeSchemaFragment_EnumConfigType_innerTypes = ConfigTypeSchemaFragment_EnumConfigType_innerTypes_EnumConfigType | ConfigTypeSchemaFragment_EnumConfigType_innerTypes_CompositeConfigType;

export interface ConfigTypeSchemaFragment_EnumConfigType {
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: ConfigTypeSchemaFragment_EnumConfigType_innerTypes[];
}

export interface ConfigTypeSchemaFragment_CompositeConfigType_innerTypes_EnumConfigType_innerTypes {
  key: string;
}

export interface ConfigTypeSchemaFragment_CompositeConfigType_innerTypes_EnumConfigType {
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: ConfigTypeSchemaFragment_CompositeConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface ConfigTypeSchemaFragment_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes {
  key: string;
}

export interface ConfigTypeSchemaFragment_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType {
  key: string;
}

export interface ConfigTypeSchemaFragment_CompositeConfigType_innerTypes_CompositeConfigType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: ConfigTypeSchemaFragment_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface ConfigTypeSchemaFragment_CompositeConfigType_innerTypes_CompositeConfigType {
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: ConfigTypeSchemaFragment_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: ConfigTypeSchemaFragment_CompositeConfigType_innerTypes_CompositeConfigType_fields[];
}

export type ConfigTypeSchemaFragment_CompositeConfigType_innerTypes = ConfigTypeSchemaFragment_CompositeConfigType_innerTypes_EnumConfigType | ConfigTypeSchemaFragment_CompositeConfigType_innerTypes_CompositeConfigType;

export interface ConfigTypeSchemaFragment_CompositeConfigType_fields_configType {
  key: string;
}

export interface ConfigTypeSchemaFragment_CompositeConfigType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: ConfigTypeSchemaFragment_CompositeConfigType_fields_configType;
}

export interface ConfigTypeSchemaFragment_CompositeConfigType {
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: ConfigTypeSchemaFragment_CompositeConfigType_innerTypes[];
  fields: ConfigTypeSchemaFragment_CompositeConfigType_fields[];
}

export type ConfigTypeSchemaFragment = ConfigTypeSchemaFragment_EnumConfigType | ConfigTypeSchemaFragment_CompositeConfigType;

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