import * as React from "react";
import gql from "graphql-tag";
import * as Color from "color";
import styled from "styled-components";
import { History } from "history";
import { Icon, Colors } from "@blueprintjs/core";
import { Route } from "react-router";
import { Link } from "react-router-dom";
import { parse as parseQueryString } from "query-string";

import { PipelineExplorerFragment } from "./types/PipelineExplorerFragment";
import PipelineGraph from "./graph/PipelineGraph";
import { PanelDivider } from "./PanelDivider";
import SidebarTabbedContainer from "./SidebarTabbedContainer";
import { SolidJumpBar } from "./PipelineJumpComponents";
import {
  PipelineExplorerSolidHandleFragment,
  PipelineExplorerSolidHandleFragment_solid
} from "./types/PipelineExplorerSolidHandleFragment";
import {
  getDagrePipelineLayout,
  IFullPipelineLayout
} from "./graph/getFullSolidLayout";

interface IPipelineExplorerProps {
  history: History;
  path: string[];
  pipeline: PipelineExplorerFragment;
  handles: PipelineExplorerSolidHandleFragment[];
  selectedHandle?: PipelineExplorerSolidHandleFragment;
  selectedDefinitionInvocations?: PipelineExplorerSolidHandleFragment[];
  parentHandle?: PipelineExplorerSolidHandleFragment;
}

interface IPipelineExplorerState {
  filter: string;
  graphVW: number;
}

export type SolidNameOrPath = { name: string } | { path: string[] };

export default class PipelineExplorer extends React.Component<
  IPipelineExplorerProps,
  IPipelineExplorerState
