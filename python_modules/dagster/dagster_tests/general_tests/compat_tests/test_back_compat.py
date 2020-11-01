# pylint: disable=protected-access
import os
import re
import sqlite3
from gzip import GzipFile

import pytest
from dagster import check, execute_pipeline, file_relative_path, pipeline, solid
from dagster.cli.debug import DebugRunPayload
from dagster.core.errors import DagsterInstanceMigrationRequired
from dagster.core.instance import DagsterInstance, InstanceRef
from dagster.core.storage.event_log.migration import migrate_event_log_data
from dagster.core.storage.event_log.sql_event_log import SqlEventLogStorage
from dagster.serdes import deserialize_json_to_dagster_namedtuple
from dagster.utils.test import copy_directory


def _migration_regex(warning, current_revision, expected_revision=None):
    instruction = re.escape("Please run `dagster instance migrate`.")
    if expected_revision:
        revision = re.escape(
            "Database is at revision {}, head is {}.".format(current_revision, expected_revision)
        )
    else:
        revision = "Database is at revision {}, head is [a-z0-9]+.".format(current_revision)
    return "{} {} {}".format(warning, revision, instruction)


def _run_storage_migration_regex(current_revision, expected_revision=None):
    warning = re.escape(
        "Instance is out of date and must be migrated (Sqlite run storage requires migration)."
    )
    return _migration_regex(warning, current_revision, expected_revision)


def _schedule_storage_migration_regex(current_revision, expected_revision=None):
    warning = re.escape(
        "Instance is out of date and must be migrated (Sqlite schedule storage requires migration)."
    )
    return _migration_regex(warning, current_revision, expected_revision)


def _event_log_migration_regex(run_id, current_revision, expected_revision=None):
    warning = re.escape(
        "Instance is out of date and must be migrated (SqliteEventLogStorage for run {}).".format(
            run_id
        )
    )
    return _migration_regex(warning, current_revision, expected_revision)


def test_event_log_step_key_migration():
    src_dir = file_relative_path(__file__, "snapshot_0_7_6_pre_event_log_migration/sqlite")
    with copy_directory(src_dir) as test_dir:
        instance = DagsterInstance.from_ref(InstanceRef.from_dir(test_dir))

        # Make sure the schema is migrated
        instance.upgrade()

        runs = instance.get_runs()
        assert len(runs) == 1
        run_ids = instance._event_storage.get_all_run_ids()
        assert run_ids == ["6405c4a0-3ccc-4600-af81-b5ee197f8528"]
        assert isinstance(instance._event_storage, SqlEventLogStorage)
        events_by_id = instance._event_storage.get_logs_for_run_by_log_id(
            "6405c4a0-3ccc-4600-af81-b5ee197f8528"
        )
        assert len(events_by_id) == 40

        step_key_records = []
        for record_id, _event in events_by_id.items():
            row_data = instance._event_storage.get_event_log_table_data(
                "6405c4a0-3ccc-4600-af81-b5ee197f8528", record_id
            )
            if row_data.step_key is not None:
                step_key_records.append(row_data)
        assert len(step_key_records) == 0

        # run the event_log backfill migration
        migrate_event_log_data(instance=instance)

        step_key_records = []
        for record_id, _event in events_by_id.items():
            row_data = instance._event_storage.get_event_log_table_data(
                "6405c4a0-3ccc-4600-af81-b5ee197f8528", record_id
            )
            if row_data.step_key is not None:
                step_key_records.append(row_data)
        assert len(step_key_records) > 0


def get_sqlite3_tables(db_path):
    con = sqlite3.connect(db_path)
    cursor = con.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    return [r[0] for r in cursor.fetchall()]


def get_current_alembic_version(db_path):
    con = sqlite3.connect(db_path)
    cursor = con.cursor()
    cursor.execute("SELECT * FROM alembic_version")
    return cursor.fetchall()[0][0]


def get_sqlite3_columns(db_path, table_name):
    con = sqlite3.connect(db_path)
    cursor = con.cursor()
    cursor.execute('PRAGMA table_info("{}");'.format(table_name))
    return [r[1] for r in cursor.fetchall()]


