import {Story, Meta} from '@storybook/react/types-6-0';
import faker from 'faker';
import * as React from 'react';

import {TerminationDialog, Props as TerminationDialogProps} from 'src/runs/TerminationDialog';
import {ApolloTestProvider} from 'src/testing/ApolloTestProvider';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'TerminationDialog',
  component: TerminationDialog,
} as Meta;

const Template: Story<TerminationDialogProps> = (props) => (
  <ApolloTestProvider>
    <TerminationDialog {...props} />
  </ApolloTestProvider>
);

const runIDs = [
  faker.random.uuid().slice(0, 8),
  faker.random.uuid().slice(0, 8),
  faker.random.uuid().slice(0, 8),
];

export const ForceTerminationCheckbox = Template.bind({});
ForceTerminationCheckbox.args = {
  isOpen: true,
  onClose: () => {
    console.log('Close!');
  },
  selectedRuns: {
    [runIDs[0]]: true,
    [runIDs[1]]: false,
    [runIDs[2]]: true,
  },
};

export const ForceTerminationNoCheckbox = Template.bind({});
ForceTerminationNoCheckbox.args = {
  isOpen: true,
  onClose: () => {
    console.log('Close!');
  },
  selectedRuns: {
    [runIDs[0]]: false,
    [runIDs[1]]: false,
    [runIDs[2]]: false,
  },
};
