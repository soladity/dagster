// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: ConfigEditorPipelineFragment
// ====================================================

export interface ConfigEditorPipelineFragment_environmentType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigEditorPipelineFragment_configTypes_RegularConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigEditorPipelineFragment_configTypes_RegularConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: ConfigEditorPipelineFragment_configTypes_RegularConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface ConfigEditorPipelineFragment_configTypes_RegularConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigEditorPipelineFragment_configTypes_RegularConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigEditorPipelineFragment_configTypes_RegularConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: ConfigEditorPipelineFragment_configTypes_RegularConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface ConfigEditorPipelineFragment_configTypes_RegularConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: ConfigEditorPipelineFragment_configTypes_RegularConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: ConfigEditorPipelineFragment_configTypes_RegularConfigType_innerTypes_CompositeConfigType_fields[];
}

export type ConfigEditorPipelineFragment_configTypes_RegularConfigType_innerTypes = ConfigEditorPipelineFragment_configTypes_RegularConfigType_innerTypes_EnumConfigType | ConfigEditorPipelineFragment_configTypes_RegularConfigType_innerTypes_CompositeConfigType;

export interface ConfigEditorPipelineFragment_configTypes_RegularConfigType {
  __typename: "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  isSelector: boolean;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  innerTypes: ConfigEditorPipelineFragment_configTypes_RegularConfigType_innerTypes[];
}

export interface ConfigEditorPipelineFragment_configTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface ConfigEditorPipelineFragment_configTypes_EnumConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigEditorPipelineFragment_configTypes_EnumConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: ConfigEditorPipelineFragment_configTypes_EnumConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface ConfigEditorPipelineFragment_configTypes_EnumConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigEditorPipelineFragment_configTypes_EnumConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigEditorPipelineFragment_configTypes_EnumConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: ConfigEditorPipelineFragment_configTypes_EnumConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface ConfigEditorPipelineFragment_configTypes_EnumConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: ConfigEditorPipelineFragment_configTypes_EnumConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: ConfigEditorPipelineFragment_configTypes_EnumConfigType_innerTypes_CompositeConfigType_fields[];
}

export type ConfigEditorPipelineFragment_configTypes_EnumConfigType_innerTypes = ConfigEditorPipelineFragment_configTypes_EnumConfigType_innerTypes_EnumConfigType | ConfigEditorPipelineFragment_configTypes_EnumConfigType_innerTypes_CompositeConfigType;

export interface ConfigEditorPipelineFragment_configTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  name: string | null;
  isSelector: boolean;
  values: ConfigEditorPipelineFragment_configTypes_EnumConfigType_values[];
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  innerTypes: ConfigEditorPipelineFragment_configTypes_EnumConfigType_innerTypes[];
}

export interface ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes_CompositeConfigType_fields[];
}

export type ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes = ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes_EnumConfigType | ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes_CompositeConfigType;

export interface ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  isList: boolean;
  isNullable: boolean;
  description: string | null;
  isSelector: boolean;
  innerTypes: ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes[];
}

export interface ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields[];
}

export type ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes = ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes_EnumConfigType | ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes_CompositeConfigType;

export interface ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_CompositeConfigType_fields_configType;
}

export interface ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  isList: boolean;
  isNullable: boolean;
  description: string | null;
  isSelector: boolean;
  innerTypes: ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes[];
  fields: ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_CompositeConfigType_fields[];
}

export interface ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_CompositeConfigType_fields[];
}

export interface ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_ListConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_ListConfigType_ofType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_ListConfigType {
  __typename: "ListConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_ListConfigType_innerTypes[];
  ofType: ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_ListConfigType_ofType;
}

export type ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes = ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_EnumConfigType | ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_CompositeConfigType | ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_ListConfigType;

export interface ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType_ofType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType {
  __typename: "ListConfigType";
  key: string;
  name: string | null;
  isList: boolean;
  isNullable: boolean;
  description: string | null;
  isSelector: boolean;
  innerTypes: ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes[];
  ofType: ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType_ofType;
}

export type ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType = ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_EnumConfigType | ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_CompositeConfigType | ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType;

export interface ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType;
}

export interface ConfigEditorPipelineFragment_configTypes_CompositeConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigEditorPipelineFragment_configTypes_CompositeConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: ConfigEditorPipelineFragment_configTypes_CompositeConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface ConfigEditorPipelineFragment_configTypes_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigEditorPipelineFragment_configTypes_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigEditorPipelineFragment_configTypes_CompositeConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: ConfigEditorPipelineFragment_configTypes_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface ConfigEditorPipelineFragment_configTypes_CompositeConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: ConfigEditorPipelineFragment_configTypes_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: ConfigEditorPipelineFragment_configTypes_CompositeConfigType_innerTypes_CompositeConfigType_fields[];
}

export type ConfigEditorPipelineFragment_configTypes_CompositeConfigType_innerTypes = ConfigEditorPipelineFragment_configTypes_CompositeConfigType_innerTypes_EnumConfigType | ConfigEditorPipelineFragment_configTypes_CompositeConfigType_innerTypes_CompositeConfigType;

export interface ConfigEditorPipelineFragment_configTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  isSelector: boolean;
  fields: ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields[];
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  innerTypes: ConfigEditorPipelineFragment_configTypes_CompositeConfigType_innerTypes[];
}

export type ConfigEditorPipelineFragment_configTypes = ConfigEditorPipelineFragment_configTypes_RegularConfigType | ConfigEditorPipelineFragment_configTypes_EnumConfigType | ConfigEditorPipelineFragment_configTypes_CompositeConfigType;

export interface ConfigEditorPipelineFragment {
  __typename: "Pipeline";
  name: string;
  environmentType: ConfigEditorPipelineFragment_environmentType;
  configTypes: ConfigEditorPipelineFragment_configTypes[];
}
