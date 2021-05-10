import {gql, useLazyQuery, useQuery} from '@apollo/client';
import Fuse from 'fuse.js';
import * as React from 'react';

import {buildRepoPath} from '../workspace/buildRepoAddress';
import {workspacePath} from '../workspace/workspacePath';

import {SearchResult, SearchResultType} from './types';
import {SearchBootstrapQuery} from './types/SearchBootstrapQuery';
import {SearchSecondaryQuery} from './types/SearchSecondaryQuery';

const fuseOptions = {
  keys: ['label', 'tags', 'type'],
  limit: 10,
  threshold: 0.3,
  useExtendedSearch: true,
};

const bootstrapDataToSearchResults = (data?: SearchBootstrapQuery) => {
  if (
    !data?.repositoryLocationsOrError ||
    data?.repositoryLocationsOrError?.__typename !== 'RepositoryLocationConnection'
  ) {
    return new Fuse([]);
  }

  const {nodes} = data.repositoryLocationsOrError;
  const manyRepos = nodes.length > 1;

  const allEntries = nodes.reduce((accum, repoLocation) => {
    if (repoLocation.__typename === 'RepositoryLocationLoadFailure') {
      return accum;
    }

    const repos = repoLocation.repositories;
    return [
      ...accum,
      ...repos.reduce((inner, repo) => {
        const {name, partitionSets, pipelines, schedules, sensors} = repo;
        const {name: locationName} = repoLocation;
        const repoPath = buildRepoPath(name, locationName);

        const allPipelines = pipelines.map((pipeline) => ({
          key: `${repoPath}-${pipeline.name}`,
          label: pipeline.name,
          description: manyRepos ? `Pipeline in ${repoPath}` : 'Pipeline',
          href: workspacePath(name, locationName, `/pipelines/${pipeline.name}`),
          type: SearchResultType.Pipeline,
        }));

        const allSchedules = schedules.map((schedule) => ({
          key: `${repoPath}-${schedule.name}`,
          label: schedule.name,
          description: manyRepos ? `Schedule in ${repoPath}` : 'Schedule',
          href: workspacePath(name, locationName, `/schedules/${schedule.name}`),
          type: SearchResultType.Schedule,
        }));

        const allSensors = sensors.map((sensor) => ({
          key: `${repoPath}-${sensor.name}`,
          label: sensor.name,
          description: manyRepos ? `Sensor in ${repoPath}` : 'Sensor',
          href: workspacePath(name, locationName, `/sensors/${sensor.name}`),
          type: SearchResultType.Sensor,
        }));

        const allPartitionSets = partitionSets.map((partitionSet) => ({
          key: `${repoPath}-${partitionSet.name}`,
          label: partitionSet.name,
          description: manyRepos ? `Partition set in ${repoPath}` : 'Partition set',
          href: workspacePath(
            name,
            locationName,
            `/pipelines/${partitionSet.pipelineName}/partitions?partitionSet=${partitionSet.name}`,
          ),
          type: SearchResultType.PartitionSet,
        }));

        return [...inner, ...allPipelines, ...allSchedules, ...allSensors, ...allPartitionSets];
      }, []),
    ];
  }, []);

  return new Fuse(allEntries, fuseOptions);
};

const secondaryDataToSearchResults = (data?: SearchSecondaryQuery) => {
  if (!data?.assetsOrError || data.assetsOrError.__typename === 'PythonError') {
    return new Fuse([]);
  }

  const {nodes} = data.assetsOrError;
  const allEntries = nodes.map((node) => {
    const {key} = node;
    const path = key.path.join(' › ');
    return {
      key: path,
      label: path,
      description: 'Asset',
      href: `/instance/assets/${key.path.join('/')}`,
      type: SearchResultType.Asset,
    };
  });

  return new Fuse(allEntries, fuseOptions);
};

export const useRepoSearch = () => {
  const {data: bootstrapData, loading: bootstrapLoading} = useQuery<SearchBootstrapQuery>(
    SEARCH_BOOTSTRAP_QUERY,
    {
      fetchPolicy: 'cache-and-network',
    },
  );

  const [
    performQuery,
    {data: secondaryData, loading: secondaryLoading, called: secondaryQueryCalled},
  ] = useLazyQuery<SearchSecondaryQuery>(SEARCH_SECONDARY_QUERY, {
    fetchPolicy: 'cache-and-network',
  });

  const bootstrapFuse = React.useMemo(() => bootstrapDataToSearchResults(bootstrapData), [
    bootstrapData,
  ]);
  const secondaryFuse = React.useMemo(() => secondaryDataToSearchResults(secondaryData), [
    secondaryData,
  ]);
  const loading = bootstrapLoading || secondaryLoading;
  const performSearch = React.useCallback(
    (queryString: string, buildSecondary?: boolean): Fuse.FuseResult<SearchResult>[] => {
      if ((queryString || buildSecondary) && !secondaryQueryCalled) {
        performQuery();
      }
      const bootstrapResults = bootstrapFuse.search(queryString);
      const secondaryResults = secondaryFuse.search(queryString);
      return [...bootstrapResults, ...secondaryResults];
    },
    [bootstrapFuse, secondaryFuse, performQuery, secondaryQueryCalled],
  );

  return {loading, performSearch};
};

const SEARCH_BOOTSTRAP_QUERY = gql`
  query SearchBootstrapQuery {
    repositoryLocationsOrError {
      __typename
      ... on RepositoryLocationConnection {
        nodes {
          __typename
          ... on RepositoryLocation {
            id
            name
            repositories {
              id
              ... on Repository {
                id
                name
                pipelines {
                  id
                  name
                }
                schedules {
                  id
                  name
                }
                sensors {
                  id
                  name
                }
                partitionSets {
                  id
                  name
                  pipelineName
                }
              }
            }
          }
        }
      }
    }
  }
`;

const SEARCH_SECONDARY_QUERY = gql`
  query SearchSecondaryQuery {
    assetsOrError {
      __typename
      ... on AssetConnection {
        nodes {
          id
          key {
            path
          }
        }
      }
    }
  }
`;
