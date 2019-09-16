import * as React from "react";
import * as qs from "query-string";

import {
  Button,
  ButtonGroup,
  Icon,
  Menu,
  MenuItem,
  NonIdealState,
  Popover,
  Position,
  Spinner,
  Colors,
  InputGroup
} from "@blueprintjs/core";
import {
  Details,
  Header,
  Legend,
  LegendColumn,
  RowColumn,
  RowContainer,
  ScrollContainer
} from "../ListComponents";
import { IRunStatus, RunStatus, titleForRun } from "./RunUtils";
import { formatElapsedTime, formatStepKey } from "../Util";

import { HighlightedCodeBlock } from "../HighlightedCodeBlock";
import { Link } from "react-router-dom";
import { RunHistoryRunFragment } from "./types/RunHistoryRunFragment";
import gql from "graphql-tag";
import { showCustomAlert } from "../CustomAlertProvider";
import { IconNames } from "@blueprintjs/icons";
import styled from "styled-components";

function dateString(timestamp: number) {
  if (timestamp === 0) {
    return null;
  }
  return new Date(timestamp).toLocaleString();
}

function getStartTime(run: RunHistoryRunFragment) {
  for (const log of run.logs.nodes) {
    if (log.__typename === "PipelineStartEvent") {
      return Number(log.timestamp);
    }
  }
  return 0;
}

function getEndTime(run: RunHistoryRunFragment) {
  for (const log of run.logs.nodes) {
    if (
      log.__typename === "PipelineSuccessEvent" ||
      log.__typename === "PipelineFailureEvent"
    ) {
      return Number(log.timestamp);
    }
  }
  return 0;
}

function getDetailedStats(run: RunHistoryRunFragment) {
  // 18 steps succeeded, 3 steps failed, 4 materializations 10 expectations, etc.
  const stats = {
    stepsSucceeded: 0,
    stepsFailed: 0,
    materializations: 0,
    expectationsSucceeded: 0,
    expectationsFailed: 0
  };
  for (const log of run.logs.nodes) {
    if (log.__typename === "ExecutionStepFailureEvent") {
      stats.stepsFailed += 1;
    }
    if (log.__typename === "ExecutionStepSuccessEvent") {
      stats.stepsSucceeded += 1;
    }
    if (log.__typename === "StepMaterializationEvent") {
      stats.materializations += 1;
    }
    if (log.__typename === "StepExpectationResultEvent") {
      if (log.expectationResult.success) {
        stats.expectationsSucceeded += 1;
      } else {
        stats.expectationsFailed += 1;
      }
    }
  }
  return stats;
}

enum RunSort {
  START_TIME_ASC,
  START_TIME_DSC,
  END_TIME_ASC,
  END_TIME_DSC
}

const AllRunStatuses: IRunStatus[] = [
  "NOT_STARTED",
  "STARTED",
  "SUCCESS",
  "FAILURE"
];

function sortLabel(sort: RunSort) {
  switch (sort) {
    case RunSort.START_TIME_ASC:
      return "Start Time (Asc)";
    case RunSort.START_TIME_DSC:
      return "Start Time (Desc)";
    case RunSort.END_TIME_ASC:
      return "End Time (Asc)";
    case RunSort.END_TIME_DSC:
      return "End Time (Desc)";
  }
}

interface RunHistoryProps {
  runs: RunHistoryRunFragment[];
  initialSearch: string;
}

interface RunHistoryState {
  sort: RunSort;
  search: string;
  statuses: IRunStatus[];
}

export default class RunHistory extends React.Component<
  RunHistoryProps,
  RunHistoryState
