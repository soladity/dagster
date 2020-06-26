import os
import sys
from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor

import grpc

from dagster import check, seven
from dagster.core.execution.api import create_execution_plan
from dagster.core.origin import PipelinePythonOrigin
from dagster.core.snap.execution_plan_snapshot import snapshot_from_execution_plan
from dagster.serdes import (
    deserialize_json_to_dagster_namedtuple,
    serialize_dagster_namedtuple,
    whitelist_for_serdes,
)
from dagster.serdes.ipc import setup_interrupt_support
from dagster.utils.hosted_user_process import recon_pipeline_from_origin

from .__generated__ import api_pb2
from .__generated__.api_pb2_grpc import DagsterApiServicer, add_DagsterApiServicer_to_server


@whitelist_for_serdes
class ExecutionPlanSnapshotArgs(
    namedtuple(
        '_ExecutionPlanSnapshotArgs',
        'pipeline_origin solid_selection run_config mode step_keys_to_execute pipeline_snapshot_id',
    )
):
    def __new__(
        cls,
        pipeline_origin,
        solid_selection,
        run_config,
        mode,
        step_keys_to_execute,
        pipeline_snapshot_id,
    ):
        return super(ExecutionPlanSnapshotArgs, cls).__new__(
            cls,
            pipeline_origin=check.inst_param(
                pipeline_origin, 'pipeline_origin', PipelinePythonOrigin
            ),
            solid_selection=check.opt_list_param(solid_selection, 'solid_selection', of_type=str),
            run_config=check.dict_param(run_config, 'run_config'),
            mode=check.str_param(mode, 'mode'),
            step_keys_to_execute=check.opt_list_param(
                step_keys_to_execute, 'step_keys_to_execute', of_type=str
            ),
            pipeline_snapshot_id=check.str_param(pipeline_snapshot_id, 'pipeline_snapshot_id'),
        )


class CouldNotBindGrpcServerToAddress(Exception):
    pass


class DagsterApiServer(DagsterApiServicer):
    def Ping(self, request, _context):
        echo = request.echo
        return api_pb2.PingReply(echo=echo)

    def ExecutionPlanSnapshot(self, request, _context):
        execution_plan_args = deserialize_json_to_dagster_namedtuple(
            request.serialized_execution_plan_snapshot_args
        )

        check.inst_param(execution_plan_args, 'execution_plan_args', ExecutionPlanSnapshotArgs)

        recon_pipeline = (
            recon_pipeline_from_origin(execution_plan_args.pipeline_origin).subset_for_execution(
                execution_plan_args.solid_selection
            )
            if execution_plan_args.solid_selection
            else recon_pipeline_from_origin(execution_plan_args.pipeline_origin)
        )

        execution_plan_snapshot = snapshot_from_execution_plan(
            create_execution_plan(
                pipeline=recon_pipeline,
                run_config=execution_plan_args.run_config,
                mode=execution_plan_args.mode,
                step_keys_to_execute=execution_plan_args.step_keys_to_execute,
            ),
            execution_plan_args.pipeline_snapshot_id,
        )
        return api_pb2.ExecutionPlanSnapshotReply(
            serialized_execution_plan_snapshot=serialize_dagster_namedtuple(execution_plan_snapshot)
        )


# This is not a splendid scheme. We could possibly use a sentinel file for this, or send a custom
# signal back to the client process (Unix only, i think, and questionable); or maybe the client
# could poll the ping rpc instead/in addition to this
SERVER_STARTED_TOKEN = 'dagster_grpc_server_started'

SERVER_STARTED_TOKEN_BYTES = b'dagster_grpc_server_started'

SERVER_FAILED_TO_BIND_TOKEN = 'dagster_grpc_server_failed_to_bind'

SERVER_FAILED_TO_BIND_TOKEN_BYTES = b'dagster_grpc_server_failed_to_bind'


class DagsterGrpcServer(object):
    def __init__(self, host='localhost', port=None, socket=None, max_workers=1):
        setup_interrupt_support()

        check.opt_str_param(host, 'host')
        check.opt_int_param(port, 'port')
        check.opt_str_param(socket, 'socket')
        check.invariant(
            port is not None if seven.IS_WINDOWS else True,
            'You must pass a valid `port` on Windows: `socket` not supported.',
        )
        check.invariant(
            (port or socket) and not (port and socket),
            'You must pass one and only one of `port` or `socket`.',
        )

        check.invariant(
            host is not None if port else True, 'Must provide a host when serving on a port',
        )

        self.server = grpc.server(ThreadPoolExecutor(max_workers=max_workers))
        add_DagsterApiServicer_to_server(DagsterApiServer(), self.server)

        if port:
            server_address = host + ':' + str(port)
        else:
            server_address = 'unix:' + os.path.abspath(socket)

        # grpc.Server.add_insecure_port returns:
        # - 0 on failure
        # - port number when a port is successfully bound
        # - 1 when a UDS is successfully bound
        res = self.server.add_insecure_port(server_address)
        if socket and res != 1:
            print(SERVER_FAILED_TO_BIND_TOKEN)
            raise CouldNotBindGrpcServerToAddress(socket)
        if port and res != port:
            print(SERVER_FAILED_TO_BIND_TOKEN)
            raise CouldNotBindGrpcServerToAddress(port)

    def serve(self):
        # Unfortunately it looks like ports bind late (here) and so this can fail with an error
        # from C++ like:
        #
        #    E0625 08:46:56.180112000 4697443776 server_chttp2.cc:40]
        #    {"created":"@1593089216.180085000","description":"Only 1 addresses added out of total
        #    2 resolved","file":"src/core/ext/transport/chttp2/server/chttp2_server.cc",
        #    "file_line":406,"referenced_errors":[{"created":"@1593089216.180083000","description":
        #    "Unable to configure socket","fd":6,"file":
        #    "src/core/lib/iomgr/tcp_server_utils_posix_common.cc","file_line":217,
        #    "referenced_errors":[{"created":"@1593089216.180079000",
        #    "description":"Address already in use","errno":48,"file":
        #    "src/core/lib/iomgr/tcp_server_utils_posix_common.cc","file_line":190,"os_error":
        #    "Address already in use","syscall":"bind"}]}]}
        #
        # This is printed to stdout and there is no return value from server.start or exception
        # raised in Python that we can use to handle this. The standard recipes for hijacking C
        # stdout (so we could inspect this output and respond accordingly), e.g.
        # https://eli.thegreenplace.net/2015/redirecting-all-kinds-of-stdout-in-python/, don't seem
        # to work (at least on Mac OS X) against grpc, and in any case would involve a huge
        # cross-version and cross-platform maintenance burden. We have an issue open against grpc,
        # https://github.com/grpc/grpc/issues/23315, and our own tracking issue at

        self.server.start()
        print(SERVER_STARTED_TOKEN)
        sys.stdout.flush()
        self.server.wait_for_termination()
