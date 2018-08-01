

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: AppQuery
// ====================================================

export interface AppQuery_pipelines_solids_inputs_sources_arguments {
  name: string;
  description: string | null;
  type: Type;
  isOptional: boolean;
}

export interface AppQuery_pipelines_solids_inputs_sources {
  name: string;
  description: string | null;
  arguments: AppQuery_pipelines_solids_inputs_sources_arguments[];
}

export interface AppQuery_pipelines_solids_inputs_dependsOn {
  name: string;
}

export interface AppQuery_pipelines_solids_inputs {
  name: string;
  description: string | null;
  sources: AppQuery_pipelines_solids_inputs_sources[];
  dependsOn: AppQuery_pipelines_solids_inputs_dependsOn | null;
}

export interface AppQuery_pipelines_solids_output_materializations_arguments {
  name: string;
  description: string | null;
  type: Type;
  isOptional: boolean;
}

export interface AppQuery_pipelines_solids_output_materializations {
  name: string;
  description: string | null;
  arguments: AppQuery_pipelines_solids_output_materializations_arguments[];
}

export interface AppQuery_pipelines_solids_output_expectations {
  name: string;
  description: string | null;
}

export interface AppQuery_pipelines_solids_output {
  materializations: AppQuery_pipelines_solids_output_materializations[];
  expectations: AppQuery_pipelines_solids_output_expectations[];
}

export interface AppQuery_pipelines_solids {
  name: string;
  description: string | null;
  inputs: AppQuery_pipelines_solids_inputs[];
  output: AppQuery_pipelines_solids_output;
}

export interface AppQuery_pipelines_context_arguments {
  name: string;
  description: string | null;
  type: Type;
  isOptional: boolean;
}

export interface AppQuery_pipelines_context {
  name: string;
  description: string | null;
  arguments: AppQuery_pipelines_context_arguments[];
}

export interface AppQuery_pipelines {
  name: string;
  description: string | null;
  solids: AppQuery_pipelines_solids[];
  context: AppQuery_pipelines_context[];
}

export interface AppQuery {
  pipelines: AppQuery_pipelines[];
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

//==============================================================
// START Enums and Input Objects
//==============================================================

export enum Type {
  BOOL = "BOOL",
  INT = "INT",
  PATH = "PATH",
  STRING = "STRING",
}

//==============================================================
// END Enums and Input Objects
//==============================================================