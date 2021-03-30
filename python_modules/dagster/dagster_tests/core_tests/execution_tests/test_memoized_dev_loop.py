import tempfile

import pytest
from dagster import execute_pipeline, reexecute_pipeline
from dagster.core.errors import DagsterNoStepsToExecuteException
from dagster.core.execution.api import create_execution_plan
from dagster.core.execution.resolve_versions import resolve_memoized_execution_plan
from dagster.core.instance import DagsterInstance, InstanceType
from dagster.core.launcher import DefaultRunLauncher
from dagster.core.run_coordinator import DefaultRunCoordinator
from dagster.core.storage.event_log import ConsolidatedSqliteEventLogStorage
from dagster.core.storage.local_compute_log_manager import LocalComputeLogManager
from dagster.core.storage.root import LocalArtifactStorage
from dagster.core.storage.runs import SqliteRunStorage
from dagster.core.system_config.objects import EnvironmentConfig

from .memoized_dev_loop_pipeline import asset_pipeline


def get_ephemeral_instance(temp_dir):
    run_store = SqliteRunStorage.from_local(temp_dir)
    event_store = ConsolidatedSqliteEventLogStorage(temp_dir)
    compute_log_manager = LocalComputeLogManager(temp_dir)
    instance = DagsterInstance(
        instance_type=InstanceType.PERSISTENT,
        local_artifact_storage=LocalArtifactStorage(temp_dir),
        run_storage=run_store,
        event_storage=event_store,
        compute_log_manager=compute_log_manager,
        run_launcher=DefaultRunLauncher(),
        run_coordinator=DefaultRunCoordinator(),
    )
    return instance


def get_step_keys_to_execute(pipeline, run_config, mode, instance):
    memoized_execution_plan = resolve_memoized_execution_plan(
        create_execution_plan(pipeline, run_config=run_config, mode=mode),
        pipeline,
        run_config,
        instance,
        EnvironmentConfig.build(pipeline, run_config=run_config, mode=mode),
    )
    return memoized_execution_plan.step_keys_to_execute


def test_dev_loop_changing_versions():
    with tempfile.TemporaryDirectory() as temp_dir:
        instance = get_ephemeral_instance(temp_dir)

        run_config = {
            "solids": {
                "create_string_1_asset": {"config": {"input_str": "apple"}},
                "take_string_1_asset": {"config": {"input_str": "apple"}},
            },
            "resources": {"io_manager": {"config": {"base_dir": temp_dir}}},
        }

        result = execute_pipeline(
            asset_pipeline,
            run_config=run_config,
            mode="only_mode",
            tags={"dagster/is_memoized_run": "true"},
            instance=instance,
        )
        assert result.success
        assert not get_step_keys_to_execute(asset_pipeline, run_config, "only_mode", instance)

        run_config["solids"]["take_string_1_asset"]["config"]["input_str"] = "banana"

        assert get_step_keys_to_execute(asset_pipeline, run_config, "only_mode", instance) == [
            "take_string_1_asset"
        ]
        result = reexecute_pipeline(
            asset_pipeline,
            parent_run_id=result.run_id,
            run_config=run_config,
            mode="only_mode",
            tags={"dagster/is_memoized_run": "true"},
            instance=instance,
        )
        assert result.success
        assert not get_step_keys_to_execute(asset_pipeline, run_config, "only_mode", instance)
        # Ensure pipeline execution fails with proper error if every step has already been memoized.
        with pytest.raises(DagsterNoStepsToExecuteException):
            reexecute_pipeline(
                asset_pipeline,
                parent_run_id=result.run_id,
                run_config=run_config,
                mode="only_mode",
                tags={"dagster/is_memoized_run": "true"},
                instance=instance,
            )
