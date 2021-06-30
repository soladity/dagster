import {useQuery} from '@apollo/client';
import {Colors, NonIdealState} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import * as React from 'react';

import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {UnloadableSchedules} from '../jobs/UnloadableJobs';
import {InstigationType} from '../types/globalTypes';
import {Box} from '../ui/Box';
import {Group} from '../ui/Group';
import {Loading} from '../ui/Loading';
import {Page} from '../ui/Page';
import {Subheading} from '../ui/Text';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';

import {SCHEDULES_ROOT_QUERY, SchedulerTimezoneNote} from './ScheduleUtils';
import {SchedulerInfo} from './SchedulerInfo';
import {SchedulesNextTicks} from './SchedulesNextTicks';
import {SchedulesTable} from './SchedulesTable';
import {SchedulesRootQuery} from './types/SchedulesRootQuery';

export const SchedulesRoot = ({repoAddress}: {repoAddress: RepoAddress}) => {
  useDocumentTitle('Schedules');
  const repositorySelector = repoAddressToSelector(repoAddress);

  const queryResult = useQuery<SchedulesRootQuery>(SCHEDULES_ROOT_QUERY, {
    variables: {
      repositorySelector: repositorySelector,
      instigationType: InstigationType.SCHEDULE,
    },
    fetchPolicy: 'cache-and-network',
    pollInterval: 50 * 1000,
    partialRefetch: true,
  });

  return (
    <Page>
      <Loading queryResult={queryResult} allowStaleData={true}>
        {(result) => {
          const {
            repositoryOrError,
            scheduler,
            unloadableInstigationStatesOrError,
            instance,
          } = result;
          let schedulesSection = null;

          if (repositoryOrError.__typename === 'PythonError') {
            schedulesSection = <PythonErrorInfo error={repositoryOrError} />;
          } else if (repositoryOrError.__typename === 'RepositoryNotFoundError') {
            schedulesSection = (
              <NonIdealState
                icon={IconNames.ERROR}
                title="Repository not found"
                description="Could not load this repository."
              />
            );
          } else if (!repositoryOrError.schedules.length) {
            schedulesSection = (
              <NonIdealState
                icon={IconNames.TIME}
                title="No Schedules Found"
                description={
                  <p>
                    This repository does not have any schedules defined. Visit the{' '}
                    <a href="https://docs.dagster.io/overview/schedules-sensors/schedules">
                      scheduler documentation
                    </a>{' '}
                    for more information about scheduling pipeline runs in Dagster.
                  </p>
                }
              />
            );
          } else {
            schedulesSection = repositoryOrError.schedules.length > 0 && (
              <Group direction="column" spacing={16}>
                <SchedulerTimezoneNote schedulerOrError={scheduler} />
                <SchedulesTable schedules={repositoryOrError.schedules} repoAddress={repoAddress} />
                <Box
                  margin={{vertical: 16}}
                  padding={{bottom: 8}}
                  border={{side: 'bottom', width: 1, color: Colors.LIGHT_GRAY3}}
                >
                  <Subheading>Scheduled ticks</Subheading>
                </Box>
                <SchedulesNextTicks repos={[repositoryOrError]} />
              </Group>
            );
          }

          return (
            <Group direction="column" spacing={20}>
              <SchedulerInfo schedulerOrError={scheduler} daemonHealth={instance.daemonHealth} />
              {schedulesSection}
              {unloadableInstigationStatesOrError.__typename === 'PythonError' ? (
                <PythonErrorInfo error={unloadableInstigationStatesOrError} />
              ) : (
                <UnloadableSchedules scheduleStates={unloadableInstigationStatesOrError.results} />
              )}
            </Group>
          );
        }}
      </Loading>
    </Page>
  );
};
