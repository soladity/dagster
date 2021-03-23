import {NonIdealState} from '@blueprintjs/core';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {Group} from '../ui/Group';
import {LoadingSpinner} from '../ui/Loading';
import {Page} from '../ui/Page';
import {PageHeader} from '../ui/PageHeader';
import {Table} from '../ui/Table';
import {Heading} from '../ui/Text';

import {useRepositoryOptions} from './WorkspaceContext';
import {workspacePath} from './workspacePath';

export const WorkspaceOverviewRoot = () => {
  const {loading, error, options} = useRepositoryOptions();

  const content = () => {
    if (loading) {
      return <LoadingSpinner purpose="page" />;
    }

    if (error) {
      return (
        <NonIdealState
          icon="cube"
          title="Error loading repositories"
          description="Could not load repositories in this workspace."
        />
      );
    }

    if (!options.length) {
      return (
        <NonIdealState
          icon="cube"
          title="Empty workspace"
          description="There are no repositories in this workspace."
        />
      );
    }

    return (
      <Table>
        <thead>
          <tr>
            <th>Repository</th>
            <th>Pipelines</th>
            <th>Solids</th>
            <th>Schedules</th>
          </tr>
        </thead>
        <tbody>
          {options.map((repository) => {
            const {
              repository: {name},
              repositoryLocation: {name: location},
            } = repository;
            const repoString = `${name}@${location}`;
            return (
              <tr key={repoString}>
                <td style={{width: '40%'}}>{repoString}</td>
                <td>
                  <Link to={workspacePath(name, location, '/pipelines')}>Pipelines</Link>
                </td>
                <td>
                  <Link to={workspacePath(name, location, '/solids')}>Solids</Link>
                </td>
                <td>
                  <Link to={workspacePath(name, location, '/schedules')}>Schedules</Link>
                </td>
              </tr>
            );
          })}
        </tbody>
      </Table>
    );
  };

  return (
    <Page>
      <Group direction="column" spacing={16}>
        <PageHeader title={<Heading>Workspace</Heading>} />
        {content()}
      </Group>
    </Page>
  );
};
