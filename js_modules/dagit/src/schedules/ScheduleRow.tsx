import * as React from "react";
import * as qs from "query-string";
import { useMutation } from "@apollo/react-hooks";

import {
  Button,
  Classes,
  Colors,
  Switch,
  Icon,
  Menu,
  MenuItem,
  MenuDivider,
  Popover,
  Tooltip,
  Tag,
  Intent
} from "@blueprintjs/core";
import { HighlightedCodeBlock } from "../HighlightedCodeBlock";
import { RowColumn, RowContainer } from "../ListComponents";
import { RunStatus, titleForRun } from "../runs/RunUtils";
import { ScheduleFragment } from "./types/ScheduleFragment";
import { ScheduleStatus, ScheduleAttemptStatus } from "../types/globalTypes";
import { Link, useRouteMatch } from "react-router-dom";
import cronstrue from "cronstrue";
import gql from "graphql-tag";
import { showCustomAlert } from "../CustomAlertProvider";
import styled from "styled-components";
import { copyValue, unixTimestampToString } from "../Util";

const NUM_RUNS_TO_DISPLAY = 10;

export const ScheduleRow: React.FunctionComponent<{
  schedule: ScheduleFragment;
}> = ({ schedule }) => {
  const {
    id,
    status,
    scheduleDefinition,
    logsPath,
    attempts,
    attemptsCount
  } = schedule;
  const {
    name,
    cronSchedule,
    executionParamsString,
    environmentConfigYaml
  } = scheduleDefinition;
  const executionParams = JSON.parse(executionParamsString);
  const pipelineName = executionParams.selector.name;
  const mode = executionParams.mode;

  const [startSchedule] = useMutation(START_SCHEDULE_MUTATION);
  const [stopSchedule] = useMutation(STOP_SCHEDULE_MUTATION);
  const match = useRouteMatch("/schedule/:scheduleName");

  const mostRecentAttempt = attempts.length > 0 ? attempts[0] : null;
  const mostRecentAttemptLogError = mostRecentAttempt
    ? JSON.parse(mostRecentAttempt.jsonResult)
    : null;

  const getNaturalLanguageCronString = (cronSchedule: string) => {
    try {
      return cronstrue.toString(cronSchedule);
    } catch {
      return "Invalid cron string";
    }
  };

  const displayName = match ? (
    <ScheduleName>{name}</ScheduleName>
  ) : (
    <Link to={`/schedule/${name}`}>
      <ScheduleName>{name}</ScheduleName>
    </Link>
  );

  return (
    <RowContainer key={name}>
      <RowColumn style={{ maxWidth: 60, paddingLeft: 0, textAlign: "center" }}>
        <Switch
          checked={status === ScheduleStatus.RUNNING}
          large={true}
          innerLabelChecked="on"
          innerLabel="off"
          onChange={() => {
            if (status === ScheduleStatus.RUNNING) {
              stopSchedule({
                variables: { scheduleName: name },
                optimisticResponse: {
                  stopRunningSchedule: {
                    __typename: "RunningScheduleResult",
                    schedule: {
                      id: id,
                      __typename: "RunningSchedule",
                      status: ScheduleStatus.STOPPED
                    }
                  }
                }
              });
            } else {
              startSchedule({
                variables: { scheduleName: name },
                optimisticResponse: {
                  startSchedule: {
                    __typename: "RunningScheduleResult",
                    schedule: {
                      id: id,
                      __typename: "RunningSchedule",
                      status: ScheduleStatus.RUNNING
                    }
                  }
                }
              });
            }
          }}
        />
      </RowColumn>
      <RowColumn style={{ flex: 1.4 }}>{displayName}</RowColumn>
      <RowColumn>
        <Link to={`/p/${pipelineName}/explore/`}>
          <Icon icon="diagram-tree" /> {pipelineName}
        </Link>
      </RowColumn>
      <RowColumn
        style={{
          maxWidth: 150
        }}
      >
        {cronSchedule ? (
          <Tooltip
            className={Classes.TOOLTIP_INDICATOR}
            position={"top"}
            content={cronSchedule}
          >
            {getNaturalLanguageCronString(cronSchedule)}
          </Tooltip>
        ) : (
          "-"
        )}
      </RowColumn>
      <RowColumn style={{ flex: 1 }}>
        {attempts && attempts.length > 0
          ? attempts.slice(0, NUM_RUNS_TO_DISPLAY).map((attempt, i) => (
              <div
                style={{
                  display: "inline-block",
                  cursor: "pointer",
                  marginRight: 5
                }}
                key={i}
              >
                {attempt.run ? (
                  <Link
                    to={`/p/${attempt.run.pipeline.name}/runs/${attempt.run.runId}`}
                  >
                    <Tooltip
                      position={"top"}
                      content={titleForRun(attempt.run)}
                      wrapperTagName="div"
                      targetTagName="div"
                    >
                      <RunStatus status={attempt.run.status} />
                    </Tooltip>
                  </Link>
                ) : (
                  <span
                    onClick={() =>
                      showCustomAlert({
                        title: "Schedule Response",
                        body: (
                          <>
                            <HighlightedCodeBlock
                              value={JSON.stringify(
                                JSON.parse(attempt.jsonResult),
                                null,
                                2
                              )}
                              languages={["json"]}
                            />
                          </>
                        )
                      })
                    }
                  >
                    <Tooltip
                      position={"top"}
                      content="View scheduling error"
                      wrapperTagName="div"
                      targetTagName="div"
                    >
                      <AttemptStatus status={attempt.status} />
                    </Tooltip>
                  </span>
                )}
              </div>
            ))
          : "-"}
        {attemptsCount > NUM_RUNS_TO_DISPLAY && (
          <Link
            to={`/schedule/${encodeURIComponent(
              schedule.scheduleDefinition.name
            )}`}
            style={{ verticalAlign: "top" }}
          >
            {" "}
            +{attemptsCount - NUM_RUNS_TO_DISPLAY} more
          </Link>
        )}
      </RowColumn>
      <RowColumn style={{ flex: 1 }}>
        {mostRecentAttempt
          ? unixTimestampToString(mostRecentAttempt.time)
          : "-"}

        {mostRecentAttempt &&
          mostRecentAttempt.status === ScheduleAttemptStatus.ERROR && (
            <ErrorTag>
              <Tag intent={Intent.WARNING}>
                Latest run failed:
                <ButtonLink
                  onClick={() =>
                    showCustomAlert({
                      title: "Error",
                      body: (
                        <>
                          <ErrorHeader>
                            {mostRecentAttemptLogError.__typename}
                          </ErrorHeader>
                          <ErrorWrapper>
                            <HighlightedCodeBlock
                              value={JSON.stringify(
                                mostRecentAttemptLogError,
                                null,
                                2
                              )}
                              languages={["json"]}
                            />
                          </ErrorWrapper>
                        </>
                      )
                    })
                  }
                >
                  View Error
                </ButtonLink>
              </Tag>
            </ErrorTag>
          )}
      </RowColumn>
      <RowColumn
        style={{
          display: "flex",
          alignItems: "flex-start",
          flex: 1
        }}
      >
        <div style={{ flex: 1 }}>
          <div>{`Mode: ${mode}`}</div>
        </div>
        <Popover
          content={
            <Menu>
              <MenuItem
                text="View Configuration..."
                icon="share"
                onClick={() =>
                  showCustomAlert({
                    title: "Config",
                    body: (
                      <HighlightedCodeBlock
                        value={environmentConfigYaml}
                        languages={["yaml"]}
                      />
                    )
                  })
                }
              />
              <MenuItem
                text="Open in Execute Tab..."
                icon="edit"
                target="_blank"
                href={`/p/${
                  executionParams.selector.name
                }/execute/setup?${qs.stringify({
                  mode: executionParams.mode,
                  config: environmentConfigYaml,
                  solidSubset: executionParams.selector.solidSubset
                })}`}
              />
              <MenuDivider />
              <MenuItem
                text="Copy Path to Debug Logs"
                icon="clipboard"
                onClick={(e: React.MouseEvent<any>) => copyValue(e, logsPath)}
              />
            </Menu>
          }
          position={"bottom"}
        >
          <Button minimal={true} icon="chevron-down" />
        </Popover>
      </RowColumn>
    </RowContainer>
  );
};

