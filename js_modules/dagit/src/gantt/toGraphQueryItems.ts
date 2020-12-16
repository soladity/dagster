import {weakmapMemoize} from 'src/Util';
import {IGanttNode} from 'src/gantt/Constants';
import {GanttChartExecutionPlanFragment} from 'src/gantt/types/GanttChartExecutionPlanFragment';

/**
 * Converts a Run execution plan into a tree of `GraphQueryItem` items that
 * can be used as the input to the "solid query" filtering algorithm. The idea
 * is that this data structure is generic, but it's really a fake solid tree.
 */
export const toGraphQueryItems = weakmapMemoize((plan: GanttChartExecutionPlanFragment) => {
  const nodeTable: {[key: string]: IGanttNode} = {};

  for (const step of plan.steps) {
    const node: IGanttNode = {
      name: step.key,
      inputs: [],
      outputs: [],
    };
    nodeTable[step.key] = node;
  }

  for (const step of plan.steps) {
    for (const input of step.inputs) {
      nodeTable[step.key].inputs.push({
        dependsOn: input.dependsOn.map((d) => ({
          solid: {
            name: d.key,
          },
        })),
      });

      for (const upstream of input.dependsOn) {
        let output = nodeTable[upstream.key].outputs[0];
        if (!output) {
          output = {
            dependedBy: [],
          };
          nodeTable[upstream.key].outputs.push(output);
        }
        output.dependedBy.push({
          solid: {name: step.key},
        });
      }
    }
  }

  return Object.values(nodeTable);
});
