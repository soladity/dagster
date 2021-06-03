import {gql, useQuery} from '@apollo/client';
import {NonIdealState} from '@blueprintjs/core';
import * as React from 'react';
import styled from 'styled-components/macro';

import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {explorerPathFromString, useStripSnapshotFromPath} from '../pipelines/PipelinePathUtils';
import {Box} from '../ui/Box';
import {Loading} from '../ui/Loading';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';

import {PartitionView} from './PartitionView';
import {
  PipelinePartitionsRootQuery,
  PipelinePartitionsRootQueryVariables,
} from './types/PipelinePartitionsRootQuery';

interface Props {
  pipelinePath: string;
  repoAddress: RepoAddress;
}

export const PipelinePartitionsRoot: React.FC<Props> = (props) => {
  const {pipelinePath, repoAddress} = props;
  const {pipelineName} = explorerPathFromString(pipelinePath);
  useDocumentTitle(`Pipeline: ${pipelineName}`);
  useStripSnapshotFromPath(props);

  const repositorySelector = repoAddressToSelector(repoAddress);

  const queryResult = useQuery<PipelinePartitionsRootQuery, PipelinePartitionsRootQueryVariables>(
    PIPELINE_PARTITIONS_ROOT_QUERY,
    {
      variables: {repositorySelector, pipelineName},
      fetchPolicy: 'network-only',
    },
  );
  const [selected = undefined, setSelected] = useQueryPersistedState<string>({
    queryKey: 'partitionSet',
  });

  return (
    <Loading queryResult={queryResult}>
      {({partitionSetsOrError}) => {
        if (partitionSetsOrError.__typename !== 'PartitionSets') {
          return (
            <Wrapper>
              <NonIdealState
                icon="multi-select"
                title="Partitions"
                description={partitionSetsOrError.message}
              />
            </Wrapper>
          );
        }

        if (!partitionSetsOrError.results.length) {
          return (
            <Wrapper>
              <NonIdealState
                icon="multi-select"
                title="Partitions"
                description={
                  <p>
                    There are no partition sets defined for pipeline <code>{pipelineName}</code>.
                  </p>
                }
              />
            </Wrapper>
          );
        }

        const selectionHasMatch =
          selected && !!partitionSetsOrError.results.filter((x) => x.name === selected).length;
        const partitionSet =
          selectionHasMatch && selected
            ? partitionSetsOrError.results.filter((x) => x.name === selected)[0]
            : partitionSetsOrError.results[0];

        return (
          <Box padding={20}>
            <PartitionView
              partitionSet={partitionSet}
              partitionSets={partitionSetsOrError.results}
              onChangePartitionSet={(x) => setSelected(x.name)}
              pipelineName={pipelineName}
              repoAddress={repoAddress}
            />
          </Box>
        );
      }}
    </Loading>
  );
};

const PIPELINE_PARTITIONS_ROOT_QUERY = gql`
  query PipelinePartitionsRootQuery(
    $pipelineName: String!
    $repositorySelector: RepositorySelector!
  ) {
    partitionSetsOrError(pipelineName: $pipelineName, repositorySelector: $repositorySelector) {
      ... on PipelineNotFoundError {
        message
      }
      ... on PythonError {
        message
      }
      ... on PartitionSets {
        results {
          id
          name
        }
      }
    }
  }
`;

const Wrapper = styled.div`
  width: 100%;
  height: 100%;
  min-width: 0;
`;
