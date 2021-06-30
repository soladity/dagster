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
  Icon,
} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import * as React from 'react';
import styled from 'styled-components/macro';

import {showCustomAlert} from '../app/CustomAlertProvider';
import {PythonErrorInfo, PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {assertUnreachable} from '../app/Util';
import {RunTable, RUN_TABLE_RUN_FRAGMENT} from '../runs/RunTable';
import {InstigationTickStatus, InstigationType} from '../types/globalTypes';
import {Box} from '../ui/Box';
import {ButtonLink} from '../ui/ButtonLink';
import {Group} from '../ui/Group';
import {Spinner} from '../ui/Spinner';
import {Body} from '../ui/Text';

import {LaunchedRunListQuery, LaunchedRunListQueryVariables} from './types/LaunchedRunListQuery';
import {TickTagFragment} from './types/TickTagFragment';

export const TickTag: React.FunctionComponent<{
  tick: TickTagFragment;
  instigationType?: InstigationType;
}> = ({tick, instigationType}) => {
  const [open, setOpen] = React.useState<boolean>(false);
  switch (tick.status) {
    case InstigationTickStatus.STARTED:
      return (
        <Tag minimal={true} intent={Intent.NONE}>
          Started
        </Tag>
      );
    case InstigationTickStatus.SUCCESS:
      if (!tick.runIds.length) {
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
              {tick.runIds.length} Requested
            </ButtonLink>
          </Tag>
          <Dialog
            isOpen={open}
            onClose={() => setOpen(false)}
            style={{width: '90vw'}}
            title={`Launched runs`}
          >
            <Box background={Colors.WHITE} padding={16} margin={{bottom: 16}}>
              {open && <RunList runIds={tick.runIds} />}
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
    case InstigationTickStatus.SKIPPED:
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
    case InstigationTickStatus.FAILURE:
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
                title: instigationType
                  ? instigationType === InstigationType.SCHEDULE
                    ? 'Schedule Response'
                    : 'Sensor Response'
                  : 'Python Error',
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

export const RunList: React.FunctionComponent<{
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
    return <Spinner purpose="section" />;
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

export const FailedRunList: React.FunctionComponent<{
  originRunIds?: string[];
}> = ({originRunIds}) => {
  if (!originRunIds || !originRunIds.length) {
    return null;
  }
  return (
    <Group direction="column" spacing={16}>
      <Box padding={12} border={{side: 'bottom', width: 1, color: Colors.LIGHT_GRAY1}}>
        <Body>
          Failed Runs
          <Tooltip content="Failed runs this tick reacted on and reported back to.">
            <Icon
              icon="info-sign"
              iconSize={12}
              color={Colors.GRAY3}
              style={{position: 'relative', top: '-2px', marginLeft: '6px'}}
            />
          </Tooltip>
        </Body>

        <RunList runIds={originRunIds} />
      </Box>
      <Box padding={12} margin={{bottom: 8}}>
        <Body>
          Requested Runs
          <Tooltip content="Runs launched by the run requests in this tick.">
            <Icon
              icon="info-sign"
              iconSize={12}
              color={Colors.GRAY3}
              style={{position: 'relative', top: '-2px', marginLeft: '6px'}}
            />
          </Tooltip>
        </Body>
        <NonIdealState description="Sensor does not target a pipeline." />
      </Box>
    </Group>
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
  fragment TickTagFragment on InstigationTick {
    id
    status
    timestamp
    skipReason
    runIds
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
  ${RUN_TABLE_RUN_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
`;
