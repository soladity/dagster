import * as React from "react";
import gql from "graphql-tag";
import { useQuery } from "react-apollo";
import { Spinner } from "@blueprintjs/core";
import { InstanceDetailsQuery } from "./types/InstanceDetailsQuery";
import { ScrollContainer, Header } from "./ListComponents";
import { UnControlled as CodeMirrorReact } from "react-codemirror2";
import { createGlobalStyle } from "styled-components/macro";

const CodeMirrorShimStyle = createGlobalStyle`
  .react-codemirror2 {
    height: 100%;
    flex: 1;
    position: relative;
  }
  .react-codemirror2 .CodeMirror {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    height: initial;
  }
`;

export const InstanceDetailsRoot: React.FunctionComponent = () => {
  const { data } = useQuery<InstanceDetailsQuery>(INSTANCE_DETAILS_QUERY, {
    fetchPolicy: "cache-and-network"
  });

  return data ? (
    <ScrollContainer>
      <Header>{`Dagster ${data.version}`}</Header>
      <CodeMirrorShimStyle />
      <CodeMirrorReact
        value={data?.instance.info}
        options={{
          mode: "yaml",
          readOnly: true
        }}
      />
    </ScrollContainer>
  ) : (
    <Spinner size={35} />
  );
};

export const INSTANCE_DETAILS_QUERY = gql`
  query InstanceDetailsQuery {
    version
    instance {
      info
    }
  }
`;
