import {Spinner, Button} from '@blueprintjs/core';
import {Colors} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import * as React from 'react';
import styled from 'styled-components/macro';

import {CursorHistoryControls} from 'src/CursorControls';
import {TokenizingFieldValue} from 'src/TokenizingField';
import {colorHash} from 'src/Util';
import {PIPELINE_LABEL, PartitionGraph} from 'src/partitions/PartitionGraph';
import {PartitionPageSizeSelector} from 'src/partitions/PartitionPageSizeSelector';
import {PartitionRunMatrix} from 'src/partitions/PartitionRunMatrix';
import {PartitionSetSelector} from 'src/partitions/PartitionSetSelector';
import {PartitionsBackfillPartitionSelector} from 'src/partitions/PartitionsBackfill';
import {
  PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results,
  PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results_runs,
} from 'src/partitions/types/PartitionLongitudinalQuery';
import {PipelinePartitionsRootQuery_partitionSetsOrError_PartitionSets_results} from 'src/partitions/types/PipelinePartitionsRootQuery';
import {useChunkedPartitionsQuery} from 'src/partitions/useChunkedPartitionsQuery';
import {RunsFilter} from 'src/runs/RunsFilter';

type PartitionSet = PipelinePartitionsRootQuery_partitionSetsOrError_PartitionSets_results;
type Partition = PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results;
type Run = PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results_runs;

interface PartitionViewProps {
  pipelineName: string;
  partitionSet: PartitionSet;
  partitionSets: PartitionSet[];
  onChangePartitionSet: (set: PartitionSet) => void;
}

export const PartitionView: React.FunctionComponent<PartitionViewProps> = ({
  pipelineName,
  partitionSet,
  partitionSets,
  onChangePartitionSet,
}) => {
  const [pageSize, setPageSize] = React.useState<number | 'all'>(30);
  const [runTags, setRunTags] = React.useState<{[key: string]: string}>({});
  const [showBackfillSetup, setShowBackfillSetup] = React.useState(false);
  const {loading, partitions, paginationProps} = useChunkedPartitionsQuery(
    partitionSet.name,
    pageSize,
  );

  const allStepKeys = {};
  partitions.forEach((partition) => {
    partition.runs?.forEach((run) => {
      if (!run) {
        return;
      }
      run.stepStats.forEach((stat) => {
        allStepKeys[stat.stepKey] = true;
      });
    });
  });

  return (
    <div>
      {showBackfillSetup && (
        <PartitionsBackfillPartitionSelector
          partitionSetName={partitionSet.name}
          pipelineName={pipelineName}
          onLaunch={(backfillId: string) => {
            setRunTags({'dagster/backfill': backfillId});
            setShowBackfillSetup(false);
          }}
        />
      )}
      <PartitionPagerContainer>
        <PartitionSetSelector
          selected={partitionSet}
          partitionSets={partitionSets}
          onSelect={onChangePartitionSet}
        />
        <div style={{width: 10}} />
        <PartitionPageSizeSelector
          value={paginationProps.hasPrevCursor ? undefined : pageSize}
          onChange={(value) => {
            setPageSize(value);
            paginationProps.reset();
          }}
        />
        {loading && (
          <div style={{marginLeft: 15, display: 'flex', alignItems: 'center'}}>
            <Spinner size={19} />
            <div style={{width: 5}} />
            Loading Partitions...
          </div>
        )}
        <div style={{flex: 1}} />
        <Button
          onClick={() => setShowBackfillSetup(!showBackfillSetup)}
          icon={IconNames.ADD}
          active={showBackfillSetup}
        >
          Launch a partition backfill
        </Button>
        <div style={{width: 10}} />
        <CursorHistoryControls {...paginationProps} />
      </PartitionPagerContainer>
      <div style={{position: 'relative'}}>
        <PartitionRunMatrix pipelineName={pipelineName} partitions={partitions} runTags={runTags} />
        <PartitionContent partitions={partitions} allStepKeys={Object.keys(allStepKeys)} />
      </div>
    </div>
  );
};

