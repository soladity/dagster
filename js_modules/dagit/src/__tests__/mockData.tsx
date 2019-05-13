import { ROOT_PIPELINES_QUERY } from "../App";
import { TYPE_EXPLORER_CONTAINER_QUERY } from "../typeexplorer/TypeExplorerContainer";
import { TYPE_LIST_CONTAINER_QUERY } from "../typeexplorer/TypeListContainer";
import { PIPELINE_EXPLORER_ROOT_QUERY } from "../PipelineExplorerRoot";

const MOCKS = [
  {
    request: {
      operationName: "RootPipelinesQuery",
      queryVariableName: "ROOT_PIPELINES_QUERY",
      query: ROOT_PIPELINES_QUERY,
      variables: undefined
    },
    result: {
      data: {
        pipelinesOrError: {
          __typename: "PipelineConnection",
          nodes: [
            { name: "pandas_hello_world", __typename: "Pipeline" },
            {
              name: "papermill_pandas_hello_world_pipeline",
              __typename: "Pipeline"
            }
          ]
        }
      }
    }
  },

  {
    request: {
      operationName: "PipelineExplorerRootQuery",
      queryVariableName: "PIPELINE_EXPLORER_ROOT_QUERY",
      query: PIPELINE_EXPLORER_ROOT_QUERY,
      variables: { name: "pandas_hello_world" }
    },
    result: {
      data: {
        pipeline: {
          name: "pandas_hello_world",
          description: null,
          solids: [
            {
              name: "sum_solid",
              definition: {
                metadata: [],
                configDefinition: null,
                __typename: "SolidDefinition",
                description: null
              },
              inputs: [
                {
                  definition: {
                    name: "num",
                    type: {
                      name: "PandasDataFrame",
                      __typename: "RegularRuntimeType",
                      isNothing: false,
                      displayName: "PandasDataFrame",
                      description:
                        "Two-dimensional size-mutable, potentially heterogeneous\n    tabular data structure with labeled axes (rows and columns).\n    See http://pandas.pydata.org/"
                    },
                    __typename: "InputDefinition",
                    description: null,
                    expectations: []
                  },
                  dependsOn: null,
                  __typename: "Input"
                }
              ],
              outputs: [
                {
                  definition: {
                    name: "result",
                    type: {
                      name: "PandasDataFrame",
                      __typename: "RegularRuntimeType",
                      isNothing: false,
                      displayName: "PandasDataFrame",
                      description:
                        "Two-dimensional size-mutable, potentially heterogeneous\n    tabular data structure with labeled axes (rows and columns).\n    See http://pandas.pydata.org/"
                    },
                    expectations: [],
                    __typename: "OutputDefinition",
                    description: null
                  },
                  dependedBy: [
                    {
                      solid: { name: "sum_sq_solid", __typename: "Solid" },
                      definition: {
                        name: "sum_df",
                        type: {
                          name: "PandasDataFrame",
                          __typename: "RegularRuntimeType"
                        },
                        __typename: "InputDefinition"
                      },
                      __typename: "Input"
                    }
                  ],
                  __typename: "Output"
                }
              ],
              __typename: "Solid"
            },
            {
              name: "sum_sq_solid",
              definition: {
                metadata: [],
                configDefinition: null,
                __typename: "SolidDefinition",
                description: null
              },
              inputs: [
                {
                  definition: {
                    name: "sum_df",
                    type: {
                      name: "PandasDataFrame",
                      __typename: "RegularRuntimeType",
                      isNothing: false,
                      displayName: "PandasDataFrame",
                      description:
                        "Two-dimensional size-mutable, potentially heterogeneous\n    tabular data structure with labeled axes (rows and columns).\n    See http://pandas.pydata.org/"
                    },
                    __typename: "InputDefinition",
                    description: null,
                    expectations: []
                  },
                  dependsOn: {
                    definition: {
                      name: "result",
                      type: {
                        name: "PandasDataFrame",
                        __typename: "RegularRuntimeType"
                      },
                      __typename: "OutputDefinition"
                    },
                    solid: { name: "sum_solid", __typename: "Solid" },
                    __typename: "Output"
                  },
                  __typename: "Input"
                }
              ],
              outputs: [
                {
                  definition: {
                    name: "result",
                    type: {
                      name: "PandasDataFrame",
                      __typename: "RegularRuntimeType",
                      isNothing: false,
                      displayName: "PandasDataFrame",
                      description:
                        "Two-dimensional size-mutable, potentially heterogeneous\n    tabular data structure with labeled axes (rows and columns).\n    See http://pandas.pydata.org/"
                    },
                    expectations: [],
                    __typename: "OutputDefinition",
                    description: null
                  },
                  dependedBy: [],
                  __typename: "Output"
                }
              ],
              __typename: "Solid"
            }
          ],
          __typename: "Pipeline",
          environmentType: {
            name: "PandasHelloWorld.Environment",
            __typename: "CompositeConfigType"
          }
        }
      }
    }
  },

  {
    request: {
      operationName: "TypeExplorerContainerQuery",
      queryVariableName: "TYPE_EXPLORER_CONTAINER_QUERY",
      query: TYPE_EXPLORER_CONTAINER_QUERY,
      variables: {
        pipelineName: "pandas_hello_world",
        runtimeTypeName: "PandasDataFrame"
      }
    },
    result: {
      data: {
        runtimeTypeOrError: {
          __typename: "RegularRuntimeType",
          name: "PandasDataFrame",
          description:
            "Two-dimensional size-mutable, potentially heterogeneous\n    tabular data structure with labeled axes (rows and columns).\n    See http://pandas.pydata.org/",
          inputSchemaType: {
            key: "DataFrameInputSchema",
            name: "DataFrameInputSchema",
            description: null,
            isList: false,
            isNullable: false,
            isSelector: true,
            innerTypes: [
              {
                key: "Path",
                __typename: "RegularConfigType",
                name: "Path",
                description: "",
                isList: false,
                isNullable: false,
                isSelector: false,
                innerTypes: []
              },
              {
                key: "String",
                __typename: "RegularConfigType",
                name: "String",
                description: "",
                isList: false,
                isNullable: false,
                isSelector: false,
                innerTypes: []
              },
              {
                key: "Dict.26",
                __typename: "CompositeConfigType",
                name: null,
                description: "A configuration dictionary with typed fields",
                isList: false,
                isNullable: false,
                isSelector: false,
                innerTypes: [
                  { key: "Path", __typename: "RegularConfigType" },
                  { key: "String", __typename: "RegularConfigType" }
                ],
                fields: [
                  {
                    name: "path",
                    description: null,
                    isOptional: false,
                    configType: {
                      key: "Path",
                      __typename: "RegularConfigType"
                    },
                    __typename: "ConfigTypeField"
                  },
                  {
                    name: "sep",
                    description: null,
                    isOptional: true,
                    configType: {
                      key: "String",
                      __typename: "RegularConfigType"
                    },
                    __typename: "ConfigTypeField"
                  }
                ]
              },
              {
                key: "Dict.28",
                __typename: "CompositeConfigType",
                name: null,
                description: "A configuration dictionary with typed fields",
                isList: false,
                isNullable: false,
                isSelector: false,
                innerTypes: [{ key: "Path", __typename: "RegularConfigType" }],
                fields: [
                  {
                    name: "path",
                    description: null,
                    isOptional: false,
                    configType: {
                      key: "Path",
                      __typename: "RegularConfigType"
                    },
                    __typename: "ConfigTypeField"
                  }
                ]
              },
              {
                key: "Dict.27",
                __typename: "CompositeConfigType",
                name: null,
                description: "A configuration dictionary with typed fields",
                isList: false,
                isNullable: false,
                isSelector: false,
                innerTypes: [{ key: "Path", __typename: "RegularConfigType" }],
                fields: [
                  {
                    name: "path",
                    description: null,
                    isOptional: false,
                    configType: {
                      key: "Path",
                      __typename: "RegularConfigType"
                    },
                    __typename: "ConfigTypeField"
                  }
                ]
              }
            ],
            fields: [
              {
                name: "csv",
                description: null,
                isOptional: false,
                configType: {
                  key: "Dict.26",
                  __typename: "CompositeConfigType"
                },
                __typename: "ConfigTypeField"
              },
              {
                name: "parquet",
                description: null,
                isOptional: false,
                configType: {
                  key: "Dict.27",
                  __typename: "CompositeConfigType"
                },
                __typename: "ConfigTypeField"
              },
              {
                name: "table",
                description: null,
                isOptional: false,
                configType: {
                  key: "Dict.28",
                  __typename: "CompositeConfigType"
                },
                __typename: "ConfigTypeField"
              }
            ],
            __typename: "CompositeConfigType"
          },
          outputSchemaType: {
            key: "DataFrameOutputSchema",
            name: "DataFrameOutputSchema",
            description: null,
            isList: false,
            isNullable: false,
            isSelector: true,
            innerTypes: [
              {
                key: "Path",
                __typename: "RegularConfigType",
                name: "Path",
                description: "",
                isList: false,
                isNullable: false,
                isSelector: false,
                innerTypes: []
              },
              {
                key: "String",
                __typename: "RegularConfigType",
                name: "String",
                description: "",
                isList: false,
                isNullable: false,
                isSelector: false,
                innerTypes: []
              },
              {
                key: "Dict.23",
                __typename: "CompositeConfigType",
                name: null,
                description: "A configuration dictionary with typed fields",
                isList: false,
                isNullable: false,
                isSelector: false,
                innerTypes: [
                  { key: "Path", __typename: "RegularConfigType" },
                  { key: "String", __typename: "RegularConfigType" }
                ],
                fields: [
                  {
                    name: "path",
                    description: null,
                    isOptional: false,
                    configType: {
                      key: "Path",
                      __typename: "RegularConfigType"
                    },
                    __typename: "ConfigTypeField"
                  },
                  {
                    name: "sep",
                    description: null,
                    isOptional: true,
                    configType: {
                      key: "String",
                      __typename: "RegularConfigType"
                    },
                    __typename: "ConfigTypeField"
                  }
                ]
              },
              {
                key: "Dict.25",
                __typename: "CompositeConfigType",
                name: null,
                description: "A configuration dictionary with typed fields",
                isList: false,
                isNullable: false,
                isSelector: false,
                innerTypes: [{ key: "Path", __typename: "RegularConfigType" }],
                fields: [
                  {
                    name: "path",
                    description: null,
                    isOptional: false,
                    configType: {
                      key: "Path",
                      __typename: "RegularConfigType"
                    },
                    __typename: "ConfigTypeField"
                  }
                ]
              },
              {
                key: "Dict.24",
                __typename: "CompositeConfigType",
                name: null,
                description: "A configuration dictionary with typed fields",
                isList: false,
                isNullable: false,
                isSelector: false,
                innerTypes: [{ key: "Path", __typename: "RegularConfigType" }],
                fields: [
                  {
                    name: "path",
                    description: null,
                    isOptional: false,
                    configType: {
                      key: "Path",
                      __typename: "RegularConfigType"
                    },
                    __typename: "ConfigTypeField"
                  }
                ]
              }
            ],
            fields: [
              {
                name: "csv",
                description: null,
                isOptional: false,
                configType: {
                  key: "Dict.23",
                  __typename: "CompositeConfigType"
                },
                __typename: "ConfigTypeField"
              },
              {
                name: "parquet",
                description: null,
                isOptional: false,
                configType: {
                  key: "Dict.24",
                  __typename: "CompositeConfigType"
                },
                __typename: "ConfigTypeField"
              },
              {
                name: "table",
                description: null,
                isOptional: false,
                configType: {
                  key: "Dict.25",
                  __typename: "CompositeConfigType"
                },
                __typename: "ConfigTypeField"
              }
            ],
            __typename: "CompositeConfigType"
          }
        }
      }
    }
  },

  {
    request: {
      operationName: "TypeListContainerQuery",
      queryVariableName: "TYPE_LIST_CONTAINER_QUERY",
      query: TYPE_LIST_CONTAINER_QUERY,
      variables: { pipelineName: "pandas_hello_world" }
    },
    result: {
      data: {
        pipelineOrError: {
          __typename: "Pipeline",
          runtimeTypes: [
            {
              name: "Any",
              isBuiltin: true,
              displayName: "Any",
              description: null,
              __typename: "RegularRuntimeType"
            },
            {
              name: "Bool",
              isBuiltin: true,
              displayName: "Bool",
              description: null,
              __typename: "RegularRuntimeType"
            },
            {
              name: "Float",
              isBuiltin: true,
              displayName: "Float",
              description: null,
              __typename: "RegularRuntimeType"
            },
            {
              name: "Int",
              isBuiltin: true,
              displayName: "Int",
              description: null,
              __typename: "RegularRuntimeType"
            },
            {
              name: "Nothing",
              isBuiltin: true,
              displayName: "Nothing",
              description: null,
              __typename: "RegularRuntimeType"
            },
            {
              name: "PandasDataFrame",
              isBuiltin: false,
              displayName: "PandasDataFrame",
              description:
                "Two-dimensional size-mutable, potentially heterogeneous\n    tabular data structure with labeled axes (rows and columns).\n    See http://pandas.pydata.org/",
              __typename: "RegularRuntimeType"
            },
            {
              name: "Path",
              isBuiltin: true,
              displayName: "Path",
              description: null,
              __typename: "RegularRuntimeType"
            },
            {
              name: "String",
              isBuiltin: true,
              displayName: "String",
              description: null,
              __typename: "RegularRuntimeType"
            }
          ]
        }
      }
    }
  }
];

export default MOCKS;
