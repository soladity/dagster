import * as React from "react";
import gql from "graphql-tag";
import { useQuery } from "react-apollo";
import {
  RootRepositoriesQuery,
  RootRepositoriesQuery_repositoriesOrError_RepositoryConnection_nodes,
  RootRepositoriesQuery_repositoriesOrError_RepositoryConnection_nodes_location
} from "./types/RootRepositoriesQuery";
import { InstanceExecutableQuery } from "./types/InstanceExecutableQuery";
import PythonErrorInfo from "./PythonErrorInfo";
import { RepositoryInformationFragment } from "./RepositoryInformation";
import { RepositorySelector } from "./types/globalTypes";

export type Repository = RootRepositoriesQuery_repositoriesOrError_RepositoryConnection_nodes;
export type RepositoryLocation = RootRepositoriesQuery_repositoriesOrError_RepositoryConnection_nodes_location;

export interface DagsterRepoOption {
  repositoryLocation: RepositoryLocation;
  repository: Repository;
}

export const repositorySelectorFromDagsterRepoOption = (
  dagsterRepoOption: DagsterRepoOption
): RepositorySelector => {
  const { repository } = dagsterRepoOption;

  return {
    repositoryLocationName: repository.location.name,
    repositoryName: repository.name
  };
};

const LAST_REPO_KEY = "dagit.last-repo";

export const DagsterRepositoryContext = React.createContext<DagsterRepoOption>(
  new Error("DagsterRepositoryContext should never be uninitialized") as any
);

export const ROOT_REPOSITORIES_QUERY = gql`
  query RootRepositoriesQuery {
    repositoriesOrError {
      __typename
      ... on RepositoryConnection {
        nodes {
          id
          name
          pipelines {
            name
            pipelineSnapshotId
          }
          location {
            name
            isReloadSupported
            environmentPath
          }
          ...RepositoryInfoFragment
        }
      }
      ...PythonErrorFragment
    }
  }
  ${PythonErrorInfo.fragments.PythonErrorFragment}
  ${RepositoryInformationFragment}
`;

export const getRepositoryOptionHash = (a: DagsterRepoOption) =>
  `${a.repository.name}:${a.repositoryLocation.name}`;

export const isRepositoryOptionEqual = (a: DagsterRepoOption, b: DagsterRepoOption) =>
  getRepositoryOptionHash(a) === getRepositoryOptionHash(b);

/**
 * useRepositoryOptions vends the set of available repositories by fetching them via GraphQL
 * and coercing the response to the DagsterRepoOption[] type.
 */
export const useRepositoryOptions = () => {
  const { data } = useQuery<RootRepositoriesQuery>(ROOT_REPOSITORIES_QUERY, {
    fetchPolicy: "cache-and-network"
  });

  let options: DagsterRepoOption[] = [];
  if (!data || !data.repositoriesOrError) {
    return { options, error: null };
  }
  if (data.repositoriesOrError.__typename === "PythonError") {
    return { options, error: data.repositoriesOrError };
  }

  options = data.repositoriesOrError.nodes.map(repository => ({
    repository,
    repositoryLocation: repository.location
  }));

  return { error: null, options };
};

/**
 * useCurrentRepositoryState vends `[repo, setRepo]` and internally mirrors the current
 * selection into localStorage so that the default selection in new browser windows
 * is the repo currently active in your session.
 */
export const useCurrentRepositoryState = (options: DagsterRepoOption[]) => {
  const [repo, _setRepo] = React.useState<DagsterRepoOption | null>(null);

  const setRepo = (next: DagsterRepoOption) => {
    window.localStorage.setItem(LAST_REPO_KEY, getRepositoryOptionHash(next));
    _setRepo(next);
  };

  // If the selection is null or the selected repository cannot be found in the set,
  // coerce the selection to the last used repo or [0].
  React.useEffect(() => {
    if (!options.length) {
      return;
    }
    if (!repo || !options.some(o => getRepositoryOptionHash(o) === getRepositoryOptionHash(repo))) {
      const lastHash = window.localStorage.getItem(LAST_REPO_KEY);
      const last = lastHash && options.find(o => getRepositoryOptionHash(o) === lastHash);
      setRepo(last || options[0]);
    }
  }, [repo, options]);

  return [repo, setRepo] as [typeof repo, typeof setRepo];
};

export const useRepositorySelector = (): RepositorySelector => {
  const repository = useRepository();
  return {
    repositoryLocationName: repository.location.name,
    repositoryName: repository.name
  };
};

export const useRepository = () => {
  const { repository, repositoryLocation } = React.useContext(DagsterRepositoryContext);

  if (!repository || !repositoryLocation) {
    // use legacy fields
    throw Error("no legacy repository");
  }

  return repository;
};

export const usePipelineSelector = (pipelineName: string, solidSelection?: string[]) => {
  const repositorySelector = useRepositorySelector();
  return {
    ...repositorySelector,
    pipelineName,
    solidSelection
  };
};

export const useScheduleSelector = (scheduleName: string) => {
  const repositorySelector = useRepositorySelector();
  return {
    ...repositorySelector,
    scheduleName
  };
};

export const INSTANCE_EXECUTABLE_QUERY = gql`
  query InstanceExecutableQuery {
    instance {
      executablePath
    }
  }
`;
export const useDagitExecutablePath = () => {
  const { data } = useQuery<InstanceExecutableQuery>(INSTANCE_EXECUTABLE_QUERY, {
    fetchPolicy: "cache-and-network"
  });

  return data?.instance.executablePath;
};

export const scheduleSelectorWithRepository = (
  scheduleName: string,
  repositorySelector?: RepositorySelector
) => {
  return {
    ...repositorySelector,
    scheduleName
  };
};
