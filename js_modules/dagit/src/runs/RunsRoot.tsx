import * as React from "react";

import Loading from "../Loading";
import { RouteComponentProps } from "react-router";
import { RunTable } from "./RunTable";
import { RunsQueryRefetchContext } from "./RunUtils";
import { RunsRootQuery, RunsRootQueryVariables } from "./types/RunsRootQuery";
import { RunsFilter, runsFilterForSearchTokens, useRunFiltering } from "./RunsFilter";

import gql from "graphql-tag";
import { IconNames } from "@blueprintjs/icons";
import { NonIdealState } from "@blueprintjs/core";
import { ScrollContainer, Header } from "../ListComponents";
import styled from "styled-components/macro";
import { useCursorPaginatedQuery } from "./useCursorPaginatedQuery";
import { CursorPaginationControls } from "../CursorPaginationControls";

const PAGE_SIZE = 25;

export const RunsRoot: React.FunctionComponent<RouteComponentProps> = () => {
  const [filterTokens, setFilterTokens] = useRunFiltering();
  const { queryResult, paginationProps } = useCursorPaginatedQuery<
    RunsRootQuery,
    RunsRootQueryVariables
  >({
    nextCursorForResult: runs => {
      if (runs.pipelineRunsOrError.__typename !== "PipelineRuns") return undefined;
      return runs.pipelineRunsOrError.results[PAGE_SIZE]?.runId;
    },
    variables: { filter: runsFilterForSearchTokens(filterTokens) },
    query: RUNS_ROOT_QUERY,
    pageSize: PAGE_SIZE
  });

  return (
    <RunsQueryRefetchContext.Provider value={{ refetch: queryResult.refetch }}>
      <ScrollContainer>
        <div
          style={{
            display: "flex",
            alignItems: "baseline",
            justifyContent: "space-between"
          }}
        >
          <Header>All Runs</Header>
          <Filters>
            <RunsFilter
              tokens={filterTokens}
              onChange={setFilterTokens}
              loading={queryResult.loading}
            />
          </Filters>
        </div>

        <Loading queryResult={queryResult} allowStaleData={true}>
          {({ pipelineRunsOrError }) => {
            if (pipelineRunsOrError.__typename !== "PipelineRuns") {
              return (
                <NonIdealState
                  icon={IconNames.ERROR}
                  title="Query Error"
                  description={pipelineRunsOrError.message}
                />
              );
            }
            return (
              <>
                <RunTable
                  runs={pipelineRunsOrError.results.slice(0, PAGE_SIZE)}
                  onSetFilter={setFilterTokens}
                />
                <CursorPaginationControls {...paginationProps} />
              </>
            );
          }}
        </Loading>
      </ScrollContainer>
    </RunsQueryRefetchContext.Provider>
  );
};

export const RUNS_ROOT_QUERY = gql`
  query RunsRootQuery($limit: Int, $cursor: String, $filter: PipelineRunsFilter!) {
    pipelineRunsOrError(limit: $limit, cursor: $cursor, filter: $filter) {
      ... on PipelineRuns {
        results {
          ...RunTableRunFragment
        }
      }
      ... on InvalidPipelineRunsFilterError {
        message
      }
      ... on PythonError {
        message
      }
    }
  }

  ${RunTable.fragments.RunTableRunFragment}
`;

const Filters = styled.div`
  float: right;
  display: flex;
  align-items: center;
  margin-bottom: 14px;
`;
