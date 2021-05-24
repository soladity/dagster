import {loader} from 'graphql.macro';
import * as React from 'react';
import {MemoryRouter, MemoryRouterProps} from 'react-router-dom';

import {AppContext, AppContextValue} from '../app/AppContext';
import {PERMISSIONS_ALLOW_ALL} from '../app/Permissions';
import {WorkspaceProvider} from '../workspace/WorkspaceContext';

import {ApolloTestProps, ApolloTestProvider} from './ApolloTestProvider';

const typeDefs = loader('../graphql/schema.graphql');

const testValue = {
  basePath: '',
  permissions: PERMISSIONS_ALLOW_ALL,
  rootServerURI: '',
  websocketURI: 'ws://foo',
};

interface Props {
  appContextProps?: Partial<AppContextValue>;
  routerProps?: MemoryRouterProps;
  apolloProps?: ApolloTestProps;
}

export const TestProvider: React.FC<Props> = (props) => {
  const {apolloProps, appContextProps, routerProps} = props;

  return (
    <AppContext.Provider value={{...testValue, ...appContextProps}}>
      <MemoryRouter {...routerProps}>
        <ApolloTestProvider {...apolloProps} typeDefs={typeDefs}>
          <WorkspaceProvider>{props.children}</WorkspaceProvider>
        </ApolloTestProvider>
      </MemoryRouter>
    </AppContext.Provider>
  );
};
