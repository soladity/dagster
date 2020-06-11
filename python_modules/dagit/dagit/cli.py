import os
import sys
import threading
from contextlib import contextmanager

import click
import six
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler

from dagster import check, seven
from dagster.cli.workspace import Workspace, get_workspace_from_kwargs, workspace_target_argument
from dagster.core.instance import DagsterInstance
from dagster.core.telemetry import START_DAGIT_WEBSERVER, log_action, log_repo_stats, upload_logs
from dagster.utils import DEFAULT_WORKSPACE_YAML_FILENAME

from .app import create_app_from_workspace
from .version import __version__


def create_dagit_cli():
    return ui  # pylint: disable=no-value-for-parameter


REPO_TARGET_WARNING = 'Can only use ONE of --workspace/-w, --python-file/-f, --module-name/-m.'

DEFAULT_DAGIT_HOST = '127.0.0.1'
DEFAULT_DAGIT_PORT = 3000


@click.command(
    name='ui',
    help=(
        'Run dagit. Loads a repository or pipeline.\n\n{warning}'.format(
            warning=REPO_TARGET_WARNING
        )
        + (
            '\n\n Examples:'
            '\n\n1. dagit (works if .{default_filename} exists)'
            '\n\n2. dagit -w path/to/{default_filename}'
            '\n\n3. dagit -f path/to/file.py'
            '\n\n4. dagit -m some_module'
            '\n\n5. dagit -f path/to/file.py -a define_repo'
            '\n\n6. dagit -m some_module -a define_repo'
            '\n\n7. dagit -p 3333'
            '\n\nOptions Can also provide arguments via environment variables prefixed with DAGIT_'
            '\n\n    DAGIT_PORT=3333 dagit'
        ).format(default_filename=DEFAULT_WORKSPACE_YAML_FILENAME)
    ),
)
@workspace_target_argument
@click.option(
    '--host',
    '-h',
    type=click.STRING,
    default=DEFAULT_DAGIT_HOST,
    help="Host to run server on, default is {default_host}".format(default_host=DEFAULT_DAGIT_HOST),
)
@click.option(
    '--port',
    '-p',
    type=click.INT,
    help="Port to run server on, default is {default_port}".format(default_port=DEFAULT_DAGIT_PORT),
)
@click.option(
    '--storage-fallback',
    help="Base directory for dagster storage if $DAGSTER_HOME is not set",
    default=None,
    type=click.Path(),
)
@click.version_option(version=__version__, prog_name='dagit')
def ui(host, port, storage_fallback, **kwargs):
    # add the path for the cwd so imports in dynamically loaded code work correctly
    sys.path.append(os.getcwd())

    if port is None:
        port_lookup = True
        port = DEFAULT_DAGIT_PORT
    else:
        port_lookup = False

    if storage_fallback is None:
        storage_fallback = seven.TemporaryDirectory().name

    host_dagit_ui(host, port, storage_fallback, port_lookup, **kwargs)


def host_dagit_ui(host, port, storage_fallback, port_lookup=True, **kwargs):
    workspace = get_workspace_from_kwargs(kwargs)
    if not workspace:
        raise Exception('Unable to load workspace with cli_args: {}'.format(kwargs))

    return host_dagit_ui_with_workspace(workspace, host, port, storage_fallback, port_lookup)


def host_dagit_ui_with_workspace(workspace, host, port, storage_fallback, port_lookup=True):
    check.inst_param(workspace, 'workspace', Workspace)

    instance = DagsterInstance.get(storage_fallback)

    if len(workspace.repository_location_handles) == 1:
        repository_location_handle = workspace.repository_location_handles[0]
        if len(repository_location_handle.repository_code_pointer_dict) == 1:
            pointer = next(iter(repository_location_handle.repository_code_pointer_dict.values()))

            from dagster.core.definitions.reconstructable import ReconstructableRepository

            recon_repo = ReconstructableRepository(pointer)

            log_repo_stats(instance=instance, repo=recon_repo, source='dagit')

    app = create_app_from_workspace(workspace, instance)

    start_server(host, port, app, port_lookup)


@contextmanager
def uploading_logging_thread():
    stop_event = threading.Event()
    logging_thread = threading.Thread(target=upload_logs, args=([stop_event]))
    try:
        logging_thread.start()
        yield
    finally:
        stop_event.set()
        logging_thread.join()


def start_server(host, port, app, port_lookup, port_lookup_attempts=0):
    server = pywsgi.WSGIServer((host, port), app, handler_class=WebSocketHandler)

    print(
        'Serving on http://{host}:{port} in process {pid}'.format(
            host=host, port=port, pid=os.getpid()
        )
    )

    log_action(START_DAGIT_WEBSERVER)
    with uploading_logging_thread():
        try:
            server.serve_forever()
        except OSError as os_error:
            if 'Address already in use' in str(os_error):
                if port_lookup and (
                    port_lookup_attempts > 0
                    or click.confirm(
                        (
                            'Another process on your machine is already listening on port {port}. '
                            'Would you like to run the app at another port instead?'
                        ).format(port=port)
                    )
                ):
                    port_lookup_attempts += 1
                    start_server(host, port + port_lookup_attempts, app, True, port_lookup_attempts)
                else:
                    six.raise_from(
                        Exception(
                            (
                                'Another process on your machine is already listening on port {port}. '
                                'It is possible that you have another instance of dagit '
                                'running somewhere using the same port. Or it could be another '
                                'random process. Either kill that process or use the -p option to '
                                'select another port.'
                            ).format(port=port)
                        ),
                        os_error,
                    )
            else:
                raise os_error


cli = create_dagit_cli()


def main():
    # click magic
    cli(auto_envvar_prefix='DAGIT')  # pylint:disable=E1120