def test_snapshot_0_7_6_pre_add_pipeline_snapshot():
    run_id = "fb0b3905-068b-4444-8f00-76fcbaef7e8b"
    src_dir = file_relative_path(__file__, "snapshot_0_7_6_pre_add_pipeline_snapshot/sqlite")
    with copy_directory(src_dir) as test_dir:
        # invariant check to make sure migration has not been run yet

        db_path = os.path.join(test_dir, "history", "runs.db")

        assert get_current_alembic_version(db_path) == "9fe9e746268c"

        assert "snapshots" not in get_sqlite3_tables(db_path)

        instance = DagsterInstance.from_ref(InstanceRef.from_dir(test_dir))

        @solid
        def noop_solid(_):
            pass

        @pipeline
        def noop_pipeline():
            noop_solid()

        with pytest.raises(
            DagsterInstanceMigrationRequired,
            match=_run_storage_migration_regex(current_revision="9fe9e746268c"),
        ):
            execute_pipeline(noop_pipeline, instance=instance)

        assert len(instance.get_runs()) == 1

        # Make sure the schema is migrated
        instance.upgrade()

        assert "snapshots" in get_sqlite3_tables(db_path)
        assert {"id", "snapshot_id", "snapshot_body", "snapshot_type"} == set(
            get_sqlite3_columns(db_path, "snapshots")
        )

        assert len(instance.get_runs()) == 1

        run = instance.get_run_by_id(run_id)

        assert run.run_id == run_id
        assert run.pipeline_snapshot_id is None

        result = execute_pipeline(noop_pipeline, instance=instance)

        assert result.success

        runs = instance.get_runs()
        assert len(runs) == 2

        new_run_id = result.run_id

        new_run = instance.get_run_by_id(new_run_id)

        assert new_run.pipeline_snapshot_id


def test_downgrade_and_upgrade():
    src_dir = file_relative_path(__file__, "snapshot_0_7_6_pre_add_pipeline_snapshot/sqlite")
    with copy_directory(src_dir) as test_dir:
        # invariant check to make sure migration has not been run yet

        db_path = os.path.join(test_dir, "history", "runs.db")

        assert get_current_alembic_version(db_path) == "9fe9e746268c"

        assert "snapshots" not in get_sqlite3_tables(db_path)

        instance = DagsterInstance.from_ref(InstanceRef.from_dir(test_dir))

        assert len(instance.get_runs()) == 1

        # Make sure the schema is migrated
        instance.upgrade()

        assert "snapshots" in get_sqlite3_tables(db_path)
        assert {"id", "snapshot_id", "snapshot_body", "snapshot_type"} == set(
            get_sqlite3_columns(db_path, "snapshots")
        )

        assert len(instance.get_runs()) == 1

        instance._run_storage._alembic_downgrade(rev="9fe9e746268c")

        assert get_current_alembic_version(db_path) == "9fe9e746268c"

        assert "snapshots" not in get_sqlite3_tables(db_path)

        instance = DagsterInstance.from_ref(InstanceRef.from_dir(test_dir))

        assert len(instance.get_runs()) == 1

        instance.upgrade()

        assert "snapshots" in get_sqlite3_tables(db_path)
        assert {"id", "snapshot_id", "snapshot_body", "snapshot_type"} == set(
            get_sqlite3_columns(db_path, "snapshots")
        )

        assert len(instance.get_runs()) == 1


def test_event_log_asset_key_migration():
    src_dir = file_relative_path(__file__, "snapshot_0_7_8_pre_asset_key_migration/sqlite")
    with copy_directory(src_dir) as test_dir:
        db_path = os.path.join(
            test_dir, "history", "runs", "722183e4-119f-4a00-853f-e1257be82ddb.db"
        )
        assert get_current_alembic_version(db_path) == "3b1e175a2be3"
        assert "asset_key" not in set(get_sqlite3_columns(db_path, "event_log"))

        # Make sure the schema is migrated
        instance = DagsterInstance.from_ref(InstanceRef.from_dir(test_dir))
        instance.upgrade()

        assert "asset_key" in set(get_sqlite3_columns(db_path, "event_logs"))


def test_0_8_0_scheduler_migration():
    src_dir = file_relative_path(__file__, "snapshot_0_8_0_scheduler_change")
    with copy_directory(src_dir) as test_dir:
        instance = DagsterInstance.from_ref(InstanceRef.from_dir(test_dir))
        with pytest.raises(
            DagsterInstanceMigrationRequired,
            match=_schedule_storage_migration_regex(current_revision="da7cd32b690d"),
        ) as exc_info:
            instance.all_stored_schedule_state()

        assert "no such column: schedules.schedule_origin_id" in exc_info.exconly()

        instance.upgrade()

        # upgrade just drops tables, and user upgrade flow is cli entry - so
        # emulate by new-ing up instance which will create new tables
        instance = DagsterInstance.from_ref(InstanceRef.from_dir(test_dir))

        instance.all_stored_schedule_state()


def instance_from_debug_payloads(payload_files):
    debug_payloads = []
    for input_file in payload_files:
        with GzipFile(input_file, "rb") as file:
            blob = file.read().decode()
            debug_payload = deserialize_json_to_dagster_namedtuple(blob)

            check.invariant(isinstance(debug_payload, DebugRunPayload))

            debug_payloads.append(debug_payload)

    return DagsterInstance.ephemeral(preload=debug_payloads)


def test_object_store_operation_result_data_new_fields():
    """We added address and version fields to ObjectStoreOperationResultData.
    Make sure we can still deserialize old ObjectStoreOperationResultData without those fields."""
    instance_from_debug_payloads([file_relative_path(__file__, "0_9_12_nothing_fs_storage.gz")])
