import sys
from contextlib import contextmanager

from dagster import file_relative_path
from dagster.core.host_representation import (
    GrpcServerRepositoryLocation,
    ManagedGrpcPythonEnvRepositoryLocationOrigin,
    PipelineHandle,
    RepositoryLocation,
    RepositoryLocationHandle,
)
from dagster.core.types.loadable_target_origin import LoadableTargetOrigin


def get_bar_repo_repository_location_handle():
    loadable_target_origin = LoadableTargetOrigin(
        executable_path=sys.executable,
        python_file=file_relative_path(__file__, "api_tests_repo.py"),
    )
    location_name = "bar_repo_location"

    origin = ManagedGrpcPythonEnvRepositoryLocationOrigin(loadable_target_origin, location_name)

    return RepositoryLocationHandle.create_from_repository_location_origin(origin)


@contextmanager
def get_bar_repo_grpc_repository_location_handle():
    with RepositoryLocationHandle.create_from_repository_location_origin(
        ManagedGrpcPythonEnvRepositoryLocationOrigin(
            loadable_target_origin=LoadableTargetOrigin(
                executable_path=sys.executable,
                attribute="bar_repo",
                python_file=file_relative_path(__file__, "api_tests_repo.py"),
            ),
            location_name="bar_repo",
        )
    ) as handle:
        yield handle


@contextmanager
def get_bar_repo_handle():
    with get_bar_repo_repository_location_handle() as location_handle:
        yield RepositoryLocation.from_handle(location_handle).get_repository("bar_repo").handle


@contextmanager
def get_bar_grpc_repo_handle():
    with get_bar_repo_grpc_repository_location_handle() as handle:
        yield GrpcServerRepositoryLocation(handle).get_repository("bar_repo").handle


@contextmanager
def get_foo_pipeline_handle():
    with get_bar_repo_handle() as repo_handle:
        yield PipelineHandle("foo", repo_handle)


@contextmanager
def get_foo_grpc_pipeline_handle():
    with get_bar_grpc_repo_handle() as repo_handle:
        yield PipelineHandle("foo", repo_handle)
