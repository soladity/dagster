import * as React from "react";
import * as yaml from "yaml";
import gql from "graphql-tag";
import styled from "styled-components";
import { Button, Colors, Spinner } from "@blueprintjs/core";
import { IconNames } from "@blueprintjs/icons";
import { ApolloConsumer, Mutation, MutationFunction } from "react-apollo";

import ExecutionStartButton from "./ExecutionStartButton";
import { ExecutionTabs } from "./ExecutionTabs";
import {
  handleStartExecutionResult,
  HANDLE_START_EXECUTION_FRAGMENT
} from "../runs/RunUtils";
import { RunPreview } from "./RunPreview";
import { SplitPanelChildren } from "../SplitPanelChildren";
import SolidSelector from "./SolidSelector";
import {
  ConfigEditor,
  ConfigEditorHelpContext,
  isHelpContextEqual
} from "../configeditor/ConfigEditor";
import { ConfigEditorPresetsPicker } from "./ConfigEditorPresetsPicker";
import { ConfigEditorModePicker } from "./ConfigEditorModePicker";
import {
  applyChangesToSession,
  applySelectSession,
  applyRemoveSession,
  applyCreateSession,
  IStorageData,
  IExecutionSession,
  IExecutionSessionChanges
} from "../LocalStorage";
import {
  CONFIG_EDITOR_VALIDATION_FRAGMENT,
  CONFIG_EDITOR_ENVIRONMENT_SCHEMA_FRAGMENT,
  responseToValidationResult
} from "../configeditor/ConfigEditorUtils";

import { ConfigEditorEnvironmentSchemaFragment } from "../configeditor/types/ConfigEditorEnvironmentSchemaFragment";
import {
  PreviewConfigQuery,
  PreviewConfigQueryVariables
} from "./types/PreviewConfigQuery";
import {
  PipelineExecutionContainerFragment,
  PipelineExecutionContainerFragment_InvalidSubsetError
} from "./types/PipelineExecutionContainerFragment";
import {
  PipelineExecutionContainerEnvironmentSchemaFragment,
  PipelineExecutionContainerEnvironmentSchemaFragment_ModeNotFoundError
} from "./types/PipelineExecutionContainerEnvironmentSchemaFragment";
import { PipelineDetailsFragment } from "./types/PipelineDetailsFragment";
import {
  StartPipelineExecution,
  StartPipelineExecutionVariables
} from "./types/StartPipelineExecution";
import { ConfigEditorHelp } from "./ConfigEditorHelp";

const YAML_SYNTAX_INVALID = `The YAML you provided couldn't be parsed. Please fix the syntax errors and try again.`;

interface IPipelineExecutionContainerProps {
  data: IStorageData;
  onSave: (data: IStorageData) => void;
  pipelineOrError: PipelineExecutionContainerFragment | undefined;
  environmentSchemaOrError:
    | PipelineExecutionContainerEnvironmentSchemaFragment
    | undefined;
  pipelineName: string;
  currentSession: IExecutionSession;
}

interface IPipelineExecutionContainerState {
  editorHelpContext: ConfigEditorHelpContext | null;
  preview: PreviewConfigQuery | null;
  showWhitespace: boolean;
}

export type SubsetError =
  | PipelineExecutionContainerFragment_InvalidSubsetError
  | undefined;

export type ModeNotFoundError =
  | PipelineExecutionContainerEnvironmentSchemaFragment_ModeNotFoundError
  | undefined;

export default class PipelineExecutionContainer extends React.Component<
  IPipelineExecutionContainerProps,
  IPipelineExecutionContainerState
