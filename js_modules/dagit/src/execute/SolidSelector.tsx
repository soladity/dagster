import {
  Colors,
  Button,
  Classes,
  Dialog,
  Intent,
  Spinner
} from "@blueprintjs/core";
import * as React from "react";
import gql from "graphql-tag";
import PipelineGraph from "../graph/PipelineGraph";
import { useQuery } from "react-apollo";
import {
  SolidSelectorQuery,
  SolidSelectorQuery_pipeline,
  SolidSelectorQuery_pipeline_solids
} from "./types/SolidSelectorQuery";
import {
  getDagrePipelineLayout,
  layoutsIntersect,
  pointsToBox
} from "../graph/getFullSolidLayout";
import SVGViewport from "../graph/SVGViewport";
import { IconNames } from "@blueprintjs/icons";
import { SubsetError } from "./PipelineExecutionContainer";

interface ISolidSelectorProps {
  pipelineName: string;
  subsetError: SubsetError;
  value: string[] | null;
  onChange: (value: string[] | null) => void;
}

interface ISolidSelectorInnerProps extends ISolidSelectorProps {
  pipeline: SolidSelectorQuery_pipeline | null;
}

interface ISolidSelectorState {
  // True if the modal is open
  open: boolean;

  // The list of solids currently highlighted in the modal.
  // (The solidSubset value to be committed upon close.)
  highlighted: string[];

  // The start / stop of the marquee selection tool
  toolRectStart: null | { x: number; y: number };
  toolRectEnd: null | { x: number; y: number };
}

function subsetDescription(
  solidSubset: string[] | null,
  pipeline: SolidSelectorQuery_pipeline
) {
  if (
    !solidSubset ||
    solidSubset.length === 0 ||
    solidSubset.length === pipeline.solids.length
  ) {
    return "All Solids";
  }
  if (solidSubset.length === 1) {
    return solidSubset[0];
  }

  // try to find a start solid that can get us to all the solids without
  // any others in the path, indicating that an range label (eg "A -> B")
  // would fit. TODO: Bidirectional A-star?!
  const rangeDescription = solidSubset
    .map(startName => {
      let solidName = startName;
      let rest = solidSubset.filter(s => s !== solidName);

      const nameMatch = (s: SolidSelectorQuery_pipeline_solids) =>
        s.name === solidName;

      const downstreamSolidSearch = (n: string) => rest.indexOf(n) !== -1;

      while (rest.length > 0) {
        const solid = pipeline.solids.find(nameMatch);
        if (!solid) return false;

        const downstreamSolidNames = solid.outputs.reduce(
          (v: string[], o) => v.concat(o.dependedBy.map(s => s.solid.name)),
          []
        );

        const nextSolidName = downstreamSolidNames.find(downstreamSolidSearch);
        if (!nextSolidName) return false;
        rest = rest.filter(s => s !== nextSolidName);
        solidName = nextSolidName;
      }
      return `${startName} → ${solidName}`;
    })
    .find(n => n !== false);

  if (rangeDescription) {
    return rangeDescription;
  }
  return `${solidSubset.length} solids`;
}

class SolidSelector extends React.PureComponent<
  ISolidSelectorInnerProps,
  ISolidSelectorState
