import {gql, useQuery} from '@apollo/client';
import * as querystring from 'query-string';
import * as React from 'react';
import {useHistory, useLocation} from 'react-router-dom';
import {AutoSizer, CellMeasurer, CellMeasurerCache, List} from 'react-virtualized';
import styled from 'styled-components/macro';

import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {Box} from '../ui/Box';
import {ColorsWIP} from '../ui/Colors';
import {Loading} from '../ui/Loading';
import {NonIdealState} from '../ui/NonIdealState';
import {SplitPanelContainer} from '../ui/SplitPanelContainer';
import {
  SuggestionProvider,
  TokenizingField,
  TokenizingFieldValue,
  stringFromValue,
  tokenizedValuesFromString,
} from '../ui/TokenizingField';
import {FontFamily} from '../ui/styles';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

import {SolidDetailScrollContainer, UsedSolidDetails} from './SolidDetailsRoot';
import {SolidTypeSignature, SOLID_TYPE_SIGNATURE_FRAGMENT} from './SolidTypeSignature';
import {
  SolidsRootQuery,
  SolidsRootQuery_repositoryOrError_Repository_usedSolids,
} from './types/SolidsRootQuery';

function flatUniq(arrs: string[][]) {
  const results: {[key: string]: boolean} = {};
  for (const arr of arrs) {
    for (const item of arr) {
      results[item] = true;
    }
  }
  return Object.keys(results).sort((a, b) => a.localeCompare(b));
}

type Solid = SolidsRootQuery_repositoryOrError_Repository_usedSolids;

function searchSuggestionsForSolids(solids: Solid[]): SuggestionProvider[] {
  return [
    {
      token: 'name',
      values: () => solids.map((s) => s.definition.name),
    },
    {
      token: 'job',
      values: () =>
        flatUniq(
          solids.map((s) =>
            s.invocations.filter((i) => !i.pipeline.isJob).map((i) => i.pipeline.name),
          ),
        ),
    },
    {
      token: 'pipeline',
      values: () =>
        flatUniq(
          solids.map((s) =>
            s.invocations.filter((i) => i.pipeline.isJob).map((i) => i.pipeline.name),
          ),
        ),
    },
    {
      token: 'input',
      values: () =>
        flatUniq(solids.map((s) => s.definition.inputDefinitions.map((d) => d.type.displayName))),
    },
    {
      token: 'output',
      values: () =>
        flatUniq(solids.map((s) => s.definition.outputDefinitions.map((d) => d.type.displayName))),
    },
  ];
}

function filterSolidsWithSearch(solids: Solid[], search: TokenizingFieldValue[]) {
  return solids.filter((s) => {
    for (const item of search) {
      if (
        (item.token === 'name' || item.token === undefined) &&
        !s.definition.name.startsWith(item.value)
      ) {
        return false;
      }
      if (
        (item.token === 'pipeline' || item.token === 'job') &&
        !s.invocations.some((i) => i.pipeline.name === item.value)
      ) {
        return false;
      }
      if (
        item.token === 'input' &&
        !s.definition.inputDefinitions.some((i) => i.type.displayName.startsWith(item.value))
      ) {
        return false;
      }
      if (
        item.token === 'output' &&
        !s.definition.outputDefinitions.some((i) => i.type.displayName.startsWith(item.value))
      ) {
        return false;
      }
    }
    return true;
  });
}

interface Props {
  name?: string;
  repoAddress: RepoAddress;
}

export const SolidsRoot: React.FC<Props> = (props) => {
  const {name, repoAddress} = props;

  useDocumentTitle('Ops');
  const repositorySelector = repoAddressToSelector(repoAddress);

  const queryResult = useQuery<SolidsRootQuery>(SOLIDS_ROOT_QUERY, {
    variables: {repositorySelector},
  });

  return (
    <div style={{height: '100%'}}>
      <Loading queryResult={queryResult}>
        {({repositoryOrError}) => {
          if (repositoryOrError?.__typename === 'Repository' && repositoryOrError.usedSolids) {
            return (
              <SolidsRootWithData
                {...props}
                name={name}
                repoAddress={repoAddress}
                usedSolids={repositoryOrError.usedSolids}
              />
            );
          }
          return null;
        }}
      </Loading>
    </div>
  );
};

