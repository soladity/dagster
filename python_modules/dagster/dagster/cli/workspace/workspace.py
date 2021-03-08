import sys
import warnings
from collections import OrderedDict, namedtuple
from contextlib import ExitStack

from dagster import check
from dagster.core.host_representation import (
    GrpcServerRepositoryLocationHandle,
    RepositoryLocationOrigin,
)
from dagster.core.host_representation.grpc_server_registry import ProcessGrpcServerRegistry
from dagster.utils.error import serializable_error_info_from_exc_info


class WorkspaceSnapshot(
    namedtuple("WorkspaceSnapshot", "location_origin_dict location_error_dict")
):
    """
    This class is request-scoped object that stores a reference to all the locaiton origins and errors
    that were on a `Workspace`.

    This object is needed because a workspace and handles/errors on that workspace can be updated
    (for example, from a thread on the process context). If a request is accessing a repository location
    at the same time the repository location was being cleaned up, we would run into errors.
    """

    def __new__(cls, location_origin_dict, _location_error_dict):
        return super(WorkspaceSnapshot, cls).__new__(
            cls, location_origin_dict, _location_error_dict
        )

    def is_reload_supported(self, location_name):
        return self.location_origin_dict[location_name].is_reload_supported

    @property
    def repository_location_names(self):
        return list(self.location_origin_dict.keys())

    @property
    def repository_location_errors(self):
        return list(self.location_error_dict.values())

    def has_repository_location_error(self, location_name):
        check.str_param(location_name, "location_name")
        return location_name in self.location_error_dict

    def get_repository_location_error(self, location_name):
        check.str_param(location_name, "location_name")
        return self.location_error_dict[location_name]


class Workspace:
    def __init__(self, workspace_load_target):
        from .cli_target import WorkspaceLoadTarget

        self._stack = ExitStack()

        self._workspace_load_target = check.opt_inst_param(
            workspace_load_target, "workspace_load_target", WorkspaceLoadTarget
        )
        self._grpc_server_registry = self._stack.enter_context(
            ProcessGrpcServerRegistry(reload_interval=0, heartbeat_ttl=30)
        )
        self._load_workspace()

    def _load_workspace(self):
        repository_location_origins = (
            self._workspace_load_target.create_origins() if self._workspace_load_target else []
        )

        self._location_origin_dict = OrderedDict()
        check.list_param(
            repository_location_origins,
            "repository_location_origins",
            of_type=RepositoryLocationOrigin,
        )

        self._location_handle_dict = {}
        self._location_error_dict = {}
        for origin in repository_location_origins:
            check.invariant(
                self._location_origin_dict.get(origin.location_name) is None,
                'Cannot have multiple locations with the same name, got multiple "{name}"'.format(
                    name=origin.location_name,
                ),
            )

            self._location_origin_dict[origin.location_name] = origin
            self._load_handle(origin.location_name)

    # Can be overidden in subclasses that need different logic for loading repository
    # locations from origins
    def create_handle_from_origin(self, origin):
        if not self._grpc_server_registry.supports_origin(origin):  # pylint: disable=no-member
            return origin.create_handle()
        else:
            endpoint = self._grpc_server_registry.reload_grpc_endpoint(  # pylint: disable=no-member
                origin
            )
            return GrpcServerRepositoryLocationHandle(
                origin=origin,
                server_id=endpoint.server_id,
                port=endpoint.port,
                socket=endpoint.socket,
                host=endpoint.host,
                heartbeat=True,
                watch_server=False,
                grpc_server_registry=self._grpc_server_registry,
            )

    def _load_handle(self, location_name):
        if self._location_handle_dict.get(location_name):
            del self._location_handle_dict[location_name]

        if self._location_error_dict.get(location_name):
            del self._location_error_dict[location_name]

        origin = self._location_origin_dict[location_name]
        try:
            handle = self.create_handle_from_origin(origin)
            self._location_handle_dict[location_name] = handle
        except Exception:  # pylint: disable=broad-except
            error_info = serializable_error_info_from_exc_info(sys.exc_info())
            self._location_error_dict[location_name] = error_info
            warnings.warn(
                "Error loading repository location {location_name}:{error_string}".format(
                    location_name=location_name, error_string=error_info.to_string()
                )
            )

    def create_snapshot(self):
        return WorkspaceSnapshot(
            self._location_origin_dict.copy(), self._location_error_dict.copy()
        )

    @property
    def repository_location_handles(self):
        return list(self._location_handle_dict.values())

    def has_repository_location_handle(self, location_name):
        check.str_param(location_name, "location_name")
        return location_name in self._location_handle_dict

    def get_repository_location_handle(self, location_name):
        check.str_param(location_name, "location_name")
        return self._location_handle_dict[location_name]

    def has_repository_location_error(self, location_name):
        check.str_param(location_name, "location_name")
        return location_name in self._location_error_dict

    def reload_repository_location(self, location_name):
        self._load_handle(location_name)

    def reload_workspace(self):
        for handle in self.repository_location_handles:
            handle.cleanup()
        self._load_workspace()

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        for handle in self.repository_location_handles:
            handle.cleanup()
        self._stack.close()
