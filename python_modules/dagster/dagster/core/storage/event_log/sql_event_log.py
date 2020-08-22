import logging
from abc import abstractmethod
from collections import defaultdict

import six
import sqlalchemy as db

from dagster import check, seven
from dagster.core.definitions.events import AssetKey, Materialization
from dagster.core.errors import DagsterEventLogInvalidForRun
from dagster.core.events import DagsterEventType
from dagster.core.events.log import EventRecord
from dagster.core.execution.stats import RunStepKeyStatsSnapshot, StepEventStatus
from dagster.serdes import deserialize_json_to_dagster_namedtuple, serialize_dagster_namedtuple
from dagster.utils import datetime_as_float, utc_datetime_from_timestamp

from ..pipeline_run import PipelineRunStatsSnapshot
from .base import AssetAwareEventLogStorage, EventLogStorage
from .schema import SqlEventLogStorageTable


class SqlEventLogStorage(EventLogStorage):
    """Base class for SQL backed event log storages.
    """

    @abstractmethod
    def connect(self, run_id=None):
        """Context manager yielding a connection.

        Args:
            run_id (Optional[str]): Enables those storages which shard based on run_id, e.g.,
                SqliteEventLogStorage, to connect appropriately.
        """

    @abstractmethod
    def upgrade(self):
        """This method should perform any schema or data migrations necessary to bring an
        out-of-date instance of the storage up to date.
        """

    def prepare_insert_statement(self, event):
        """ Helper method for preparing the event log SQL insertion statement.  Abstracted away to
        have a single place for the logical table representation of the event, while having a way
        for SQL backends to implement different execution implementations for `store_event`. See
        the `dagster-postgres` implementation which overrides the generic SQL implementation of
        `store_event`.
        """

        dagster_event_type = None
        asset_key_str = None
        step_key = event.step_key

        if event.is_dagster_event:
            dagster_event_type = event.dagster_event.event_type_value
            step_key = event.dagster_event.step_key
            if event.dagster_event.asset_key:
                check.inst_param(event.dagster_event.asset_key, "asset_key", AssetKey)
                asset_key_str = event.dagster_event.asset_key.to_string()

        # https://stackoverflow.com/a/54386260/324449
        return SqlEventLogStorageTable.insert().values(  # pylint: disable=no-value-for-parameter
            run_id=event.run_id,
            event=serialize_dagster_namedtuple(event),
            dagster_event_type=dagster_event_type,
            timestamp=utc_datetime_from_timestamp(event.timestamp),
            step_key=step_key,
            asset_key=asset_key_str,
        )

    def store_event(self, event):
        """Store an event corresponding to a pipeline run.

        Args:
            event (EventRecord): The event to store.
        """
        check.inst_param(event, "event", EventRecord)
        sql_statement = self.prepare_insert_statement(event)
        run_id = event.run_id

        with self.connect(run_id) as conn:
            conn.execute(sql_statement)

    def get_logs_for_run_by_log_id(self, run_id, cursor=-1):
        check.str_param(run_id, "run_id")
        check.int_param(cursor, "cursor")
        check.invariant(
            cursor >= -1,
            "Don't know what to do with negative cursor {cursor}".format(cursor=cursor),
        )

        # cursor starts at 0 & auto-increment column starts at 1 so adjust
        cursor = cursor + 1

        query = (
            db.select([SqlEventLogStorageTable.c.id, SqlEventLogStorageTable.c.event])
            .where(SqlEventLogStorageTable.c.run_id == run_id)
            .where(SqlEventLogStorageTable.c.id > cursor)
            .order_by(SqlEventLogStorageTable.c.id.asc())
        )

        with self.connect(run_id) as conn:
            results = conn.execute(query).fetchall()

        events = {}
        try:
            for (record_id, json_str,) in results:
                events[record_id] = check.inst_param(
                    deserialize_json_to_dagster_namedtuple(json_str), "event", EventRecord
                )
        except (seven.JSONDecodeError, check.CheckError) as err:
            six.raise_from(DagsterEventLogInvalidForRun(run_id=run_id), err)

        return events

    def get_logs_for_run(self, run_id, cursor=-1):
        """Get all of the logs corresponding to a run.

        Args:
            run_id (str): The id of the run for which to fetch logs.
            cursor (Optional[int]): Zero-indexed logs will be returned starting from cursor + 1,
                i.e., if cursor is -1, all logs will be returned. (default: -1)
        """
        check.str_param(run_id, "run_id")
        check.int_param(cursor, "cursor")
        check.invariant(
            cursor >= -1,
            "Don't know what to do with negative cursor {cursor}".format(cursor=cursor),
        )

        events_by_id = self.get_logs_for_run_by_log_id(run_id, cursor)
        return [event for id, event in sorted(events_by_id.items(), key=lambda x: x[0])]

    def get_stats_for_run(self, run_id):
        check.str_param(run_id, "run_id")

        query = (
            db.select(
                [
                    SqlEventLogStorageTable.c.dagster_event_type,
                    db.func.count().label("n_events_of_type"),
                    db.func.max(SqlEventLogStorageTable.c.timestamp).label("last_event_timestamp"),
                ]
            )
            .where(SqlEventLogStorageTable.c.run_id == run_id)
            .group_by("dagster_event_type")
        )

        with self.connect(run_id) as conn:
            results = conn.execute(query).fetchall()

        try:
            counts = {}
            times = {}
            for result in results:
                (dagster_event_type, n_events_of_type, last_event_timestamp) = result
                if dagster_event_type:
                    counts[dagster_event_type] = n_events_of_type
                    times[dagster_event_type] = last_event_timestamp

            start_time = times.get(DagsterEventType.PIPELINE_START.value, None)
            end_time = times.get(
                DagsterEventType.PIPELINE_SUCCESS.value,
                times.get(DagsterEventType.PIPELINE_FAILURE.value, None),
            )

            return PipelineRunStatsSnapshot(
                run_id=run_id,
                steps_succeeded=counts.get(DagsterEventType.STEP_SUCCESS.value, 0),
                steps_failed=counts.get(DagsterEventType.STEP_FAILURE.value, 0),
                materializations=counts.get(DagsterEventType.STEP_MATERIALIZATION.value, 0),
                expectations=counts.get(DagsterEventType.STEP_EXPECTATION_RESULT.value, 0),
                start_time=datetime_as_float(start_time) if start_time else None,
                end_time=datetime_as_float(end_time) if end_time else None,
            )
        except (seven.JSONDecodeError, check.CheckError) as err:
            six.raise_from(DagsterEventLogInvalidForRun(run_id=run_id), err)

    def get_step_stats_for_run(self, run_id):
        check.str_param(run_id, "run_id")

        STEP_STATS_EVENT_TYPES = [
            DagsterEventType.STEP_START.value,
            DagsterEventType.STEP_SUCCESS.value,
            DagsterEventType.STEP_SKIPPED.value,
            DagsterEventType.STEP_FAILURE.value,
        ]

        by_step_query = (
            db.select(
                [
                    SqlEventLogStorageTable.c.step_key,
                    SqlEventLogStorageTable.c.dagster_event_type,
                    db.func.max(SqlEventLogStorageTable.c.timestamp).label("timestamp"),
                ]
            )
            .where(SqlEventLogStorageTable.c.run_id == run_id)
            .where(SqlEventLogStorageTable.c.step_key != None)
            .where(SqlEventLogStorageTable.c.dagster_event_type.in_(STEP_STATS_EVENT_TYPES))
            .group_by(
                SqlEventLogStorageTable.c.step_key, SqlEventLogStorageTable.c.dagster_event_type,
            )
        )

        with self.connect(run_id) as conn:
            results = conn.execute(by_step_query).fetchall()

        by_step_key = defaultdict(dict)
        for result in results:
            step_key = result.step_key
            if result.dagster_event_type == DagsterEventType.STEP_START.value:
                by_step_key[step_key]["start_time"] = (
                    datetime_as_float(result.timestamp) if result.timestamp else None
                )
            if result.dagster_event_type == DagsterEventType.STEP_FAILURE.value:
                by_step_key[step_key]["end_time"] = (
                    datetime_as_float(result.timestamp) if result.timestamp else None
                )
                by_step_key[step_key]["status"] = StepEventStatus.FAILURE
            if result.dagster_event_type == DagsterEventType.STEP_SUCCESS.value:
                by_step_key[step_key]["end_time"] = (
                    datetime_as_float(result.timestamp) if result.timestamp else None
                )
                by_step_key[step_key]["status"] = StepEventStatus.SUCCESS
            if result.dagster_event_type == DagsterEventType.STEP_SKIPPED.value:
                by_step_key[step_key]["end_time"] = (
                    datetime_as_float(result.timestamp) if result.timestamp else None
                )
                by_step_key[step_key]["status"] = StepEventStatus.SKIPPED

        materializations = defaultdict(list)
        expectation_results = defaultdict(list)
        raw_event_query = (
            db.select([SqlEventLogStorageTable.c.event])
            .where(SqlEventLogStorageTable.c.run_id == run_id)
            .where(SqlEventLogStorageTable.c.step_key != None)
            .where(
                SqlEventLogStorageTable.c.dagster_event_type.in_(
                    [
                        DagsterEventType.STEP_MATERIALIZATION.value,
                        DagsterEventType.STEP_EXPECTATION_RESULT.value,
                    ]
                )
            )
            .order_by(SqlEventLogStorageTable.c.id.asc())
        )

        with self.connect(run_id) as conn:
            results = conn.execute(raw_event_query).fetchall()

        try:
            for (json_str,) in results:
                event = check.inst_param(
                    deserialize_json_to_dagster_namedtuple(json_str), "event", EventRecord
                )
                if event.dagster_event.event_type == DagsterEventType.STEP_MATERIALIZATION:
                    materializations[event.step_key].append(
                        event.dagster_event.event_specific_data.materialization
                    )
                elif event.dagster_event.event_type == DagsterEventType.STEP_EXPECTATION_RESULT:
                    expectation_results[event.step_key].append(
                        event.dagster_event.event_specific_data.expectation_result
                    )
        except (seven.JSONDecodeError, check.CheckError) as err:
            six.raise_from(DagsterEventLogInvalidForRun(run_id=run_id), err)

        return [
            RunStepKeyStatsSnapshot(
                run_id=run_id,
                step_key=step_key,
                status=value.get("status"),
                start_time=value.get("start_time"),
                end_time=value.get("end_time"),
                materializations=materializations.get(step_key),
                expectation_results=expectation_results.get(step_key),
            )
            for step_key, value in by_step_key.items()
        ]

    def wipe(self):
        """Clears the event log storage."""
        # Should be overridden by SqliteEventLogStorage and other storages that shard based on
        # run_id
        # https://stackoverflow.com/a/54386260/324449
        with self.connect() as conn:
            conn.execute(SqlEventLogStorageTable.delete())  # pylint: disable=no-value-for-parameter

    def delete_events(self, run_id):
        check.str_param(run_id, "run_id")

        statement = SqlEventLogStorageTable.delete().where(  # pylint: disable=no-value-for-parameter
            SqlEventLogStorageTable.c.run_id == run_id
        )

        with self.connect(run_id) as conn:
            conn.execute(statement)

    @property
    def is_persistent(self):
        return True

    def update_event_log_record(self, record_id, event):
        """ Utility method for migration scripts to update SQL representation of event records. """
        check.int_param(record_id, "record_id")
        check.inst_param(event, "event", EventRecord)
        dagster_event_type = None
        asset_key_str = None
        if event.is_dagster_event:
            dagster_event_type = event.dagster_event.event_type_value
            if event.dagster_event.asset_key:
                check.inst_param(event.dagster_event.asset_key, "asset_key", AssetKey)
                asset_key_str = event.dagster_event.asset_key.to_string()

        with self.connect(run_id=event.run_id) as conn:
            conn.execute(
                SqlEventLogStorageTable.update()  # pylint: disable=no-value-for-parameter
                .where(SqlEventLogStorageTable.c.id == record_id)
                .values(
                    event=serialize_dagster_namedtuple(event),
                    dagster_event_type=dagster_event_type,
                    timestamp=utc_datetime_from_timestamp(event.timestamp),
                    step_key=event.step_key,
                    asset_key=asset_key_str,
                )
            )

    def get_event_log_table_data(self, run_id, record_id):
        """ Utility method to test representation of the record in the SQL table.  Returns all of
        the columns stored in the event log storage (as opposed to the deserialized `EventRecord`).
        This allows checking that certain fields are extracted to support performant lookups (e.g.
        extracting `step_key` for fast filtering)"""
        with self.connect(run_id=run_id) as conn:
            query = (
                db.select([SqlEventLogStorageTable])
                .where(SqlEventLogStorageTable.c.id == record_id)
                .order_by(SqlEventLogStorageTable.c.id.asc())
            )
            return conn.execute(query).fetchone()


