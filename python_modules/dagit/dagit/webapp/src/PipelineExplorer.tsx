import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { History } from "history";
import { Colors } from "@blueprintjs/core";
import { Route } from "react-router";
import { parse as parseQueryString } from "query-string";
import { PipelineExplorerFragment } from "./types/PipelineExplorerFragment";
import { PipelineExplorerSolidFragment } from "./types/PipelineExplorerSolidFragment";
import PipelineGraph from "./graph/PipelineGraph";
import { getDagrePipelineLayout } from "./graph/getFullSolidLayout";
import { PanelDivider } from "./PanelDivider";
import Config from "./Config";
import SidebarTabbedContainer from "./SidebarTabbedContainer";

interface IPipelineExplorerProps {
  history: History;
  pipeline: PipelineExplorerFragment;
  solid: PipelineExplorerSolidFragment | undefined;
}

interface IPipelineExplorerState {
  filter: string;
  graphVW: number;
  configCode: string;
}

export default class PipelineExplorer extends React.Component<
  IPipelineExplorerProps,
  IPipelineExplorerState
> {
  static fragments = {
    PipelineExplorerFragment: gql`
      fragment PipelineExplorerFragment on Pipeline {
        name
        description
        contexts {
          name
          description
          config {
            ...ConfigFragment
          }
        }
        ...PipelineGraphFragment
        ...SidebarTabbedContainerPipelineFragment
      }

      ${Config.fragments.ConfigFragment}
      ${PipelineGraph.fragments.PipelineGraphFragment}
      ${SidebarTabbedContainer.fragments.SidebarTabbedContainerPipelineFragment}
    `,
    PipelineExplorerSolidFragment: gql`
      fragment PipelineExplorerSolidFragment on Solid {
        name
        ...PipelineGraphSolidFragment
        ...SidebarTabbedContainerSolidFragment
      }

      ${PipelineGraph.fragments.PipelineGraphSolidFragment}
      ${SidebarTabbedContainer.fragments.SidebarTabbedContainerSolidFragment}
    `
  };

  constructor(props: IPipelineExplorerProps) {
    super(props);
    const configKey = getConfigStorageKey(props.pipeline);
    let configCode = localStorage.getItem(configKey);
    if (!configCode || typeof configCode !== "string") {
      configCode = "# This is config editor. Enjoy!";
    }
    this.state = {
      filter: "",
      graphVW: 70,
      configCode
    };
  }

  handleConfigChange = (newValue: string) => {
    const configKey = getConfigStorageKey(this.props.pipeline);
    localStorage.setItem(configKey, newValue);
    this.setState({
      configCode: newValue
    });
  };

  handleClickSolid = (solidName: string) => {
    const { history, pipeline } = this.props;
    history.push(`/${pipeline.name}/${solidName}`);
  };

  handleClickBackground = () => {
    const { history, pipeline } = this.props;
    history.push(`/${pipeline.name}`);
  };

  public render() {
    const { pipeline, solid } = this.props;
    const { filter, graphVW } = this.state;

    return (
      <PipelinesContainer>
        <PipelinePanel key="graph" style={{ width: `${graphVW}vw` }}>
          <SearchOverlay>
            <input
              type="text"
              placeholder="Filter..."
              value={filter}
              onChange={e => this.setState({ filter: e.target.value })}
            />
          </SearchOverlay>
          <PipelineGraph
            pipeline={pipeline}
            onClickSolid={this.handleClickSolid}
            onClickBackground={this.handleClickBackground}
            layout={getDagrePipelineLayout(pipeline)}
            selectedSolid={solid}
            highlightedSolids={pipeline.solids.filter(
              s => filter && s.name.includes(filter)
            )}
          />
        </PipelinePanel>
        <PanelDivider onMove={(vw: number) => this.setState({ graphVW: vw })} />
        <RightInfoPanel style={{ width: `${100 - graphVW}vw` }}>
          <Route
            children={({ location }: { location: any }) => (
              <SidebarTabbedContainer
                pipeline={pipeline}
                solid={solid}
                configCode={this.state.configCode}
                onConfigChange={this.handleConfigChange}
                {...parseQueryString(location.search || "")}
              />
            )}
          />
        </RightInfoPanel>
      </PipelinesContainer>
    );
  }
}

function getConfigStorageKey(pipeline: PipelineExplorerFragment) {
  return `dagit.pipelineConfigStorage.${pipeline.name}`;
}

const PipelinesContainer = styled.div`
  flex: 1 1;
  display: flex;
  width: 100%;
  height: 100vh;
  top: 0;
  position: absolute;
  padding-top: 50px;
`;

const PipelinePanel = styled.div`
  height: 100%;
  position: relative;
`;

const RightInfoPanel = styled.div`
  height: 100%;
  overflow-y: scroll;
  background: ${Colors.WHITE};
`;

const SearchOverlay = styled.div`
  background: rgba(0, 0, 0, 0.2);
  z-index: 2;
  padding: 7px;
  display: inline-block;
  width: 150px;
  position: absolute;
  right: 0;
`;
