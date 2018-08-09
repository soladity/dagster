import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Card, Colors } from "@blueprintjs/core";
import { LinkHorizontal as Link } from "@vx/shape";
import PanAndZoom from "./PanAndZoom";
import PipelineColorScale from "./PipelineColorScale";
import PipelineLegend from "./PipelineLegend";
import SolidNode from "./SolidNode";
import {
  getDagrePipelineLayout,
  IFullPipelineLayout
} from "./getFullSolidLayout";
import { PipelineGraphFragment } from "./types/PipelineGraphFragment";

interface IPipelineGraphProps {
  pipeline: PipelineGraphFragment;
  selectedSolid?: string;
  onClickSolid?: (solidName: string) => void;
}

export default class PipelineGraph extends React.Component<
  IPipelineGraphProps,
  {}
> {
  static fragments = {
    PipelineGraphFragment: gql`
      fragment PipelineGraphFragment on Pipeline {
        solids {
          ...SolidNodeFragment
        }
      }

      ${SolidNode.fragments.SolidNodeFragment}
    `
  };

  renderSolids(layout: IFullPipelineLayout) {
    return this.props.pipeline.solids.map((solid, i) => {
      const solidLayout = layout.solids[solid.name];
      return (
        <SolidNode
          key={solid.name}
          solid={solid}
          layout={solidLayout}
          onClick={this.props.onClickSolid}
          selected={this.props.selectedSolid === solid.name}
        />
      );
    });
  }

  renderConnections(layout: IFullPipelineLayout) {
    const connections: Array<{
      from: string;
      to: { solidName: string; inputName: string };
    }> = [];

    this.props.pipeline.solids.forEach(solid => {
      solid.inputs.forEach(input => {
        if (input.dependsOn) {
          connections.push({
            from: input.dependsOn.name,
            to: {
              solidName: solid.name,
              inputName: input.name
            }
          });
        }
      });
    });

    const links = connections.map(
      ({ from, to: { solidName, inputName } }, i) => (
        <StyledLink
          key={i}
          data={{
            source: layout.solids[from].output.port,
            target: layout.solids[solidName].inputs[inputName].port
          }}
          x={(d: { x: number; y: number }) => d.x}
          y={(d: { x: number; y: number }) => d.y}
        />
      )
    );

    return <g>{links}</g>;
  }

  render() {
    const layout = getDagrePipelineLayout(this.props.pipeline);

    return (
      <GraphWrapper>
        <LegendWrapper>
          <PipelineLegend />
        </LegendWrapper>
        <PanAndZoomStyled
          width={layout.width}
          height={layout.height + 300}
          renderOnChange={true}
          scaleFactor={1.1}
        >
          <SVGContainer width={layout.width} height={layout.height + 300}>
            {this.renderConnections(layout)}
            {this.renderSolids(layout)}
          </SVGContainer>
        </PanAndZoomStyled>
      </GraphWrapper>
    );
  }
}

const GraphWrapper = styled.div`
  width: 100%;
  height: 100%;
  position: relative;
  overflow: hidden;
  user-select: none;
  background-color: ${Colors.LIGHT_GRAY5};
`;

const PanAndZoomStyled = styled(PanAndZoom)`
  width: 100%;
  height: 100%;
`;

const SVGContainer = styled.svg`
  border-radius: 0;
`;

const LegendWrapper = styled.div`
  padding: 10px;
  margin: 5px;
  border: 1px solid ${Colors.GRAY1};
  border-radius: 3px;
  width: auto;
  position: absolute;
`;

const StyledLink = styled(Link)`
  stroke-width: 2;
  stroke: ${Colors.BLACK}
  strokeOpacity: 0.6;
  fill: none;
`;
