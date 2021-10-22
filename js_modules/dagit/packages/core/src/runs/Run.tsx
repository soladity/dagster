import {useMutation} from '@apollo/client';
import * as React from 'react';
import styled from 'styled-components/macro';

import {AppContext} from '../app/AppContext';
import {showCustomAlert} from '../app/CustomAlertProvider';
import {filterByQuery} from '../app/GraphQueryImpl';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {showLaunchError} from '../execute/showLaunchError';
import {GanttChart, GanttChartLoadingState, GanttChartMode, QueuedState} from '../gantt/GanttChart';
import {toGraphQueryItems} from '../gantt/toGraphQueryItems';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {useFavicon} from '../hooks/useFavicon';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {RunStatus} from '../types/globalTypes';
import {Box} from '../ui/Box';
import {NonIdealState} from '../ui/NonIdealState';
import {FirstOrSecondPanelToggle, SplitPanelContainer} from '../ui/SplitPanelContainer';
import {useRepositoryForRun} from '../workspace/useRepositoryForRun';

import {ComputeLogPanel} from './ComputeLogPanel';
import {LogFilter, LogsProvider, LogsProviderLogs} from './LogsProvider';
import {LogsScrollingTable} from './LogsScrollingTable';
import {LogsToolbar, LogType} from './LogsToolbar';
import {RunActionButtons} from './RunActionButtons';
import {RunContext} from './RunContext';
import {IRunMetadataDict, RunMetadataProvider} from './RunMetadataProvider';
import {
  LAUNCH_PIPELINE_REEXECUTION_MUTATION,
  getReexecutionVariables,
  handleLaunchResult,
  ReExecutionStyle,
} from './RunUtils';
import {
  LaunchPipelineReexecution,
  LaunchPipelineReexecutionVariables,
} from './types/LaunchPipelineReexecution';
import {
  RunDagsterRunEventFragment,
  RunDagsterRunEventFragment_ExecutionStepFailureEvent,
} from './types/RunDagsterRunEventFragment';
import {RunFragment} from './types/RunFragment';
import {useQueryPersistedLogFilter} from './useQueryPersistedLogFilter';

interface RunProps {
  runId: string;
  run?: RunFragment;
}

const runStatusFavicon = (status: RunStatus) => {
  switch (status) {
    case RunStatus.CANCELED:
    case RunStatus.CANCELING:
    case RunStatus.FAILURE:
      return '/favicon-run-failed.svg';
    case RunStatus.SUCCESS:
      return '/favicon-run-success.svg';
    default:
      return '/favicon-run-pending.svg';
  }
};

export const Run: React.FC<RunProps> = (props) => {
  const {run, runId} = props;
  const [logsFilter, setLogsFilter] = useQueryPersistedLogFilter();
  const [selectionQuery, setSelectionQuery] = useQueryPersistedState<string>({
    queryKey: 'selection',
    defaults: {selection: ''},
  });

  useFavicon(run ? runStatusFavicon(run.status) : '/favicon.svg');
  useDocumentTitle(
    run ? `${run.pipeline.name} ${runId.slice(0, 8)} [${run.status}]` : `Run: ${runId}`,
  );

  const onShowStateDetails = (stepKey: string, logs: RunDagsterRunEventFragment[]) => {
    const errorNode = logs.find(
      (node) => node.__typename === 'ExecutionStepFailureEvent' && node.stepKey === stepKey,
    ) as RunDagsterRunEventFragment_ExecutionStepFailureEvent;

    if (errorNode) {
      showCustomAlert({
        body: <PythonErrorInfo error={errorNode} />,
      });
    }
  };

  const onSetSelectionQuery = (query: string) => {
    setSelectionQuery(query);
    setLogsFilter({
      ...logsFilter,
      logQuery: query !== '*' ? [{token: 'query', value: query}] : [],
    });
  };

  return (
    <RunContext.Provider value={run}>
      <LogsProvider key={runId} runId={runId}>
        {(logs) => (
          <RunMetadataProvider logs={logs.allNodes}>
            {(metadata) => (
              <RunWithData
                run={run}
                runId={runId}
                logs={logs}
                logsFilter={logsFilter}
                metadata={metadata}
                selectionQuery={selectionQuery}
                onSetLogsFilter={setLogsFilter}
                onSetSelectionQuery={onSetSelectionQuery}
                onShowStateDetails={onShowStateDetails}
              />
            )}
          </RunMetadataProvider>
        )}
      </LogsProvider>
    </RunContext.Provider>
  );
};

