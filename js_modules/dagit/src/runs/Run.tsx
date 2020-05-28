import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components/macro";
import { useMutation } from "react-apollo";
import ApolloClient from "apollo-client";

import LogsScrollingTable from "./LogsScrollingTable";
import { LogsProvider, GetDefaultLogFilter, LogFilter } from "./LogsProvider";
import { RunFragment } from "./types/RunFragment";
import { SplitPanelContainer, SplitPanelToggles } from "../SplitPanelContainer";
import { RunMetadataProvider, IStepState } from "../RunMetadataProvider";
import LogsToolbar from "./LogsToolbar";
import {
  handleReexecutionResult,
  getReexecutionVariables,
  START_PIPELINE_REEXECUTION_MUTATION,
  LAUNCH_PIPELINE_REEXECUTION_MUTATION
} from "./RunUtils";
import { StartPipelineReexecutionVariables } from "./types/StartPipelineReexecution";
import { RunStatusToPageAttributes } from "./RunStatusToPageAttributes";
import { RunContext } from "./RunContext";

import {
  RunPipelineRunEventFragment_ExecutionStepFailureEvent,
  RunPipelineRunEventFragment
} from "./types/RunPipelineRunEventFragment";
import { GaantChart, GaantChartMode } from "../gaant/GaantChart";
import { RunActionButtons } from "./RunActionButtons";
import { showCustomAlert } from "../CustomAlertProvider";
import PythonErrorInfo from "../PythonErrorInfo";
import { NonIdealState } from "@blueprintjs/core";
import { IconNames } from "@blueprintjs/icons";
import { DagsterRepositoryContext } from "../DagsterRepositoryContext";

interface RunProps {
  client: ApolloClient<any>;
  run?: RunFragment;
}

interface RunState {
  logsFilter: LogFilter;
  query: string;
  selectedSteps: string[];
}

export class Run extends React.Component<RunProps, RunState> {
  static fragments = {
    RunFragment: gql`
      fragment RunFragment on PipelineRun {
        ...RunStatusPipelineRunFragment

        runConfigYaml
        runId
        canTerminate
        status
        mode
        tags {
          key
          value
        }
        rootRunId
        parentRunId
        pipeline {
          __typename
          ... on PipelineReference {
            name
          }
          ... on Pipeline {
            solids {
              name
            }
          }
        }
        executionPlan {
          steps {
            key
            inputs {
              dependsOn {
                key
                outputs {
                  name
                  type {
                    name
                  }
                }
              }
            }
          }
          artifactsPersisted
          ...GaantChartExecutionPlanFragment
        }
        stepKeysToExecute
      }

      ${RunStatusToPageAttributes.fragments.RunStatusPipelineRunFragment}
      ${GaantChart.fragments.GaantChartExecutionPlanFragment}
    `,
    RunPipelineRunEventFragment: gql`
      fragment RunPipelineRunEventFragment on PipelineRunEvent {
        ... on MessageEvent {
          message
          timestamp
          level
          step {
            key
          }
        }

        ...LogsScrollingTableMessageFragment
        ...RunMetadataProviderMessageFragment
      }

      ${RunMetadataProvider.fragments.RunMetadataProviderMessageFragment}
      ${LogsScrollingTable.fragments.LogsScrollingTableMessageFragment}
      ${PythonErrorInfo.fragments.PythonErrorFragment}
    `
  };

  state: RunState = {
    logsFilter: GetDefaultLogFilter(),
    query: "*",
    selectedSteps: []
  };

  onShowStateDetails = (
    stepKey: string,
    logs: RunPipelineRunEventFragment[]
  ) => {
    const errorNode = logs.find(
      node =>
        node.__typename === "ExecutionStepFailureEvent" &&
        node.step != null &&
        node.step.key === stepKey
    ) as RunPipelineRunEventFragment_ExecutionStepFailureEvent;

    if (errorNode) {
      showCustomAlert({
        body: <PythonErrorInfo error={errorNode} />
      });
    }
  };

  onSetLogsFilter = (logsFilter: LogFilter) => {
    this.setState({ logsFilter });
  };

  onSetQuery = (query: string) => {
    this.setState({ query });

    // filter the log following the DSL step selection
    this.setState(prevState => {
      return {
        logsFilter: {
          ...prevState.logsFilter,
          values: query !== "*" ? [{ token: "query", value: query }] : []
        }
      };
    });
  };

  onSetSelectedSteps = (selectedSteps: string[]) => {
    this.setState({ selectedSteps });
  };

  render() {
    const { client, run } = this.props;
    const { logsFilter, query, selectedSteps } = this.state;

    return (
      <RunContext.Provider value={run}>
        {run && <RunStatusToPageAttributes run={run} />}

        <LogsProvider
          client={client}
          runId={run ? run.runId : ""}
          filter={logsFilter}
          selectedSteps={selectedSteps}
        >
          {({ filteredNodes, allNodes, loaded }) => (
            <ReexecuteWithData
              run={run}
              filteredNodes={filteredNodes}
              allNodes={allNodes}
              logsLoading={!loaded}
              logsFilter={logsFilter}
              query={query}
              selectedSteps={selectedSteps}
              onSetLogsFilter={this.onSetLogsFilter}
              onSetQuery={this.onSetQuery}
              onSetSelectedSteps={this.onSetSelectedSteps}
              onShowStateDetails={this.onShowStateDetails}
              getReexecutionVariables={getReexecutionVariables}
            />
          )}
        </LogsProvider>
      </RunContext.Provider>
    );
  }
}

