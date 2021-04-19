import {Button, Classes, Colors, Dialog} from '@blueprintjs/core';
import React from 'react';
import {Link} from 'react-router-dom';

import {Timestamp} from '../app/time/Timestamp';
import {PipelineReference} from '../pipelines/PipelineReference';
import {MetadataEntries} from '../runs/MetadataEntry';
import {RunStatusTagWithStats} from '../runs/RunStatusTag';
import {titleForRun} from '../runs/RunUtils';
import {ButtonLink} from '../ui/ButtonLink';
import {Group} from '../ui/Group';
import {Table} from '../ui/Table';
import {FontFamily} from '../ui/styles';

import {AssetLineageElements} from './AssetLineageElements';
import {AssetQuery_assetOrError_Asset_assetMaterializations as Materialization} from './types/AssetQuery';

type HistoricalMaterizalization = {
  latest: Materialization;
  predecessors?: Materialization[];
};

const NO_PARTITION_KEY = '__NO_PARTITION__';

export const AssetMaterializationTable: React.FC<{
  isPartitioned: boolean;
  hasLineage: boolean;
  materializations: Materialization[];
  shouldBucketPartitions?: boolean;
}> = ({isPartitioned, hasLineage, materializations, shouldBucketPartitions = true}) => {
  const bucketed = React.useMemo(() => {
    if (!isPartitioned || !shouldBucketPartitions) {
      return materializations.map((materialization) => ({
        latest: materialization,
      }));
    }

    const buckets: {[key: string]: Materialization[]} = materializations.reduce(
      (accum, materialization) => {
        const partition = materialization.partition;
        const key = partition || NO_PARTITION_KEY;
        const materializationsForKey = accum[key] || [];
        return {...accum, [key]: [...materializationsForKey, materialization]};
      },
      {},
    );

    const separate = (key: string) => {
      const materializationsForKey = [...buckets[key]].sort(
        (a, b) =>
          Number(b.materializationEvent?.timestamp) - Number(a.materializationEvent?.timestamp),
      );
      const [latest, ...predecessors] = materializationsForKey;
      return {latest, predecessors};
    };

    return Object.keys(buckets)
      .sort()
      .reverse()
      .filter((key) => key !== NO_PARTITION_KEY)
      .map(separate)
      .concat(buckets.hasOwnProperty(NO_PARTITION_KEY) ? [separate(NO_PARTITION_KEY)] : []);
  }, [isPartitioned, materializations, shouldBucketPartitions]);

  return (
    <Table>
      <thead>
        <tr>
          {isPartitioned && <th style={{minWidth: 100}}>Partition</th>}
          <th style={{paddingLeft: 0}}>Materialization Metadata</th>
          {hasLineage && <th style={{minWidth: 100}}>Parent Assets</th>}
          <th style={{minWidth: 150}}>Timestamp</th>
          <th style={{minWidth: 150}}>Pipeline</th>
          <th style={{width: 200}}>Run</th>
        </tr>
      </thead>
      <tbody>
        {bucketed.map((m) => (
          <AssetMaterializationRow
            key={m.latest.materializationEvent.timestamp}
            isPartitioned={isPartitioned}
            hasLineage={hasLineage}
            assetMaterialization={m}
          />
        ))}
      </tbody>
    </Table>
  );
};

const AssetMaterializationRow: React.FC<{
  assetMaterialization: HistoricalMaterizalization;
  isPartitioned: boolean;
  hasLineage: boolean;
}> = ({assetMaterialization, isPartitioned, hasLineage}) => {
  const {latest, predecessors} = assetMaterialization;
  const run = latest.runOrError.__typename === 'PipelineRun' ? latest.runOrError : undefined;
  if (!run) {
    return <span />;
  }
  const {materialization, assetLineage, timestamp} = latest.materializationEvent;
  const metadataEntries = materialization.metadataEntries;

  return (
    <tr>
      {isPartitioned && (
        <td>{latest.partition || <span style={{color: Colors.GRAY3}}>None</span>}</td>
      )}
      <td style={{fontSize: 12, padding: '4px 12px 0 0'}}>
        {materialization.description ? (
          <div style={{fontSize: '0.8rem', marginTop: 10}}>{materialization.description}</div>
        ) : null}
        {metadataEntries && metadataEntries.length ? (
          <MetadataEntries entries={metadataEntries} />
        ) : null}
      </td>
      {hasLineage && <td>{<AssetLineageElements elements={assetLineage} />}</td>}
      <td>
        <Group direction="column" spacing={4}>
          <Timestamp timestamp={{ms: Number(timestamp)}} />
          {predecessors?.length ? (
            <AssetPredecessorLink
              isPartitioned={isPartitioned}
              hasLineage={hasLineage}
              predecessors={predecessors}
            />
          ) : null}
        </Group>
      </td>
      <td>
        <PipelineReference
          pipelineName={run.pipelineName}
          pipelineHrefContext="repo-unknown"
          snapshotId={run.pipelineSnapshotId}
          mode={run.mode}
        />
      </td>
      <td>
        <Link
          style={{marginRight: 5, fontFamily: FontFamily.monospace}}
          to={`/instance/runs/${run.runId}?timestamp=${timestamp}`}
        >
          {titleForRun(run)}
        </Link>
        <RunStatusTagWithStats status={run.status} runId={run.runId} />
      </td>
    </tr>
  );
};

interface PredecessorDialogProps {
  hasLineage: boolean;
  isPartitioned: boolean;
  predecessors: Materialization[];
}

const AssetPredecessorLink: React.FC<PredecessorDialogProps> = ({
  hasLineage,
  isPartitioned,
  predecessors,
}) => {
  const [open, setOpen] = React.useState(false);
  const count = predecessors.length;
  const title = () => {
    if (isPartitioned) {
      const partition = predecessors[0].partition;
      if (partition) {
        return `Previous materializations for ${partition}`;
      }
    }
    return `Previous materializations`;
  };

  return (
    <>
      <ButtonLink onClick={() => setOpen(true)}>{`View ${count} previous`}</ButtonLink>
      <Dialog
        isOpen={open}
        canEscapeKeyClose
        canOutsideClickClose
        onClose={() => setOpen(false)}
        style={{width: '80%', minWidth: '800px'}}
        title={title()}
      >
        <div className={Classes.DIALOG_BODY}>
          <AssetMaterializationTable
            hasLineage={hasLineage}
            isPartitioned={isPartitioned}
            materializations={predecessors}
            shouldBucketPartitions={false}
          />
        </div>
        <div className={Classes.DIALOG_FOOTER}>
          <div className={Classes.DIALOG_FOOTER_ACTIONS}>
            <Button intent="primary" onClick={() => setOpen(false)}>
              OK
            </Button>
          </div>
        </div>
      </Dialog>
    </>
  );
};
