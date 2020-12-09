import {gql, useQuery} from '@apollo/client';
import {
  Tag,
  Tooltip,
  Dialog,
  Button,
  Intent,
  NonIdealState,
  Classes,
  Colors,
  Spinner,
} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import * as React from 'react';
import styled from 'styled-components/macro';

import {showCustomAlert} from 'src/CustomAlertProvider';
import {PythonErrorInfo} from 'src/PythonErrorInfo';
import {assertUnreachable} from 'src/Util';
import {RunTable} from 'src/runs/RunTable';
import {LaunchedRunListQuery, LaunchedRunListQueryVariables} from 'src/types/LaunchedRunListQuery';
import {TickTagFragment} from 'src/types/TickTagFragment';
import {JobTickStatus, JobType} from 'src/types/globalTypes';
import {Box} from 'src/ui/Box';
import {ButtonLink} from 'src/ui/ButtonLink';

export const TickTag: React.FunctionComponent<{
  tick: TickTagFragment;
  jobType: JobType;
}> = ({tick, jobType}) => {
  const [open, setOpen] = React.useState<boolean>(false);
  switch (tick.status) {
    case JobTickStatus.STARTED:
      return (
        <Tag minimal={true} intent={Intent.NONE}>
          Started
        </Tag>
      );
    case JobTickStatus.SUCCESS:
      if (!tick.runs.length) {
        return (
          <Tag minimal={true} intent={Intent.PRIMARY}>
            Requested
          </Tag>
        );
      }
      return (
        <>
          <Tag minimal={true} intent={Intent.PRIMARY} interactive={true}>
            <ButtonLink underline="never" onClick={() => setOpen(true)}>
              {tick.runs.length} Requested
            </ButtonLink>
          </Tag>
          <Dialog
            isOpen={open}
            onClose={() => setOpen(false)}
            style={{width: '90vw'}}
            title={`Launched runs`}
          >
            <Box background={Colors.WHITE} padding={16} margin={{bottom: 16}}>
              {open && <RunList runIds={tick.runs.map((x) => x.id)} />}
            </Box>
            <div className={Classes.DIALOG_FOOTER}>
              <div className={Classes.DIALOG_FOOTER_ACTIONS}>
                <Button intent="primary" onClick={() => setOpen(false)}>
                  OK
                </Button>
              </div>
            </div>
          </Dialog>
        </>
      );
    case JobTickStatus.SKIPPED:
      if (!tick.skipReason) {
        return (
          <Tag minimal={true} intent={Intent.WARNING}>
            Skipped
          </Tag>
        );
      }
      return (
        <Tooltip
          position={'right'}
          content={tick.skipReason}
          wrapperTagName="div"
          targetTagName="div"
        >
          <Tag minimal={true} intent={Intent.WARNING}>
            Skipped
          </Tag>
        </Tooltip>
      );
    case JobTickStatus.FAILURE:
      if (!tick.error) {
        return (
          <Tag minimal={true} intent={Intent.DANGER}>
            Failure
          </Tag>
        );
      } else {
        const error = tick.error;
        return (
          <LinkButton
            onClick={() =>
              showCustomAlert({
                title: jobType === JobType.SCHEDULE ? 'Schedule Response' : 'Sensor Response',
                body: <PythonErrorInfo error={error} />,
              })
            }
          >
            <Tag minimal={true} intent={Intent.DANGER} interactive={true}>
              Failure
            </Tag>
          </LinkButton>
        );
      }
    default:
      return assertUnreachable(tick.status);
  }
};

const RunList: React.FunctionComponent<{
  runIds: string[];
}> = ({runIds}) => {
  const {data, loading} = useQuery<LaunchedRunListQuery, LaunchedRunListQueryVariables>(
    LAUNCHED_RUN_LIST_QUERY,
    {
      variables: {
        filter: {
          runIds,
        },
      },
    },
  );

  if (loading || !data) {
    return <Spinner />;
  }
  if (data.pipelineRunsOrError.__typename !== 'PipelineRuns') {
    return (
      <NonIdealState
        icon={IconNames.ERROR}
        title="Query Error"
        description={data.pipelineRunsOrError.message}
      />
    );
  }
  return (
    <div>
      <RunTable runs={data.pipelineRunsOrError.results} onSetFilter={() => {}} />
    </div>
  );
};

const LinkButton = styled.button`
  background: inherit;
  border: none;
  cursor: pointer;
  font-size: inherit;
  text-decoration: none;
  padding: 0;
`;

export const TICK_TAG_FRAGMENT = gql`
  fragment TickTagFragment on JobTick {
    id
    status
    timestamp
    skipReason
    runs {
      id
    }
    error {
      ...PythonErrorFragment
    }
  }
`;

const LAUNCHED_RUN_LIST_QUERY = gql`
  query LaunchedRunListQuery($filter: PipelineRunsFilter!) {
    pipelineRunsOrError(filter: $filter, limit: 500) {
      ... on PipelineRuns {
        results {
          ...RunTableRunFragment
          id
          runId
        }
      }
      ... on InvalidPipelineRunsFilterError {
        message
      }
      ... on PythonError {
        ...PythonErrorFragment
      }
    }
  }
  ${RunTable.fragments.RunTableRunFragment}
  ${PythonErrorInfo.fragments.PythonErrorFragment}
`;
