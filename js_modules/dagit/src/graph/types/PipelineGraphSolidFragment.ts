// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: PipelineGraphSolidFragment
// ====================================================

export interface PipelineGraphSolidFragment_definition_CompositeSolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface PipelineGraphSolidFragment_definition_CompositeSolidDefinition {
  __typename: "CompositeSolidDefinition";
  metadata: PipelineGraphSolidFragment_definition_CompositeSolidDefinition_metadata[];
}

export interface PipelineGraphSolidFragment_definition_SolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface PipelineGraphSolidFragment_definition_SolidDefinition_configDefinition_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  name: string | null;
  description: string | null;
}

export interface PipelineGraphSolidFragment_definition_SolidDefinition_configDefinition {
  __typename: "ConfigTypeField";
  configType: PipelineGraphSolidFragment_definition_SolidDefinition_configDefinition_configType;
}

export interface PipelineGraphSolidFragment_definition_SolidDefinition {
  __typename: "SolidDefinition";
  metadata: PipelineGraphSolidFragment_definition_SolidDefinition_metadata[];
  configDefinition: PipelineGraphSolidFragment_definition_SolidDefinition_configDefinition | null;
}

export type PipelineGraphSolidFragment_definition = PipelineGraphSolidFragment_definition_CompositeSolidDefinition | PipelineGraphSolidFragment_definition_SolidDefinition;

export interface PipelineGraphSolidFragment_inputs_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
  isNothing: boolean;
}

export interface PipelineGraphSolidFragment_inputs_definition {
  __typename: "InputDefinition";
  name: string;
  type: PipelineGraphSolidFragment_inputs_definition_type;
}

export interface PipelineGraphSolidFragment_inputs_dependsOn_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
}

export interface PipelineGraphSolidFragment_inputs_dependsOn_definition {
  __typename: "OutputDefinition";
  name: string;
  type: PipelineGraphSolidFragment_inputs_dependsOn_definition_type;
}

export interface PipelineGraphSolidFragment_inputs_dependsOn_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineGraphSolidFragment_inputs_dependsOn {
  __typename: "Output";
  definition: PipelineGraphSolidFragment_inputs_dependsOn_definition;
  solid: PipelineGraphSolidFragment_inputs_dependsOn_solid;
}

export interface PipelineGraphSolidFragment_inputs {
  __typename: "Input";
  definition: PipelineGraphSolidFragment_inputs_definition;
  dependsOn: PipelineGraphSolidFragment_inputs_dependsOn[];
}

export interface PipelineGraphSolidFragment_outputs_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
  isNothing: boolean;
}

export interface PipelineGraphSolidFragment_outputs_definition_expectations {
  __typename: "Expectation";
  name: string;
  description: string | null;
}

export interface PipelineGraphSolidFragment_outputs_definition {
  __typename: "OutputDefinition";
  name: string;
  type: PipelineGraphSolidFragment_outputs_definition_type;
  expectations: PipelineGraphSolidFragment_outputs_definition_expectations[];
}

export interface PipelineGraphSolidFragment_outputs_dependedBy_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineGraphSolidFragment_outputs_dependedBy_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
}

export interface PipelineGraphSolidFragment_outputs_dependedBy_definition {
  __typename: "InputDefinition";
  name: string;
  type: PipelineGraphSolidFragment_outputs_dependedBy_definition_type;
}

export interface PipelineGraphSolidFragment_outputs_dependedBy {
  __typename: "Input";
  solid: PipelineGraphSolidFragment_outputs_dependedBy_solid;
  definition: PipelineGraphSolidFragment_outputs_dependedBy_definition;
}

export interface PipelineGraphSolidFragment_outputs {
  __typename: "Output";
  definition: PipelineGraphSolidFragment_outputs_definition;
  dependedBy: PipelineGraphSolidFragment_outputs_dependedBy[];
}

export interface PipelineGraphSolidFragment {
  __typename: "Solid";
  name: string;
  definition: PipelineGraphSolidFragment_definition;
  inputs: PipelineGraphSolidFragment_inputs[];
  outputs: PipelineGraphSolidFragment_outputs[];
}
