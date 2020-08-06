import sys
import threading
from collections import namedtuple
from enum import Enum

from dagster import check
from dagster.api.list_repositories import sync_list_repositories_grpc
from dagster.core.code_pointer import CodePointer
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.host_representation.selector import PipelineSelector
from dagster.core.origin import RepositoryGrpcServerOrigin, RepositoryPythonOrigin

# This is a hard-coded name for the special "in-process" location.
# This is typically only used for test, although we may allow
# users to load user code into a host process as well. We want
# to encourage the user code to be in user processes as much
# as possible since that it how this system will be used in prod.
# We used a hard-coded name so that we don't have to create
# made up names for this case.
IN_PROCESS_NAME = '<<in_process>>'


def _assign_grpc_location_name(port, socket, host):
    check.opt_int_param(port, 'port')
    check.opt_str_param(socket, 'socket')
    check.str_param(host, 'host')
    check.invariant(port or socket)
    return 'grpc:{host}:{socket_or_port}'.format(
        host=host, socket_or_port=(socket if socket else port)
    )


def _assign_python_env_location_name(repository_code_pointer_dict):
    check.dict_param(
        repository_code_pointer_dict,
        'repository_code_pointer_dict',
        key_type=str,
        value_type=CodePointer,
    )
    if len(repository_code_pointer_dict) > 1:
        raise DagsterInvariantViolationError(
            'If there is one than more repository you must provide a location name'
        )

    return next(iter(repository_code_pointer_dict.keys()))


# Which API the host process should use to communicate with the process
# containing user code
class UserProcessApi(Enum):
    # Execute via the command-line API
    CLI = 'CLI'
    # Connect via gRPC
    GRPC = 'GRPC'


class RepositoryLocationHandle:
    @staticmethod
    def create_in_process_location(pointer):
        check.inst_param(pointer, 'pointer', CodePointer)

        # If we are here we know we are in a hosted_user_process so we can do this
        from dagster.core.definitions.reconstructable import repository_def_from_pointer

        repo_def = repository_def_from_pointer(pointer)
        return InProcessRepositoryLocationHandle(IN_PROCESS_NAME, {repo_def.name: pointer})

    @staticmethod
    def create_out_of_process_location(
        location_name, repository_code_pointer_dict,
    ):
        return RepositoryLocationHandle.create_python_env_location(
            executable_path=sys.executable,
            location_name=location_name,
            repository_code_pointer_dict=repository_code_pointer_dict,
        )

    @staticmethod
    def create_python_env_location(
        executable_path, location_name, repository_code_pointer_dict,
    ):
        check.str_param(executable_path, 'executable_path')
        check.opt_str_param(location_name, 'location_name')
        check.dict_param(
            repository_code_pointer_dict,
            'repository_code_pointer_dict',
            key_type=str,
            value_type=CodePointer,
        )
        return PythonEnvRepositoryLocationHandle(
            location_name=location_name
            if location_name
            else _assign_python_env_location_name(repository_code_pointer_dict),
            executable_path=executable_path,
            repository_code_pointer_dict=repository_code_pointer_dict,
        )

    @staticmethod
    def create_process_bound_grpc_server_location(loadable_target_origin, location_name):
        from dagster.grpc.client import client_heartbeat_thread
        from dagster.grpc.server import GrpcServerProcess

        server = GrpcServerProcess(
            loadable_target_origin=loadable_target_origin, max_workers=2, heartbeat=True
        )
        client = server.create_ephemeral_client()
        heartbeat_thread = threading.Thread(target=client_heartbeat_thread, args=(client,))
        heartbeat_thread.daemon = True
        heartbeat_thread.start()
        list_repositories_response = sync_list_repositories_grpc(client)

        code_pointer_dict = list_repositories_response.repository_code_pointer_dict

        return ManagedGrpcPythonEnvRepositoryLocationHandle(
            executable_path=list_repositories_response.executable_path,
            location_name=location_name
            if location_name
            else _assign_python_env_location_name(code_pointer_dict),
            repository_code_pointer_dict=code_pointer_dict,
            client=client,
            grpc_server_process=server,
        )

    @staticmethod
    def create_grpc_server_location(port, socket, host, location_name=None):
        from dagster.grpc.client import DagsterGrpcClient

        check.opt_int_param(port, 'port')
        check.opt_str_param(socket, 'socket')
        check.str_param(host, 'host')
        check.opt_str_param(location_name, 'location_name')

        client = DagsterGrpcClient(port=port, socket=socket, host=host)

        list_repositories_response = sync_list_repositories_grpc(client)

        repository_names = set(
            symbol.repository_name for symbol in list_repositories_response.repository_symbols
        )

        return GrpcServerRepositoryLocationHandle(
            port=port,
            socket=socket,
            host=host,
            location_name=location_name
            if location_name
            else _assign_grpc_location_name(port, socket, host),
            client=client,
            repository_names=repository_names,
        )


