import {IconName, Tab, Tabs, Colors} from '@blueprintjs/core';
import {Tooltip2 as Tooltip} from '@blueprintjs/popover2';
import React from 'react';
import {Link, useRouteMatch} from 'react-router-dom';

import {useFeatureFlags} from '../app/Flags';
import {DISABLED_MESSAGE, PermissionSet, usePermissions} from '../app/Permissions';
import {
  explorerPathFromString,
  explorerPathToString,
  PipelineExplorerPath,
} from '../pipelines/PipelinePathUtils';
import {Box} from '../ui/Box';
import {Group} from '../ui/Group';
import {PageHeader} from '../ui/PageHeader';
import {Heading} from '../ui/Text';
import {useRepository} from '../workspace/WorkspaceContext';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

import {JobMetadata} from './JobMetadata';
import {RepositoryLink} from './RepositoryLink';

interface TabConfig {
  title: string;
  pathComponent: string;
  icon: IconName;
  isAvailable?: (permissions: PermissionSet) => boolean;
}

const pipelineTabs: {[key: string]: TabConfig} = {
  overview: {title: 'Overview', pathComponent: '', icon: 'dashboard'},
  playground: {
    title: 'Playground',
    pathComponent: 'playground',
    icon: 'manually-entered-data',
    isAvailable: (permissions: PermissionSet) => permissions.canLaunchPipelineExecution,
  },
  runs: {
    title: 'Runs',
    pathComponent: 'runs',
    icon: 'history',
  },
  partitions: {
    title: 'Partitions',
    pathComponent: 'partitions',
    icon: 'multi-select',
  },
};

const currentOrder = ['overview', 'playground', 'runs', 'partitions'];

export function tabForPipelinePathComponent(component?: string): TabConfig {
  const tabList = Object.keys(pipelineTabs);
  const match =
    tabList.find((t) => pipelineTabs[t].pathComponent === component) ||
    tabList.find((t) => pipelineTabs[t].pathComponent === '')!;
  return pipelineTabs[match];
}

const tabForKey = (repoAddress: RepoAddress, explorerPath: PipelineExplorerPath) => {
  const explorerPathForTab = explorerPathToString({
    ...explorerPath,
    pathSolids: [],
  });

  // When you click one of the top tabs, it resets the snapshot you may be looking at
  // in the Definition tab and also clears solids from the path
  return (key: string) => {
    const tab = pipelineTabs[key];
    return {
      text: tab.title,
      href: workspacePathFromAddress(
        repoAddress,
        `/pipelines/${explorerPathForTab}${tab.pathComponent}`,
      ),
      isAvailable: tab.isAvailable,
    };
  };
};

interface Props {
  repoAddress: RepoAddress;
}

export const PipelineNav: React.FC<Props> = (props) => {
  const {repoAddress} = props;
  const permissions = usePermissions();
  const {flagPipelineModeTuples} = useFeatureFlags();
  const repo = useRepository(repoAddress);
  const match = useRouteMatch<{tab?: string; selector: string}>([
    '/workspace/:repoPath/pipelines/:selector/:tab?',
    '/workspace/:repoPath/jobs/:selector/:tab?',
  ]);

  const active = tabForPipelinePathComponent(match!.params.tab);
  const explorerPath = explorerPathFromString(match!.params.selector);
  const {pipelineName, pipelineMode, snapshotId} = explorerPath;
  const partitionSets = repo?.repository.partitionSets || [];

  // If using pipeline:mode tuple (crag flag), check for partition sets that are for this specific
  // pipeline:mode tuple. Otherwise, just check for a pipeline name match.
  const hasPartitionSet = partitionSets.some(
    (partitionSet) =>
      partitionSet.pipelineName === pipelineName &&
      (!flagPipelineModeTuples || partitionSet.mode === pipelineMode),
  );

  const tabs = currentOrder
    .filter((key) => hasPartitionSet || key !== 'partitions')
    .map(tabForKey(repoAddress, explorerPath));

  return (
    <Group direction="column" spacing={12} padding={{top: 20, horizontal: 20}}>
      <PageHeader
        title={
          <Heading>
            {pipelineName}
            {flagPipelineModeTuples && pipelineMode !== 'default' ? (
              <span style={{opacity: 0.5}}> : {pipelineMode}</span>
            ) : null}
          </Heading>
        }
        icon={flagPipelineModeTuples ? 'send-to-graph' : 'diagram-tree'}
        description={
          <>
            <Link
              to={workspacePathFromAddress(
                repoAddress,
                flagPipelineModeTuples ? '/jobs' : '/pipelines',
              )}
            >
              {flagPipelineModeTuples ? 'Job' : 'Pipeline'}
            </Link>{' '}
            in <RepositoryLink repoAddress={repoAddress} />
          </>
        }
        metadata={
          snapshotId ? null : (
            <JobMetadata
              pipelineName={pipelineName}
              pipelineMode={pipelineMode}
              repoAddress={repoAddress}
            />
          )
        }
      />
      <Box border={{side: 'bottom', width: 1, color: Colors.LIGHT_GRAY3}}>
        <Tabs large={false} selectedTabId={active.title}>
          {tabs.map((tab) => {
            const {href, text, isAvailable} = tab;
            const disabled = isAvailable && !isAvailable(permissions);
            const title = disabled ? (
              <Tooltip content={DISABLED_MESSAGE} placement="top">
                {text}
              </Tooltip>
            ) : (
              <Link to={href}>{text}</Link>
            );
            return <Tab key={text} id={text} title={title} disabled={disabled} />;
          })}
        </Tabs>
      </Box>
    </Group>
  );
};