const PartitionPagerContainer = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
`;

const PartitionContent = ({
  partitions,
  allStepKeys,
}: {
  partitions: Partition[];
  allStepKeys: string[];
}) => {
  const initial: {[stepKey: string]: boolean} = {[PIPELINE_LABEL]: true};
  allStepKeys.forEach((stepKey) => (initial[stepKey] = true));
  const [selectedStepKeys, setSelectedStepKeys] = React.useState(initial);
  const [tokens, setTokens] = React.useState<TokenizingFieldValue[]>([]);
  const durationGraph = React.useRef<any>(undefined);
  const materializationGraph = React.useRef<any>(undefined);
  const successGraph = React.useRef<any>(undefined);
  const failureGraph = React.useRef<any>(undefined);
  const rateGraph = React.useRef<any>(undefined);
  const graphs = [durationGraph, materializationGraph, successGraph, failureGraph, rateGraph];

  const onStepChange = (selectedKeys: {[stepKey: string]: boolean}) => {
    setSelectedStepKeys(selectedKeys);
    graphs.forEach((graph) => {
      const chart = graph?.current?.chart?.current?.chartInstance;
      const datasets = chart?.data?.datasets || [];
      datasets.forEach((dataset: any, idx: number) => {
        const meta = chart.getDatasetMeta(idx);
        meta.hidden = dataset.label in selectedKeys ? !selectedKeys[dataset.label] : false;
      });
    });
  };

  const runsByPartitionName = {};
  partitions.forEach((partition) => {
    runsByPartitionName[partition.name] = partition.runs.filter(
      (run) => !tokens.length || tokens.every((token) => applyFilter(token, run)),
    );
  });

  return (
    <PartitionContentContainer>
      <div style={{flex: 1}}>
        <PartitionGraph
          title="Execution Time by Partition"
          yLabel="Execution time (secs)"
          runsByPartitionName={runsByPartitionName}
          getPipelineDataForRun={getPipelineDurationForRun}
          getStepDataForRun={getStepDurationsForRun}
          ref={durationGraph}
        />
        <PartitionGraph
          title="Materialization Count by Partition"
          yLabel="Number of materializations"
          runsByPartitionName={runsByPartitionName}
          getPipelineDataForRun={getPipelineMaterializationCountForRun}
          getStepDataForRun={getStepMaterializationCountForRun}
          ref={materializationGraph}
        />
        <PartitionGraph
          title="Expectation Successes by Partition"
          yLabel="Number of successes"
          runsByPartitionName={runsByPartitionName}
          getPipelineDataForRun={getPipelineExpectationSuccessForRun}
          getStepDataForRun={getStepExpectationSuccessForRun}
          ref={successGraph}
        />
        <PartitionGraph
          title="Expectation Failures by Partition"
          yLabel="Number of failures"
          runsByPartitionName={runsByPartitionName}
          getPipelineDataForRun={getPipelineExpectationFailureForRun}
          getStepDataForRun={getStepExpectationFailureForRun}
          ref={failureGraph}
        />
        <PartitionGraph
          title="Expectation Rate by Partition"
          yLabel="Rate of success"
          runsByPartitionName={runsByPartitionName}
          getPipelineDataForRun={getPipelineExpectationiRateForRun}
          getStepDataForRun={getStepExpectationRateForRun}
          ref={rateGraph}
        />
      </div>
      <div style={{width: 450}}>
        <NavContainer>
          <NavSectionHeader>Run filters</NavSectionHeader>
          <NavSection>
            <RunsFilter tokens={tokens} onChange={setTokens} enabledFilters={['status', 'tag']} />
          </NavSection>
          <StepSelector selected={selectedStepKeys} onChange={onStepChange} />
        </NavContainer>
      </div>
    </PartitionContentContainer>
  );
};

const StepSelector: React.FunctionComponent<{
  selected: {[stepKey: string]: boolean};
  onChange: (selected: {[stepKey: string]: boolean}) => void;
}> = ({selected, onChange}) => {
  const onStepClick = (stepKey: string) => {
    return (evt: React.MouseEvent) => {
      if (evt.shiftKey) {
        // toggle on shift+click
        onChange({...selected, [stepKey]: !selected[stepKey]});
      } else {
        // regular click
        const newSelected = {};

        const alreadySelected = Object.keys(selected).every((key) => {
          return key === stepKey ? selected[key] : !selected[key];
        });

        Object.keys(selected).forEach((key) => {
          newSelected[key] = alreadySelected || key === stepKey;
        });

        onChange(newSelected);
      }
    };
  };

  return (
    <>
      <NavSectionHeader>
        Run steps
        <div style={{flex: 1}} />
        <span style={{fontSize: 13, opacity: 0.5}}>Tip: Shift-click to multi-select</span>
      </NavSectionHeader>
      <NavSection>
        {Object.keys(selected).map((stepKey) => (
          <Item
            key={stepKey}
            shown={selected[stepKey]}
            onClick={onStepClick(stepKey)}
            color={stepKey === PIPELINE_LABEL ? Colors.GRAY2 : colorHash(stepKey)}
          >
            <div
              style={{
                display: 'inline-block',
                marginRight: 5,
                borderRadius: 5,
                height: 10,
                width: 10,
                backgroundColor: selected[stepKey]
                  ? stepKey === PIPELINE_LABEL
                    ? Colors.GRAY2
                    : colorHash(stepKey)
                  : '#aaaaaa',
              }}
            />
            {stepKey}
          </Item>
        ))}
      </NavSection>
    </>
  );
};

const NavSectionHeader = styled.div`
  border-bottom: 1px solid ${Colors.GRAY5};
  margin-bottom: 10px;
  padding-bottom: 5px;
  display: flex;
