import {gql} from '@apollo/client';
import {AnchorButton, Button, Classes, Colors, Dialog} from '@blueprintjs/core';
import {Tooltip2 as Tooltip} from '@blueprintjs/popover2';
import * as React from 'react';

import {AppContext} from '../app/AppContext';
import {TimestampDisplay} from '../schedules/TimestampDisplay';
import {PipelineRunStatus} from '../types/globalTypes';
import {Group} from '../ui/Group';
import {HighlightedCodeBlock} from '../ui/HighlightedCodeBlock';
import {MetadataTable} from '../ui/MetadataTable';

import {RunTags} from './RunTags';
import {TimeElapsed} from './TimeElapsed';
import {RunDetailsFragment} from './types/RunDetailsFragment';
import {RunFragment} from './types/RunFragment';

const timingStringForStatus = (status?: PipelineRunStatus) => {
  switch (status) {
    case PipelineRunStatus.QUEUED:
      return 'Queued';
    case PipelineRunStatus.CANCELED:
      return 'Canceled';
    case PipelineRunStatus.CANCELING:
      return 'Canceling…';
    case PipelineRunStatus.FAILURE:
      return 'Failed';
    case PipelineRunStatus.NOT_STARTED:
      return 'Waiting to start…';
    case PipelineRunStatus.STARTED:
      return 'Started…';
    case PipelineRunStatus.STARTING:
      return 'Starting…';
    case PipelineRunStatus.SUCCESS:
      return 'Succeeded';
    default:
      return 'None';
  }
};

const LoadingOrValue: React.FC<{
  loading: boolean;
  children: () => React.ReactNode;
}> = ({loading, children}) =>
  loading ? <div style={{color: Colors.GRAY3}}>Loading…</div> : <div>{children()}</div>;

const TIME_FORMAT = {showSeconds: true, showTimezone: false};

export const RunDetails: React.FC<{
  loading: boolean;
  run: RunDetailsFragment | undefined;
}> = ({loading, run}) => {
  return (
    <MetadataTable
      spacing={0}
      rows={[
        {
          key: 'Started',
          value: (
            <LoadingOrValue loading={loading}>
              {() => {
                if (run?.stats.__typename === 'PipelineRunStatsSnapshot' && run.stats.startTime) {
                  return (
                    <TimestampDisplay timestamp={run.stats.startTime} timeFormat={TIME_FORMAT} />
                  );
                }
                return (
                  <div style={{color: Colors.GRAY3}}>{timingStringForStatus(run?.status)}</div>
                );
              }}
            </LoadingOrValue>
          ),
        },
        {
          key: 'Ended',
          value: (
            <LoadingOrValue loading={loading}>
              {() => {
                if (run?.stats.__typename === 'PipelineRunStatsSnapshot' && run.stats.endTime) {
                  return (
                    <TimestampDisplay timestamp={run.stats.endTime} timeFormat={TIME_FORMAT} />
                  );
                }
                return (
                  <div style={{color: Colors.GRAY3}}>{timingStringForStatus(run?.status)}</div>
                );
              }}
            </LoadingOrValue>
          ),
        },
        {
          key: 'Duration',
          value: (
            <LoadingOrValue loading={loading}>
              {() => {
                if (run?.stats.__typename === 'PipelineRunStatsSnapshot' && run.stats.startTime) {
                  return (
                    <TimeElapsed startUnix={run.stats.startTime} endUnix={run.stats.endTime} />
                  );
                }
                return (
                  <div style={{color: Colors.GRAY3}}>{timingStringForStatus(run?.status)}</div>
                );
              }}
            </LoadingOrValue>
          ),
        },
      ]}
    />
  );
};

export const RunConfigDialog: React.FC<{run: RunFragment}> = ({run}) => {
  const [showDialog, setShowDialog] = React.useState(false);
  const {rootServerURI} = React.useContext(AppContext);
  return (
    <div>
      <Group direction="row" spacing={8}>
        <Button text="View tags and config" icon="tag" onClick={() => setShowDialog(true)} />
        <Tooltip content="Loadable in dagit-debug" position="bottom-right">
          <AnchorButton
            text="Debug file"
            icon="download"
            href={`${rootServerURI}/download_debug/${run.runId}`}
          />
        </Tooltip>
      </Group>

      <Dialog
        isOpen={showDialog}
        onClose={() => setShowDialog(false)}
        style={{width: '800px'}}
        title="Run configuration"
      >
        <div className={Classes.DIALOG_BODY}>
          <Group direction="column" spacing={20}>
            <Group direction="column" spacing={12}>
              <div style={{fontSize: '16px', fontWeight: 600}}>Tags</div>
              <div>
                <RunTags tags={run.tags} />
              </div>
            </Group>
            <Group direction="column" spacing={12}>
              <div style={{fontSize: '16px', fontWeight: 600}}>Config</div>
              <HighlightedCodeBlock value={run?.runConfigYaml || ''} language="yaml" />
            </Group>
          </Group>
        </div>
        <div className={Classes.DIALOG_FOOTER}>
          <div className={Classes.DIALOG_FOOTER_ACTIONS}>
            <Button onClick={() => setShowDialog(false)} intent="primary">
              OK
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  );
};

export const RUN_DETAILS_FRAGMENT = gql`
  fragment RunDetailsFragment on PipelineRun {
    id
    stats {
      ... on PipelineRunStatsSnapshot {
        id
        endTime
        startTime
      }
    }
    status
  }
`;
