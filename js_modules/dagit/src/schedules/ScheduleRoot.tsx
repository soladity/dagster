import * as React from "react";

import {
  Header,
  ScrollContainer,
  RowColumn,
  RowContainer
} from "../ListComponents";
import { Query, QueryResult } from "react-apollo";
import {
  ScheduleRootQuery,
  ScheduleRootQuery_scheduleOrError_RunningSchedule_ticksList,
  ScheduleRootQuery_scheduleOrError_RunningSchedule_ticksList_tickSpecificData
} from "./types/ScheduleRootQuery";
import Loading from "../Loading";
import gql from "graphql-tag";
import { RouteComponentProps } from "react-router";
import { ScheduleRow, ScheduleRowFragment } from "./ScheduleRow";

import { showCustomAlert } from "../CustomAlertProvider";
import { unixTimestampToString, assertUnreachable } from "../Util";
import { ScheduleTickStatus } from "../types/globalTypes";
import { Intent, Tag, AnchorButton } from "@blueprintjs/core";
import { __RouterContext as RouterContext } from "react-router";
import PythonErrorInfo from "../PythonErrorInfo";
import * as querystring from "query-string";
import { PartitionView } from "./PartitionView";
import { RunStatus } from "../runs/RunUtils";

const NUM_RUNS_TO_DISPLAY = 10;
const NUM_TICKS_TO_TO_DISPLAY = 5;

export const ScheduleRoot: React.FunctionComponent<RouteComponentProps<{
  scheduleName: string;
}>> = ({ match, location }) => {
  const { scheduleName } = match.params;

  const { history } = React.useContext(RouterContext);
  const qs = querystring.parse(location.search);
  const cursor = (qs.cursor as string) || undefined;
  const setCursor = (cursor: string | undefined) => {
    history.push({ search: `?${querystring.stringify({ ...qs, cursor })}` });
  };

  return (
    <Query
      query={SCHEDULE_ROOT_QUERY}
      variables={{
        scheduleName,
        limit: NUM_RUNS_TO_DISPLAY,
        ticksLimit: NUM_TICKS_TO_TO_DISPLAY
      }}
      fetchPolicy="cache-and-network"
      pollInterval={15 * 1000}
      partialRefetch={true}
    >
      {(queryResult: QueryResult<ScheduleRootQuery, any>) => (
        <Loading queryResult={queryResult} allowStaleData={true}>
          {result => {
            const { scheduleOrError } = result;

            if (scheduleOrError.__typename === "RunningSchedule") {
              const partitionSetName =
                scheduleOrError.scheduleDefinition.partitionSet?.name;
              return (
                <ScrollContainer>
                  <Header>Schedules</Header>
                  <ScheduleRow schedule={scheduleOrError} />
                  <TicksTable ticks={scheduleOrError.ticksList} />
                  {partitionSetName ? (
                    <PartitionView
                      partitionSetName={partitionSetName}
                      cursor={cursor}
                      setCursor={setCursor}
                    />
                  ) : null}
                </ScrollContainer>
              );
            } else {
              return null;
            }
          }}
        </Loading>
      )}
    </Query>
  );
};

const RenderEventSpecificData: React.FunctionComponent<{
  data: ScheduleRootQuery_scheduleOrError_RunningSchedule_ticksList_tickSpecificData | null;
}> = ({ data }) => {
  if (!data) {
    return null;
  }

  switch (data.__typename) {
    case "ScheduleTickFailureData":
      return (
        <AnchorButton
          minimal={true}
          onClick={() =>
            showCustomAlert({
              title: "Schedule Response",
              body: (
                <>
                  <PythonErrorInfo error={data.error} />
                </>
              )
            })
          }
        >
          <Tag fill={true} minimal={true} intent={Intent.DANGER}>
            See Error
          </Tag>
        </AnchorButton>
      );
    case "ScheduleTickSuccessData":
      return (
        <AnchorButton
          minimal={true}
          href={`/runs/${data.run?.pipeline.name}/${data.run?.runId}`}
        >
          <div style={{ display: "flex" }}>
            {data.run?.status && <RunStatus status={data.run?.status} />}
            <Tag fill={true} minimal={true} style={{ marginLeft: 10 }}>
              Run {data.run?.runId}
            </Tag>
          </div>
        </AnchorButton>
      );
  }
};

const TickTag: React.FunctionComponent<{ status: ScheduleTickStatus }> = ({
  status
}) => {
  switch (status) {
    case ScheduleTickStatus.STARTED:
      return (
        <Tag minimal={true} intent={Intent.PRIMARY}>
          Started
        </Tag>
      );
    case ScheduleTickStatus.SUCCESS:
      return (
        <Tag minimal={true} intent={Intent.SUCCESS}>
          Success
        </Tag>
      );
    case ScheduleTickStatus.SKIPPED:
      return (
        <Tag minimal={true} intent={Intent.WARNING}>
          Skipped
        </Tag>
      );
    case ScheduleTickStatus.FAILURE:
      return (
        <Tag minimal={true} intent={Intent.DANGER}>
          Failure
        </Tag>
      );
    default:
      return assertUnreachable(status);
  }
};

const TicksTable: React.FunctionComponent<{
  ticks: ScheduleRootQuery_scheduleOrError_RunningSchedule_ticksList[];
}> = ({ ticks }) => {
  return ticks && ticks.length ? (
    <div style={{ marginTop: 25 }}>
      <Header>Schedule Attempts Log</Header>
      <div>
        {ticks.map((tick, i) => {
          return (
            <RowContainer key={i}>
              <RowColumn>
                {unixTimestampToString(tick.timestamp)}
                <div style={{ marginLeft: 20, display: "inline" }}>
                  <TickTag status={tick.status} />
                </div>
              </RowColumn>
              <RowColumn>
                <RenderEventSpecificData data={tick.tickSpecificData} />
              </RowColumn>
            </RowContainer>
          );
        })}
      </div>
    </div>
  ) : null;
};

export const SCHEDULE_ROOT_QUERY = gql`
  query ScheduleRootQuery(
    $scheduleName: String!
    $limit: Int!
    $ticksLimit: Int!
  ) {
    scheduleOrError(scheduleName: $scheduleName) {
      ... on RunningSchedule {
        ...ScheduleFragment
        scheduleDefinition {
          name
          cronSchedule
          partitionSet {
            name
          }
        }
        ticksList: ticks(limit: $ticksLimit) {
          tickId
          status
          timestamp
          tickSpecificData {
            __typename
            ... on ScheduleTickSuccessData {
              run {
                pipeline {
                  name
                }
                status
                runId
              }
            }
            ... on ScheduleTickFailureData {
              error {
                ...PythonErrorFragment
              }
            }
          }
        }
      }
      ... on ScheduleNotFoundError {
        message
      }
      ... on PythonError {
        message
        stack
      }
    }
  }

  ${ScheduleRowFragment}
  ${PythonErrorInfo.fragments.PythonErrorFragment}
`;
