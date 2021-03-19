import {Meta} from '@storybook/react/types-6-0';
import faker from 'faker';
import * as React from 'react';

import {RepoNavItem} from 'src/nav/RepoNavItem';
import {RepoDetails} from 'src/nav/RepoSelector';
import {ApolloTestProvider} from 'src/testing/ApolloTestProvider';
import {Box} from 'src/ui/Box';
import {buildRepoAddress} from 'src/workspace/buildRepoAddress';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'RepoNavItem',
  component: RepoNavItem,
} as Meta;

const OPTIONS = [
  {
    repoAddress: buildRepoAddress(
      faker.random.word().toLowerCase(),
      faker.random.words(2).toLowerCase().replace(/ /g, '-'),
    ),
    metadata: [
      {key: 'host', value: faker.random.word().toLowerCase()},
      {key: 'port', value: faker.random.number(9999).toString()},
    ],
  },
  {
    repoAddress: buildRepoAddress(
      faker.random.word().toLowerCase(),
      faker.random.words(4).toLowerCase().replace(/ /g, '-'),
    ),
    metadata: [
      {key: 'host', value: faker.random.word().toLowerCase()},
      {key: 'port', value: faker.random.number(9999).toString()},
    ],
  },
  {
    repoAddress: buildRepoAddress(
      faker.random.word().toLowerCase(),
      faker.random.words(2).toLowerCase().replace(/ /g, '-'),
    ),
    metadata: [
      {key: 'host', value: faker.random.word().toLowerCase()},
      {key: 'port', value: faker.random.number(9999).toString()},
    ],
  },
  {
    repoAddress: buildRepoAddress(
      faker.random.word().toLowerCase(),
      faker.random.words(5).toLowerCase().replace(/ /g, '-'),
    ),
    metadata: [
      {key: 'host', value: faker.random.word().toLowerCase()},
      {key: 'port', value: faker.random.number(9999).toString()},
    ],
  },
  {
    repoAddress: buildRepoAddress(
      faker.random.word().toLowerCase(),
      faker.random.words(2).toLowerCase().replace(/ /g, '-'),
    ),
    metadata: [
      {key: 'host', value: faker.random.word().toLowerCase()},
      {key: 'port', value: faker.random.number(9999).toString()},
    ],
  },
  {
    repoAddress: buildRepoAddress(
      faker.random.word().toLowerCase(),
      faker.random.words(6).toLowerCase().replace(/ /g, '-'),
    ),
    metadata: [
      {key: 'host', value: faker.random.word().toLowerCase()},
      {key: 'port', value: faker.random.number(9999).toString()},
    ],
  },
  {
    repoAddress: buildRepoAddress(
      faker.random.word().toLowerCase(),
      faker.random.words(2).toLowerCase().replace(/ /g, '-'),
    ),
    metadata: [
      {key: 'host', value: faker.random.word().toLowerCase()},
      {key: 'port', value: faker.random.number(9999).toString()},
    ],
  },
  {
    repoAddress: buildRepoAddress(
      faker.random.words(5).toLowerCase().replace(/ /g, '-'),
      faker.random.words(2).toLowerCase().replace(/ /g, '-'),
    ),
    metadata: [
      {key: 'host', value: faker.random.word().toLowerCase()},
      {key: 'port', value: faker.random.number(9999).toString()},
    ],
  },
  {
    repoAddress: buildRepoAddress(
      faker.random.word().toLowerCase(),
      faker.random.words(2).toLowerCase().replace(/ /g, '-'),
    ),
    metadata: [
      {key: 'host', value: faker.random.word().toLowerCase()},
      {key: 'port', value: faker.random.number(9999).toString()},
    ],
  },
];
export const ManyRepos = () => {
  const [selected, setSelected] = React.useState<Set<RepoDetails>>(() => new Set());

  const onToggle = React.useCallback(
    (repoDetails: RepoDetails) => {
      const copy = new Set(selected);
      if (selected.has(repoDetails)) {
        copy.delete(repoDetails);
      } else {
        copy.add(repoDetails);
      }
      setSelected(copy);
    },
    [selected],
  );

  return (
    <ApolloTestProvider>
      <Box flex={{direction: 'column', justifyContent: 'center'}} style={{height: '500px'}}>
        <div style={{width: '234px'}}>
          <RepoNavItem allRepos={OPTIONS} selected={selected} onToggle={onToggle} />
        </div>
      </Box>
    </ApolloTestProvider>
  );
};

const ONE_REPO = [OPTIONS[0]];

export const OneRepo = () => {
  const [selected, setSelected] = React.useState<Set<RepoDetails>>(() => new Set(ONE_REPO));

  const onToggle = React.useCallback(
    (repoDetails: RepoDetails) => {
      const copy = new Set(selected);
      if (selected.has(repoDetails)) {
        copy.delete(repoDetails);
      } else {
        copy.add(repoDetails);
      }
      setSelected(copy);
    },
    [selected],
  );

  return (
    <ApolloTestProvider>
      <Box flex={{direction: 'column', justifyContent: 'center'}} style={{height: '500px'}}>
        <div style={{width: '234px'}}>
          <RepoNavItem allRepos={ONE_REPO} selected={selected} onToggle={onToggle} />
        </div>
      </Box>
    </ApolloTestProvider>
  );
};
