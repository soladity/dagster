import * as React from "react";
import gql from "graphql-tag";
import { showCustomAlert } from "../CustomAlertProvider";
import { RunTableRunFragment } from "./types/RunTableRunFragment";
import { RunActionMenuFragment } from "./types/RunActionMenuFragment";

import { useMutation, useLazyQuery } from "react-apollo";
import {
  Button,
  Menu,
  MenuItem,
  Popover,
  MenuDivider,
  Intent,
  Tooltip,
  Position
} from "@blueprintjs/core";
import { SharedToaster } from "../DomUtils";
import { HighlightedCodeBlock } from "../HighlightedCodeBlock";
import * as qs from "query-string";
import { REEXECUTE_PIPELINE_UNKNOWN } from "./RunActionButtons";
import { DagsterRepositoryContext } from "../DagsterRepositoryContext";
import {
  LAUNCH_PIPELINE_REEXECUTION_MUTATION,
  CANCEL_MUTATION,
  DELETE_MUTATION,
  getReexecutionVariables,
  handleLaunchResult,
  RunsQueryRefetchContext
} from "./RunUtils";

export const RunActionsMenu: React.FunctionComponent<{
  run: RunTableRunFragment | RunActionMenuFragment;
}> = ({ run }) => {
  const { refetch } = React.useContext(RunsQueryRefetchContext);

  const [reexecute] = useMutation(LAUNCH_PIPELINE_REEXECUTION_MUTATION);
  const [cancel] = useMutation(CANCEL_MUTATION, { onCompleted: refetch });
  const [destroy] = useMutation(DELETE_MUTATION, { onCompleted: refetch });
  const { repositoryLocation, repository } = React.useContext(DagsterRepositoryContext);
  const [loadEnv, { called, loading, data }] = useLazyQuery(PipelineEnvironmentYamlQuery, {
    variables: { runId: run.runId }
  });

  const envYaml = data?.pipelineRunOrError?.runConfigYaml;
  const infoReady = called ? !loading : false;
  return (
    <Popover
      content={
        <Menu>
          <MenuItem
            text={loading ? "Loading Configuration..." : "View Configuration..."}
            disabled={envYaml == null}
            icon="share"
            onClick={() =>
              showCustomAlert({
                title: "Config",
                body: <HighlightedCodeBlock value={envYaml} languages={["yaml"]} />
              })
            }
          />
          <MenuDivider />

          <Tooltip
            content={OPEN_PLAYGROUND_UNKNOWN}
            position={Position.BOTTOM}
            disabled={infoReady}
            wrapperTagName="div"
          >
            <MenuItem
              text="Open in Playground..."
              disabled={!infoReady}
              icon="edit"
              target="_blank"
              href={`/pipeline/${run.pipelineName}/playground/setup?${qs.stringify({
                mode: run.mode,
                config: envYaml,
                solidSelection: run.solidSelection
              })}`}
            />
          </Tooltip>
          <Tooltip
            content={REEXECUTE_PIPELINE_UNKNOWN}
            position={Position.BOTTOM}
            disabled={infoReady}
            wrapperTagName="div"
          >
            <MenuItem
              text="Re-execute"
              disabled={!infoReady}
              icon="repeat"
              onClick={async () => {
                const result = await reexecute({
                  variables: getReexecutionVariables({
                    run,
                    envYaml,
                    repositoryLocationName: repositoryLocation?.name,
                    repositoryName: repository?.name
                  })
                });
                handleLaunchResult(run.pipelineName, result, { openInNewWindow: false });
              }}
            />
          </Tooltip>
          <MenuItem
            text="Cancel"
            icon="stop"
            disabled={!run.canTerminate}
            onClick={async () => {
              const result = await cancel({ variables: { runId: run.runId } });
              showToastFor(result.data.terminatePipelineExecution, "Run cancelled.");
            }}
          />
          <MenuDivider />
          <MenuItem
            text="Delete"
            icon="trash"
            disabled={run.canTerminate}
            onClick={async () => {
              const result = await destroy({ variables: { runId: run.runId } });
              showToastFor(result.data.deletePipelineRun, "Run deleted.");
            }}
          />
        </Menu>
      }
      position={"bottom"}
      onOpening={() => {
        if (!called) {
          loadEnv();
        }
      }}
    >
      <Button minimal={true} icon="more" />
    </Popover>
  );
};

const OPEN_PLAYGROUND_UNKNOWN =
  "Playground is unavailable because the pipeline is not present in the current repository.";

function showToastFor(
  possibleError: { __typename: string; message?: string },
  successMessage: string
) {
  if ("message" in possibleError) {
    SharedToaster.show({
      message: possibleError.message,
      icon: "error",
      intent: Intent.DANGER
    });
  } else {
    SharedToaster.show({
      message: successMessage,
      icon: "confirm",
      intent: Intent.SUCCESS
    });
  }
}

// Avoid fetching envYaml on load in Runs page. It is slow.
const PipelineEnvironmentYamlQuery = gql`
  query PipelineEnvironmentYamlQuery($runId: ID!) {
    pipelineRunOrError(runId: $runId) {
      ... on PipelineRun {
        runConfigYaml
      }
    }
  }
`;
