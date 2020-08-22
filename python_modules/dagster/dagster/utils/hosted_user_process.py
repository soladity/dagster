"""
This file contains a set of utilities for dealing with test
environments where we want to go back and forth between
abstractions that reside in user process (e.g. definitions and
reconstructables) and abstractions that reside in host processes
(e.g. handles and externals).

These should only be invoked from contexts where we know this
to be the case.
"""

import sys

from dagster import check
from dagster.core.code_pointer import CodePointer
from dagster.core.definitions.reconstructable import (
    ReconstructableRepository,
    repository_def_from_pointer,
)
from dagster.core.host_representation import ExternalPipeline, ExternalRepository, RepositoryHandle
from dagster.core.host_representation.external_data import (
    external_pipeline_data_from_def,
    external_repository_data_from_def,
)
from dagster.core.host_representation.handle import (
    InProcessRepositoryLocationHandle,
    PythonEnvRepositoryLocationHandle,
    RepositoryLocationHandle,
)
from dagster.core.origin import PipelinePythonOrigin, RepositoryOrigin


def recon_pipeline_from_origin(origin):
    check.inst_param(origin, "origin", PipelinePythonOrigin)
    recon_repo = ReconstructableRepository(origin.get_repo_pointer())
    return recon_repo.get_reconstructable_pipeline(origin.pipeline_name)


def recon_repository_from_origin(origin):
    check.inst_param(origin, "origin", RepositoryOrigin)
    return ReconstructableRepository(origin.code_pointer)


def external_repo_from_def(repository_def, repository_handle):
    return ExternalRepository(external_repository_data_from_def(repository_def), repository_handle)


def recon_repo_from_external_repo(external_repo):
    return ReconstructableRepository(external_repo.get_origin().code_pointer)


def external_pipeline_from_recon_pipeline(recon_pipeline, solid_selection, repository_handle):
    if solid_selection:
        sub_pipeline = recon_pipeline.subset_for_execution(solid_selection)
        pipeline_def = sub_pipeline.get_definition()
    else:
        pipeline_def = recon_pipeline.get_definition()

    return ExternalPipeline(
        external_pipeline_data_from_def(pipeline_def), repository_handle=repository_handle,
    )


def is_repository_location_in_same_python_env(repository_location_handle):
    # either this directly in-process
    if isinstance(repository_location_handle, InProcessRepositoryLocationHandle):
        return True

    # or it is out-of-process but using the same python executable
    return (
        isinstance(repository_location_handle, PythonEnvRepositoryLocationHandle)
        and repository_location_handle.executable_path == sys.executable
    )


def repository_def_from_repository_handle(repository_handle):
    check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
    check.param_invariant(
        is_repository_location_in_same_python_env(repository_handle.repository_location_handle),
        "repository_handle",
        "In order to use this function the location of the repository must be in process "
        "or it must a python environment with the exact same executable.",
    )
    return repository_def_from_pointer(repository_handle.get_origin().code_pointer)


def create_in_process_ephemeral_workspace(pointer):
    from dagster.cli.workspace.workspace import Workspace

    check.inst_param(pointer, "pointer", CodePointer)
    repository_location_handles = [RepositoryLocationHandle.create_in_process_location(pointer)]
    workspace = Workspace(repository_location_handles=repository_location_handles)
    return workspace