interface ReexecuteWithDataProps {
  run?: RunFragment;
  allNodes: (RunPipelineRunEventFragment & { clientsideKey: string })[];
  filteredNodes: (RunPipelineRunEventFragment & { clientsideKey: string })[];
  logsFilter: LogFilter;
  query: string;
  selectedSteps: string[];
  logsLoading: boolean;
  onSetQuery: (v: string) => void;
  onSetSelectedSteps: (v: string[]) => void;
  onSetLogsFilter: (v: LogFilter) => void;
  onShowStateDetails: (
    stepKey: string,
    logs: RunPipelineRunEventFragment[]
  ) => void;
  getReexecutionVariables: (input: {
    run: RunFragment;
    stepKeys?: string[];
    stepQuery?: string;
    resumeRetry?: boolean;
    repositoryLocationName?: string;
    repositoryName?: string;
  }) => StartPipelineReexecutionVariables | undefined;
}

const ReexecuteWithData = ({
  run,
  allNodes,
  filteredNodes,
  logsFilter,
  logsLoading,
  query,
  selectedSteps,
  onSetLogsFilter,
  onSetQuery,
  onSetSelectedSteps,
  getReexecutionVariables
}: ReexecuteWithDataProps) => {
  const [startPipelineReexecution] = useMutation(
    START_PIPELINE_REEXECUTION_MUTATION
  );
  const [launchPipelineReexecution] = useMutation(
    LAUNCH_PIPELINE_REEXECUTION_MUTATION
  );
  const { repositoryLocation, repository } = React.useContext(
    DagsterRepositoryContext
  );
  const splitPanelContainer = React.createRef<SplitPanelContainer>();
  const stepQuery = query !== "*" ? query : "";
  const onExecute = async (stepKeys?: string[], resumeRetry?: boolean) => {
    if (!run || run.pipeline.__typename === "UnknownPipeline") return;
    const variables = getReexecutionVariables({
      run,
      stepKeys,
      stepQuery,
      resumeRetry,
      repositoryLocationName: repositoryLocation?.name,
      repositoryName: repository?.name
    });
    const result = await startPipelineReexecution({ variables });
    handleReexecutionResult(run.pipeline.name, result, {
      openInNewWindow: false
    });
  };
  const onLaunch = async (stepKeys?: string[], resumeRetry?: boolean) => {
    if (!run || run.pipeline.__typename === "UnknownPipeline") return;
    const variables = getReexecutionVariables({
      run,
      stepKeys,
      stepQuery,
      resumeRetry,
      repositoryLocationName: repositoryLocation?.name,
      repositoryName: repository?.name
    });
    const result = await launchPipelineReexecution({ variables });
    handleReexecutionResult(run.pipeline.name, result, {
      openInNewWindow: false
    });
  };

  const onClickStep = (stepKey: string, evt: React.MouseEvent<any>) => {
    const index = selectedSteps.indexOf(stepKey);
    let newSelected: string[];

    if (evt.shiftKey) {
      // shift-click to multi select steps
      newSelected = [...selectedSteps];

      if (index !== -1) {
        // deselect the step if already selected
        newSelected.splice(index, 1);
      } else {
        // select the step otherwise
        newSelected.push(stepKey);
      }
    } else {
      if (selectedSteps.length === 1 && index !== -1) {
        // deselect the step if already selected
        newSelected = [];
      } else {
        // select the step otherwise
        newSelected = [stepKey];
      }
    }

    onSetSelectedSteps(newSelected);
    onSetQuery(newSelected.join(", ") || "*");
  };

  return (
    <RunMetadataProvider logs={allNodes}>
      {metadata => (
        <SplitPanelContainer
          ref={splitPanelContainer}
          axis={"vertical"}
          identifier="run-gaant"
          firstInitialPercent={35}
          firstMinSize={40}
          first={
            run?.executionPlan ? (
              <GaantChart
                options={{
                  mode: GaantChartMode.WATERFALL_TIMED
                }}
                toolbarLeftActions={
                  <SplitPanelToggles
                    axis={"vertical"}
                    container={splitPanelContainer}
                  />
                }
                toolbarActions={
                  <RunActionButtons
                    run={run}
                    executionPlan={run.executionPlan}
                    artifactsPersisted={run.executionPlan.artifactsPersisted}
                    onExecute={onExecute}
                    onLaunch={onLaunch}
                    selectedSteps={selectedSteps}
                    selectedStepStates={selectedSteps.map(
                      selectedStep =>
                        (selectedStep && metadata.steps[selectedStep]?.state) ||
                        IStepState.PREPARING
                    )}
                  />
                }
                plan={run.executionPlan}
                metadata={metadata}
                selectedSteps={selectedSteps}
                onClickStep={onClickStep}
                onSetSelectedSteps={onSetSelectedSteps}
                query={query}
                onSetQuery={onSetQuery}
              />
            ) : (
              <NonIdealState
                icon={IconNames.ERROR}
                title="Unable to build execution plan"
              />
            )
          }
          second={
            <LogsContainer>
              <LogsToolbar
                filter={logsFilter}
                onSetFilter={onSetLogsFilter}
                steps={Object.keys(metadata.steps)}
                metadata={metadata}
              />
              <LogsScrollingTable
                nodes={filteredNodes}
                loading={logsLoading}
                filterKey={JSON.stringify(logsFilter)}
                metadata={metadata}
              />
            </LogsContainer>
          }
        />
      )}
    </RunMetadataProvider>
  );
};

const LogsContainer = styled.div`
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #f1f6f9;
`;
