import logging
import os
from abc import ABCMeta
from collections import defaultdict, namedtuple
from enum import Enum

import six
import yaml
from rx import Observable

from dagster import check, seven
from dagster.core.definitions.environment_configs import SystemNamedDict
from dagster.core.errors import DagsterInvalidConfigError, DagsterInvariantViolationError
from dagster.core.serdes import whitelist_for_serdes
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.core.types import Field, PermissiveDict, String
from dagster.core.types.evaluator import evaluate_config
from dagster.utils.yaml_utils import load_yaml_from_globs

from .config import DAGSTER_CONFIG_YAML_FILENAME, dagster_feature_set, dagster_instance_config
from .features import DagsterFeatures
from .ref import InstanceRef, LocalInstanceRef


def _is_dagster_home_set():
    return bool(os.getenv('DAGSTER_HOME'))


def _dagster_root_storage_dir():
    dagster_home_path = os.getenv('DAGSTER_HOME')

    if not dagster_home_path:
        raise DagsterInvariantViolationError(
            'DAGSTER_HOME is not set, check is_dagster_home_set before invoking.'
        )

    return os.path.expanduser(dagster_home_path)


def _dagster_compute_log_manager(base_dir):
    config = dagster_instance_config(base_dir)
    compute_log_base = os.path.join(base_dir, 'storage')
    if config and config.get('compute_logs'):
        if 'module' in config['compute_logs'] and 'class' in config['compute_logs']:
            from dagster.core.storage.compute_log_manager import ComputeLogManager

            try:
                module = __import__(config['compute_logs']['module'])
                klass = getattr(module, config['compute_logs']['class'])
                check.subclass_param(klass, 'compute_log_manager', ComputeLogManager)
                kwargs = config['compute_logs'].get('config', {})
                compute_log_manager = klass(compute_log_base, **kwargs)
                check.inst_param(compute_log_manager, 'compute_log_manager', ComputeLogManager)
                return compute_log_manager
            except Exception:
                raise DagsterInvariantViolationError(
                    'Invalid dagster config in `{config_yaml_filename}`. Expecting `module`, '
                    '`class`, and `config`, returning a valid instance of '
                    '`ComputeLogManager`'.format(config_yaml_filename=DAGSTER_CONFIG_YAML_FILENAME)
                )

    from dagster.core.storage.local_compute_log_manager import LocalComputeLogManager

    return LocalComputeLogManager(compute_log_base)


class _EventListenerLogHandler(logging.Handler):
    def __init__(self, instance):
        self._instance = instance
        super(_EventListenerLogHandler, self).__init__()

    def emit(self, record):
        from dagster.core.events.log import construct_event_record, StructuredLoggerMessage

        try:
            event = construct_event_record(
                StructuredLoggerMessage(
                    name=record.name,
                    message=record.msg,
                    level=record.levelno,
                    meta=record.dagster_meta,
                    record=record,
                )
            )

            self._instance.handle_new_event(event)

        except Exception as e:  # pylint: disable=W0703
            logging.critical('Error during instance event listen')
            logging.exception(str(e))
            raise


class InstanceType(Enum):
    LOCAL = 'LOCAL'
    EPHEMERAL = 'EPHEMERAL'
    REMOTE = 'REMOTE'


