from abc import ABC, abstractmethod, abstractproperty
from typing import Callable, Iterable, List, Optional

import pyrsistent
from dagster.core.definitions.events import AssetKey
from dagster.core.events.log import EventRecord
from dagster.core.execution.stats import (
    RunStepKeyStatsSnapshot,
    build_run_stats_from_events,
    build_run_step_stats_from_events,
)
from dagster.core.storage.pipeline_run import PipelineRunStatsSnapshot


class EventLogSequence(pyrsistent.CheckedPVector):
    __type__ = EventRecord


class EventLogStorage(ABC):
    """Abstract base class for storing structured event logs from pipeline runs.

    Note that event log storages using SQL databases as backing stores should implement
    :py:class:`~dagster.core.storage.event_log.SqlEventLogStorage`.

    Users should not directly instantiate concrete subclasses of this class; they are instantiated
    by internal machinery when ``dagit`` and ``dagster-graphql`` load, based on the values in the
    ``dagster.yaml`` file in ``$DAGSTER_HOME``. Configuration of concrete subclasses of this class
    should be done by setting values in that file.
    """

    @abstractmethod
    def get_logs_for_run(self, run_id: str, cursor: Optional[int] = -1) -> Iterable[EventRecord]:
        """Get all of the logs corresponding to a run.

        Args:
            run_id (str): The id of the run for which to fetch logs.
            cursor (Optional[int]): Zero-indexed logs will be returned starting from cursor + 1,
                i.e., if cursor is -1, all logs will be returned. (default: -1)
        """

    def get_stats_for_run(self, run_id: str) -> PipelineRunStatsSnapshot:
        """Get a summary of events that have ocurred in a run."""
        return build_run_stats_from_events(run_id, self.get_logs_for_run(run_id))

    def get_step_stats_for_run(self, run_id: str, step_keys=None) -> RunStepKeyStatsSnapshot:
        """Get per-step stats for a pipeline run."""
        logs = self.get_logs_for_run(run_id)
        if step_keys:
            logs = [
                event
                for event in logs
                if event.is_dagster_event and event.dagster_event.step_key in step_keys
            ]

        return build_run_step_stats_from_events(run_id, logs)

    @abstractmethod
    def store_event(self, event: EventRecord):
        """Store an event corresponding to a pipeline run.

        Args:
            event (EventRecord): The event to store.
        """

    @abstractmethod
    def delete_events(self, run_id: str):
        """Remove events for a given run id"""

    @abstractmethod
    def upgrade(self):
        """This method should perform any schema migrations necessary to bring an
        out-of-date instance of the storage up to date.
        """

    @abstractmethod
    def reindex(self, print_fn: Callable = lambda _: None, force: bool = False):
        """Call this method to run any data migrations, reindexing to build summary tables."""

    @abstractmethod
    def wipe(self):
        """Clear the log storage."""

    @abstractmethod
    def watch(self, run_id: str, start_cursor: int, callback: Callable):
        """Call this method to start watching."""

    @abstractmethod
    def end_watch(self, run_id: str, handler: Callable):
        """Call this method to stop watching."""

    @abstractmethod
    def has_secondary_index(self, name: str, run_id: str = None) -> bool:
        """Whether the secondary index for a given name is enabled."""

    @abstractmethod
    def enable_secondary_index(self, name: str, run_id: str = None):
        """Call to enable the secondary index for a given name."""

    @abstractproperty
    def is_persistent(self) -> bool:
        """bool: Whether the storage is persistent."""

    def dispose(self):
        """Explicit lifecycle management."""

    @property
    def is_asset_aware(self) -> bool:
        return isinstance(self, AssetAwareEventLogStorage)

    def optimize_for_dagit(self, statement_timeout: int):
        """Allows for optimizing database connection / use in the context of a long lived dagit process"""


class AssetAwareEventLogStorage(ABC):
    @abstractmethod
    def has_asset_key(self, asset_key: AssetKey):
        pass

    @abstractmethod
    def get_all_asset_keys(self, prefix_path: str = None) -> Iterable[AssetKey]:
        pass

    @abstractmethod
    def get_asset_events(
        self,
        asset_key: AssetKey,
        partitions: List[str] = None,
        cursor: int = None,
        limit: int = None,
        ascending: bool = False,
        include_cursor: bool = False,
    ) -> Iterable[EventRecord]:
        pass

    @abstractmethod
    def get_asset_run_ids(self, asset_key: AssetKey) -> Iterable[str]:
        pass

    @abstractmethod
    def wipe_asset(self, asset_key: AssetKey):
        """Remove asset index history from event log for given asset_key"""
