import { Colors } from "@blueprintjs/core";
import { scaleOrdinal } from "@vx/scale";

const PipelineColorScale = scaleOrdinal({
  domain: [
    "source",
    "input",
    "inputHighlighted",
    "solid",
    "solidComposite",
    "solidDarker",
    "output",
    "outputHighlighted",
    "materializations"
  ],
  range: [
    Colors.TURQUOISE5,
    Colors.TURQUOISE3,
    Colors.TURQUOISE1,
    "#DBE6EE",
    "rgb(230, 219, 238)",
    "#7D8C97",
    Colors.BLUE3,
    Colors.BLUE1,
    Colors.ORANGE5
  ]
});

export default PipelineColorScale;
