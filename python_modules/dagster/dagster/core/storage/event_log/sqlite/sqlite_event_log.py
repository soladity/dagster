import glob
import logging
import os
import sqlite3
import threading
import time
from collections import defaultdict
from contextlib import contextmanager

import sqlalchemy as db
from dagster import StringSource, check
from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.core.storage.sql import (
    check_alembic_revision,
    create_engine,
    get_alembic_config,
    handle_schema_errors,
    run_alembic_upgrade,
    stamp_alembic_rev,
)
from dagster.core.storage.sqlite import create_db_conn_string
from dagster.serdes import ConfigurableClass, ConfigurableClassData
from dagster.utils import mkdir_p
from sqlalchemy.pool import NullPool
from tqdm import tqdm
from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer

from ..schema import SqlEventLogStorageMetadata
from ..sql_event_log import SqlEventLogStorage


class SqliteEventLogStorage(SqlEventLogStorage, ConfigurableClass):
    """SQLite-backed event log storage.

    Users should not directly instantiate this class; it is instantiated by internal machinery when
    ``dagit`` and ``dagster-graphql`` load, based on the values in the ``dagster.yaml`` file in
    ``$DAGSTER_HOME``. Configuration of this class should be done by setting values in that file.

    This is the default event log storage when none is specified in the ``dagster.yaml``.

    To explicitly specify SQLite for event log storage, you can add a block such as the following
    to your ``dagster.yaml``:

    .. code-block:: YAML

        event_log_storage:
          module: dagster.core.storage.event_log
          class: SqliteEventLogStorage
          config:
            base_dir: /path/to/dir

    The ``base_dir`` param tells the event log storage where on disk to store the databases. To
    improve concurrent performance, event logs are stored in a separate SQLite database for each
    run.
    """

    def __init__(self, base_dir, inst_data=None):
        """Note that idempotent initialization of the SQLite database is done on a per-run_id
        basis in the body of connect, since each run is stored in a separate database."""
        self._base_dir = os.path.abspath(check.str_param(base_dir, "base_dir"))
        mkdir_p(self._base_dir)

        self._watchers = defaultdict(dict)
        self._obs = Observer()
        self._obs.start()
        self._inst_data = check.opt_inst_param(inst_data, "inst_data", ConfigurableClassData)

        # Used to ensure that each run ID attempts to initialize its DB the first time it connects,
        # ensuring that the database will be created if it doesn't exist
        self._initialized_dbs = set()

        # Ensure that multiple threads (like the event log watcher) interact safely with each other
        self._db_lock = threading.Lock()

    def upgrade(self):
        all_run_ids = self.get_all_run_ids()
        print(  # pylint: disable=print-call
            "Updating event log storage for {n_runs} runs on disk...".format(
                n_runs=len(all_run_ids)
            )
        )
        alembic_config = get_alembic_config(__file__)
        for run_id in tqdm(all_run_ids):
            with self.connect(run_id) as conn:
                run_alembic_upgrade(alembic_config, conn, run_id)

        self._initialized_dbs = set()

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return {"base_dir": StringSource}

    @staticmethod
    def from_config_value(inst_data, config_value):
        return SqliteEventLogStorage(inst_data=inst_data, **config_value)

    def get_all_run_ids(self):
        all_filenames = glob.glob(os.path.join(self._base_dir, "*.db"))
        return [os.path.splitext(os.path.basename(filename))[0] for filename in all_filenames]

    def path_for_run_id(self, run_id):
        return os.path.join(self._base_dir, "{run_id}.db".format(run_id=run_id))

    def conn_string_for_run_id(self, run_id):
        check.str_param(run_id, "run_id")
        return create_db_conn_string(self._base_dir, run_id)

    def _initdb(self, engine):
        alembic_config = get_alembic_config(__file__)

        retry_limit = 10

        while True:
            try:

                with engine.connect() as connection:
                    db_revision, head_revision = check_alembic_revision(alembic_config, connection)

                    if not (db_revision and head_revision):
                        SqlEventLogStorageMetadata.create_all(engine)
                        engine.execute("PRAGMA journal_mode=WAL;")
                        stamp_alembic_rev(alembic_config, connection)

                break
            except (db.exc.DatabaseError, sqlite3.DatabaseError, sqlite3.OperationalError) as exc:
                # This is SQLite-specific handling for concurrency issues that can arise when
                # multiple processes (e.g. the dagit process and user code process) contend with
                # each other to init the db. When we hit the following errors, we know that another
                # process is on the case and we should retry.
                err_msg = str(exc)

                if not (
                    "table asset_keys already exists" in err_msg
                    or "table secondary_indexes already exists" in err_msg
                    or "table event_logs already exists" in err_msg
                    or "database is locked" in err_msg
                    or "table alembic_version already exists" in err_msg
                    or "UNIQUE constraint failed: alembic_version.version_num" in err_msg
                ):
                    raise

                if retry_limit == 0:
                    raise
                else:
                    logging.info(
                        "SqliteEventLogStorage._initdb: Encountered apparent concurrent init, "
                        "retrying ({retry_limit} retries left). Exception: {str_exc}".format(
                            retry_limit=retry_limit, str_exc=err_msg
                        )
                    )
                    time.sleep(0.2)
                    retry_limit -= 1

    @contextmanager
    def connect(self, run_id=None):
        with self._db_lock:
            check.str_param(run_id, "run_id")

            conn_string = self.conn_string_for_run_id(run_id)
            engine = create_engine(conn_string, poolclass=NullPool)

            if not run_id in self._initialized_dbs:
                self._initdb(engine)
                self._initialized_dbs.add(run_id)

            conn = engine.connect()

            try:
                with handle_schema_errors(
                    conn,
                    get_alembic_config(__file__),
                    msg="SqliteEventLogStorage for run {run_id}".format(run_id=run_id),
                ):
                    yield conn
            finally:
                conn.close()
            engine.dispose()

    def has_secondary_index(self, name, run_id=None):
        return False

    def enable_secondary_index(self, name, run_id=None):
        pass

    def wipe(self):
        for filename in (
            glob.glob(os.path.join(self._base_dir, "*.db"))
            + glob.glob(os.path.join(self._base_dir, "*.db-wal"))
            + glob.glob(os.path.join(self._base_dir, "*.db-shm"))
        ):
            os.unlink(filename)

        self._initialized_dbs = set()

    def watch(self, run_id, start_cursor, callback):
        watchdog = SqliteEventLogStorageWatchdog(self, run_id, callback, start_cursor)
        self._watchers[run_id][callback] = (
            watchdog,
            self._obs.schedule(watchdog, self._base_dir, True),
        )

    def end_watch(self, run_id, handler):
        if handler in self._watchers[run_id]:
            event_handler, watch = self._watchers[run_id][handler]
            self._obs.remove_handler_for_watch(event_handler, watch)
            del self._watchers[run_id][handler]


class SqliteEventLogStorageWatchdog(PatternMatchingEventHandler):
    def __init__(self, event_log_storage, run_id, callback, start_cursor, **kwargs):
        self._event_log_storage = check.inst_param(
            event_log_storage, "event_log_storage", SqliteEventLogStorage
        )
        self._run_id = check.str_param(run_id, "run_id")
        self._cb = check.callable_param(callback, "callback")
        self._log_path = event_log_storage.path_for_run_id(run_id)
        self._cursor = start_cursor if start_cursor is not None else -1
        super(SqliteEventLogStorageWatchdog, self).__init__(patterns=[self._log_path], **kwargs)

    def _process_log(self):
        events = self._event_log_storage.get_logs_for_run(self._run_id, self._cursor)
        self._cursor += len(events)
        for event in events:
            status = self._cb(event)

            if (
                status == PipelineRunStatus.SUCCESS
                or status == PipelineRunStatus.FAILURE
                or status == PipelineRunStatus.CANCELED
            ):
                self._event_log_storage.end_watch(self._run_id, self._cb)

    def on_modified(self, event):
        check.invariant(event.src_path == self._log_path)
        self._process_log()