class AssetAwareSqlEventLogStorage(AssetAwareEventLogStorage, SqlEventLogStorage):
    @abstractmethod
    def connect(self, run_id=None):
        pass

    @abstractmethod
    def upgrade(self):
        pass

    def _add_cursor_limit_to_query(self, query, cursor, limit):
        """ Helper function to deal with cursor/limit pagination args """

        if cursor:
            cursor_query = db.select([SqlEventLogStorageTable.c.id]).where(
                SqlEventLogStorageTable.c.id == cursor
            )
            query = query.where(SqlEventLogStorageTable.c.id < cursor_query)

        if limit:
            query = query.limit(limit)

        query = query.order_by(SqlEventLogStorageTable.c.timestamp.desc())
        return query

    def get_all_asset_keys(self):
        query = db.select([SqlEventLogStorageTable.c.asset_key]).distinct()
        with self.connect() as conn:
            results = conn.execute(query).fetchall()

        return [AssetKey.from_db_string(asset_key) for (asset_key,) in results if asset_key]

    def get_asset_events(self, asset_key, cursor=None, limit=None):
        check.inst_param(asset_key, "asset_key", AssetKey)
        asset_key_str = asset_key.to_string()
        query = db.select([SqlEventLogStorageTable.c.id, SqlEventLogStorageTable.c.event]).where(
            SqlEventLogStorageTable.c.asset_key == asset_key_str
        )
        query = self._add_cursor_limit_to_query(query, cursor, limit)
        with self.connect() as conn:
            results = conn.execute(query).fetchall()

        events = []
        for row_id, json_str in results:
            try:
                event_record = deserialize_json_to_dagster_namedtuple(json_str)
                if not isinstance(event_record, EventRecord):
                    logging.warning(
                        "Could not resolve asset event record as EventRecord for id `{}`.".format(
                            row_id
                        )
                    )
                    continue
                events.append(event_record)
            except seven.JSONDecodeError:
                logging.warning("Could not parse asset event record id `{}`.".format(row_id))
        return events

    def get_asset_run_ids(self, asset_key):
        check.inst_param(asset_key, "asset_key", AssetKey)
        asset_key_str = asset_key.to_string()
        query = (
            db.select(
                [SqlEventLogStorageTable.c.run_id, db.func.max(SqlEventLogStorageTable.c.timestamp)]
            )
            .where(SqlEventLogStorageTable.c.asset_key == asset_key_str)
            .group_by(SqlEventLogStorageTable.c.run_id,)
            .order_by(db.func.max(SqlEventLogStorageTable.c.timestamp).desc())
        )

        with self.connect() as conn:
            results = conn.execute(query).fetchall()

        return [run_id for (run_id, _timestamp) in results]

    def wipe_asset(self, asset_key):
        check.inst_param(asset_key, "asset_key", AssetKey)
        query = db.select([SqlEventLogStorageTable.c.id, SqlEventLogStorageTable.c.event]).where(
            SqlEventLogStorageTable.c.asset_key == asset_key.to_string()
        )
        with self.connect() as conn:
            results = conn.execute(query).fetchall()

        for row_id, json_str in results:
            try:
                event_record = deserialize_json_to_dagster_namedtuple(json_str)
                if not isinstance(event_record, EventRecord):
                    continue

                assert event_record.dagster_event.event_specific_data.materialization.asset_key

                dagster_event = event_record.dagster_event
                event_specific_data = dagster_event.event_specific_data
                materialization = event_specific_data.materialization
                updated_materialization = Materialization(
                    label=materialization.label,
                    description=materialization.description,
                    metadata_entries=materialization.metadata_entries,
                    asset_key=None,
                    skip_deprecation_warning=True,
                )
                updated_event_specific_data = event_specific_data._replace(
                    materialization=updated_materialization
                )
                updated_dagster_event = dagster_event._replace(
                    event_specific_data=updated_event_specific_data
                )
                updated_record = event_record._replace(dagster_event=updated_dagster_event)

                # update the event_record here
                self.update_event_log_record(row_id, updated_record)

            except seven.JSONDecodeError:
                logging.warning("Could not parse asset event record id `{}`.".format(row_id))
