import datetime
import multiprocessing
import threading
import time
import warnings
from collections import namedtuple
from contextlib import contextmanager

import sqlalchemy as db
from dagster_postgres.utils import get_conn
from six.moves.queue import Empty

from dagster import Field, String, check
from dagster.core.definitions.environment_configs import SystemNamedDict
from dagster.core.errors import DagsterInstanceMigrationRequired
from dagster.core.events.log import EventRecord
from dagster.core.serdes import (
    ConfigurableClass,
    ConfigurableClassData,
    deserialize_json_to_dagster_namedtuple,
    serialize_dagster_namedtuple,
)
from dagster.core.storage.event_log import (
    SqlEventLogStorage,
    SqlEventLogStorageMetadata,
    SqlEventLogStorageTable,
)
from dagster.core.storage.sql import (
    check_alembic_revision,
    create_engine,
    get_alembic_config,
    run_alembic_upgrade,
    stamp_alembic_rev,
)

from ..pynotify import await_pg_notifications

CHANNEL_NAME = 'run_events'

# Why? Because this is about as long as we expect a roundtrip to RDS to take.
WATCHER_POLL_INTERVAL = 0.2


class PostgresEventLogStorage(SqlEventLogStorage, ConfigurableClass):
    def __init__(self, postgres_url, inst_data=None):
        self.conn_string = check.str_param(postgres_url, 'postgres_url')
        self._event_watcher = create_event_watcher(self.conn_string)
        self._engine = create_engine(self.conn_string)
        SqlEventLogStorageMetadata.create_all(self.engine)
        alembic_config = get_alembic_config(__file__)
        with self.connect() as conn:
            db_revision, head_revision = check_alembic_revision(alembic_config, conn)
        # Fresh database
        if db_revision is None:
            stamp_alembic_rev(alembic_config, self.engine)
        elif db_revision != head_revision:
            raise DagsterInstanceMigrationRequired(
                msg='PostgresEventLogStorage', db_revision=db_revision, head_revision=head_revision
            )
        self._inst_data = check.opt_inst_param(inst_data, 'inst_data', ConfigurableClassData)

    @property
    def engine(self):
        return self._engine

    def upgrade(self):
        alembic_config = get_alembic_config(__file__)
        run_alembic_upgrade(alembic_config, self.engine)

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return SystemNamedDict('PostgresRunStorageConfig', {'postgres_url': Field(String)})

    @staticmethod
    def from_config_value(inst_data, config_value, **kwargs):
        return PostgresEventLogStorage(inst_data=inst_data, **dict(config_value, **kwargs))

    @staticmethod
    def create_clean_storage(conn_string):
        inst = PostgresEventLogStorage(conn_string)
        inst.wipe()
        return inst

    def store_event(self, event):
        '''Store an event corresponding to a pipeline run.
        Args:
            event (EventRecord): The event to store.
        '''
        check.inst_param(event, 'event', EventRecord)

        dagster_event_type = None
        if event.is_dagster_event:
            dagster_event_type = event.dagster_event.event_type_value

        run_id = event.run_id

        with self.connect() as conn:
            # https://stackoverflow.com/a/54386260/324449
            event_insert = SqlEventLogStorageTable.insert().values(  # pylint: disable=no-value-for-parameter
                run_id=run_id,
                event=serialize_dagster_namedtuple(event),
                dagster_event_type=dagster_event_type,
                timestamp=datetime.datetime.fromtimestamp(event.timestamp),
            )
            result_proxy = conn.execute(
                event_insert.returning(
                    SqlEventLogStorageTable.c.run_id, SqlEventLogStorageTable.c.id
                )
            )
            res = result_proxy.fetchone()

        with get_conn(self.conn_string).cursor() as conn:
            conn.execute(
                '''NOTIFY {channel}, %s; '''.format(channel=CHANNEL_NAME),
                (res[0] + '_' + str(res[1]),),
            )

    @contextmanager
    def connect(self, run_id=None):
        yield self.engine.connect()

    def watch(self, run_id, start_cursor, callback):
        self._event_watcher.watch_run(run_id, start_cursor, callback)

    def end_watch(self, run_id, handler):
        self._event_watcher.unwatch_run(run_id, handler)

    @property
    def event_watcher(self):
        return self._event_watcher

    def __del__(self):
        # Keep the inherent limitations of __del__ in Python in mind!
        self._event_watcher.close()


EventWatcherProcessStartedEvent = namedtuple('EventWatcherProcessStartedEvent', '')
EventWatcherStart = namedtuple('EventWatcherStart', '')
EventWatcherEvent = namedtuple('EventWatcherEvent', 'payload')
EventWatchFailed = namedtuple('EventWatchFailed', 'message')
EventWatcherEnd = namedtuple('EventWatcherEnd', '')

EventWatcherThreadEvents = (
    EventWatcherProcessStartedEvent,
    EventWatcherStart,
    EventWatcherEvent,
    EventWatchFailed,
    EventWatcherEnd,
)
EventWatcherThreadNoopEvents = (EventWatcherProcessStartedEvent, EventWatcherStart)
EventWatcherThreadEndEvents = (EventWatchFailed, EventWatcherEnd)

