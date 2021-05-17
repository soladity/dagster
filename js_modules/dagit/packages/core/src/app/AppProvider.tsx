import '@blueprintjs/core/lib/css/blueprint.css';
import '@blueprintjs/icons/lib/css/blueprint-icons.css';
import '@blueprintjs/select/lib/css/blueprint-select.css';
import '@blueprintjs/table/lib/css/table.css';
import '@blueprintjs/popover2/lib/css/blueprint-popover2.css';

import {concat, split, ApolloLink, ApolloClient, ApolloProvider, HttpLink} from '@apollo/client';
import {WebSocketLink} from '@apollo/client/link/ws';
import {getMainDefinition} from '@apollo/client/utilities';
import {Colors} from '@blueprintjs/core';
import * as React from 'react';
import {BrowserRouter} from 'react-router-dom';
import {createGlobalStyle} from 'styled-components/macro';
import {SubscriptionClient} from 'subscriptions-transport-ws';

import {FontFamily} from '../ui/styles';
import {WorkspaceProvider} from '../workspace/WorkspaceContext';

import {AppCache} from './AppCache';
import {AppContext} from './AppContext';
import {AppErrorLink} from './AppError';
import {CustomAlertProvider} from './CustomAlertProvider';
import {CustomConfirmationProvider} from './CustomConfirmationProvider';
import {CustomTooltipProvider} from './CustomTooltipProvider';
import {LayoutProvider} from './LayoutProvider';
import {Permissions} from './Permissions';
import {formatElapsedTime, patchCopyToRemoveZeroWidthUnderscores, debugLog} from './Util';
import {WebsocketStatusProvider} from './WebsocketStatus';
import {TimezoneProvider} from './time/TimezoneContext';

// The solid sidebar and other UI elements insert zero-width spaces so solid names
// break on underscores rather than arbitrary characters, but we need to remove these
// when you copy-paste so they don't get pasted into editors, etc.
patchCopyToRemoveZeroWidthUnderscores();

const GlobalStyle = createGlobalStyle`
  * {
    box-sizing: border-box;
  }

  html, body, #root {
    color: ${Colors.DARK_GRAY4};
    width: 100vw;
    height: 100vh;
    overflow: hidden;
    display: flex;
    flex: 1 1;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }

  #root {
    display: flex;
    flex-direction: column;
    align-items: stretch;
  }

  body {
    margin: 0;
    padding: 0;
  }

  body, button, input, select, textarea {
    font-family: ${FontFamily.default};
  }

  code, pre {
    font-family: ${FontFamily.monospace};
  }
`;

interface Props {
  config: {
    graphqlURI: string;
    basePath?: string;
    permissions: Permissions;
    subscriptionParams?: {[key: string]: string};
    sessionToken?: string;
  };
}

export const AppProvider: React.FC<Props> = (props) => {
  const {
    sessionToken = '',
    basePath = '',
    permissions,
    subscriptionParams = {},
    graphqlURI,
  } = props.config;

  const httpGraphqlURI = graphqlURI.replace('wss://', 'https://').replace('ws://', 'http://');

  const httpURI = httpGraphqlURI || `${document.location.origin}${basePath}/graphql`;

  const websocketURI = httpURI.replace('https://', 'wss://').replace('http://', 'ws://');

  // The address to the dagit server (eg: http://localhost:5000) based
  // on our current "GRAPHQL_URI" env var. Note there is no trailing slash.
  const rootServerURI = httpURI.replace('/graphql', '');

  const websocketClient = React.useMemo(() => {
    return new SubscriptionClient(websocketURI, {
      reconnect: true,
      connectionParams: subscriptionParams,
    });
  }, [subscriptionParams, websocketURI]);

  const apolloClient = React.useMemo(() => {
    const logLink = new ApolloLink((operation, forward) =>
      forward(operation).map((data) => {
        const time = performance.now() - operation.getContext().start;
        debugLog(`${operation.operationName} took ${formatElapsedTime(time)}`, {operation, data});
        return data;
      }),
    );

    const timeStartLink = new ApolloLink((operation, forward) => {
      operation.setContext({start: performance.now()});
      return forward(operation);
    });

    let httpLink: ApolloLink = new HttpLink({uri: httpURI});

    // add an auth header to the HTTP requests made by the app
    // note that the websocket-based subscriptions will not carry this header
    if (sessionToken) {
      const authMiddleware = new ApolloLink((operation, forward) => {
        operation.setContext({
          headers: {
            'Dagster-Session-Token': sessionToken,
          },
        });

        return forward(operation);
      });
      httpLink = concat(authMiddleware, httpLink);
    }

    const websocketLink = new WebSocketLink(websocketClient);

    // subscriptions should use the websocket link; queries & mutations should use HTTP
    const splitLink = split(
      ({query}) => {
        const definition = getMainDefinition(query);
        return definition.kind == 'OperationDefinition' && definition.operation == 'subscription';
      },
      websocketLink,
      httpLink,
    );

    return new ApolloClient({
      cache: AppCache,
      link: ApolloLink.from([logLink, AppErrorLink(), timeStartLink, splitLink]),
    });
  }, [sessionToken, httpURI, websocketClient]);

  const appContextValue = React.useMemo(
    () => ({
      basePath,
      permissions,
      rootServerURI,
      websocketURI,
    }),
    [basePath, permissions, rootServerURI, websocketURI],
  );

  return (
    <AppContext.Provider value={appContextValue}>
      <WebsocketStatusProvider websocket={websocketClient}>
        <GlobalStyle />
        <ApolloProvider client={apolloClient}>
          <BrowserRouter basename={basePath || ''}>
            <TimezoneProvider>
              <WorkspaceProvider>
                <CustomConfirmationProvider>
                  <LayoutProvider>{props.children}</LayoutProvider>
                </CustomConfirmationProvider>
                <CustomTooltipProvider />
                <CustomAlertProvider />
              </WorkspaceProvider>
            </TimezoneProvider>
          </BrowserRouter>
        </ApolloProvider>
      </WebsocketStatusProvider>
    </AppContext.Provider>
  );
};
