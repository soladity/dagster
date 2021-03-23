import {ApolloConsumer} from '@apollo/client';
import {Colors} from '@blueprintjs/core';
import memoize from 'lodash/memoize';
import * as React from 'react';
import {useRouteMatch} from 'react-router-dom';

import {
  DagsterRepoOption,
  getRepositoryOptionHash,
  WorkspaceContext,
} from '../workspace/WorkspaceContext';
import {buildRepoAddress} from '../workspace/buildRepoAddress';

import {JobsList} from './JobsList';
import {RepoNavItem} from './RepoNavItem';
import {RepoDetails} from './RepoSelector';
import {RepositoryContentList} from './RepositoryContentList';
import {RepositoryLocationStateObserver} from './RepositoryLocationStateObserver';

export const LAST_REPO_KEY = 'dagit.last-repo';
export const REPO_KEYS = 'dagit.repo-keys';

const buildDetails = memoize((option: DagsterRepoOption) => ({
  repoAddress: buildRepoAddress(option.repository.name, option.repositoryLocation.name),
  metadata: option.repository.displayMetadata,
}));

const keysFromLocalStorage = () => {
  const keys = window.localStorage.getItem(REPO_KEYS);
  if (keys) {
    const parsed: string[] = JSON.parse(keys);
    return new Set(parsed);
  }

  // todo dish: Temporary while migrating to support filtering on multiple repos in
  // left nav.
  const key = window.localStorage.getItem(LAST_REPO_KEY);
  if (key) {
    return new Set([key]);
  }

  return new Set();
};

/**
 * useNavVisibleRepos vends `[reposForKeys, toggleRepo]` and internally mirrors the current
 * selection into localStorage so that the default selection in new browser windows
 * is the repo currently active in your session.
 */
const useNavVisibleRepos = (
  options: DagsterRepoOption[],
): [typeof repoDetailsForKeys, typeof toggleRepo] => {
  // Collect keys from localStorage. Any keys that are present in our option list will be our
  // initial state. If there are none, just grab the first option.
  const [repoKeys, setRepoKeys] = React.useState<Set<string>>(() => {
    const keys = keysFromLocalStorage();
    const hashes = options.map((option) => getRepositoryOptionHash(option));
    const matches = hashes.filter((hash) => keys.has(hash));

    if (matches.length) {
      return new Set(matches);
    }

    if (hashes.length) {
      return new Set([hashes[0]]);
    }

    return new Set();
  });

  const toggleRepo = React.useCallback((option: RepoDetails) => {
    const {repoAddress} = option;
    const key = `${repoAddress.name}:${repoAddress.location}`;

    setRepoKeys((current) => {
      const copy = new Set([...Array.from(current || [])]);
      if (copy.has(key)) {
        copy.delete(key);
      } else {
        copy.add(key);
      }
      return copy;
    });
  }, []);

  const reposForKeys = React.useMemo(
    () => options.filter((o) => repoKeys.has(getRepositoryOptionHash(o))),
    [options, repoKeys],
  );

  // When the list of matching repos changes, update localStorage.
  React.useEffect(() => {
    const foundKeys = reposForKeys.map((option) => getRepositoryOptionHash(option));
    window.localStorage.setItem(REPO_KEYS, JSON.stringify(foundKeys));
  }, [reposForKeys]);

  const repoDetailsForKeys = React.useMemo(() => new Set(reposForKeys.map(buildDetails)), [
    reposForKeys,
  ]);

  return [repoDetailsForKeys, toggleRepo];
};

const LoadedRepositorySection: React.FC<{allRepos: DagsterRepoOption[]}> = ({allRepos}) => {
  const match = useRouteMatch<
    | {repoPath: string; selector: string; tab: string; rootTab: undefined}
    | {selector: undefined; tab: undefined; rootTab: string}
  >([
    '/workspace/:repoPath/pipelines/:selector/:tab?',
    '/workspace/:repoPath/solids/:selector',
    '/workspace/:repoPath/schedules/:selector',
    '/:rootTab?',
  ]);

  const [visibleRepos, toggleRepo] = useNavVisibleRepos(allRepos);

  const visibleOptions = React.useMemo(() => {
    return Array.from(visibleRepos)
      .map((visible) => {
        const {repoAddress} = visible;
        return allRepos.find(
          (option) =>
            getRepositoryOptionHash(option) === `${repoAddress.name}:${repoAddress.location}`,
        );
      })
      .filter((option) => !!option) as DagsterRepoOption[];
  }, [allRepos, visibleRepos]);

  return (
    <div
      className="bp3-dark"
      style={{
        background: `rgba(0,0,0,0.3)`,
        color: Colors.WHITE,
        display: 'flex',
        flex: 1,
        overflow: 'none',
        flexDirection: 'column',
        minHeight: 0,
      }}
    >
      <RepoNavItem
        allRepos={allRepos.map(buildDetails)}
        selected={visibleRepos}
        onToggle={toggleRepo}
      />
      <ApolloConsumer>
        {(client) => <RepositoryLocationStateObserver client={client} />}
      </ApolloConsumer>
      {visibleRepos.size ? (
        <div style={{display: 'flex', flex: 1, flexDirection: 'column', minHeight: 0}}>
          <RepositoryContentList {...match?.params} repos={visibleOptions} />
          <JobsList {...match?.params} repos={visibleOptions} />
        </div>
      ) : null}
    </div>
  );
};

export const LeftNavRepositorySection = () => {
  const {allRepos, loading} = React.useContext(WorkspaceContext);

  if (loading) {
    return <div style={{flex: 1}} />;
  }

  return <LoadedRepositorySection allRepos={allRepos} />;
};
