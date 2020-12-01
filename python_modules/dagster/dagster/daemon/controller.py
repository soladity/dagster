import datetime
import uuid

import pendulum
from dagster import check
from dagster.core.run_coordinator import QueuedRunCoordinator
from dagster.core.scheduler import DagsterDaemonScheduler
from dagster.daemon.daemon import SchedulerDaemon, SensorDaemon, get_default_daemon_logger
from dagster.daemon.run_coordinator.queued_run_coordinator_daemon import QueuedRunCoordinatorDaemon
from dagster.daemon.types import DaemonHeartbeat

# How many expected heartbeats can be skipped before the daemon is considered unhealthy.
# E.g, if a daemon has an interval of 30s, tolerating 1 skip means that it will be considered
# unhealthy 60s after the last heartbeat.
DAEMON_HEARTBEAT_SKIP_TOLERANCE = 2


def _sorted_quoted(strings):
    return "[" + ", ".join(["'{}'".format(s) for s in sorted(list(strings))]) + "]"


class DagsterDaemonController:
    def __init__(self, instance):
        self._instance = instance

        self._daemon_uuid = str(uuid.uuid4())

        self._daemons = {}
        self._last_heartbeat_time = None

        self._logger = get_default_daemon_logger("dagster-daemon")

        if isinstance(instance.scheduler, DagsterDaemonScheduler):
            max_catchup_runs = instance.scheduler.max_catchup_runs
            self._add_daemon(
                SchedulerDaemon(
                    instance,
                    interval_seconds=self._get_interval_seconds(instance, SchedulerDaemon.__name__),
                    max_catchup_runs=max_catchup_runs,
                )
            )

        self._add_daemon(
            SensorDaemon(
                instance,
                interval_seconds=self._get_interval_seconds(instance, SensorDaemon.__name__),
            )
        )

        if isinstance(instance.run_coordinator, QueuedRunCoordinator):
            max_concurrent_runs = instance.run_coordinator.max_concurrent_runs
            self._add_daemon(
                QueuedRunCoordinatorDaemon(
                    instance,
                    interval_seconds=self._get_interval_seconds(
                        instance, QueuedRunCoordinatorDaemon.__name__
                    ),
                    max_concurrent_runs=max_concurrent_runs,
                )
            )

        assert set(self._expected_daemons(instance)) == self._daemons.keys()

        if not self._daemons:
            raise Exception("No daemons configured on the DagsterInstance")

        self._logger.info(
            "instance is configured with the following daemons: {}".format(
                _sorted_quoted(type(daemon).__name__ for daemon in self.daemons)
            )
        )

    def _add_daemon(self, daemon):
        self._daemons[type(daemon).__name__] = daemon

    def get_daemon(self, daemon_type):
        return self._daemons.get(daemon_type)

    @property
    def daemons(self):
        return list(self._daemons.values())

    def run_iteration(self, curr_time):
        for daemon in self.daemons:
            if (not daemon.last_iteration_time) or (
                (curr_time - daemon.last_iteration_time).total_seconds() >= daemon.interval_seconds
            ):
                daemon.last_iteration_time = curr_time
                self._add_heartbeat(daemon)
                daemon.run_iteration()

    def _add_heartbeat(self, daemon):
        """
        Add a heartbeat for the given daemon
        """
        self._instance.add_daemon_heartbeat(
            DaemonHeartbeat(pendulum.now("UTC"), type(daemon).__name__, None, None)
        )

    @staticmethod
    def _get_interval_seconds(instance, daemon_type):
        """
        Return the interval in which each daemon is configured to run
        """
        if daemon_type == QueuedRunCoordinatorDaemon.__name__:
            return instance.run_coordinator.dequeue_interval_seconds

        # default
        return 30

    @staticmethod
    def required(instance):
        """
        True if the instance configuration has classes that require the daemon to be enabled.

        Note: this is currently always true due to the SensorDaemon
        """
        return len(DagsterDaemonController._expected_daemons(instance)) > 0

    @staticmethod
    def _expected_daemons(instance):
        """
        Return which daemon types are required by the instance
        """
        daemons = [SensorDaemon.__name__]
        if isinstance(instance.scheduler, DagsterDaemonScheduler):
            daemons.append(SchedulerDaemon.__name__)
        if isinstance(instance.run_coordinator, QueuedRunCoordinator):
            daemons.append(QueuedRunCoordinatorDaemon.__name__)
        return daemons

    @staticmethod
    def daemon_healthy(instance, curr_time=None):
        """
        True if the daemon process has had a recent heartbeat

        Note: this method (and its dependencies) are static because it is called by the dagit
        process, which shouldn't need to instantiate each of the daemons.
        """
        curr_time = check.opt_inst_param(
            curr_time, "curr_time", datetime.datetime, default=pendulum.now()
        )
        assert DagsterDaemonController.required(instance)

        daemon_types = DagsterDaemonController._expected_daemons(instance)
        for daemon_type in daemon_types:
            heartbeat = instance.get_daemon_heartbeats().get(daemon_type, None)

            if not heartbeat:
                return False

            heartbeat_time = pendulum.instance(heartbeat.timestamp)
            maximum_tolerated_time = heartbeat_time.add(
                seconds=(DAEMON_HEARTBEAT_SKIP_TOLERANCE + 1)
                * DagsterDaemonController._get_interval_seconds(instance, daemon_type)
            )
            if curr_time > maximum_tolerated_time:
                return False

        return True