> {
  state: ISolidSelectorState = {
    open: false,
    highlighted: [],
    toolRectStart: null,
    toolRectEnd: null
  };

  handleSVGMouseDown = (
    viewport: SVGViewport,
    event: React.MouseEvent<HTMLDivElement>
  ) => {
    const point = viewport.getOffsetXY(event);
    this.setState({ toolRectStart: point, toolRectEnd: point });

    const onMove = (event: MouseEvent) => {
      this.setState({ toolRectEnd: viewport.getOffsetXY(event) });
    };
    const onUp = () => {
      document.removeEventListener("mousemove", onMove);
      document.removeEventListener("mouseup", onUp);
      this.handleSelectSolidsInToolRect(viewport);
    };

    document.addEventListener("mousemove", onMove);
    document.addEventListener("mouseup", onUp);
    event.stopPropagation();
  };

  handleSelectSolidsInToolRect = (viewport: SVGViewport) => {
    const layout = getDagrePipelineLayout(
      this.props.pipeline ? this.props.pipeline.solids : []
    );
    const { toolRectEnd, toolRectStart } = this.state;
    if (!toolRectEnd || !toolRectStart) return;

    // Convert the tool rectangle to SVG coords
    const svgToolBox = pointsToBox(
      viewport.screenToSVGCoords(toolRectStart),
      viewport.screenToSVGCoords(toolRectEnd)
    );
    let highlighted = Object.keys(layout.solids).filter(name =>
      layoutsIntersect(svgToolBox, layout.solids[name].boundingBox)
    );

    // If you clicked a single solid, toggle the selection. Otherwise,
    // we blow away the ccurrently highlighted solids in favor of the new selection
    if (
      highlighted.length === 1 &&
      toolRectEnd.x === toolRectStart.x &&
      toolRectEnd.y === toolRectStart.y
    ) {
      const clickedSolid = highlighted[0];
      if (this.state.highlighted.indexOf(clickedSolid) !== -1) {
        highlighted = this.state.highlighted.filter(s => s !== clickedSolid);
      } else {
        highlighted = [...this.state.highlighted, clickedSolid];
      }
    }

    this.setState({
      toolRectEnd: null,
      toolRectStart: null,
      highlighted
    });
  };

  // Note: Having no elements highlighted means the entire pipeline executes.
  // The equivalent solidSubset is `null`, not `[]`, so we do some conversion here.

  handleOpen = () => {
    const { value, pipeline } = this.props;
    const valid = (value || []).filter(
      name => pipeline && !!pipeline.solids.find(s => s.name === name)
    );
    this.setState({ open: true, highlighted: valid });
  };

  handleSave = () => {
    const { highlighted } = this.state;
    this.props.onChange(highlighted.length > 0 ? [...highlighted] : null);
    this.setState({ open: false, highlighted: [] });
  };

  render() {
    const { pipeline, subsetError } = this.props;
    const { open, highlighted, toolRectEnd, toolRectStart } = this.state;

    const valid = !subsetError;

    const allSolidsSelected =
      !highlighted.length ||
      !pipeline ||
      highlighted.length === pipeline.solids.length;

    return (
      <div>
        <Dialog
          icon="info-sign"
          onClose={() => this.setState({ open: false })}
          style={{ width: "80vw", maxWidth: 1400, height: "80vh" }}
          title={"Select Solids to Execute"}
          usePortal={true}
          isOpen={open}
        >
          <div
            className={Classes.DIALOG_BODY}
            style={{
              margin: 0,
              marginBottom: 17,
              height: `calc(100% - 85px)`
            }}
          >
            <PipelineGraph
              backgroundColor={Colors.LIGHT_GRAY5}
              pipelineName={pipeline ? pipeline.name : ""}
              solids={pipeline ? pipeline.solids : []}
              interactor={{
                onMouseDown: this.handleSVGMouseDown,
                onWheel: () => {},
                render: () => {
                  if (!toolRectEnd || !toolRectStart) return null;
                  const box = pointsToBox(toolRectEnd, toolRectStart);
                  return (
                    <div
                      style={{
                        position: "absolute",
                        border: `1px dashed ${Colors.GRAY3}`,
                        left: box.x,
                        top: box.y,
                        width: box.width,
                        height: box.height
                      }}
                    />
                  );
                }
              }}
              layout={getDagrePipelineLayout(
                pipeline && pipeline.solids ? pipeline.solids : []
              )}
              highlightedSolids={
                pipeline
                  ? pipeline.solids.filter(
                      (s: any) => highlighted.indexOf(s.name) !== -1
                    )
                  : []
              }
            />
          </div>
          <div className={Classes.DIALOG_FOOTER}>
            <div className={Classes.DIALOG_FOOTER_ACTIONS}>
              <div style={{ alignSelf: "center" }}>
                {allSolidsSelected ? "All" : highlighted.length} solid
                {highlighted.length !== 1 || allSolidsSelected ? "s" : ""}{" "}
                selected
              </div>
              <Button onClick={() => this.setState({ open: false })}>
                Cancel
              </Button>
              <Button intent="primary" onClick={this.handleSave}>
                Apply
              </Button>
            </div>
          </div>
        </Dialog>
        <Button
          icon={valid ? IconNames.SEARCH_AROUND : IconNames.WARNING_SIGN}
          intent={valid ? Intent.NONE : Intent.WARNING}
          onClick={this.handleOpen}
        >
          {valid && this.props.pipeline
            ? subsetDescription(this.props.value, this.props.pipeline)
            : "Invalid Solid Selection"}
        </Button>
      </div>
    );
  }
}

export const SOLID_SELECTOR_QUERY = gql`
  query SolidSelectorQuery($name: String!) {
    pipeline(params: { name: $name }) {
      name
      solids {
        name
        ...PipelineGraphSolidFragment
      }
    }
  }
  ${PipelineGraph.fragments.PipelineGraphSolidFragment}
`;

export default (props: ISolidSelectorProps) => {
  const { data } = useQuery<SolidSelectorQuery>(SOLID_SELECTOR_QUERY, {
    variables: { name: props.pipelineName },

    // Note: By default, useQuery does not re-run the query when variables change, it only
    // impacts the item retrieved from the local cache, which is most likely null. fetchPolicy
    // "cache-and-network" would work but {data} is the old pipeline until the new pipeline is
    // returned. "network-only" ensures {data} is null or the correct server-provided result.
    fetchPolicy: "network-only"
  });

  if (data?.pipeline?.__typename !== "Pipeline") {
    return (
      <Button icon={IconNames.SEARCH_AROUND} intent={Intent.NONE}>
        <Spinner size={17} />
      </Button>
    );
  }

  return <SolidSelector {...props} pipeline={data.pipeline} />;
};
