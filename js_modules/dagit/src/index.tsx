import * as React from "react";
import * as ReactDOM from "react-dom";
import { createGlobalStyle } from "styled-components";
import ApolloClient from "apollo-client";
import { ApolloLink } from "apollo-link";
import { onError } from "apollo-link-error";
import { ApolloProvider } from "react-apollo";
import { SubscriptionClient } from "subscriptions-transport-ws";
import { WebSocketLink } from "apollo-link-ws";
import { WebsocketStatusProvider } from "./WebsocketStatus";
import { App } from "./App";
import AppCache from "./AppCache";
import { Toaster, Position, Intent } from "@blueprintjs/core";

import "@blueprintjs/core/lib/css/blueprint.css";
import "@blueprintjs/table/lib/css/table.css";
import "@blueprintjs/icons/lib/css/blueprint-icons.css";
import "@blueprintjs/select/lib/css/blueprint-select.css";
import { WEBSOCKET_URI, patchCopyToRemoveZeroWidthUnderscores } from "./Util";

// The solid sidebar and other UI elements insert zero-width spaces so solid names
// break on underscores rather than arbitrary characters, but we need to remove these
// when you copy-paste so they don't get pasted into editors, etc.
patchCopyToRemoveZeroWidthUnderscores();

const GlobalStyle = createGlobalStyle`
  * {
    box-sizing: border-box;
  }

  html, body, #root {
    width: 100vw;
    height: 100vh;
    overflow: hidden;
    display: flex;
    flex: 1 1;
  }

  #root {
    display: flex;
    flex-direction: column;
    align-items: stretch;
  }

  body {
    margin: 0;
    padding: 0;
    font-family: sans-serif;
  }
`;

const ErrorToaster = Toaster.create({ position: Position.TOP_RIGHT });

const websocketClient = new SubscriptionClient(WEBSOCKET_URI, {
  reconnect: true,
  lazy: true
});

const errorLink = onError(({ graphQLErrors, networkError }) => {
  if (graphQLErrors) {
    graphQLErrors.map(error => {
      ErrorToaster.show({
        message: `[GraphQL error] ${error.message}`,
        intent: Intent.DANGER
      });
      console.error("[GraphQL error]", error);
      return null;
    });
  }
  if (networkError) {
    ErrorToaster.show({
      message: `[Network error] ${networkError}`,
      intent: Intent.DANGER
    });
    console.error("[Network error]", networkError);
  }
});

const client = new ApolloClient({
  cache: AppCache,
  link: ApolloLink.from([errorLink, new WebSocketLink(websocketClient)])
});

ReactDOM.render(
  <WebsocketStatusProvider websocket={websocketClient}>
    <GlobalStyle />
    <ApolloProvider client={client}>
      <App />
    </ApolloProvider>
  </WebsocketStatusProvider>,
  document.getElementById("root") as HTMLElement
);
