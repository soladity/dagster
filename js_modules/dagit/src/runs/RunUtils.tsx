import * as React from "react";

import { Colors, Spinner } from "@blueprintjs/core";

import { StartPipelineExecution } from "./types/StartPipelineExecution";
import { LaunchPipelineExecution } from "./types/LaunchPipelineExecution";
import gql from "graphql-tag";
import { showCustomAlert } from "../CustomAlertProvider";
import styled from "styled-components/macro";

export type IRunStatus =
  | "SUCCESS"
  | "NOT_STARTED"
  | "FAILURE"
  | "STARTED"
  | "MANAGED";

export function titleForRun(run: { runId: string }) {
  return run.runId.split("-").shift();
}

export function handleExecutionResult(
  pipelineName: string,
  result: void | {
    data?: StartPipelineExecution | LaunchPipelineExecution;
  },
  opts: { openInNewWindow: boolean }
) {
  if (!result || !result.data) {
    showCustomAlert({ body: `No data was returned. Did Dagit crash?` });
    return;
  }

  const obj = (result.data as StartPipelineExecution).startPipelineExecution
    ? (result.data as StartPipelineExecution).startPipelineExecution
    : (result.data as LaunchPipelineExecution).launchPipelineExecution;

  if (
    obj.__typename === "LaunchPipelineExecutionSuccess" ||
    obj.__typename === "StartPipelineExecutionSuccess"
  ) {
    const url = `/p/${obj.run.pipeline.name}/runs/${obj.run.runId}`;
    if (opts.openInNewWindow) {
      window.open(url, "_blank");
    } else {
      window.location.href = url;
    }
  } else if (obj.__typename === "PythonError") {
    console.log(obj);
    const message = `${obj.message}`;
    showCustomAlert({ body: message });
  } else {
    let message = `${pipelineName} cannot be executed with the provided config.`;

    if ("errors" in obj) {
      message += ` Please fix the following errors:\n\n${obj.errors
        .map(error => error.message)
        .join("\n\n")}`;
    }

    showCustomAlert({ body: message });
  }
}

export const RunStatus: React.SFC<{ status: IRunStatus }> = ({ status }) => {
  if (status === "STARTED") {
    return (
      <div style={{ display: "inline-block" }}>
        <Spinner size={11} />
      </div>
    );
  }
  return <RunStatusDot status={status} />;
};

// eslint-disable-next-line no-unexpected-multiline
const RunStatusDot = styled.div<{ status: IRunStatus }>`
  display: inline-block;
  width: 11px;
  height: 11px;
  border-radius: 5.5px;
  align-self: center;
  transition: background 200ms linear;
  background: ${({ status }) =>
    ({
      NOT_STARTED: Colors.GRAY1,
      MANAGED: Colors.GRAY3,
      STARTED: Colors.GRAY3,
      SUCCESS: Colors.GREEN2,
      FAILURE: Colors.RED3
    }[status])};
  &:hover {
    background: ${({ status }) =>
      ({
        NOT_STARTED: Colors.GRAY1,
        STARTED: Colors.GRAY3,
        SUCCESS: Colors.GREEN2,
        FAILURE: Colors.RED5
      }[status])};
  }
`;

export const START_PIPELINE_EXECUTION_MUTATION = gql`
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
      ... on PythonError {
        message
        stack
      }
    }
  }
`;

export const LAUNCH_PIPELINE_EXECUTION_MUTATION = gql`
  mutation LaunchPipelineExecution($executionParams: ExecutionParams!) {
    launchPipelineExecution(executionParams: $executionParams) {
      __typename
      ... on LaunchPipelineExecutionSuccess {
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
      ... on PythonError {
        message
        stack
      }
    }
  }
`;

export const DELETE_MUTATION = gql`
  mutation Delete($runId: String!) {
    deletePipelineRun(runId: $runId) {
      __typename
      ... on PythonError {
        message
      }
      ... on PipelineRunNotFoundError {
        message
      }
    }
  }
`;

export const CANCEL_MUTATION = gql`
  mutation Cancel($runId: String!) {
    cancelPipelineExecution(runId: $runId) {
      __typename
      ... on CancelPipelineExecutionFailure {
        message
      }
      ... on PipelineRunNotFoundError {
        message
      }
      ... on CancelPipelineExecutionSuccess {
        run {
          runId
          canCancel
        }
      }
    }
  }
`;