> {
  static fragments = {
    PipelineExplorerFragment: gql`
      fragment PipelineExplorerFragment on Pipeline {
        name
        description
        ...SidebarTabbedContainerPipelineFragment
      }

      ${SidebarTabbedContainer.fragments.SidebarTabbedContainerPipelineFragment}
    `,
    PipelineExplorerSolidHandleFragment: gql`
      fragment PipelineExplorerSolidHandleFragment on SolidHandle {
        handleID
        solid {
          name
          ...PipelineGraphSolidFragment
          ...SidebarTabbedContainerSolidFragment
        }
      }

      ${PipelineGraph.fragments.PipelineGraphSolidFragment}
      ${SidebarTabbedContainer.fragments.SidebarTabbedContainerSolidFragment}
    `
  };

  state = {
    filter: "",
    graphVW: 70
  };

  handleAdjustPath = (fn: (solidNames: string[]) => void) => {
    const { history, pipeline, path } = this.props;
    let next = [...path];
    const retValue = fn(next);
    if (retValue !== undefined) {
      throw new Error(
        "handleAdjustPath function is expected to mutate the array"
      );
    }
    history.push(`/${pipeline.name}/explore/${next.join("/")}`);
  };

  handleClickSolid = (arg: SolidNameOrPath) => {
    this.handleAdjustPath(solidNames => {
      if ("name" in arg) {
        solidNames[solidNames.length - 1] = arg.name;
      } else {
        solidNames.length = 0;
        solidNames.push(...arg.path);
      }
    });
  };

  handleEnterCompositeSolid = (arg: SolidNameOrPath) => {
    // To animate the rect of the composite solid expanding correctly, we need
    // to select it before entering it so we can draw the "initial state" of the
    // labeled rectangle.
    this.handleClickSolid(arg);

    window.requestAnimationFrame(() => {
      this.handleAdjustPath(solidNames => {
        const last = "name" in arg ? arg.name : arg.path[arg.path.length - 1];
        solidNames[solidNames.length - 1] = last;
        solidNames.push("");
      });
    });
  };

  handleLeaveCompositeSolid = () => {
    this.handleAdjustPath(solidNames => {
      solidNames.pop();
    });
  };

  handleClickBackground = () => {
    this.handleClickSolid({ name: "" });
  };

  _layoutCacheKey: string | undefined;
  _layoutCache: IFullPipelineLayout | undefined;

  getLayout = (solids: PipelineExplorerSolidHandleFragment_solid[]) => {
    const key = solids.map(s => s.name).join("|");
    if (this._layoutCacheKey === key && this._layoutCache) {
      return this._layoutCache;
    }
    this._layoutCache = getDagrePipelineLayout(solids);
    this._layoutCacheKey = key;
    return this._layoutCache;
  };

  public render() {
    const {
      pipeline,
      parentHandle,
      selectedHandle,
      selectedDefinitionInvocations,
      path
    } = this.props;
    const { filter, graphVW } = this.state;

    const solids = this.props.handles.map(h => h.solid);

    const backgroundColor = parentHandle
      ? Colors.LIGHT_GRAY3
      : Colors.LIGHT_GRAY5;

    const backgroundTranslucent = Color(backgroundColor)
      .fade(0.6)
      .toString();

    return (
      <PipelinesContainer>
        <PipelinePanel key="graph" style={{ width: `${graphVW}vw` }}>
          <PathOverlay style={{ background: backgroundTranslucent }}>
            <Link style={{ padding: 3 }} to={`/${pipeline.name}/explore/`}>
              <Icon icon="diagram-tree" />
            </Link>
            <Icon icon="chevron-right" />
            {path.slice(0, path.length - 1).map((name, idx) => (
              <React.Fragment key={idx}>
                <Link
                  style={{ padding: 3 }}
                  to={`/${pipeline.name}/explore/${path
                    .slice(0, idx + 1)
                    .join("/")}`}
                >
                  {name}
                </Link>
                <Icon icon="chevron-right" />
              </React.Fragment>
            ))}
            <SolidJumpBar
              solids={solids}
              selectedSolid={selectedHandle && selectedHandle.solid}
              onItemSelect={solid =>
                this.handleClickSolid({ name: solid.name })
              }
            />
          </PathOverlay>
          <SearchOverlay style={{ background: backgroundTranslucent }}>
            <SolidSearchInput
              type="text"
              placeholder="Filter..."
              value={filter}
              onChange={e => this.setState({ filter: e.target.value })}
            />
          </SearchOverlay>
          <PipelineGraph
            pipelineName={pipeline.name}
            backgroundColor={backgroundColor}
            solids={solids}
            selectedHandleID={selectedHandle && selectedHandle.handleID}
            selectedSolid={selectedHandle && selectedHandle.solid}
            parentHandleID={parentHandle && parentHandle.handleID}
            parentSolid={parentHandle && parentHandle.solid}
            onClickSolid={this.handleClickSolid}
            onClickBackground={this.handleClickBackground}
            onEnterCompositeSolid={this.handleEnterCompositeSolid}
            onLeaveCompositeSolid={this.handleLeaveCompositeSolid}
            layout={this.getLayout(solids)}
            highlightedSolids={solids.filter(
              s => filter && s.name.includes(filter)
            )}
          />
        </PipelinePanel>
        <PanelDivider
          axis="horizontal"
          onMove={(graphVW: number) => this.setState({ graphVW })}
        />
        <RightInfoPanel style={{ width: `${100 - graphVW}vw` }}>
          <Route
            children={({ location }: { location: any }) => (
              <SidebarTabbedContainer
                pipeline={pipeline}
                solid={selectedHandle && selectedHandle.solid}
                solidDefinitionInvocations={selectedDefinitionInvocations}
                parentSolid={parentHandle && parentHandle.solid}
                onEnterCompositeSolid={this.handleEnterCompositeSolid}
                onClickSolid={this.handleClickSolid}
                {...parseQueryString(location.search || "")}
              />
            )}
          />
        </RightInfoPanel>
      </PipelinesContainer>
    );
  }
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
  z-index: 2;
  padding: 7px 5px;
  display: inline-flex;
  align-items: stretch;
  position: absolute;
  right: 0;
`;

const PathOverlay = styled.div`
  z-index: 2;
  padding: 7px;
  padding-left: 10px;
  max-width: 80%;
  display: inline-flex;
  align-items: center;
  position: absolute;
  left: 0;
`;

const SolidSearchInput = styled.input`
  margin-left: 7px;
  padding: 5px 5px;
  font-size: 14px;
  border: 1px solid ${Colors.GRAY4};
`;
