import React from "react";
import {
  Colors,
  InputGroup,
  ButtonGroup,
  Button,
  Icon
} from "@blueprintjs/core";
import gql from "graphql-tag";
import { useQuery } from "react-apollo";
import { Link } from "react-router-dom";
import styled from "styled-components/macro";

import { tabForPipelinePathComponent } from "./PipelineNav";
import { ContentListSolidsQuery } from "./types/ContentListSolidsQuery";
import { DagsterRepositoryContext } from "../DagsterRepositoryContext";

const iincludes = (haystack: string, needle: string) =>
  haystack.toLowerCase().includes(needle.toLowerCase());

export const EnvironmentContentList: React.FunctionComponent<{
  selector?: string;
  tab?: string;
}> = ({ tab, selector }) => {
  const [type, setType] = React.useState<"pipelines" | "solids">("pipelines");
  const { repository } = React.useContext(DagsterRepositoryContext);
  const pipelineTab = tabForPipelinePathComponent(tab);
  const [q, setQ] = React.useState<string>("");

  // Load solids, but only if the user clicks on the Solid option
  const solids = useQuery<ContentListSolidsQuery>(CONTENT_LIST_SOLIDS_QUERY, {
    fetchPolicy: "cache-first"
  });
  React.useEffect(() => {
    if (type === "solids") {
      solids.refetch();
    }
  }, [type, solids]);

  return (
    <div style={{ display: "flex", flexDirection: "column", flex: 1 }}>
      <Header>
        <InputGroup
          type="text"
          value={q}
          small
          placeholder={`Search ${type}...`}
          onChange={(e: React.ChangeEvent<any>) => setQ(e.target.value)}
          style={{
            border: `1px solid ${Colors.DARK_GRAY5}`,
            background: Colors.DARK_GRAY4
          }}
        />
        <div style={{ width: 4 }} />
        <ButtonGroup>
          <Button
            small={true}
            active={type === "pipelines"}
            intent={type === "pipelines" ? "primary" : "none"}
            icon={<Icon icon="diagram-tree" iconSize={13} />}
            onClick={() => setType("pipelines")}
          />
          <Button
            small={true}
            active={type === "solids"}
            intent={type === "solids" ? "primary" : "none"}
            icon={<Icon icon="git-commit" iconSize={13} />}
            onClick={() => setType("solids")}
          />
        </ButtonGroup>
      </Header>
      {type === "pipelines" ? (
        <Items>
          {(repository?.pipelines || [])
            .map(pipeline => pipeline.name)
            .filter(p => !q || iincludes(p, q))
            .map(p => (
              <Item
                key={p}
                className={p === selector ? "selected" : ""}
                to={`/pipeline/${p}/${pipelineTab.pathComponent}`}
              >
                {p}
              </Item>
            ))}
        </Items>
      ) : (
        <Items>
          {solids.data?.usedSolids
            .filter(
              s =>
                !q ||
                iincludes(s.definition.name, q) ||
                s.invocations.some(i => iincludes(i.pipeline.name, q))
            )
            .map(({ definition }) => (
              <Item
                key={definition.name}
                to={`/solid/${definition.name}`}
                className={definition.name === selector ? "selected" : ""}
              >
                {definition.name}
              </Item>
            ))}
        </Items>
      )}
    </div>
  );
};

const Header = styled.div`
  margin: 6px 10px;
  display: flex;
  & .bp3-input-group {
    flex: 1;
  }
`;

const Items = styled.div`
  flex: 1;
  overflow: auto;
  max-height: calc(100vh - 300px);
  &::-webkit-scrollbar {
    width: 11px;
  }

  scrollbar-width: thin;
  scrollbar-color: ${Colors.GRAY1} ${Colors.DARK_GRAY1};

  &::-webkit-scrollbar-track {
    background: ${Colors.DARK_GRAY1};
  }
  &::-webkit-scrollbar-thumb {
    background-color: ${Colors.GRAY1};
    border-radius: 6px;
    border: 3px solid ${Colors.DARK_GRAY1};
  }
`;

const Item = styled(Link)`
  font-size: 13px;
  text-overflow: ellipsis;
  overflow: hidden;
  padding: 8px 12px;
  padding-left: 8px;
  border-left: 4px solid transparent;
  border-bottom: 1px solid transparent;
  display: block;
  color: ${Colors.LIGHT_GRAY3} !important;
  &:hover {
    text-decoration: none;
    color: ${Colors.WHITE} !important;
  }
  &:focus {
    outline: 0;
  }
  &.selected {
    border-left: 4px solid ${Colors.COBALT3};
    border-bottom: 1px solid ${Colors.DARK_GRAY2};
    background: ${Colors.BLACK};
    font-weight: 600;
    color: ${Colors.WHITE} !important;
  }
`;

export const CONTENT_LIST_SOLIDS_QUERY = gql`
  query ContentListSolidsQuery {
    usedSolids {
      __typename
      definition {
        name
      }
      invocations {
        __typename
        pipeline {
          name
        }
      }
    }
  }
`;
