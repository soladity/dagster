import json
import os
import sys

from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler
from graphql import graphql
from graphql.execution.executors.gevent import GeventExecutor as Executor
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
import click


from dagster import check
from dagster.cli.dynamic_loader import repository_target_argument, load_target_info_from_cli_args

from .app import create_app, RepositoryContainer
from .pipeline_execution_manager import SynchronousExecutionManager
from .pipeline_run_storage import PipelineRunStorage, LogFilePipelineRun, InMemoryPipelineRun
from .schema import create_schema
from .schema.context import DagsterGraphQLContext
from .version import __version__


def create_dagit_cli():
    return ui


class ReloaderHandler(FileSystemEventHandler):
    def __init__(self, repository_container):
        super(ReloaderHandler, self).__init__()
        self.repository_container = repository_container

    def on_any_event(self, event):
        if event.src_path.endswith('.py'):
            print('Reloading repository...')
            self.repository_container.reload()


REPO_TARGET_WARNING = (
    'Can only use ONE of --repository-yaml/-y, --python-file/-f, --module-name/-m.'
)


def execute_query_from_cli(repository_container, query, variables):
    check.str_param(query, 'query')
    check.opt_str_param(variables, 'variables')

    create_pipeline_run = InMemoryPipelineRun
    pipeline_run_storage = PipelineRunStorage(create_pipeline_run=create_pipeline_run)
    execution_manager = SynchronousExecutionManager()

    context = DagsterGraphQLContext(
        repository_container=repository_container,
        pipeline_runs=pipeline_run_storage,
        execution_manager=execution_manager,
    )

    result = graphql(
        request_string=query,
        schema=create_schema(),
        context=context,
        variables=json.loads(variables) if variables else None,
        executor=Executor(),
    )

    print(json.dumps(result.to_dict()))


@click.command(
    name='ui',
    help=(
        'Run dagit. Loads a repository or pipeline.\n\n{warning}'.format(
            warning=REPO_TARGET_WARNING
        )
        + '\n\n Examples:'
        '\n\n1. dagit'
        '\n\n2. dagit -y path/to/repository.yml'
        '\n\n3. dagit -f path/to/file.py -n define_repo'
        '\n\n4. dagit -m some_module -n define_repo'
        '\n\n5. dagit -f path/to/file.py -n define_pipeline'
        '\n\n6. dagit -m some_module -n define_pipeline'
    ),
)
@repository_target_argument
@click.option('--host', '-h', type=click.STRING, default='127.0.0.1', help="Host to run server on")
@click.option('--port', '-p', type=click.INT, default=3000, help="Port to run server on")
@click.option(
    '--watch/--no-watch',
    default=True,
    help='Watch for changes in the current working directory and all recursive subfolders',
)
@click.option('--sync', is_flag=True, help='Use the synchronous execution manager')
@click.option('--log', is_flag=False, help='Record logs of pipeline runs')
@click.option('--log-dir', help="Directory to record logs to", default='dagit_run_logs/')
@click.option('--query', '-q', type=click.STRING)
@click.option('--variables', '-v', type=click.STRING)
@click.version_option(version=__version__)
def ui(host, port, watch, sync, log, log_dir, query, variables, **kwargs):
    repository_target_info = load_target_info_from_cli_args(kwargs)

    sys.path.append(os.getcwd())
    repository_container = RepositoryContainer(repository_target_info)

    if query:
        return execute_query_from_cli(repository_container, query, variables)
    else:
        if variables:
            raise Exception('if you specify --variables/-v you need to specify --query/-q')

    host_dagit_ui(log, log_dir, watch, repository_container, sync, host, port)


def host_dagit_ui(log, log_dir, watch, repository_container, sync, host, port):
    if log:

        def create_pipeline_run(*args, **kwargs):
            return LogFilePipelineRun(log_dir, *args, **kwargs)

    else:
        create_pipeline_run = InMemoryPipelineRun

    pipeline_run_storage = PipelineRunStorage(create_pipeline_run=create_pipeline_run)

    if watch:
        observer = Observer()
        handler = ReloaderHandler(repository_container)
        observer.schedule(handler, os.path.dirname(os.path.abspath(os.getcwd())), recursive=True)
        observer.start()
    try:
        app = create_app(
            repository_container, pipeline_run_storage, use_synchronous_execution_manager=sync
        )
        server = pywsgi.WSGIServer((host, port), app, handler_class=WebSocketHandler)
        print('Serving on http://{host}:{port}'.format(host=host, port=port))
        server.serve_forever()
    except KeyboardInterrupt:
        if watch:
            observer.stop()


def main():
    cli = create_dagit_cli()
    # click magic
    cli(obj={})  # pylint:disable=E1120
