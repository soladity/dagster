import {useMutation} from '@apollo/client';
import {Button, IconName, Intent} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import * as React from 'react';

import {SharedToaster} from 'src/DomUtils';
import {IStepState} from 'src/RunMetadataProvider';
import {LaunchButtonConfiguration, LaunchButtonDropdown} from 'src/execute/LaunchButton';
import {CANCEL_MUTATION, ReExecutionStyle} from 'src/runs/RunUtils';
import {StepSelection} from 'src/runs/StepSelection';
import {Cancel} from 'src/runs/types/Cancel';
import {RunFragment} from 'src/runs/types/RunFragment';
import {PipelineRunStatus} from 'src/types/globalTypes';
import {useRepositoryForRun} from 'src/workspace/useRepositoryForRun';

// Descriptions of re-execute options
export const REEXECUTE_PIPELINE_UNKNOWN =
  'Re-execute is unavailable because the pipeline is not present in the current workspace.';
const REEXECUTE_SUBSET = 'Re-run the following steps with existing configuration:';
const REEXECUTE_SUBSET_NO_SELECTION =
  'Re-execute is only enabled when steps are selected. Try selecting a step or typing a step subset to re-execute.';
const REEXECUTE_SUBSET_NOT_DONE = 'Wait for the selected steps to finish to re-execute it.';

interface RunActionButtonsProps {
  run?: RunFragment;
  selection: StepSelection;
  selectionStates: IStepState[];
  artifactsPersisted: boolean;
  executionPlan?: {
    artifactsPersisted: boolean;
  } | null;
  onLaunch: (style: ReExecutionStyle) => Promise<void>;
}

const CancelRunButton: React.FC<{run: RunFragment}> = ({run}) => {
  const [cancel] = useMutation<Cancel>(CANCEL_MUTATION);
  const [inFlight, setInFlight] = React.useState(false);
  return (
    <Button
      icon={IconNames.STOP}
      small={true}
      text="Terminate"
      intent="warning"
      disabled={inFlight}
      onClick={async () => {
        setInFlight(true);
        const {data} = await cancel({
          variables: {runId: run.runId},
        });
        const execution = data?.terminatePipelineExecution;
        const message = execution && 'message' in execution ? execution.message : null;
        if (message) {
          SharedToaster.show({
            message,
            icon: 'error',
            intent: Intent.DANGER,
          });
        }
        setInFlight(false);
      }}
    />
  );
};

export const RunActionButtons: React.FC<RunActionButtonsProps> = ({
  selection,
  selectionStates,
  artifactsPersisted,
  onLaunch,
  run,
  executionPlan,
}) => {
  const pipelineError = usePipelineAvailabilityErrorForRun(run);

  const isSelectionPresent = selection.keys.length > 0;
  const isSelectionFinished = selectionStates.every((stepState) =>
    [IStepState.FAILED, IStepState.SUCCEEDED].includes(stepState),
  );
  const isFinalStatus =
    run?.status === PipelineRunStatus.FAILURE || run?.status === PipelineRunStatus.SUCCESS;
  const isFailedWithPlan = executionPlan && run && run.status === PipelineRunStatus.FAILURE;
  const isFailureInSelection = selection.keys.length && selectionStates.includes(IStepState.FAILED);

  const full: LaunchButtonConfiguration = {
    icon: 'repeat',
    scope: '*',
    title: 'All Steps',
    tooltip: 'Re-execute the pipeline run from scratch',
    disabled: !isFinalStatus,
    onClick: () => onLaunch({type: 'all'}),
  };

  const selected: LaunchButtonConfiguration = {
    icon: 'select',
    scope: selection.query,
    title: selection.keys.length > 1 ? 'Selected Steps' : 'Selected Step',
    disabled: !isSelectionPresent || !(isSelectionFinished || isFailureInSelection),
    tooltip: (
      <div>
        {!isSelectionPresent
          ? REEXECUTE_SUBSET_NO_SELECTION
          : !isSelectionFinished
          ? REEXECUTE_SUBSET_NOT_DONE
          : REEXECUTE_SUBSET}
        <div style={{paddingLeft: '10px'}}>
          {isSelectionPresent &&
            selection.keys.map((step) => (
              <span key={step} style={{display: 'block'}}>{`* ${step}`}</span>
            ))}
        </div>
      </div>
    ),
    onClick: () => onLaunch({type: 'selection', selection}),
  };

  const fromSelected: LaunchButtonConfiguration = {
    icon: 'inheritance',
    title: 'From Selected',
    disabled: !isFinalStatus || selection.keys.length !== 1,
    tooltip: 'Re-execute the pipeline downstream from the selected steps',
    onClick: () => onLaunch({type: 'from-selected', selection}),
  };

  const fromFailure: LaunchButtonConfiguration = {
    icon: 'redo',
    title: 'From Failure',
    disabled: !isFailedWithPlan,
    tooltip: !isFailedWithPlan
      ? 'Retry is only enabled when the pipeline has failed.'
      : 'Retry the pipeline run, skipping steps that completed successfully',
    onClick: () => onLaunch({type: 'from-failure'}),
  };

  if (!artifactsPersisted) {
    [selected, fromFailure, fromSelected].forEach((option) => {
      option.disabled = true;
      option.title =
        'Retry and re-execute are only enabled on persistent storage. Try rerunning with a different storage configuration.';
    });
  }

  const options = [full, selected, fromSelected, fromFailure];
  const primary = isSelectionPresent && artifactsPersisted ? selected : full;

  return (
    <>
      <LaunchButtonDropdown
        small={true}
        primary={primary}
        options={options}
        title={primary.scope === '*' ? `Re-execute All (*)` : `Re-execute (${primary.scope})`}
        tooltip={pipelineError?.tooltip}
        icon={pipelineError?.icon}
        disabled={pipelineError?.disabled}
      />
      {run?.canTerminate && (
        <>
          <div style={{minWidth: 6}} />
          <CancelRunButton run={run} />
        </>
      )}
    </>
  );
};

function usePipelineAvailabilityErrorForRun(
  run: RunFragment | null | undefined,
): null | {tooltip?: string; icon?: IconName; disabled: boolean} {
  const repoMatch = useRepositoryForRun(run);

  // The run hasn't loaded, so no error.
  if (!run) {
    return null;
  }

  if (run?.pipeline.__typename === 'UnknownPipeline') {
    return {
      icon: IconNames.ERROR,
      tooltip: `"${run.pipeline.name}" could not be found.`,
      disabled: true,
    };
  }

  if (repoMatch) {
    const {type: matchType} = repoMatch;

    // The run matches the active snapshot ID for the pipeline, so we're safe to execute the run.
    if (matchType === 'snapshot') {
      return null;
    }

    // A repo was found, but only because the pipeline name matched. The run might not work
    // as expected.
    return {
      icon: IconNames.WARNING_SIGN,
      tooltip:
        `The pipeline "${run.pipeline.name}" in the current repository is` +
        ` a different version than the original pipeline run.`,
      disabled: false,
    };
  }

  // We could not find a repo that contained this pipeline.
  return {
    icon: IconNames.ERROR,
    tooltip: `"${run.pipeline.name}" is not available in the current workspace.`,
    disabled: true,
  };
}
