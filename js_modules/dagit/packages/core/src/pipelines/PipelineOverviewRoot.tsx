import * as React from 'react';
import {RouteComponentProps, useHistory, useLocation} from 'react-router-dom';

import {useFeatureFlags} from '../app/Flags';
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
  const {flagPipelineModeTuples} = useFeatureFlags();

  useJobTitle(explorerPath);
  useStripSnapshotFromPath({pipelinePath: explorerPathToString(explorerPath)});

  const onChangeExplorerPath = React.useCallback(
    (path: PipelineExplorerPath, action: 'push' | 'replace') => {
      history[action]({
        search: location.search,
        pathname: workspacePathFromAddress(
          repoAddress,
          `/${flagPipelineModeTuples ? 'jobs' : 'pipelines'}/${explorerPathToString(path)}`,
        ),
      });
    },
    [location, history, repoAddress, flagPipelineModeTuples],
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