POLLING_CADENCE = 0.25


def _postgres_event_watcher_event_loop(conn_string, queue, run_id_dict):
    init_called = False
    queue.put(EventWatcherProcessStartedEvent())
    try:
        for notif in await_pg_notifications(
            conn_string, channels=[CHANNEL_NAME], timeout=POLLING_CADENCE, yield_on_timeout=True
        ):
            if not init_called:
                init_called = True
                queue.put(EventWatcherStart())

            if notif is not None:
                run_id, index = notif.payload.split('_')
                if run_id in run_id_dict:
                    queue.put(EventWatcherEvent((run_id, index)))
            else:
                # The polling window has timed out
                pass

    except Exception as e:  # pylint: disable=broad-except
        queue.put(EventWatchFailed(message=str(e)))
    finally:
        queue.put(EventWatcherEnd())


def create_event_watcher(conn_string):
    check.str_param(conn_string, 'conn_string')

    queue = multiprocessing.Queue()
    m_dict = multiprocessing.Manager().dict()
    process = multiprocessing.Process(
        target=_postgres_event_watcher_event_loop, args=(conn_string, queue, m_dict)
    )

    process.start()

    # block and ensure that the process has actually started. This was required
    # to get processes to start in linux in buildkite.
    check.inst(queue.get(block=True), EventWatcherProcessStartedEvent)

    return PostgresEventWatcher(process, queue, m_dict, conn_string)


def watcher_thread(conn_string, queue, handlers_dict, dict_lock, watcher_thread_exit):
    done = False
    while not done and not watcher_thread_exit.is_set():
        event_list = []
        while not queue.empty():
            try:
                evt = queue.get_nowait()
                event_list.append(evt)
            except Empty:
                pass

        for event in event_list:
            if not isinstance(event, EventWatcherThreadEvents):
                warnings.warn(
                    'Event watcher thread got unexpected event {event}'.format(event=event)
                )
                continue
            if isinstance(event, EventWatcherThreadNoopEvents):
                continue
            elif isinstance(event, EventWatcherThreadEndEvents):
                done = True
            else:
                assert isinstance(event, EventWatcherEvent)
                run_id, index_str = event.payload
                index = int(index_str)
                with dict_lock:
                    handlers = handlers_dict.get(run_id, [])

                engine = create_engine(conn_string)
                res = engine.execute(
                    db.select([SqlEventLogStorageTable.c.event]).where(
                        SqlEventLogStorageTable.c.id == index
                    )
                )
                dagster_event = deserialize_json_to_dagster_namedtuple(res.fetchone()[0])

                for (cursor, callback) in handlers:
                    if index >= cursor:
                        callback(dagster_event)
        time.sleep(WATCHER_POLL_INTERVAL)


class PostgresEventWatcher(object):
    def __init__(self, process, queue, run_id_dict, conn_string):
        self.process = check.inst_param(process, 'process', multiprocessing.Process)
        self.run_id_dict = check.inst_param(
            run_id_dict, 'run_id_dict', multiprocessing.managers.DictProxy
        )
        self.handlers_dict = {}
        self.dict_lock = threading.Lock()
        self.queue = check.inst_param(queue, 'queue', multiprocessing.queues.Queue)
        self.conn_string = conn_string
        self.watcher_thread_exit = threading.Event()
        self.watcher_thread = threading.Thread(
            target=watcher_thread,
            args=(
                self.conn_string,
                self.queue,
                self.handlers_dict,
                self.dict_lock,
                self.watcher_thread_exit,
            ),
        )
        self.watcher_thread.start()

    def has_run_id(self, run_id):
        with self.dict_lock:
            _has_run_id = run_id in self.run_id_dict
        return _has_run_id

    def watch_run(self, run_id, start_cursor, callback):
        with self.dict_lock:
            if run_id in self.run_id_dict:
                self.handlers_dict[run_id].append((start_cursor, callback))
            else:
                # See: https://docs.python.org/2/library/multiprocessing.html#multiprocessing.managers.SyncManager
                run_id_dict = self.run_id_dict
                run_id_dict[run_id] = None
                self.run_id_dict = run_id_dict
                self.handlers_dict[run_id] = [(start_cursor, callback)]

    def unwatch_run(self, run_id, handler):
        with self.dict_lock:
            if run_id in self.run_id_dict:
                self.handlers_dict[run_id] = [
                    (start_cursor, callback)
                    for (start_cursor, callback) in self.handlers_dict[run_id]
                    if callback != handler
                ]
            if not self.handlers_dict[run_id]:
                del self.handlers_dict[run_id]
                run_id_dict = self.run_id_dict
                del run_id_dict[run_id]
                self.run_id_dict = run_id_dict

    def close(self):
        self.process.terminate()
        self.process.join()
        self.watcher_thread_exit.set()