const SolidsRootWithData: React.FC<Props & {usedSolids: Solid[]}> = (props) => {
  const {name, repoAddress, usedSolids} = props;
  const history = useHistory();
  const location = useLocation();

  const {q, typeExplorer} = querystring.parse(location.search);
  const suggestions = searchSuggestionsForSolids(usedSolids);
  const search = tokenizedValuesFromString((q as string) || '', suggestions);
  const filtered = filterSolidsWithSearch(usedSolids, search);

  const selected = usedSolids.find((s) => s.definition.name === name);

  const onSearch = (search: TokenizingFieldValue[]) => {
    history.replace({
      search: `?${querystring.stringify({q: stringFromValue(search)})}`,
    });
  };

  const onClickSolid = (defName: string) => {
    history.replace(
      workspacePathFromAddress(repoAddress, `/solids/${defName}?${querystring.stringify({q})}`),
    );
  };

  React.useEffect(() => {
    // If the user has typed in a search that brings us to a single result, autoselect it
    if (filtered.length === 1 && (!selected || filtered[0] !== selected)) {
      onClickSolid(filtered[0].definition.name);
    }

    // If the user has clicked a type, translate it into a search
    if (typeof typeExplorer === 'string') {
      onSearch([...search, {token: 'input', value: typeExplorer}]);
    }
  });

  const onClickInvocation = React.useCallback(
    ({pipelineName, handleID}) => {
      history.push(
        workspacePathFromAddress(
          repoAddress,
          `/pipeline_or_job/${pipelineName}/${handleID.split('.').join('/')}`,
        ),
      );
    },
    [history, repoAddress],
  );

  return (
    <div style={{height: '100%', display: 'flex'}}>
      <SplitPanelContainer
        identifier="ops"
        firstInitialPercent={40}
        firstMinSize={420}
        first={
          <SolidListColumnContainer>
            <Box
              padding={{vertical: 12, horizontal: 24}}
              border={{side: 'bottom', width: 1, color: ColorsWIP.KeylineGray}}
            >
              <TokenizingField
                values={search}
                onChange={(search) => onSearch(search)}
                suggestionProviders={suggestions}
                placeholder={'Filter by name or input/output type...'}
              />
            </Box>
            <div style={{flex: 1}}>
              <AutoSizer nonce={window.__webpack_nonce__}>
                {({height, width}) => (
                  <SolidList
                    height={height}
                    width={width}
                    selected={selected}
                    onClickSolid={onClickSolid}
                    items={filtered.sort((a, b) =>
                      a.definition.name.localeCompare(b.definition.name),
                    )}
                  />
                )}
              </AutoSizer>
            </div>
          </SolidListColumnContainer>
        }
        second={
          selected ? (
            <SolidDetailScrollContainer>
              <UsedSolidDetails
                name={selected.definition.name}
                onClickInvocation={onClickInvocation}
                repoAddress={repoAddress}
              />
            </SolidDetailScrollContainer>
          ) : (
            <Box padding={{vertical: 64}}>
              <NonIdealState
                icon="no-results"
                title="No op selected"
                description="Select an op to see its definition and invocations"
              />
            </Box>
          )
        }
      />
    </div>
  );
};

interface SolidListProps {
  items: Solid[];
  width: number;
  height: number;
  selected: Solid | undefined;
  onClickSolid: (name: string) => void;
}

const SolidList: React.FunctionComponent<SolidListProps> = (props) => {
  const {items, selected} = props;
  const cache = React.useRef(new CellMeasurerCache({defaultHeight: 60, fixedWidth: true}));

  // Reset our cell sizes when the panel's width is changed. This is similar to a useEffect
  // but we need it to run /before/ the render not just after it completes.
  const lastWidth = React.useRef(props.width);
  if (props.width !== lastWidth.current) {
    cache.current.clearAll();
    lastWidth.current = props.width;
  }

  const selectedIndex = selected ? items.findIndex((item) => item === selected) : undefined;

  return (
    <Container>
      <List
        width={props.width}
        height={props.height}
        rowCount={props.items.length}
        rowHeight={cache.current.rowHeight}
        scrollToIndex={selectedIndex}
        className="solids-list"
        rowRenderer={({parent, index, key, style}) => {
          const solid = props.items[index];
          return (
            <CellMeasurer cache={cache.current} index={index} parent={parent} key={key}>
              <SolidListItem
                style={style}
                selected={solid === props.selected}
                onClick={() => props.onClickSolid(solid.definition.name)}
              >
                <SolidName>{solid.definition.name}</SolidName>
                <SolidTypeSignature definition={solid.definition} />
              </SolidListItem>
            </CellMeasurer>
          );
        }}
        overscanRowCount={10}
      />
    </Container>
  );
};

const Container = styled.div`
  .solids-list:focus {
    outline: none;
  }
`;

const SOLIDS_ROOT_QUERY = gql`
  query SolidsRootQuery($repositorySelector: RepositorySelector!) {
    repositoryOrError(repositorySelector: $repositorySelector) {
      ... on Repository {
        id
        usedSolids {
          __typename
          definition {
            name
            ...SolidTypeSignatureFragment
          }
          invocations {
            __typename
            pipeline {
              id
              isJob
              name
            }
          }
        }
      }
    }
  }
  ${SOLID_TYPE_SIGNATURE_FRAGMENT}
`;

const SolidListItem = styled.div<{selected: boolean}>`
  background: ${({selected}) => (selected ? ColorsWIP.Gray100 : ColorsWIP.White)};
  box-shadow: ${({selected}) => (selected ? ColorsWIP.HighlightGreen : 'transparent')} 4px 0 0 inset,
    ${ColorsWIP.KeylineGray} 0 -1px 0 inset;
  color: ${ColorsWIP.Gray800};
  cursor: pointer;
  font-size: 14px;
  display: flex;
  flex-direction: column;
  padding: 12px 24px;
  user-select: none;

  & > code.bp3-code {
    color: ${ColorsWIP.Gray800};
    background: transparent;
    font-family: ${FontFamily.monospace};
    padding: 5px 0 0 0;
  }
`;

const SolidName = styled.div`
  flex: 1;
  font-weight: 600;
`;

const SolidListColumnContainer = styled.div`
  display: flex;
  flex-direction: column;
  height: 100%;
`;
