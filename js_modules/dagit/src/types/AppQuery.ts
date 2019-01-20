

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: AppQuery
// ====================================================

export interface AppQuery_pipelinesOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_RegularType_innerTypes_RegularType_innerTypes {
  name: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_RegularType_innerTypes_RegularType_typeAttributes {
  isNamed: boolean;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_RegularType_innerTypes_RegularType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_RegularType_innerTypes_RegularType_innerTypes[];
  typeAttributes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_RegularType_innerTypes_RegularType_typeAttributes;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_RegularType_innerTypes_CompositeType_innerTypes {
  name: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_RegularType_innerTypes_CompositeType_typeAttributes {
  isNamed: boolean;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_RegularType_innerTypes_CompositeType_fields_type {
  name: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_RegularType_innerTypes_CompositeType_fields {
  name: string;
  description: string | null;
  type: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_RegularType_innerTypes_CompositeType_fields_type;
  isOptional: boolean;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_RegularType_innerTypes_CompositeType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_RegularType_innerTypes_CompositeType_innerTypes[];
  typeAttributes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_RegularType_innerTypes_CompositeType_typeAttributes;
  fields: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_RegularType_innerTypes_CompositeType_fields[];
}

export type AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_RegularType_innerTypes = AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_RegularType_innerTypes_RegularType | AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_RegularType_innerTypes_CompositeType;

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_RegularType_typeAttributes {
  isNamed: boolean;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_RegularType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_RegularType_innerTypes[];
  typeAttributes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_RegularType_typeAttributes;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType_innerTypes_RegularType_innerTypes {
  name: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType_innerTypes_RegularType_typeAttributes {
  isNamed: boolean;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType_innerTypes_RegularType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType_innerTypes_RegularType_innerTypes[];
  typeAttributes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType_innerTypes_RegularType_typeAttributes;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType_innerTypes_CompositeType_innerTypes {
  name: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType_innerTypes_CompositeType_typeAttributes {
  isNamed: boolean;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType_innerTypes_CompositeType_fields_type {
  name: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType_innerTypes_CompositeType_fields {
  name: string;
  description: string | null;
  type: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType_innerTypes_CompositeType_fields_type;
  isOptional: boolean;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType_innerTypes_CompositeType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType_innerTypes_CompositeType_innerTypes[];
  typeAttributes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType_innerTypes_CompositeType_typeAttributes;
  fields: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType_innerTypes_CompositeType_fields[];
}

export type AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType_innerTypes = AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType_innerTypes_RegularType | AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType_innerTypes_CompositeType;

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType_typeAttributes {
  isNamed: boolean;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType_fields_type {
  name: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType_fields {
  name: string;
  description: string | null;
  type: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType_fields_type;
  isOptional: boolean;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType_innerTypes[];
  typeAttributes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType_typeAttributes;
  fields: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType_fields[];
}

export type AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type = AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_RegularType | AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType;

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config {
  type: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_RegularType_innerTypes_RegularType_innerTypes {
  name: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_RegularType_innerTypes_RegularType_typeAttributes {
  isNamed: boolean;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_RegularType_innerTypes_RegularType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_RegularType_innerTypes_RegularType_innerTypes[];
  typeAttributes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_RegularType_innerTypes_RegularType_typeAttributes;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_RegularType_innerTypes_CompositeType_innerTypes {
  name: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_RegularType_innerTypes_CompositeType_typeAttributes {
  isNamed: boolean;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_RegularType_innerTypes_CompositeType_fields_type {
  name: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_RegularType_innerTypes_CompositeType_fields {
  name: string;
  description: string | null;
  type: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_RegularType_innerTypes_CompositeType_fields_type;
  isOptional: boolean;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_RegularType_innerTypes_CompositeType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_RegularType_innerTypes_CompositeType_innerTypes[];
  typeAttributes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_RegularType_innerTypes_CompositeType_typeAttributes;
  fields: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_RegularType_innerTypes_CompositeType_fields[];
}

export type AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_RegularType_innerTypes = AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_RegularType_innerTypes_RegularType | AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_RegularType_innerTypes_CompositeType;

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_RegularType_typeAttributes {
  isNamed: boolean;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_RegularType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_RegularType_innerTypes[];
  typeAttributes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_RegularType_typeAttributes;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_innerTypes_RegularType_innerTypes {
  name: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_innerTypes_RegularType_typeAttributes {
  isNamed: boolean;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_innerTypes_RegularType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_innerTypes_RegularType_innerTypes[];
  typeAttributes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_innerTypes_RegularType_typeAttributes;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_innerTypes_CompositeType_innerTypes {
  name: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_innerTypes_CompositeType_typeAttributes {
  isNamed: boolean;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_innerTypes_CompositeType_fields_type {
  name: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_innerTypes_CompositeType_fields {
  name: string;
  description: string | null;
  type: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_innerTypes_CompositeType_fields_type;
  isOptional: boolean;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_innerTypes_CompositeType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_innerTypes_CompositeType_innerTypes[];
  typeAttributes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_innerTypes_CompositeType_typeAttributes;
  fields: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_innerTypes_CompositeType_fields[];
}

export type AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_innerTypes = AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_innerTypes_RegularType | AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_innerTypes_CompositeType;

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_typeAttributes {
  isNamed: boolean;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_fields_type {
  name: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_fields {
  name: string;
  description: string | null;
  type: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_fields_type;
  isOptional: boolean;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_CompositeType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_innerTypes[];
  typeAttributes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_typeAttributes;
  fields: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_fields[];
}

export type AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type = AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_RegularType | AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_CompositeType;

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config {
  type: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources {
  name: string;
  description: string | null;
  config: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config | null;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts {
  name: string;
  description: string | null;
  config: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config | null;
  resources: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources[];
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_metadata {
  key: string;
  value: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType_innerTypes_RegularType_innerTypes {
  name: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType_innerTypes_RegularType_typeAttributes {
  isNamed: boolean;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType_innerTypes_RegularType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType_innerTypes_RegularType_innerTypes[];
  typeAttributes: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType_innerTypes_RegularType_typeAttributes;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType_innerTypes_CompositeType_innerTypes {
  name: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType_innerTypes_CompositeType_typeAttributes {
  isNamed: boolean;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType_innerTypes_CompositeType_fields_type {
  name: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType_innerTypes_CompositeType_fields {
  name: string;
  description: string | null;
  type: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType_innerTypes_CompositeType_fields_type;
  isOptional: boolean;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType_innerTypes_CompositeType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType_innerTypes_CompositeType_innerTypes[];
  typeAttributes: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType_innerTypes_CompositeType_typeAttributes;
  fields: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType_innerTypes_CompositeType_fields[];
}

export type AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType_innerTypes = AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType_innerTypes_RegularType | AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType_innerTypes_CompositeType;

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType_typeAttributes {
  isNamed: boolean;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType_innerTypes[];
  typeAttributes: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType_typeAttributes;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_innerTypes_RegularType_innerTypes {
  name: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_innerTypes_RegularType_typeAttributes {
  isNamed: boolean;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_innerTypes_RegularType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_innerTypes_RegularType_innerTypes[];
  typeAttributes: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_innerTypes_RegularType_typeAttributes;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_innerTypes_CompositeType_innerTypes {
  name: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_innerTypes_CompositeType_typeAttributes {
  isNamed: boolean;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_innerTypes_CompositeType_fields_type {
  name: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_innerTypes_CompositeType_fields {
  name: string;
  description: string | null;
  type: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_innerTypes_CompositeType_fields_type;
  isOptional: boolean;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_innerTypes_CompositeType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_innerTypes_CompositeType_innerTypes[];
  typeAttributes: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_innerTypes_CompositeType_typeAttributes;
  fields: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_innerTypes_CompositeType_fields[];
}

export type AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_innerTypes = AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_innerTypes_RegularType | AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_innerTypes_CompositeType;

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_typeAttributes {
  isNamed: boolean;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_fields_type {
  name: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_fields {
  name: string;
  description: string | null;
  type: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_fields_type;
  isOptional: boolean;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_innerTypes[];
  typeAttributes: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_typeAttributes;
  fields: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_fields[];
}

export type AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type = AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType | AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType;

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition {
  type: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition {
  metadata: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_metadata[];
  configDefinition: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition | null;
  description: string | null;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_inputs_definition_type_typeAttributes {
  isNamed: boolean;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_inputs_definition_type {
  name: string;
  description: string | null;
  typeAttributes: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_inputs_definition_type_typeAttributes;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_inputs_definition_expectations {
  name: string;
  description: string | null;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_inputs_definition {
  name: string;
  type: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_inputs_definition_type;
  description: string | null;
  expectations: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_inputs_definition_expectations[];
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_inputs_dependsOn_definition {
  name: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_inputs_dependsOn_solid {
  name: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_inputs_dependsOn {
  definition: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_inputs_dependsOn_definition;
  solid: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_inputs_dependsOn_solid;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_inputs {
  definition: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_inputs_definition;
  dependsOn: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_inputs_dependsOn | null;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_outputs_definition_type_typeAttributes {
  isNamed: boolean;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_outputs_definition_type {
  name: string;
  description: string | null;
  typeAttributes: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_outputs_definition_type_typeAttributes;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_outputs_definition_expectations {
  name: string;
  description: string | null;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_outputs_definition {
  name: string;
  type: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_outputs_definition_type;
  expectations: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_outputs_definition_expectations[];
  description: string | null;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_outputs_dependedBy_solid {
  name: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_outputs_dependedBy {
  solid: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_outputs_dependedBy_solid;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_outputs {
  definition: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_outputs_definition;
  dependedBy: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_outputs_dependedBy[];
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids {
  name: string;
  definition: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition;
  inputs: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_inputs[];
  outputs: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_outputs[];
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_environmentType {
  name: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes {
  name: string;
  description: string | null;
  contexts: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts[];
  solids: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids[];
  environmentType: AppQuery_pipelinesOrError_PipelineConnection_nodes_environmentType;
}

export interface AppQuery_pipelinesOrError_PipelineConnection {
  __typename: "PipelineConnection";
  nodes: AppQuery_pipelinesOrError_PipelineConnection_nodes[];
}

export type AppQuery_pipelinesOrError = AppQuery_pipelinesOrError_PythonError | AppQuery_pipelinesOrError_PipelineConnection;

export interface AppQuery {
  pipelinesOrError: AppQuery_pipelinesOrError;
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