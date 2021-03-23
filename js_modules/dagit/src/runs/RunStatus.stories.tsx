import {Meta} from '@storybook/react/types-6-0';
import * as React from 'react';

import {PipelineRunStatus} from '../types/globalTypes';
import {Box} from '../ui/Box';
import {MetadataTable} from '../ui/MetadataTable';

import {RunStatus} from './RunStatusDots';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'RunStatus',
  component: RunStatus,
} as Meta;

export const Example = () => {
  return (
    <MetadataTable
      rows={Object.values(PipelineRunStatus).map((value: PipelineRunStatus) => ({
        key: value,
        value: (
          <Box padding={{top: 2}}>
            <RunStatus status={value} />
          </Box>
        ),
      }))}
    />
  );
};
