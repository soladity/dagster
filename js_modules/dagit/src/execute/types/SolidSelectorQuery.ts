// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: SolidSelectorQuery
// ====================================================

export interface SolidSelectorQuery_pipeline_solids_definition_CompositeSolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface SolidSelectorQuery_pipeline_solids_definition_CompositeSolidDefinition {
  __typename: "CompositeSolidDefinition";
  metadata: SolidSelectorQuery_pipeline_solids_definition_CompositeSolidDefinition_metadata[];
}

export interface SolidSelectorQuery_pipeline_solids_definition_SolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface SolidSelectorQuery_pipeline_solids_definition_SolidDefinition_configDefinition_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  name: string | null;
  description: string | null;
}

export interface SolidSelectorQuery_pipeline_solids_definition_SolidDefinition_configDefinition {
  __typename: "ConfigTypeField";
  configType: SolidSelectorQuery_pipeline_solids_definition_SolidDefinition_configDefinition_configType;
}

export interface SolidSelectorQuery_pipeline_solids_definition_SolidDefinition {
  __typename: "SolidDefinition";
  metadata: SolidSelectorQuery_pipeline_solids_definition_SolidDefinition_metadata[];
  configDefinition: SolidSelectorQuery_pipeline_solids_definition_SolidDefinition_configDefinition | null;
}

export type SolidSelectorQuery_pipeline_solids_definition = SolidSelectorQuery_pipeline_solids_definition_CompositeSolidDefinition | SolidSelectorQuery_pipeline_solids_definition_SolidDefinition;

export interface SolidSelectorQuery_pipeline_solids_inputs_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
  isNothing: boolean;
}

export interface SolidSelectorQuery_pipeline_solids_inputs_definition {
  __typename: "InputDefinition";
  name: string;
  type: SolidSelectorQuery_pipeline_solids_inputs_definition_type;
}

export interface SolidSelectorQuery_pipeline_solids_inputs_dependsOn_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
}

export interface SolidSelectorQuery_pipeline_solids_inputs_dependsOn_definition {
  __typename: "OutputDefinition";
  name: string;
  type: SolidSelectorQuery_pipeline_solids_inputs_dependsOn_definition_type;
}

export interface SolidSelectorQuery_pipeline_solids_inputs_dependsOn_solid {
  __typename: "Solid";
  name: string;
}

export interface SolidSelectorQuery_pipeline_solids_inputs_dependsOn {
  __typename: "Output";
  definition: SolidSelectorQuery_pipeline_solids_inputs_dependsOn_definition;
  solid: SolidSelectorQuery_pipeline_solids_inputs_dependsOn_solid;
}

export interface SolidSelectorQuery_pipeline_solids_inputs {
  __typename: "Input";
  definition: SolidSelectorQuery_pipeline_solids_inputs_definition;
  dependsOn: SolidSelectorQuery_pipeline_solids_inputs_dependsOn[];
}

export interface SolidSelectorQuery_pipeline_solids_outputs_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
  isNothing: boolean;
}

export interface SolidSelectorQuery_pipeline_solids_outputs_definition_expectations {
  __typename: "Expectation";
  name: string;
  description: string | null;
}

export interface SolidSelectorQuery_pipeline_solids_outputs_definition {
  __typename: "OutputDefinition";
  name: string;
  type: SolidSelectorQuery_pipeline_solids_outputs_definition_type;
  expectations: SolidSelectorQuery_pipeline_solids_outputs_definition_expectations[];
}

export interface SolidSelectorQuery_pipeline_solids_outputs_dependedBy_solid {
  __typename: "Solid";
  name: string;
}

export interface SolidSelectorQuery_pipeline_solids_outputs_dependedBy_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
}

export interface SolidSelectorQuery_pipeline_solids_outputs_dependedBy_definition {
  __typename: "InputDefinition";
  name: string;
  type: SolidSelectorQuery_pipeline_solids_outputs_dependedBy_definition_type;
}

export interface SolidSelectorQuery_pipeline_solids_outputs_dependedBy {
  __typename: "Input";
  solid: SolidSelectorQuery_pipeline_solids_outputs_dependedBy_solid;
  definition: SolidSelectorQuery_pipeline_solids_outputs_dependedBy_definition;
}

export interface SolidSelectorQuery_pipeline_solids_outputs {
  __typename: "Output";
  definition: SolidSelectorQuery_pipeline_solids_outputs_definition;
  dependedBy: SolidSelectorQuery_pipeline_solids_outputs_dependedBy[];
}

export interface SolidSelectorQuery_pipeline_solids {
  __typename: "Solid";
  name: string;
  definition: SolidSelectorQuery_pipeline_solids_definition;
  inputs: SolidSelectorQuery_pipeline_solids_inputs[];
  outputs: SolidSelectorQuery_pipeline_solids_outputs[];
}

export interface SolidSelectorQuery_pipeline {
  __typename: "Pipeline";
  name: string;
  solids: SolidSelectorQuery_pipeline_solids[];
}

export interface SolidSelectorQuery {
  pipeline: SolidSelectorQuery_pipeline;
}

export interface SolidSelectorQueryVariables {
  name: string;
}