> {
  static fragments = {
    PipelineExecutionContainerFragment: gql`
      fragment PipelineExecutionContainerFragment on PipelineOrError {
        ...PipelineDetailsFragment
        ... on InvalidSubsetError {
          message
          pipeline {
            ...PipelineDetailsFragment
          }
        }
      }

      fragment PipelineDetailsFragment on Pipeline {
        name
        modes {
          name
          description
        }
      }
    `,
    EnvironmentSchemaOrErrorFragment: gql`
      fragment PipelineExecutionContainerEnvironmentSchemaFragment on EnvironmentSchemaOrError {
        __typename
        ... on EnvironmentSchema {
          ...ConfigEditorEnvironmentSchemaFragment
        }
        ... on ModeNotFoundError {
          message
        }
      }
      ${CONFIG_EDITOR_ENVIRONMENT_SCHEMA_FRAGMENT}
    `
  };

  state: IPipelineExecutionContainerState = {
    preview: null,
    showWhitespace: true,
    editorHelpContext: null
  };

  mounted = false;

  componentDidMount() {
    this.mounted = true;
  }

  componentWillUnmount() {
    this.mounted = false;
  }

  onConfigChange = (config: any) => {
    this.onSaveSession(this.props.currentSession.key, {
      environmentConfigYaml: config
    });
  };

  onSolidSubsetChange = (solidSubset: string[] | null) => {
    this.onSaveSession(this.props.currentSession.key, { solidSubset });
  };

  onModeChange = (mode: string) => {
    this.onSaveSession(this.props.currentSession.key, { mode });
  };

  onSelectSession = (session: string) => {
    this.props.onSave(applySelectSession(this.props.data, session));
  };

  onSaveSession = (session: string, changes: IExecutionSessionChanges) => {
    this.props.onSave(applyChangesToSession(this.props.data, session, changes));
  };

  onCreateSession = (initial?: Partial<IExecutionSession>) => {
    this.props.onSave(applyCreateSession(this.props.data, initial));
  };

  onRemoveSession = (session: string) => {
    this.props.onSave(applyRemoveSession(this.props.data, session));
  };

  getPipeline = (): PipelineDetailsFragment | undefined => {
    const obj = this.props.pipelineOrError;
    if (obj === undefined) {
      return undefined;
    } else if (obj.__typename === "Pipeline") {
      return obj;
    } else if (obj.__typename === "InvalidSubsetError") {
      return obj.pipeline;
    }
    throw new Error(`Recieved unexpected "${obj.__typename}"`);
  };

  getEnvironmentSchema = ():
    | ConfigEditorEnvironmentSchemaFragment
    | undefined => {
    const obj = this.props.environmentSchemaOrError;
    if (obj && obj.__typename === "EnvironmentSchema") {
      return obj;
    }
    return undefined;
  };

  getModeError = (): ModeNotFoundError => {
    const obj = this.props.environmentSchemaOrError;
    if (obj && obj.__typename === "ModeNotFoundError") {
      return obj;
    }
    return undefined;
  };

  getSubsetError = (): SubsetError => {
    const obj = this.props.pipelineOrError;
    if (obj && obj.__typename === "InvalidSubsetError") {
      return obj;
    }
    return undefined;
  };

  onExecute = async (
    startPipelineExecution: MutationFunction<
      StartPipelineExecution,
      StartPipelineExecutionVariables
    >
  ) => {
    const { preview } = this.state;
    const pipeline = this.getPipeline();

    if (!preview || !pipeline) {
      alert(
        "Dagit is still retrieving pipeline info. Please try again in a moment."
      );
      return;
    }

    const variables = this.buildExecutionVariables();
    if (!variables) return;

    const result = await startPipelineExecution({ variables });
    handleStartExecutionResult(pipeline.name, result, {
      openInNewWindow: true
    });
  };

  buildExecutionVariables = () => {
    const { currentSession } = this.props;
    const pipeline = this.getPipeline();
    if (!pipeline || !currentSession || !currentSession.mode) return;

    let environmentConfigData = {};
    try {
      // Note: parsing `` returns null rather than an empty object,
      // which is preferable for representing empty config.
      environmentConfigData =
        yaml.parse(currentSession.environmentConfigYaml) || {};
    } catch (err) {
      alert(YAML_SYNTAX_INVALID);
      return;
    }

    return {
      executionParams: {
        environmentConfigData,
        selector: {
          name: pipeline.name,
          solidSubset: currentSession.solidSubset
        },
        mode: currentSession.mode
      }
    };
  };

  render() {
    const { currentSession, pipelineName } = this.props;
    const { preview, editorHelpContext, showWhitespace } = this.state;
    const pipeline = this.getPipeline();
    const subsetError = this.getSubsetError();
    const environmentSchema = this.getEnvironmentSchema();
    const modeError = this.getModeError();

    return (
      <>
        <Mutation<StartPipelineExecution, StartPipelineExecutionVariables>
          mutation={START_PIPELINE_EXECUTION_MUTATION}
        >
          {startPipelineExecution => (
            <TabBarContainer className="bp3-dark">
              <ExecutionTabs
                sessions={this.props.data.sessions}
                currentSession={currentSession}
                onSelectSession={this.onSelectSession}
                onCreateSession={this.onCreateSession}
                onRemoveSession={this.onRemoveSession}
                onSaveSession={this.onSaveSession}
              />
              <div style={{ flex: 1 }} />
              {!pipeline || !this.state.preview ? (
                <Spinner size={17} />
              ) : (
                <ExecutionStartButton
                  title="Start Execution"
                  icon={IconNames.PLAY}
                  onClick={() => this.onExecute(startPipelineExecution)}
                />
              )}
            </TabBarContainer>
          )}
        </Mutation>
        {currentSession ? (
          <PipelineExecutionWrapper>
            <SplitPanelChildren
              identifier={"execution"}
              leftInitialPercent={75}
              left={
                <>
                  <ConfigEditorPresetInsertionContainer className="bp3-dark">
                    <ConfigEditorPresetsPicker
                      pipelineName={pipelineName}
                      solidSubset={currentSession.solidSubset}
                      onCreateSession={this.onCreateSession}
                    />
                  </ConfigEditorPresetInsertionContainer>
                  <ConfigEditorHelp context={editorHelpContext} />
                  <ApolloConsumer>
                    {client => (
                      <ConfigEditor
                        readOnly={false}
                        environmentSchema={environmentSchema}
                        configCode={currentSession.environmentConfigYaml}
                        onConfigChange={this.onConfigChange}
                        onHelpContextChange={next => {
                          if (!isHelpContextEqual(editorHelpContext, next)) {
                            this.setState({ editorHelpContext: next });
                          }
                        }}
                        showWhitespace={showWhitespace}
                        checkConfig={async environmentConfigData => {
                          if (!currentSession.mode || modeError) {
                            return {
                              isValid: false,
                              errors: [
                                // FIXME this should be specific -- we should have an enumerated
                                // validation error when there is no mode provided
                                {
                                  message: "Must specify a mode",
                                  path: ["root"],
                                  reason: "MISSING_REQUIRED_FIELD"
                                }
                              ]
                            };
                          }
                          const { data } = await client.query<
                            PreviewConfigQuery,
                            PreviewConfigQueryVariables
                          >({
                            fetchPolicy: "no-cache",
                            query: PREVIEW_CONFIG_QUERY,
                            variables: {
                              environmentConfigData,
                              pipeline: {
                                name: pipelineName,
                                solidSubset: currentSession.solidSubset
                              },
                              mode: currentSession.mode || "default"
                            }
                          });

                          if (this.mounted) {
                            this.setState({ preview: data });
                          }

                          return responseToValidationResult(
                            environmentConfigData,
                            data.isPipelineConfigValid
                          );
                        }}
                      />
                    )}
                  </ApolloConsumer>
                  <SessionSettingsBar className="bp3-dark">
                    <SolidSelector
                      pipelineName={pipelineName}
                      subsetError={subsetError}
                      value={currentSession.solidSubset || null}
                      onChange={this.onSolidSubsetChange}
                    />
                    <div style={{ width: 5 }} />
                    {pipeline && (
                      <ConfigEditorModePicker
                        modes={pipeline.modes}
                        modeError={modeError}
                        onModeChange={this.onModeChange}
                        modeName={currentSession.mode}
                      />
                    )}
                    <Button
                      icon="paragraph"
                      small={true}
                      active={showWhitespace}
                      style={{ marginLeft: "auto" }}
                      onClick={() =>
                        this.setState({ showWhitespace: !showWhitespace })
                      }
                    />
                  </SessionSettingsBar>
                </>
              }
              right={
                preview ? (
                  <RunPreview
                    plan={preview.executionPlan}
                    validation={preview.isPipelineConfigValid}
                  />
                ) : (
                  <RunPreview />
                )
              }
            />
          </PipelineExecutionWrapper>
        ) : (
          <span />
        )}
      </>
    );
  }
}

