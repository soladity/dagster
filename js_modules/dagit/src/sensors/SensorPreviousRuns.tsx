import {gql, useQuery} from '@apollo/client';
import * as React from 'react';

import {DagsterTag} from 'src/runs/RunTag';
import {PreviousRunsForSensorQuery} from 'src/sensors/types/PreviousRunsForSensorQuery';
import {SensorFragment} from 'src/sensors/types/SensorFragment';
import {PreviousRunsSection, PREVIOUS_RUNS_FRAGMENT} from 'src/workspace/PreviousRunsSection';
import {RepoAddress} from 'src/workspace/types';

interface Props {
  sensor: SensorFragment;
  repoAddress: RepoAddress;
}

const RUNS_LIMIT = 20;

export const SensorPreviousRuns = (props: Props) => {
  const {sensor} = props;
  const {data, loading} = useQuery<PreviousRunsForSensorQuery>(PREVIOUS_RUNS_FOR_SENSOR_QUERY, {
    fetchPolicy: 'cache-and-network',
    variables: {
      limit: RUNS_LIMIT,
      filter: {
        pipelineName: sensor.pipelineName,
        tags: [{key: DagsterTag.SensorName, value: sensor.name}],
      },
    },
  });

  return <PreviousRunsSection loading={loading} data={data?.pipelineRunsOrError} />;
};

const PREVIOUS_RUNS_FOR_SENSOR_QUERY = gql`
  query PreviousRunsForSensorQuery($filter: PipelineRunsFilter, $limit: Int) {
    pipelineRunsOrError(filter: $filter, limit: $limit) {
      __typename
      ...PreviousRunsFragment
    }
  }
  ${PREVIOUS_RUNS_FRAGMENT}
`;
