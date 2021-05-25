# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['TestMaterializations.test_materializations[postgres_with_default_run_launcher_deployed_grpc_env] 1'] = [
    'PipelineStartingEvent',
    'PipelineStartEvent',
    'LogsCapturedEvent',
    'ExecutionStepStartEvent',
    'StepMaterializationEvent',
    'ExecutionStepOutputEvent',
    'HandledOutputEvent',
    'ExecutionStepSuccessEvent',
    'PipelineSuccessEvent'
]

snapshots['TestMaterializations.test_materializations[postgres_with_default_run_launcher_managed_grpc_env] 1'] = [
    'PipelineStartingEvent',
    'PipelineStartEvent',
    'LogsCapturedEvent',
    'ExecutionStepStartEvent',
    'StepMaterializationEvent',
    'ExecutionStepOutputEvent',
    'HandledOutputEvent',
    'ExecutionStepSuccessEvent',
    'PipelineSuccessEvent'
]

snapshots['TestMaterializations.test_materializations[sqlite_with_default_run_launcher_deployed_grpc_env] 1'] = [
    'PipelineStartingEvent',
    'PipelineStartEvent',
    'LogsCapturedEvent',
    'ExecutionStepStartEvent',
    'StepMaterializationEvent',
    'ExecutionStepOutputEvent',
    'HandledOutputEvent',
    'ExecutionStepSuccessEvent',
    'PipelineSuccessEvent'
]

snapshots['TestMaterializations.test_materializations[sqlite_with_default_run_launcher_managed_grpc_env] 1'] = [
    'PipelineStartingEvent',
    'PipelineStartEvent',
    'LogsCapturedEvent',
    'ExecutionStepStartEvent',
    'StepMaterializationEvent',
    'ExecutionStepOutputEvent',
    'HandledOutputEvent',
    'ExecutionStepSuccessEvent',
    'PipelineSuccessEvent'
]
