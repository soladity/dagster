import time
import weakref

from dagster import check, seven
from dagster.core.errors import DagsterLaunchFailedError
from dagster.core.host_representation import ExternalPipeline
from dagster.core.host_representation.handle import (
    GrpcServerRepositoryLocationHandle,
    ManagedGrpcPythonEnvRepositoryLocationHandle,
)
from dagster.core.instance import DagsterInstance
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.core.storage.tags import GRPC_INFO_TAG
from dagster.grpc.client import DagsterGrpcClient
from dagster.grpc.types import CanCancelExecutionRequest, CancelExecutionRequest, ExecuteRunArgs
from dagster.serdes import ConfigurableClass
from dagster.utils import merge_dicts

from .base import RunLauncher

SUBPROCESS_TICK = 0.5

GRPC_REPOSITORY_LOCATION_HANDLE_TYPES = (
    GrpcServerRepositoryLocationHandle,
    ManagedGrpcPythonEnvRepositoryLocationHandle,
)


class GrpcRunLauncher(RunLauncher, ConfigurableClass):
    """Launches runs against running GRPC servers.

    During the transition period from the previous CLI-based user process strategy to GRPC, you
    should use the :py:class`dagster.DefaultRunLauncher`, which is aware of instance- and
    repository-level settings allowing it to switch between the two strategies.
    """

    def __init__(self, inst_data=None):
        self._instance_weakref = None
        self._inst_data = inst_data

        # Used for test cleanup purposes only
        self._run_id_to_repository_location_handle_cache = {}

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return {}

    @staticmethod
    def from_config_value(inst_data, config_value):
        return GrpcRunLauncher(inst_data=inst_data)

    @property
    def _instance(self):
        return self._instance_weakref() if self._instance_weakref else None

    def initialize(self, instance):
        check.inst_param(instance, "instance", DagsterInstance)
        check.invariant(self._instance is None, "Must only call initialize once")
        # Store a weakref to avoid a circular reference / enable GC
        self._instance_weakref = weakref.ref(instance)

    def launch_run(self, instance, run, external_pipeline):
        """Subclasses must implement this method."""

        check.inst_param(run, "run", PipelineRun)
        check.inst_param(external_pipeline, "external_pipeline", ExternalPipeline)

        repository_location_handle = external_pipeline.repository_handle.repository_location_handle

        check.inst(
            repository_location_handle,
            GRPC_REPOSITORY_LOCATION_HANDLE_TYPES,
            "GrpcRunLauncher: Can't launch runs for pipeline not loaded from a GRPC server",
        )

        self._instance.add_run_tags(
            run.run_id,
            {
                GRPC_INFO_TAG: seven.json.dumps(
                    merge_dicts(
                        {"host": repository_location_handle.host},
                        {"port": repository_location_handle.port}
                        if repository_location_handle.port
                        else {"socket": repository_location_handle.socket},
                    )
                )
            },
        )

        res = repository_location_handle.client.start_run(
            ExecuteRunArgs(
                pipeline_origin=external_pipeline.get_origin(),
                pipeline_run_id=run.run_id,
                instance_ref=self._instance.get_ref(),
            )
        )

        if not res.success:
            raise (
                DagsterLaunchFailedError(
                    res.message, serializable_error_info=res.serializable_error_info
                )
            )

        self._run_id_to_repository_location_handle_cache[run.run_id] = repository_location_handle

        return run

    def _get_grpc_client_for_termination(self, run_id):
        if not self._instance:
            return None

        run = self._instance.get_run_by_id(run_id)
        if not run or run.is_finished:
            return None

        tags = run.tags

        if GRPC_INFO_TAG not in tags:
            return None

        grpc_info = seven.json.loads(tags.get(GRPC_INFO_TAG))

        return DagsterGrpcClient(
            port=grpc_info.get("port"), socket=grpc_info.get("socket"), host=grpc_info.get("host")
        )

    def can_terminate(self, run_id):
        check.str_param(run_id, "run_id")

        client = self._get_grpc_client_for_termination(run_id)
        if not client:
            return False

        res = client.can_cancel_execution(CanCancelExecutionRequest(run_id=run_id))

        return res.can_cancel

    def terminate(self, run_id):
        check.str_param(run_id, "run_id")

        client = self._get_grpc_client_for_termination(run_id)

        if not client:
            return False

        res = client.cancel_execution(CancelExecutionRequest(run_id=run_id))

        return res.success

    def join(self, timeout=15):
        # If this hasn't been initialized at all, we can just do a noop
        if not self._instance:
            return

        total_time = 0
        interval = 0.01

        while True:
            active_run_ids = [
                run_id
                for run_id in self._run_id_to_repository_location_handle_cache.keys()
                if (
                    self._instance.get_run_by_id(run_id)
                    and not self._instance.get_run_by_id(run_id).is_finished
                )
            ]

            if len(active_run_ids) == 0:
                return

            if total_time >= timeout:
                raise Exception(
                    "Timed out waiting for these runs to finish: {active_run_ids}".format(
                        active_run_ids=repr(active_run_ids)
                    )
                )

            total_time += interval
            time.sleep(interval)
            interval = interval * 2

    def cleanup_managed_grpc_servers(self):
        """Shut down any managed grpc servers that used this run launcher to start a run.
        Should only be used for teardown purposes within tests.
        """
        for repository_location_handle in self._run_id_to_repository_location_handle_cache.values():
            if isinstance(repository_location_handle, ManagedGrpcPythonEnvRepositoryLocationHandle):
                repository_location_handle.client.cleanup_server()
                repository_location_handle.grpc_server_process.wait()