> {
  static fragments = {
    RunHistoryRunFragment: gql`
      fragment RunHistoryRunFragment on PipelineRun {
        runId
        status
        stepKeysToExecute
        mode
        environmentConfigYaml
        pipeline {
          name
        }
        logs {
          nodes {
            __typename
            ... on MessageEvent {
              timestamp
            }
            ... on StepExpectationResultEvent {
              expectationResult {
                success
              }
            }
          }
        }
        executionPlan {
          steps {
            key
          }
        }
      }
    `
  };

  constructor(props: RunHistoryProps) {
    super(props);
    this.state = {
      sort: RunSort.START_TIME_DSC,
      search: props.initialSearch,
      statuses: AllRunStatuses
    };
  }

  sortRuns = (runs: RunHistoryRunFragment[]) => {
    const sortType = this.state.sort;
    if (sortType === null) {
      return runs;
    }

    return runs.sort((a, b) => {
      switch (sortType) {
        case RunSort.START_TIME_ASC:
          return getStartTime(a) - getStartTime(b);
        case RunSort.START_TIME_DSC:
          return getStartTime(b) - getStartTime(a);
        case RunSort.END_TIME_ASC:
          return getEndTime(a) - getEndTime(b);
        case RunSort.END_TIME_DSC:
        default:
          return getEndTime(b) - getEndTime(a);
      }
    });
  };

  render() {
    const { runs } = this.props;
    const { statuses, search, sort } = this.state;

    const searchKeywords = search.split(" ");
    const matchesAnyKeyword = (str: string) =>
      searchKeywords.length ? searchKeywords.some(k => str.includes(k)) : true;

    const mostRecentRun = runs[runs.length - 1];
    const sortedRuns = this.sortRuns(runs.slice(0, runs.length - 1))
      .filter(r => statuses.includes(r.status))
      .filter(r =>
        [r.runId, r.mode, r.pipeline.name, ...(r.stepKeysToExecute || [])].some(
          matchesAnyKeyword
        )
      );

    return (
      <ScrollContainer>
        {runs.length === 0 ? (
          <div style={{ marginTop: 100 }}>
            <NonIdealState
              icon="history"
              title="Pipeline Runs"
              description="No runs to display. Use the Execute tab to start a pipeline."
            />
          </div>
        ) : (
          <>
            <MostRecentRun run={mostRecentRun} />
            <RunTable
              runs={sortedRuns}
              sort={sort}
              search={search}
              statuses={statuses}
              onSetSort={sort => this.setState({ sort })}
              onSetStatuses={statuses => this.setState({ statuses })}
              onSetSearch={search => this.setState({ search })}
            />
          </>
        )}
      </ScrollContainer>
    );
  }
}

const MostRecentRun: React.FunctionComponent<{
  run: RunHistoryRunFragment;
}> = ({ run }) => (
  <div>
    <Header style={{ marginTop: 0 }}>Most Recent Run</Header>
    <RunRow run={run} />
  </div>
);

interface RunTableProps {
  runs: RunHistoryRunFragment[];
  sort: RunSort;
  search: string;
  statuses: IRunStatus[];
  onSetStatuses: (statuses: IRunStatus[]) => void;
  onSetSort: (sort: RunSort) => void;
  onSetSearch: (filter: string) => void;
}

const RunTable: React.FunctionComponent<RunTableProps> = props => (
  <div>
    <div
      style={{
        display: "flex",
        alignItems: "baseline",
        justifyContent: "space-between"
      }}
    >
      <Header>{`Previous Runs (${props.runs.length})`}</Header>
      <Filters>
        <ButtonGroup style={{ marginRight: 15 }}>
          {AllRunStatuses.map(s => (
            <Button
              key={s}
              active={props.statuses.includes(s)}
              onClick={() =>
                props.onSetStatuses(
                  props.statuses.includes(s)
                    ? props.statuses.filter(a => a !== s)
                    : props.statuses.concat([s])
                )
              }
            >
              {s === "STARTED" ? (
                <Spinner size={11} value={0.4} />
              ) : (
                <RunStatus status={s} />
              )}
            </Button>
          ))}
        </ButtonGroup>

        <FilterInputGroup
          leftIcon="filter"
          placeholder="Filter runs..."
          value={props.search}
          spellCheck={false}
          rightElement={
            props.search.length ? (
              <Icon
                color={Colors.GRAY1}
                icon={IconNames.SMALL_CROSS}
                style={{ padding: 7 }}
                onClick={() => props.onSetSearch("")}
              />
            ) : (
              undefined
            )
          }
          onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
            props.onSetSearch(e.target.value)
          }
        />

        <Popover
          position={Position.BOTTOM_RIGHT}
          content={
            <Menu>
              {[
                RunSort.START_TIME_ASC,
                RunSort.START_TIME_DSC,
                RunSort.END_TIME_ASC,
                RunSort.END_TIME_DSC
              ].map((v, idx) => (
                <MenuItem
                  key={idx}
                  text={sortLabel(v)}
                  onClick={() => props.onSetSort(v)}
                />
              ))}
            </Menu>
          }
        >
          <Button
            icon={"sort"}
            rightIcon={"caret-down"}
            text={sortLabel(props.sort)}
          />
        </Popover>
      </Filters>
    </div>
    <Legend>
      <LegendColumn style={{ maxWidth: 40 }}></LegendColumn>
      <LegendColumn style={{ flex: 2.3 }}>Run</LegendColumn>
      <LegendColumn>Pipeline</LegendColumn>
      <LegendColumn>Execution Params</LegendColumn>
      <LegendColumn style={{ flex: 1.6 }}>Timing</LegendColumn>
    </Legend>
    {props.runs.map(run => (
      <RunRow run={run} key={run.runId} />
    ))}
  </div>
);