class GrpcServerRepositoryLocationHandle(
    namedtuple(
        '_GrpcServerRepositoryLocationHandle',
        'port socket host location_name client repository_names',
    ),
    RepositoryLocationHandle,
):
    '''
    Represents a gRPC server that Dagster is not responsible for managing.
    '''

    def __new__(cls, port, socket, host, location_name, client, repository_names):
        from dagster.grpc.client import DagsterGrpcClient

        return super(GrpcServerRepositoryLocationHandle, cls).__new__(
            cls,
            check.opt_int_param(port, 'port'),
            check.opt_str_param(socket, 'socket'),
            check.str_param(host, 'host'),
            check.str_param(location_name, 'location_name'),
            check.inst_param(client, 'client', DagsterGrpcClient),
            check.set_param(repository_names, 'repository_names', of_type=str),
        )

    def get_current_image(self):
        job_image = self.client.get_current_image().current_image
        if not job_image:
            raise DagsterInvariantViolationError(
                'Unable to get current image that GRPC server is running. Please make sure that '
                'env var DAGSTER_CURRENT_IMAGE is set in the GRPC server and contains the most '
                'up-to-date user code image and tag. Exiting.'
            )
        return job_image

    def get_repository_python_origin(self, repository_name):
        check.str_param(repository_name, 'repository_name')

        list_repositories_reply = self.client.list_repositories()
        repository_code_pointer_dict = list_repositories_reply.repository_code_pointer_dict

        if repository_name not in repository_code_pointer_dict:
            raise DagsterInvariantViolationError(
                'Unable to find repository name {} on GRPC server.'.format(repository_name)
            )

        code_pointer = repository_code_pointer_dict[repository_name]
        return RepositoryPythonOrigin(
            executable_path=list_repositories_reply.executable_path or sys.executable,
            code_pointer=code_pointer,
        )


class PythonEnvRepositoryLocationHandle(
    namedtuple(
        '_PythonEnvRepositoryLocationHandle',
        'executable_path location_name repository_code_pointer_dict',
    ),
    RepositoryLocationHandle,
):
    def __new__(cls, executable_path, location_name, repository_code_pointer_dict):
        return super(PythonEnvRepositoryLocationHandle, cls).__new__(
            cls,
            check.str_param(executable_path, 'executable_path'),
            check.str_param(location_name, 'location_name'),
            check.dict_param(
                repository_code_pointer_dict,
                'repository_code_pointer_dict',
                key_type=str,
                value_type=CodePointer,
            ),
        )


class ManagedGrpcPythonEnvRepositoryLocationHandle(
    namedtuple(
        '_ManagedGrpcPythonEnvRepositoryLocationHandle',
        'executable_path location_name repository_code_pointer_dict grpc_server_process client',
    ),
    RepositoryLocationHandle,
):
    '''
    A Python environment for which Dagster is managing a gRPC server.
    '''

    def __new__(
        cls,
        executable_path,
        location_name,
        repository_code_pointer_dict,
        grpc_server_process,
        client,
    ):
        from dagster.grpc.client import DagsterGrpcClient
        from dagster.grpc.server import GrpcServerProcess

        return super(ManagedGrpcPythonEnvRepositoryLocationHandle, cls).__new__(
            cls,
            check.str_param(executable_path, 'executable_path'),
            check.str_param(location_name, 'location_name'),
            check.dict_param(
                repository_code_pointer_dict,
                'repository_code_pointer_dict',
                key_type=str,
                value_type=CodePointer,
            ),
            check.inst_param(grpc_server_process, 'grpc_server_process', GrpcServerProcess),
            check.inst_param(client, 'client', DagsterGrpcClient),
        )

    @property
    def repository_names(self):
        return set(self.repository_code_pointer_dict.keys())

    @property
    def host(self):
        return 'localhost'

    @property
    def port(self):
        return self.grpc_server_process.port

    @property
    def socket(self):
        return self.grpc_server_process.socket