interface RunWithDataProps {
  run?: RunFragment;
  runId: string;
  selectionQuery: string;
  logs: LogsProviderLogs;
  logsFilter: LogFilter;
  metadata: IRunMetadataDict;
  onSetLogsFilter: (v: LogFilter) => void;
  onSetSelectionQuery: (query: string) => void;
  onShowStateDetails: (stepKey: string, logs: RunDagsterRunEventFragment[]) => void;
}

const logTypeFromQuery = (queryLogType: string) => {
  switch (queryLogType) {
    case 'stdout':
      return LogType.stdout;
    case 'stderr':
      return LogType.stderr;
    default:
      return LogType.structured;
  }
};

/**
 * Note: There are two places we keep a "step query string" in the Run view:
 * selectionQuery and logsFilter.logsQuery.
 *
 * - selectionQuery is set when you click around in the Gannt view and is the
 *   selection used for re-execution, etc. When set, we autofill logsFilter.logsQuery.
 *
 * - logsFilter.logsQuery is used for filtering the logs. It can be cleared separately
 *   from the selectionQuery, so you can select a step but navigate elsewhere in the logs.
 *
 * We could revisit this in the future but I believe we iterated quite a bit to get to this
 * solution and we should avoid locking the two filter inputs together completely.
 */
const RunWithData: React.FunctionComponent<RunWithDataProps> = ({
  run,
  runId,
  logs,
  logsFilter,
  metadata,
  selectionQuery,
  onSetLogsFilter,
  onSetSelectionQuery,
}) => {
  const [launchPipelineReexecution] = useMutation<
    LaunchPipelineReexecution,
    LaunchPipelineReexecutionVariables
  >(LAUNCH_PIPELINE_REEXECUTION_MUTATION);
  const repoMatch = useRepositoryForRun(run);
  const splitPanelContainer = React.createRef<SplitPanelContainer>();

  const {basePath} = React.useContext(AppContext);

  const [queryLogType, setQueryLogType] = useQueryPersistedState<string>({
    queryKey: 'logType',
    defaults: {logType: 'structured'},
  });

  const [computeLogKey, setComputeLogKey] = useQueryPersistedState<string>({
    queryKey: 'logKey',
  });

  const logType = logTypeFromQuery(queryLogType);
  const setLogType = (lt: LogType) => setQueryLogType(LogType[lt]);
  const [computeLogUrl, setComputeLogUrl] = React.useState<string | null>(null);

  const stepKeysJSON = JSON.stringify(Object.keys(metadata.steps).sort());
  const stepKeys = React.useMemo(() => JSON.parse(stepKeysJSON), [stepKeysJSON]);

  const runtimeGraph = run?.executionPlan && toGraphQueryItems(run?.executionPlan, metadata.steps);

  const selectionStepKeys = React.useMemo(() => {
    return runtimeGraph && selectionQuery && selectionQuery !== '*'
      ? filterByQuery(runtimeGraph, selectionQuery).all.map((n) => n.name)
      : [];
  }, [runtimeGraph, selectionQuery]);

  React.useEffect(() => {
    if (!stepKeys?.length || computeLogKey) {
      return;
    }

    if (metadata.logCaptureSteps) {
      const logKeys = Object.keys(metadata.logCaptureSteps);
      const selectedLogKey = logKeys.find((logKey) => {
        return selectionStepKeys.every(
          (stepKey) =>
            metadata.logCaptureSteps && metadata.logCaptureSteps[logKey].stepKeys.includes(stepKey),
        );
      });
      setComputeLogKey(selectedLogKey || logKeys[0]);
    } else if (!stepKeys.includes(computeLogKey)) {
      setComputeLogKey(selectionStepKeys.length === 1 ? selectionStepKeys[0] : stepKeys[0]);
    } else if (selectionStepKeys.length === 1 && computeLogKey !== selectionStepKeys[0]) {
      setComputeLogKey(selectionStepKeys[0]);
    }
  }, [stepKeys, computeLogKey, selectionStepKeys, metadata.logCaptureSteps, setComputeLogKey]);

  const onSetComputeLogKey = (logKey: string) => {
    setComputeLogKey(logKey);
  };

  const logsFilterStepKeys = runtimeGraph
    ? logsFilter.logQuery
        .filter((v) => v.token && v.token === 'query')
        .reduce((accum, v) => {
          return [...accum, ...filterByQuery(runtimeGraph, v.value).all.map((n) => n.name)];
        }, [] as string[])
    : [];

  const onLaunch = async (style: ReExecutionStyle) => {
    if (!run || run.pipeline.__typename === 'UnknownPipeline' || !repoMatch) {
      return;
    }

    const variables = getReexecutionVariables({
      run,
      style,
      repositoryLocationName: repoMatch.match.repositoryLocation.name,
      repositoryName: repoMatch.match.repository.name,
    });

    try {
      const result = await launchPipelineReexecution({variables});
      handleLaunchResult(basePath, run.pipeline.name, result);
    } catch (error) {
      showLaunchError(error as Error);
    }
  };

  const onClickStep = (stepKey: string, evt: React.MouseEvent<any>) => {
    const index = selectionStepKeys.indexOf(stepKey);
    let newSelected: string[];

    if (evt.shiftKey) {
      // shift-click to multi select steps
      newSelected = [...selectionStepKeys];

      if (index !== -1) {
        // deselect the step if already selected
        newSelected.splice(index, 1);
      } else {
        // select the step otherwise
        newSelected.push(stepKey);
      }
    } else {
      if (selectionStepKeys.length === 1 && index !== -1) {
        // deselect the step if already selected
        newSelected = [];
      } else {
        // select the step otherwise
        newSelected = [stepKey];
      }
    }

    onSetSelectionQuery(newSelected.join(', ') || '*');
  };

  const gantt = (metadata: IRunMetadataDict) => {
    if (logs.loading || !run) {
      return <GanttChartLoadingState runId={runId} />;
    }

    if (run.status === 'QUEUED') {
      return <QueuedState runId={runId} />;
    }

    if (run.executionPlan && runtimeGraph) {
      return (
        <GanttChart
          options={{
            mode: GanttChartMode.WATERFALL_TIMED,
          }}
          toolbarActions={
            <Box flex={{direction: 'row', alignItems: 'center', gap: 12}}>
              <FirstOrSecondPanelToggle axis="vertical" container={splitPanelContainer} />
              <RunActionButtons
                run={run}
                onLaunch={onLaunch}
                graph={runtimeGraph}
                metadata={metadata}
                selection={{query: selectionQuery, keys: selectionStepKeys}}
              />
            </Box>
          }
          runId={runId}
          graph={runtimeGraph}
          metadata={metadata}
          selection={{query: selectionQuery, keys: selectionStepKeys}}
          onClickStep={onClickStep}
          onSetSelection={onSetSelectionQuery}
          focusedTime={logsFilter.focusedTime}
        />
      );
    }

    return <NonIdealState icon="error" title="Unable to build execution plan" />;
  };

  return (
    <>
      <SplitPanelContainer
        ref={splitPanelContainer}
        axis="vertical"
        identifier="run-gantt"
        firstInitialPercent={35}
        firstMinSize={56}
        first={gantt(metadata)}
        second={
          <LogsContainer>
            <LogsToolbar
              logType={logType}
              onSetLogType={setLogType}
              filter={logsFilter}
              onSetFilter={onSetLogsFilter}
              steps={stepKeys}
              metadata={metadata}
              computeLogKey={computeLogKey}
              onSetComputeLogKey={onSetComputeLogKey}
              computeLogUrl={computeLogUrl}
            />
            {logType !== LogType.structured ? (
              <ComputeLogPanel
                runId={runId}
                stepKeys={stepKeys}
                computeLogKey={computeLogKey}
                ioType={LogType[logType]}
                setComputeLogUrl={setComputeLogUrl}
              />
            ) : (
              <LogsScrollingTable
                logs={logs}
                filter={logsFilter}
                filterStepKeys={logsFilterStepKeys}
                filterKey={`${JSON.stringify(logsFilter)}`}
                metadata={metadata}
              />
            )}
          </LogsContainer>
        }
      />
    </>
  );
};

const LogsContainer = styled.div`
  display: flex;
  flex-direction: column;
  height: 100%;
`;
