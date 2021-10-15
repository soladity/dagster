import * as React from 'react';
import {RouteComponentProps, useHistory, useLocation} from 'react-router-dom';

import {isThisThingAJob, useRepository} from '../workspace/WorkspaceContext';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

import {PipelineExplorerJobContext} from './PipelineExplorerJobContext';
import {PipelineExplorerContainer} from './PipelineExplorerRoot';
import {
  explorerPathFromString,
  explorerPathToString,
  PipelineExplorerPath,
  useStripSnapshotFromPath,
} from './PipelinePathUtils';
import {SidebarPipelineOrJobOverview} from './SidebarPipelineOrJobOverview';
import {useJobTitle} from './useJobTitle';

type Props = RouteComponentProps<{0: string}> & {repoAddress: RepoAddress};

export const PipelineOverviewRoot: React.FC<Props> = (props) => {
  const {match, repoAddress} = props;
  const history = useHistory();
  const location = useLocation();
  const explorerPath = explorerPathFromString(match.params['0']);

  const repo = useRepository(repoAddress);
  const isJob = isThisThingAJob(repo, explorerPath.pipelineName);

  useJobTitle(explorerPath, isJob);
  useStripSnapshotFromPath({pipelinePath: explorerPathToString(explorerPath)});

  const onChangeExplorerPath = React.useCallback(
    (path: PipelineExplorerPath, action: 'push' | 'replace') => {
      history[action]({
        search: location.search,
        pathname: workspacePathFromAddress(
          repoAddress,
          `/${isJob ? 'jobs' : 'pipelines'}/${explorerPathToString(path)}`,
        ),
      });
    },
    [history, location.search, repoAddress, isJob],
  );

  return (
    <PipelineExplorerJobContext.Provider
      value={{
        sidebarTab: (
          <SidebarPipelineOrJobOverview repoAddress={repoAddress} explorerPath={explorerPath} />
        ),
      }}
    >
      <PipelineExplorerContainer
        repoAddress={repoAddress}
        explorerPath={explorerPath}
        onChangeExplorerPath={onChangeExplorerPath}
      />
    </PipelineExplorerJobContext.Provider>
  );
};
