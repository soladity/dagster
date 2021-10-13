import {gql, useQuery} from '@apollo/client';
import {BreadcrumbProps, Breadcrumbs} from '@blueprintjs/core';
import * as React from 'react';
import {Link, Redirect, RouteComponentProps} from 'react-router-dom';
import styled from 'styled-components/macro';

import {Box} from '../ui/Box';
import {ColorsWIP} from '../ui/Colors';
import {Loading} from '../ui/Loading';
import {Page} from '../ui/Page';
import {PageHeader} from '../ui/PageHeader';
import {TagWIP} from '../ui/TagWIP';
import {Heading} from '../ui/Text';

import {AssetView} from './AssetView';
import {AssetsCatalogTable} from './AssetsCatalogTable';
import {AssetEntryRootQuery} from './types/AssetEntryRootQuery';
import {useAssetView} from './useAssetView';

// Jan 1, 2015 at 00:00 GMT
const EARLIEST_TIME = 1420070400000;

export const AssetEntryRoot: React.FC<RouteComponentProps> = ({location, match}) => {
  const currentPath: string[] = (match.params['0'] || '')
    .split('/')
    .filter((x: string) => x)
    .map(decodeURIComponent);

  const {pathname, search} = location;
  const asOf = React.useMemo(() => {
    const params = new URLSearchParams(search);
    return params.get('asOf');
  }, [search]);

  // Validate the `asOf` time, since it's user-specified.
  const invalidTime = React.useMemo(() => {
    const asOfNumber = Number(asOf);
    return asOfNumber && (asOfNumber < EARLIEST_TIME || asOfNumber > Date.now());
  }, [asOf]);

  const [view] = useAssetView();

  const queryResult = useQuery<AssetEntryRootQuery>(ASSET_ENTRY_ROOT_QUERY, {
    variables: {assetKey: {path: currentPath}},
  });

  const breadcrumbs = React.useMemo(() => {
    if (currentPath.length === 1 || view !== 'directory') {
      return null;
    }

    const list: BreadcrumbProps[] = [];
    currentPath.reduce((accum: string, elem: string) => {
      const href = `${accum}/${encodeURIComponent(elem)}`;
      list.push({text: elem, href});
      return href;
    }, '/instance/assets');

    return list;
  }, [currentPath, view]);

  // If the asOf timestamp is invalid, discard it via redirect.
  if (invalidTime) {
    return <Redirect to={pathname} />;
  }

  return (
    <Page>
      <PageHeader
        title={
          view !== 'directory' || !breadcrumbs ? (
            <Heading>{currentPath[currentPath.length - 1]}</Heading>
          ) : (
            <Box
              flex={{alignItems: 'center', gap: 4}}
              style={{maxWidth: '600px', overflow: 'hidden'}}
            >
              <Breadcrumbs
                items={breadcrumbs}
                breadcrumbRenderer={({text, href}) => (
                  <Heading>
                    <BreadcrumbLink to={href || '#'}>{text}</BreadcrumbLink>
                  </Heading>
                )}
                currentBreadcrumbRenderer={({text}) => <Heading>{text}</Heading>}
              />
            </Box>
          )
        }
        tags={<TagWIP icon="asset">Asset</TagWIP>}
      />
      <Loading queryResult={queryResult}>
        {({assetOrError}) => {
          if (assetOrError.__typename === 'AssetNotFoundError') {
            return <AssetsCatalogTable prefixPath={currentPath} />;
          }

          return <AssetView assetKey={{path: currentPath}} asOf={asOf} />;
        }}
      </Loading>
    </Page>
  );
};

const BreadcrumbLink = styled(Link)`
  color: ${ColorsWIP.Gray800};

  :hover,
  :active {
    color: ${ColorsWIP.Gray800};
  }
`;

const ASSET_ENTRY_ROOT_QUERY = gql`
  query AssetEntryRootQuery($assetKey: AssetKeyInput!) {
    assetOrError(assetKey: $assetKey) {
      __typename
      ... on Asset {
        id
        key {
          path
        }
      }
    }
  }
`;