class InProcessRepositoryLocationHandle(
    namedtuple('_InProcessRepositoryLocationHandle', 'location_name repository_code_pointer_dict'),
    RepositoryLocationHandle,
):
    def __new__(cls, location_name, repository_code_pointer_dict):
        return super(InProcessRepositoryLocationHandle, cls).__new__(
            cls,
            check.str_param(location_name, 'location_name'),
            check.dict_param(
                repository_code_pointer_dict,
                'repository_code_pointer_dict',
                key_type=str,
                value_type=CodePointer,
            ),
        )


class RepositoryHandle(
    namedtuple('_RepositoryHandle', 'repository_name repository_location_handle')
):
    def __new__(cls, repository_name, repository_location_handle):
        return super(RepositoryHandle, cls).__new__(
            cls,
            check.str_param(repository_name, 'repository_name'),
            check.inst_param(
                repository_location_handle, 'repository_location_handle', RepositoryLocationHandle
            ),
        )

    def get_origin(self):
        if isinstance(self.repository_location_handle, InProcessRepositoryLocationHandle):
            return RepositoryPythonOrigin(
                code_pointer=self.repository_location_handle.repository_code_pointer_dict[
                    self.repository_name
                ],
                executable_path=sys.executable,
            )
        elif isinstance(
            self.repository_location_handle, PythonEnvRepositoryLocationHandle
        ) or isinstance(
            self.repository_location_handle, ManagedGrpcPythonEnvRepositoryLocationHandle
        ):
            return RepositoryPythonOrigin(
                code_pointer=self.repository_location_handle.repository_code_pointer_dict[
                    self.repository_name
                ],
                executable_path=self.repository_location_handle.executable_path,
            )
        elif isinstance(self.repository_location_handle, GrpcServerRepositoryLocationHandle):
            return RepositoryGrpcServerOrigin(
                host=self.repository_location_handle.host,
                port=self.repository_location_handle.port,
                socket=self.repository_location_handle.socket,
                repository_name=self.repository_name,
            )
        else:
            check.failed(
                'Can not target represented RepositoryDefinition locally for repository from a {}.'.format(
                    self.repository_location_handle.__class__.__name__
                )
            )


class PipelineHandle(namedtuple('_PipelineHandle', 'pipeline_name repository_handle')):
    def __new__(cls, pipeline_name, repository_handle):
        return super(PipelineHandle, cls).__new__(
            cls,
            check.str_param(pipeline_name, 'pipeline_name'),
            check.inst_param(repository_handle, 'repository_handle', RepositoryHandle),
        )

    def to_string(self):
        return '{self.location_name}.{self.repository_name}.{self.pipeline_name}'.format(self=self)

    @property
    def repository_name(self):
        return self.repository_handle.repository_name

    @property
    def location_name(self):
        return self.repository_handle.repository_location_handle.location_name

    def get_origin(self):
        return self.repository_handle.get_origin().get_pipeline_origin(self.pipeline_name)

    def to_selector(self):
        return PipelineSelector(self.location_name, self.repository_name, self.pipeline_name, None)


class ScheduleHandle(namedtuple('_ScheduleHandle', 'schedule_name repository_handle')):
    def __new__(cls, schedule_name, repository_handle):
        return super(ScheduleHandle, cls).__new__(
            cls,
            check.str_param(schedule_name, 'schedule_name'),
            check.inst_param(repository_handle, 'repository_handle', RepositoryHandle),
        )

    @property
    def repository_name(self):
        return self.repository_handle.repository_name

    @property
    def location_name(self):
        return self.repository_handle.repository_location_handle.location_name

    def get_origin(self):
        return self.repository_handle.get_origin().get_schedule_origin(self.schedule_name)


class PartitionSetHandle(namedtuple('_PartitionSetHandle', 'partition_set_name repository_handle')):
    def __new__(cls, partition_set_name, repository_handle):
        return super(PartitionSetHandle, cls).__new__(
            cls,
            check.str_param(partition_set_name, 'partition_set_name'),
            check.inst_param(repository_handle, 'repository_handle', RepositoryHandle),
        )

    @property
    def repository_name(self):
        return self.repository_handle.repository_name

    @property
    def location_name(self):
        return self.repository_handle.repository_location_handle.location_name