`;
const NavSection = styled.div`
  margin-bottom: 30px;
`;
const NavContainer = styled.div`
  margin: 20px 0 0 10px;
  padding: 10px;
  background-color: #fff;
  border: 1px solid ${Colors.GRAY5};
  overflow: auto;
`;

const Item = styled.div`
  list-style-type: none;
  padding: 5px 2px;
  cursor: pointer;
  text-decoration: ${({shown}: {shown: boolean}) => (shown ? 'none' : 'line-through')};
  user-select: none;
  font-size: 12px;
  color: ${(props) => (props.shown ? props.color : '#aaaaaa')};
  white-space: nowrap;
`;
const PartitionContentContainer = styled.div`
  display: flex;
  flex-direction: row;
  position: relative;
  max-width: 1600px;
  margin: 0 auto;
`;

const getPipelineDurationForRun = (run: Run) => {
  const {stats} = run;
  if (
    stats &&
    stats.__typename === 'PipelineRunStatsSnapshot' &&
    stats.endTime &&
    stats.startTime
  ) {
    return stats.endTime - stats.startTime;
  }

  return undefined;
};

const getStepDurationsForRun = (run: Run) => {
  const {stepStats} = run;

  const perStepDuration = {};
  stepStats.forEach((stepStat) => {
    if (stepStat.endTime && stepStat.startTime) {
      perStepDuration[stepStat.stepKey] = stepStat.endTime - stepStat.startTime;
    }
  });

  return perStepDuration;
};

const getPipelineMaterializationCountForRun = (run: Run) => {
  const {stats} = run;
  if (stats && stats.__typename === 'PipelineRunStatsSnapshot') {
    return stats.materializations;
  }
  return undefined;
};

const getStepMaterializationCountForRun = (run: Run) => {
  const {stepStats} = run;
  const perStepCounts = {};
  stepStats.forEach((stepStat) => {
    perStepCounts[stepStat.stepKey] = stepStat.materializations?.length || 0;
  });
  return perStepCounts;
};

const getPipelineExpectationSuccessForRun = (run: Run) => {
  const stepCounts: {[key: string]: number} = getStepExpectationSuccessForRun(run);
  return _arraySum(Object.values(stepCounts));
};

const getStepExpectationSuccessForRun = (run: Run) => {
  const {stepStats} = run;
  const perStepCounts = {};
  stepStats.forEach((stepStat) => {
    perStepCounts[stepStat.stepKey] =
      stepStat.expectationResults?.filter((x) => x.success).length || 0;
  });
  return perStepCounts;
};

const getPipelineExpectationFailureForRun = (run: Run) => {
  const stepCounts: {[key: string]: number} = getStepExpectationFailureForRun(run);
  return _arraySum(Object.values(stepCounts));
};

const getStepExpectationFailureForRun = (run: Run) => {
  const {stepStats} = run;
  const perStepCounts = {};
  stepStats.forEach((stepStat) => {
    perStepCounts[stepStat.stepKey] =
      stepStat.expectationResults?.filter((x) => !x.success).length || 0;
  });
  return perStepCounts;
};

const _arraySum = (arr: number[]) => {
  let sum = 0;
  arr.forEach((x) => (sum += x));
  return sum;
};

const getPipelineExpectationiRateForRun = (run: Run) => {
  const stepSuccesses: {
    [key: string]: number;
  } = getStepExpectationSuccessForRun(run);
  const stepFailures: {
    [key: string]: number;
  } = getStepExpectationFailureForRun(run);

  const pipelineSuccesses = _arraySum(Object.values(stepSuccesses));
  const pipelineFailures = _arraySum(Object.values(stepFailures));
  const pipelineTotal = pipelineSuccesses + pipelineFailures;

  return pipelineTotal ? pipelineSuccesses / pipelineTotal : 0;
};

const getStepExpectationRateForRun = (run: Run) => {
  const {stepStats} = run;
  const perStepCounts = {};
  stepStats.forEach((stepStat) => {
    const results = stepStat.expectationResults || [];
    perStepCounts[stepStat.stepKey] = results.length
      ? results.filter((x) => x.success).length / results.length
      : 0;
  });
  return perStepCounts;
};

const applyFilter = (filter: TokenizingFieldValue, run: Run) => {
  if (filter.token === 'id') {
    return run.runId === filter.value;
  }
  if (filter.token === 'status') {
    return run.status === filter.value;
  }
  if (filter.token === 'tag') {
    return run.tags.some((tag) => filter.value === `${tag.key}=${tag.value}`);
  }
  return true;
};
