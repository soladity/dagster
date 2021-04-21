import json
from unittest import mock

import pytest
from dagster import pipeline, reconstructable
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.host_representation import InProcessRepositoryLocationOrigin, RepositoryHandle
from dagster.core.storage.tags import DOCKER_IMAGE_TAG
from dagster.core.test_utils import create_run_for_test, environ, instance_for_test
from dagster.utils.hosted_user_process import external_pipeline_from_recon_pipeline
from dagster_celery_k8s.config import get_celery_engine_config
from dagster_celery_k8s.executor import CELERY_K8S_CONFIG_KEY
from dagster_celery_k8s.launcher import (
    CeleryK8sRunLauncher,
    _get_validated_celery_k8s_executor_config,
)
from dagster_k8s.client import DEFAULT_WAIT_TIMEOUT
from dagster_k8s.job import UserDefinedDagsterK8sConfig
from dagster_test.test_project import get_test_project_external_pipeline


def test_get_validated_celery_k8s_executor_config():
    res = _get_validated_celery_k8s_executor_config(
        {"execution": {CELERY_K8S_CONFIG_KEY: {"config": {"job_image": "foo"}}}}
    )

    assert res == {
        "backend": "rpc://",
        "retries": {"enabled": {}},
        "job_image": "foo",
        "image_pull_policy": "IfNotPresent",
        "load_incluster_config": True,
        "job_namespace": "default",
        "repo_location_name": "<<in_process>>",
        "job_wait_timeout": DEFAULT_WAIT_TIMEOUT,
    }

    with pytest.raises(
        DagsterInvariantViolationError,
        match="celery-k8s execution configuration must be present in the run config to use the CeleryK8sRunLauncher.",
    ):
        _get_validated_celery_k8s_executor_config({})

    with environ(
        {
            "DAGSTER_K8S_PIPELINE_RUN_IMAGE": "foo",
            "DAGSTER_K8S_PIPELINE_RUN_NAMESPACE": "default",
            "DAGSTER_K8S_PIPELINE_RUN_IMAGE_PULL_POLICY": "Always",
            "DAGSTER_K8S_PIPELINE_RUN_ENV_CONFIGMAP": "config-pipeline-env",
        }
    ):
        cfg = get_celery_engine_config()
        res = _get_validated_celery_k8s_executor_config(cfg)
        assert res == {
            "backend": "rpc://",
            "retries": {"enabled": {}},
            "job_image": "foo",
            "image_pull_policy": "Always",
            "env_config_maps": ["config-pipeline-env"],
            "load_incluster_config": True,
            "job_namespace": "default",
            "repo_location_name": "<<in_process>>",
            "job_wait_timeout": DEFAULT_WAIT_TIMEOUT,
        }

    # Test setting all possible config fields
    with environ(
        {
            "TEST_PIPELINE_RUN_NAMESPACE": "default",
            "TEST_CELERY_BROKER": "redis://some-redis-host:6379/0",
            "TEST_CELERY_BACKEND": "redis://some-redis-host:6379/0",
            "TEST_PIPELINE_RUN_IMAGE": "foo",
            "TEST_PIPELINE_RUN_IMAGE_PULL_POLICY": "Always",
            "TEST_K8S_PULL_SECRET_1": "super-secret-1",
            "TEST_K8S_PULL_SECRET_2": "super-secret-2",
            "TEST_SERVICE_ACCOUNT_NAME": "my-cool-service-acccount",
            "TEST_PIPELINE_RUN_ENV_CONFIGMAP": "config-pipeline-env",
            "TEST_SECRET": "config-secret-env",
        }
    ):

        cfg = {
            "execution": {
                CELERY_K8S_CONFIG_KEY: {
                    "config": {
                        "repo_location_name": "<<in_process>>",
                        "load_incluster_config": False,
                        "kubeconfig_file": "/some/kubeconfig/file",
                        "job_namespace": {"env": "TEST_PIPELINE_RUN_NAMESPACE"},
                        "broker": {"env": "TEST_CELERY_BROKER"},
                        "backend": {"env": "TEST_CELERY_BACKEND"},
                        "include": ["dagster", "dagit"],
                        "config_source": {
                            "task_annotations": """{'*': {'on_failure': my_on_failure}}"""
                        },
                        "retries": {"disabled": {}},
                        "job_image": {"env": "TEST_PIPELINE_RUN_IMAGE"},
                        "image_pull_policy": {"env": "TEST_PIPELINE_RUN_IMAGE_PULL_POLICY"},
                        "image_pull_secrets": [
                            {"name": {"env": "TEST_K8S_PULL_SECRET_1"}},
                            {"name": {"env": "TEST_K8S_PULL_SECRET_2"}},
                        ],
                        "service_account_name": {"env": "TEST_SERVICE_ACCOUNT_NAME"},
                        "env_config_maps": [{"env": "TEST_PIPELINE_RUN_ENV_CONFIGMAP"}],
                        "env_secrets": [{"env": "TEST_SECRET"}],
                        "job_wait_timeout": DEFAULT_WAIT_TIMEOUT,
                    }
                }
            }
        }

        res = _get_validated_celery_k8s_executor_config(cfg)
        assert res == {
            "repo_location_name": "<<in_process>>",
            "load_incluster_config": False,
            "kubeconfig_file": "/some/kubeconfig/file",
            "job_namespace": "default",
            "backend": "redis://some-redis-host:6379/0",
            "broker": "redis://some-redis-host:6379/0",
            "include": ["dagster", "dagit"],
            "config_source": {"task_annotations": """{'*': {'on_failure': my_on_failure}}"""},
            "retries": {"disabled": {}},
            "job_image": "foo",
            "image_pull_policy": "Always",
            "image_pull_secrets": [{"name": "super-secret-1"}, {"name": "super-secret-2"}],
            "service_account_name": "my-cool-service-acccount",
            "env_config_maps": ["config-pipeline-env"],
            "env_secrets": ["config-secret-env"],
            "job_wait_timeout": DEFAULT_WAIT_TIMEOUT,
        }