export const ScheduleRowFragment = gql`
  fragment ScheduleFragment on RunningSchedule {
    id
    scheduleDefinition {
      name
      executionParamsString
      environmentConfigYaml
      cronSchedule
    }
    logsPath
    attempts(limit: $limit) {
      run {
        runId
        pipeline {
          name
        }
        status
      }
      time
      jsonResult
      status
    }
    attemptsCount
    status
  }
`;

const ScheduleName = styled.pre`
  margin: 0;
`;

const ErrorHeader = styled.h3`
  color: #b05c47;
  font-weight: 400;
  margin: 0.5em 0 0.25em;
`;

const ErrorWrapper = styled.pre`
  background-color: rgba(206, 17, 38, 0.05);
  border: 1px solid #d17257;
  border-radius: 3px;
  max-width: 90vw;
  padding: 1em 2em;
`;

const ErrorTag = styled.div`
  display: block;
  margin-top: 5px;
`;

const ButtonLink = styled.button`
  color: #ffffff;
  margin-left: 10px;
  font-size: 12px;
  background: none!important;
  border: none;
  padding: 0!important;
  font-family: inherit;
  cursor: pointer;
  text-decoration: underline;
  &: hover {
    color: #cccccc;
  }
}
`;

const START_SCHEDULE_MUTATION = gql`
  mutation StartSchedule($scheduleName: String!) {
    startSchedule(scheduleName: $scheduleName) {
      schedule {
        id
        status
      }
    }
  }
`;

const STOP_SCHEDULE_MUTATION = gql`
  mutation StopSchedule($scheduleName: String!) {
    stopRunningSchedule(scheduleName: $scheduleName) {
      schedule {
        id
        status
      }
    }
  }
`;

export const AttemptStatus = styled.div<{ status: ScheduleAttemptStatus }>`
  display: inline-block;
  width: 11px;
  height: 11px;
  border-radius: 5.5px;
  align-self: center;
  transition: background 200ms linear;
  background: ${({ status }) =>
    ({
      [ScheduleAttemptStatus.SUCCESS]: Colors.GREEN2,
      [ScheduleAttemptStatus.ERROR]: Colors.RED3,
      [ScheduleAttemptStatus.SKIPPED]: Colors.GOLD3
    }[status])};
  &:hover {
    background: ${({ status }) =>
      ({
        [ScheduleAttemptStatus.SUCCESS]: Colors.GREEN2,
        [ScheduleAttemptStatus.ERROR]: Colors.RED3,
        [ScheduleAttemptStatus.SKIPPED]: Colors.GOLD3
      }[status])};
  }
`;
