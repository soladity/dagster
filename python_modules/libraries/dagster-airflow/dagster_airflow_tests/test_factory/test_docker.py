# pylint: disable=unused-import
import os
import sys
import uuid

import pytest
from airflow.exceptions import AirflowException
from airflow.utils import timezone
from dagster_airflow.factory import make_airflow_dag_containerized_for_recon_repo
from dagster_airflow.test_fixtures import (
    dagster_airflow_docker_operator_pipeline,
    execute_tasks_in_dag,
)
from dagster_airflow_tests.conftest import dagster_docker_image
from dagster_airflow_tests.marks import nettest, requires_airflow_db
from dagster_test.test_project import test_project_environments_path

from dagster.core.definitions.reconstructable import ReconstructableRepository
from dagster.core.utils import make_new_run_id
from dagster.utils import git_repository_root, load_yaml_from_glob_list

from .utils import validate_pipeline_execution, validate_skip_pipeline_execution


@requires_airflow_db
def test_fs_storage_no_explicit_base_dir(
    dagster_airflow_docker_operator_pipeline, dagster_docker_image
):  # pylint: disable=redefined-outer-name
    pipeline_name = 'demo_pipeline'
    environments_path = test_project_environments_path()
    results = dagster_airflow_docker_operator_pipeline(
        pipeline_name=pipeline_name,
        recon_repo=ReconstructableRepository.for_module(
            'test_pipelines.repo', 'define_demo_execution_repo'
        ),
        environment_yaml=[
            os.path.join(environments_path, 'env.yaml'),
            os.path.join(environments_path, 'env_filesystem_no_explicit_base_dir.yaml'),
        ],
        image=dagster_docker_image,
    )
    validate_pipeline_execution(results)


@requires_airflow_db
def test_fs_storage(
    dagster_airflow_docker_operator_pipeline, dagster_docker_image
):  # pylint: disable=redefined-outer-name
    pipeline_name = 'demo_pipeline'
    environments_path = test_project_environments_path()
    results = dagster_airflow_docker_operator_pipeline(
        pipeline_name=pipeline_name,
        recon_repo=ReconstructableRepository.for_module(
            'test_pipelines.repo', 'define_demo_execution_repo'
        ),
        environment_yaml=[
            os.path.join(environments_path, 'env.yaml'),
            os.path.join(environments_path, 'env_filesystem.yaml'),
        ],
        image=dagster_docker_image,
    )
    validate_pipeline_execution(results)


@nettest
@requires_airflow_db
def test_s3_storage(
    dagster_airflow_docker_operator_pipeline, dagster_docker_image
):  # pylint: disable=redefined-outer-name
    pipeline_name = 'demo_pipeline'
    environments_path = test_project_environments_path()
    results = dagster_airflow_docker_operator_pipeline(
        pipeline_name=pipeline_name,
        recon_repo=ReconstructableRepository.for_module(
            'test_pipelines.repo', 'define_demo_execution_repo'
        ),
        environment_yaml=[
            os.path.join(environments_path, 'env.yaml'),
            os.path.join(environments_path, 'env_s3.yaml'),
        ],
        image=dagster_docker_image,
    )
    validate_pipeline_execution(results)


@nettest
@requires_airflow_db
def test_gcs_storage(
    dagster_airflow_docker_operator_pipeline, dagster_docker_image,
):  # pylint: disable=redefined-outer-name
    pipeline_name = 'demo_pipeline_gcs'
    environments_path = test_project_environments_path()
    results = dagster_airflow_docker_operator_pipeline(
        pipeline_name=pipeline_name,
        recon_repo=ReconstructableRepository.for_module(
            'test_pipelines.repo', 'define_demo_execution_repo'
        ),
        environment_yaml=[
            os.path.join(environments_path, 'env.yaml'),
            os.path.join(environments_path, 'env_gcs.yaml'),
        ],
        image=dagster_docker_image,
    )
    validate_pipeline_execution(results)


@requires_airflow_db
def test_skip_operator(
    dagster_airflow_docker_operator_pipeline, dagster_docker_image
):  # pylint: disable=redefined-outer-name
    pipeline_name = 'optional_outputs'
    environments_path = test_project_environments_path()
    results = dagster_airflow_docker_operator_pipeline(
        pipeline_name=pipeline_name,
        recon_repo=ReconstructableRepository.for_module(
            'test_pipelines.repo', 'define_demo_execution_repo'
        ),
        environment_yaml=[os.path.join(environments_path, 'env_filesystem.yaml')],
        op_kwargs={'host_tmp_dir': '/tmp'},
        image=dagster_docker_image,
    )
    validate_skip_pipeline_execution(results)


@requires_airflow_db
def test_error_dag_containerized(dagster_docker_image):  # pylint: disable=redefined-outer-name
    pipeline_name = 'demo_error_pipeline'
    recon_repo = ReconstructableRepository.for_module(
        'test_pipelines.repo', 'define_demo_execution_repo'
    )
    environments_path = test_project_environments_path()
    environment_yaml = [
        os.path.join(environments_path, 'env_s3.yaml'),
    ]
    run_config = load_yaml_from_glob_list(environment_yaml)

    run_id = make_new_run_id()
    execution_date = timezone.utcnow()

    dag, tasks = make_airflow_dag_containerized_for_recon_repo(
        recon_repo, pipeline_name, dagster_docker_image, run_config
    )

    with pytest.raises(AirflowException) as exc_info:
        execute_tasks_in_dag(dag, tasks, run_id, execution_date)

    assert 'Exception: Unusual error' in str(exc_info.value)
