// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: SolidNodeFragment
// ====================================================

export interface SolidNodeFragment_definition_CompositeSolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface SolidNodeFragment_definition_CompositeSolidDefinition {
  __typename: "CompositeSolidDefinition";
  metadata: SolidNodeFragment_definition_CompositeSolidDefinition_metadata[];
}

export interface SolidNodeFragment_definition_SolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface SolidNodeFragment_definition_SolidDefinition_configDefinition_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  name: string | null;
  description: string | null;
}

export interface SolidNodeFragment_definition_SolidDefinition_configDefinition {
  __typename: "ConfigTypeField";
  configType: SolidNodeFragment_definition_SolidDefinition_configDefinition_configType;
}

export interface SolidNodeFragment_definition_SolidDefinition {
  __typename: "SolidDefinition";
  metadata: SolidNodeFragment_definition_SolidDefinition_metadata[];
  configDefinition: SolidNodeFragment_definition_SolidDefinition_configDefinition | null;
}

export type SolidNodeFragment_definition = SolidNodeFragment_definition_CompositeSolidDefinition | SolidNodeFragment_definition_SolidDefinition;

export interface SolidNodeFragment_inputs_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
  isNothing: boolean;
}

export interface SolidNodeFragment_inputs_definition {
  __typename: "InputDefinition";
  name: string;
  type: SolidNodeFragment_inputs_definition_type;
}

export interface SolidNodeFragment_inputs_dependsOn_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
}

export interface SolidNodeFragment_inputs_dependsOn_definition {
  __typename: "OutputDefinition";
  name: string;
  type: SolidNodeFragment_inputs_dependsOn_definition_type;
}

export interface SolidNodeFragment_inputs_dependsOn_solid {
  __typename: "Solid";
  name: string;
}

export interface SolidNodeFragment_inputs_dependsOn {
  __typename: "Output";
  definition: SolidNodeFragment_inputs_dependsOn_definition;
  solid: SolidNodeFragment_inputs_dependsOn_solid;
}

export interface SolidNodeFragment_inputs {
  __typename: "Input";
  definition: SolidNodeFragment_inputs_definition;
  dependsOn: SolidNodeFragment_inputs_dependsOn[];
}

export interface SolidNodeFragment_outputs_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
  isNothing: boolean;
}

export interface SolidNodeFragment_outputs_definition_expectations {
  __typename: "Expectation";
  name: string;
  description: string | null;
}

export interface SolidNodeFragment_outputs_definition {
  __typename: "OutputDefinition";
  name: string;
  type: SolidNodeFragment_outputs_definition_type;
  expectations: SolidNodeFragment_outputs_definition_expectations[];
}

export interface SolidNodeFragment_outputs_dependedBy_solid {
  __typename: "Solid";
  name: string;
}

export interface SolidNodeFragment_outputs_dependedBy_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
}

export interface SolidNodeFragment_outputs_dependedBy_definition {
  __typename: "InputDefinition";
  name: string;
  type: SolidNodeFragment_outputs_dependedBy_definition_type;
}

export interface SolidNodeFragment_outputs_dependedBy {
  __typename: "Input";
  solid: SolidNodeFragment_outputs_dependedBy_solid;
  definition: SolidNodeFragment_outputs_dependedBy_definition;
}

export interface SolidNodeFragment_outputs {
  __typename: "Output";
  definition: SolidNodeFragment_outputs_definition;
  dependedBy: SolidNodeFragment_outputs_dependedBy[];
}

export interface SolidNodeFragment {
  __typename: "Solid";
  name: string;
  definition: SolidNodeFragment_definition;
  inputs: SolidNodeFragment_inputs[];
  outputs: SolidNodeFragment_outputs[];
}