const START_PIPELINE_EXECUTION_MUTATION = gql`
  mutation StartPipelineExecution($executionParams: ExecutionParams!) {
    startPipelineExecution(executionParams: $executionParams) {
      __typename

      ... on StartPipelineExecutionSuccess {
        run {
          runId
          pipeline {
            name
          }
        }
      }
      ... on PipelineNotFoundError {
        message
      }
      ... on PipelineConfigValidationInvalid {
        errors {
          message
        }
      }
      ...HandleStartExecutionFragment
    }
  }

  ${HANDLE_START_EXECUTION_FRAGMENT}
`;

const PREVIEW_CONFIG_QUERY = gql`
  query PreviewConfigQuery(
    $pipeline: ExecutionSelector!
    $environmentConfigData: EnvironmentConfigData!
    $mode: String!
  ) {
    isPipelineConfigValid(
      pipeline: $pipeline
      environmentConfigData: $environmentConfigData
      mode: $mode
    ) {
      ...ConfigEditorValidationFragment
      ...RunPreviewConfigValidationFragment
    }
    executionPlan(
      pipeline: $pipeline
      environmentConfigData: $environmentConfigData
      mode: $mode
    ) {
      ...RunPreviewExecutionPlanResultFragment
    }
  }
  ${RunPreview.fragments.RunPreviewConfigValidationFragment}
  ${RunPreview.fragments.RunPreviewExecutionPlanResultFragment}
  ${CONFIG_EDITOR_VALIDATION_FRAGMENT}
`;

const PipelineExecutionWrapper = styled.div`
  flex: 1 1;
  display: flex;
  flex-direction: row;
  width: 100%;
  height: 100vh;
  position: absolute;
  padding-top: 100px;
`;

const SessionSettingsBar = styled.div`
  color: white;
  display: flex;
  border-top: 1px solid ${Colors.DARK_GRAY5};
  background-color: ${Colors.DARK_GRAY2};
  align-items: center;
  height: 47px;
  padding: 8px;
}
`;

const ConfigEditorPresetInsertionContainer = styled.div`
  display: inline-block;
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 10;
`;

const TabBarContainer = styled.div`
  height: 50px;
  display: flex;
  flex-direction: row;
  align-items: center;
  border-bottom: 1px solid ${Colors.DARK_GRAY5};
  background: ${Colors.BLACK};
  padding: 8px;
  z-index: 3;
`;