const RunRow: React.FunctionComponent<{ run: RunHistoryRunFragment }> = ({
  run
}) => {
  const start = getStartTime(run);
  const end = getEndTime(run);
  const stats = getDetailedStats(run);

  return (
    <RowContainer key={run.runId}>
      <RowColumn style={{ maxWidth: 30, paddingLeft: 0, textAlign: "center" }}>
        <RunStatus status={start && end ? run.status : "STARTED"} />
      </RowColumn>
      <RowColumn style={{ flex: 2.4 }}>
        <Link
          style={{ display: "block" }}
          to={`/p/${run.pipeline.name}/runs/${run.runId}`}
        >
          {titleForRun(run)}
        </Link>
        <Details>
          {`${stats.stepsSucceeded}/${stats.stepsSucceeded +
            stats.stepsFailed} steps succeeded, `}
          <Link
            to={`/p/${run.pipeline.name}/runs/${run.runId}?q=type:materialization`}
          >{`${stats.materializations} materializations`}</Link>
          ,{" "}
          <Link
            to={`/p/${run.pipeline.name}/runs/${run.runId}?q=type:expectation`}
          >{`${stats.expectationsSucceeded}/${stats.expectationsSucceeded +
            stats.expectationsFailed} expectations passed`}</Link>
        </Details>
      </RowColumn>
      <RowColumn>
        <Link
          style={{ display: "block" }}
          to={`/p/${run.pipeline.name}/explore/`}
        >
          <Icon icon="diagram-tree" /> {run.pipeline.name}
        </Link>
      </RowColumn>
      <RowColumn
        style={{
          display: "flex",
          alignItems: "flex-start"
        }}
      >
        <div
          style={{
            flex: 1
          }}
        >
          <div>{`Mode: ${run.mode}`}</div>

          {run.stepKeysToExecute && (
            <div>
              {run.stepKeysToExecute.length === 1
                ? `Step: ${run.stepKeysToExecute.join("")}`
                : `${run.stepKeysToExecute.length} Steps`}
            </div>
          )}
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
                        value={run.environmentConfigYaml}
                        languages={["yaml"]}
                      />
                    )
                  })
                }
              />
              <MenuItem
                text="Open in Execute View..."
                icon="edit"
                target="_blank"
                href={`/p/${run.pipeline.name}/execute/setup?${qs.stringify({
                  mode: run.mode,
                  config: run.environmentConfigYaml,
                  solidSubset: run.stepKeysToExecute
                    ? run.stepKeysToExecute.map(formatStepKey)
                    : undefined
                })}`}
              />
            </Menu>
          }
          position={"bottom"}
        >
          <Button minimal={true} icon="chevron-down" />
        </Popover>
      </RowColumn>
      <RowColumn style={{ flex: 1.6 }}>
        {start ? (
          <div style={{ marginBottom: 4 }}>
            <Icon icon="calendar" /> {dateString(start)}
            <Icon
              icon="arrow-right"
              style={{ marginLeft: 10, marginRight: 10 }}
            />
            {dateString(end)}
          </div>
        ) : (
          <div style={{ marginBottom: 4 }}>
            <Icon icon="calendar" /> Starting...
          </div>
        )}
        <RunTime start={start} end={end} />
      </RowColumn>
    </RowContainer>
  );
};

class RunTime extends React.Component<{ start: number; end: number }> {
  _interval?: NodeJS.Timer;
  _timeout?: NodeJS.Timer;

  componentDidMount() {
    if (this.props.end !== 0) return;

    // align to the next second and then update every second so the elapsed
    // time "ticks" up. Our render method uses Date.now(), so all we need to
    // do is force another React render. We could clone the time into React
    // state but that is a bit messier.
    setTimeout(() => {
      this.forceUpdate();
      this._interval = setInterval(() => this.forceUpdate(), 1000);
    }, Date.now() % 1000);
  }

  componentWillUnmount() {
    if (this._timeout) clearInterval(this._timeout);
    if (this._interval) clearInterval(this._interval);
  }

  render() {
    const start = this.props.start;
    const end = this.props.end || Date.now();

    return (
      <div>
        <Icon icon="time" /> {start ? formatElapsedTime(end - start) : ""}
      </div>
    );
  }
}

const FilterInputGroup = styled(InputGroup)`
  width: 220px;
  margin-right: 10px;
`;

const Filters = styled.div`
  float: right;
  display: flex;
  align-items: center;
  margin-bottom: 14px;
`;
