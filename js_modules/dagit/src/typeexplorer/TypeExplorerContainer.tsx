import * as React from "react";
import gql from "graphql-tag";
import Loading from "../Loading";
import { Query, QueryResult } from "react-apollo";
import TypeExplorer from "./TypeExplorer";
import {
  TypeExplorerContainerQuery,
  TypeExplorerContainerQueryVariables
} from "./types/TypeExplorerContainerQuery";

interface ITypeExplorerContainerProps {
  pipelineName: string;
  typeName: string;
}

export default class TypeExplorerContainer extends React.Component<
  ITypeExplorerContainerProps
> {
  render() {
    return (
      <Query
        query={TYPE_EXPLORER_CONTAINER_QUERY}
        variables={{
          pipelineName: this.props.pipelineName,
          runtimeTypeName: this.props.typeName
        }}
      >
        {(
          queryResult: QueryResult<
            TypeExplorerContainerQuery,
            TypeExplorerContainerQueryVariables
          >
        ) => {
          return (
            <Loading queryResult={queryResult}>
              {data => {
                if (
                  data.runtimeTypeOrError &&
                  data.runtimeTypeOrError.__typename === "RegularRuntimeType"
                ) {
                  return <TypeExplorer type={data.runtimeTypeOrError} />;
                } else {
                  return <div>Type Not Found</div>;
                }
              }}
            </Loading>
          );
        }}
      </Query>
    );
  }
}

export const TYPE_EXPLORER_CONTAINER_QUERY = gql`
  query TypeExplorerContainerQuery(
    $pipelineName: String!
    $runtimeTypeName: String!
  ) {
    runtimeTypeOrError(
      pipelineName: $pipelineName
      runtimeTypeName: $runtimeTypeName
    ) {
      __typename
      ... on RegularRuntimeType {
        ...TypeExplorerFragment
      }
    }
  }

  ${TypeExplorer.fragments.TypeExplorerFragment}
`;