def test_user_defined_k8s_config_in_run_tags(kubeconfig_file):
    # Construct a K8s run launcher in a fake k8s environment.
    mock_k8s_client_batch_api = mock.MagicMock()
    celery_k8s_run_launcher = CeleryK8sRunLauncher(
        instance_config_map="dagster-instance",
        postgres_password_secret="dagster-postgresql-secret",
        dagster_home="/opt/dagster/dagster_home",
        load_incluster_config=False,
        kubeconfig_file=kubeconfig_file,
        k8s_client_batch_api=mock_k8s_client_batch_api,
    )

    # Construct Dagster run tags with user defined k8s config.
    expected_resources = {
        "requests": {"cpu": "250m", "memory": "64Mi"},
        "limits": {"cpu": "500m", "memory": "2560Mi"},
    }
    user_defined_k8s_config = UserDefinedDagsterK8sConfig(
        container_config={"resources": expected_resources},
    )
    user_defined_k8s_config_json = json.dumps(user_defined_k8s_config.to_dict())
    tags = {"dagster-k8s/config": user_defined_k8s_config_json}

    # Create fake external pipeline.
    recon_pipeline = reconstructable(fake_pipeline)
    recon_repo = recon_pipeline.repository
    location_origin = InProcessRepositoryLocationOrigin(recon_repo)
    with location_origin.create_location() as location:
        location = location_origin.create_location()
        repo_def = recon_repo.get_definition()
        repo_handle = RepositoryHandle(
            repository_name=repo_def.name,
            repository_location=location,
        )
        fake_external_pipeline = external_pipeline_from_recon_pipeline(
            recon_pipeline,
            solid_selection=None,
            repository_handle=repo_handle,
        )

        # Launch the run in a fake Dagster instance.
        with instance_for_test() as instance:
            celery_k8s_run_launcher.register_instance(instance)
            pipeline_name = "demo_pipeline"
            run_config = {"execution": {"celery-k8s": {"config": {"job_image": "fake-image-name"}}}}
            run = create_run_for_test(
                instance,
                pipeline_name=pipeline_name,
                run_config=run_config,
                tags=tags,
            )
            celery_k8s_run_launcher.launch_run(run, fake_external_pipeline)

            updated_run = instance.get_run_by_id(run.run_id)
            assert updated_run.tags[DOCKER_IMAGE_TAG] == "fake-image-name"

        # Check that user defined k8s config was passed down to the k8s job.
        mock_method_calls = mock_k8s_client_batch_api.method_calls
        assert len(mock_method_calls) > 0
        method_name, _args, kwargs = mock_method_calls[0]
        assert method_name == "create_namespaced_job"
        job_resources = kwargs["body"].spec.template.spec.containers[0].resources
        assert job_resources == expected_resources


def test_k8s_executor_config_override(kubeconfig_file):
    # Construct a K8s run launcher in a fake k8s environment.
    mock_k8s_client_batch_api = mock.MagicMock()
    celery_k8s_run_launcher = CeleryK8sRunLauncher(
        instance_config_map="dagster-instance",
        postgres_password_secret="dagster-postgresql-secret",
        dagster_home="/opt/dagster/dagster_home",
        load_incluster_config=False,
        kubeconfig_file=kubeconfig_file,
        k8s_client_batch_api=mock_k8s_client_batch_api,
    )

    with get_test_project_external_pipeline("demo_pipeline", "my_image:tag") as external_pipeline:

        # Launch the run in a fake Dagster instance.
        with instance_for_test() as instance:
            celery_k8s_run_launcher.register_instance(instance)
            pipeline_name = "demo_pipeline"

            # Launch without custom job_image
            run = create_run_for_test(
                instance,
                pipeline_name=pipeline_name,
                run_config={"execution": {"celery-k8s": {}}},
            )
            celery_k8s_run_launcher.launch_run(run, external_pipeline)

            updated_run = instance.get_run_by_id(run.run_id)
            assert updated_run.tags[DOCKER_IMAGE_TAG] == "my_image:tag"

            # Launch with custom job_image
            run = create_run_for_test(
                instance,
                pipeline_name=pipeline_name,
                run_config={
                    "execution": {"celery-k8s": {"config": {"job_image": "fake-image-name"}}}
                },
            )
            celery_k8s_run_launcher.launch_run(run, external_pipeline)

            updated_run = instance.get_run_by_id(run.run_id)
            assert updated_run.tags[DOCKER_IMAGE_TAG] == "fake-image-name"

        # Check that user defined k8s config was passed down to the k8s job.
        mock_method_calls = mock_k8s_client_batch_api.method_calls
        assert len(mock_method_calls) > 0

        _, _args, kwargs = mock_method_calls[0]
        assert kwargs["body"].spec.template.spec.containers[0].image == "my_image:tag"

        _, _args, kwargs = mock_method_calls[1]
        assert kwargs["body"].spec.template.spec.containers[0].image == "fake-image-name"


@pipeline
def fake_pipeline():
    pass