class DagsterInstance:
    _PROCESS_TEMPDIR = None

    def __init__(
        self,
        instance_type,
        root_storage,
        run_storage,
        event_storage,
        compute_log_manager,
        feature_set=None,
    ):
        from dagster.core.storage.event_log import EventLogStorage
        from dagster.core.storage.root import RootStorage
        from dagster.core.storage.runs import RunStorage
        from dagster.core.storage.compute_log_manager import ComputeLogManager

        self._instance_type = check.inst_param(instance_type, 'instance_type', InstanceType)
        self._root_storage = check.inst_param(root_storage, 'root_storage', RootStorage)
        self._event_storage = check.inst_param(event_storage, 'event_storage', EventLogStorage)
        self._run_storage = check.inst_param(run_storage, 'run_storage', RunStorage)
        self._compute_log_manager = check.inst_param(
            compute_log_manager, 'compute_log_manager', ComputeLogManager
        )
        self._feature_set = check.opt_list_param(feature_set, 'feature_set', of_type=str)

        self._subscribers = defaultdict(list)

    @staticmethod
    def ephemeral(tempdir=None):
        from dagster.core.storage.event_log import InMemoryEventLogStorage
        from dagster.core.storage.root import RootStorage
        from dagster.core.storage.runs import InMemoryRunStorage
        from dagster.core.storage.local_compute_log_manager import NoOpComputeLogManager

        if tempdir is None:
            tempdir = DagsterInstance.temp_storage()

        feature_set = dagster_feature_set(tempdir)

        return DagsterInstance(
            InstanceType.EPHEMERAL,
            root_storage=RootStorage(tempdir),
            run_storage=InMemoryRunStorage(),
            event_storage=InMemoryEventLogStorage(),
            compute_log_manager=NoOpComputeLogManager(_compute_logs_base_directory(tempdir)),
            feature_set=feature_set,
        )

    @staticmethod
    def get(fallback_storage=None):
        # 1. Use $DAGSTER_HOME to determine instance if set.
        if _is_dagster_home_set():
            # in the future we can read from config and create RemoteInstanceRef when needed
            return DagsterInstance.from_ref(
                LocalInstanceRef.from_root_storage_dir(_dagster_root_storage_dir())
            )

        # 2. If that is not set use the fallback storage directory if provided.
        # This allows us to have a nice out of the box dagit experience where runs are persisted
        # across restarts in a tempdir that gets cleaned up when the dagit watchdog process exits.
        elif fallback_storage is not None:
            return DagsterInstance.from_ref(
                LocalInstanceRef.from_root_storage_dir(fallback_storage)
            )

        # 3. If all else fails create an ephemeral in memory instance.
        else:
            return DagsterInstance.ephemeral(fallback_storage)

    @staticmethod
    def local_temp(tempdir=None, features=None):
        features = check.opt_list_param(features, 'features', str)
        if tempdir is None:
            tempdir = DagsterInstance.temp_storage()

        return DagsterInstance.from_ref(LocalInstanceRef.from_root_storage_dir(tempdir), features)

    @staticmethod
    def from_ref(instance_ref, fallback_feature_set=None):
        check.inst_param(instance_ref, 'instance_ref', InstanceRef)
        check.opt_list_param(fallback_feature_set, 'fallback_feature_set', of_type=str)

        root_storage = instance_ref.root_storage_data.rehydrate()
        run_storage = instance_ref.run_storage_data.rehydrate()
        event_storage = instance_ref.event_storage_data.rehydrate()
        feature_set = instance_ref.feature_set or fallback_feature_set

        compute_log_manager = _dagster_compute_log_manager(root_storage.root_storage_dir)

        return DagsterInstance(
            instance_type=InstanceType.LOCAL,
            root_storage=root_storage,
            run_storage=run_storage,
            event_storage=event_storage,
            compute_log_manager=compute_log_manager,
            feature_set=feature_set,
        )

    @property
    def is_remote(self):
        return self._instance_type == InstanceType.REMOTE

    @property
    def is_local(self):
        return self._instance_type == InstanceType.LOCAL

    @property
    def is_ephemeral(self):
        return self._instance_type == InstanceType.EPHEMERAL

    def get_ref(self):
        if self._instance_type == InstanceType.LOCAL:
            return LocalInstanceRef.from_root_storage_dir(self._root_storage.root_storage_dir)

        check.failed('Can not produce an instance reference for {t}'.format(t=self._instance_type))

    @staticmethod
    def temp_storage():
        if DagsterInstance._PROCESS_TEMPDIR is None:
            DagsterInstance._PROCESS_TEMPDIR = seven.TemporaryDirectory()
        return DagsterInstance._PROCESS_TEMPDIR.name

    def root_directory(self):
        return self._root_storage.root_storage_dir

    # features

    def is_feature_enabled(self, feature):
        check.inst_param(feature, 'feature', DagsterFeatures)
        return feature.value in self._feature_set

    # compute logs

    @property
    def compute_log_manager(self):
        return self._compute_log_manager

    # run storage

    def get_run(self, run_id):
        return self._run_storage.get_run_by_id(run_id)

    def get_run_stats(self, run_id):
        return self._event_storage.get_stats_for_run(run_id)

    def create_empty_run(self, run_id, pipeline_name):
        return self.create_run(PipelineRun.create_empty_run(pipeline_name, run_id))

    def create_run(self, pipeline_run):
        check.inst_param(pipeline_run, 'pipeline_run', PipelineRun)
        check.invariant(
            not self._run_storage.has_run(pipeline_run.run_id),
            'Attempting to create a different pipeline run for an existing run id',
        )

        run = self._run_storage.add_run(pipeline_run)
        return run

    def get_or_create_run(self, pipeline_run):
        # This eventually needs transactional/locking semantics
        if self.has_run(pipeline_run.run_id):
            return self.get_run(pipeline_run.run_id)
        else:
            return self.create_run(pipeline_run)

    def has_run(self, run_id):
        return self._run_storage.has_run(run_id)

    def all_runs(self):
        return self._run_storage.all_runs()

    def all_runs_for_pipeline(self, pipeline):
        return self._run_storage.all_runs_for_pipeline(pipeline)

    def all_runs_for_tag(self, key, value):
        return self._run_storage.all_runs_for_tag(key, value)

    def wipe(self):
        self._run_storage.wipe()
        self._event_storage.wipe()

    # event storage

    def logs_after(self, run_id, cursor):
        return self._event_storage.get_logs_for_run(run_id, cursor=cursor)

    def all_logs(self, run_id):
        return self._event_storage.get_logs_for_run(run_id)

    def can_watch_events(self):
        from dagster.core.storage.event_log import WatchableEventLogStorage

        return isinstance(self._event_storage, WatchableEventLogStorage)

    def watch_event_logs(self, run_id, cursor, cb):
        from dagster.core.storage.event_log import WatchableEventLogStorage

        check.invariant(
            isinstance(self._event_storage, WatchableEventLogStorage),
            'In order to call watch_event_logs the event_storage must be watchable',
        )
        return self._event_storage.watch(run_id, cursor, cb)

    # event subscriptions

    def get_logger(self):
        logger = logging.Logger('__event_listener')
        logger.addHandler(_EventListenerLogHandler(self))
        logger.setLevel(10)
        return logger

    def handle_new_event(self, event):
        run_id = event.run_id

        if self._instance_type != InstanceType.EPHEMERAL:
            check.invariant(
                self._run_storage.has_run(run_id),
                'Can not handle events for unknown run with id {run_id} on non-ephemeral instance type'.format(
                    run_id=run_id
                ),
            )

        self._event_storage.store_event(event)

        if event.is_dagster_event and event.dagster_event.is_pipeline_event:
            self._run_storage.handle_run_event(run_id, event.dagster_event)

        for sub in self._subscribers[run_id]:
            sub(event)

    def add_event_listener(self, run_id, cb):
        self._subscribers[run_id].append(cb)

    # directories

    def file_manager_directory(self, run_id):
        return self._root_storage.file_manager_dir(run_id)

    def intermediates_directory(self, run_id):
        return self._root_storage.intermediates_dir(run_id)

    def schedules_directory(self):
        return self._root_storage.schedules_dir


def _compute_logs_base_directory(base):
    return os.path.join(base, 'storage')
