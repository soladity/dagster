# pylint doesn't know about pytest fixtures
# pylint: disable=unused-argument
import datetime
import os
import sys
import time

import boto3
import pytest
from dagster_celery_k8s.launcher import CeleryK8sRunLauncher
from dagster_k8s.test import wait_for_job_and_get_logs
from dagster_test.test_project import (
    get_test_project_external_pipeline,
    test_project_environments_path,
)

from dagster import DagsterEventType
from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.core.test_utils import create_run_for_test
from dagster.utils import merge_dicts
from dagster.utils.yaml_utils import merge_yamls


def get_celery_engine_config(dagster_docker_image, helm_namespace):
    return {
        'execution': {
            'celery-k8s': {
                'config': {
                    'job_image': dagster_docker_image,
                    'job_namespace': helm_namespace,
                    'image_pull_policy': 'Always',
                    'env_config_maps': ['dagster-pipeline-env'],
                }
            }
        },
    }


@pytest.mark.integration
@pytest.mark.skipif(sys.version_info < (3, 5), reason="Very slow on Python 2")
def test_execute_on_celery_k8s(  # pylint: disable=redefined-outer-name
    dagster_docker_image, dagster_instance, helm_namespace
):
    run_config = merge_dicts(
        merge_yamls(
            [
                os.path.join(test_project_environments_path(), 'env.yaml'),
                os.path.join(test_project_environments_path(), 'env_s3.yaml'),
            ]
        ),
        get_celery_engine_config(
            dagster_docker_image=dagster_docker_image, helm_namespace=helm_namespace
        ),
    )

    pipeline_name = 'demo_pipeline_celery'
    run = create_run_for_test(
        dagster_instance, pipeline_name=pipeline_name, run_config=run_config, mode='default',
    )

    dagster_instance.launch_run(run.run_id, get_test_project_external_pipeline(pipeline_name))

    result = wait_for_job_and_get_logs(
        job_name='dagster-run-%s' % run.run_id, namespace=helm_namespace
    )

    assert not result.get('errors')
    assert result['data']
    assert (
        result['data']['executeRunInProcess']['__typename'] == 'ExecuteRunInProcessSuccess'
    ), 'no match, result: {}'.format(result)


@pytest.mark.integration
@pytest.mark.skipif(sys.version_info < (3, 5), reason="Very slow on Python 2")
def test_execute_on_celery_k8s_retry_pipeline(  # pylint: disable=redefined-outer-name
    dagster_docker_image, dagster_instance, helm_namespace
):
    run_config = merge_dicts(
        merge_yamls([os.path.join(test_project_environments_path(), 'env_s3.yaml')]),
        get_celery_engine_config(
            dagster_docker_image=dagster_docker_image, helm_namespace=helm_namespace
        ),
    )

    pipeline_name = 'retry_pipeline'
    run = create_run_for_test(
        dagster_instance, pipeline_name=pipeline_name, run_config=run_config, mode='default',
    )

    dagster_instance.launch_run(run.run_id, get_test_project_external_pipeline(pipeline_name))

    result = wait_for_job_and_get_logs(
        job_name='dagster-run-%s' % run.run_id, namespace=helm_namespace
    )

    assert not result.get('errors')
    assert result['data']
    assert (
        result['data']['executeRunInProcess']['__typename'] == 'ExecuteRunInProcessSuccess'
    ), 'no match, result: {}'.format(result)

    stats = dagster_instance.get_run_stats(run.run_id)
    assert stats.steps_succeeded == 1

    assert DagsterEventType.STEP_START in [
        event.dagster_event.event_type
        for event in dagster_instance.all_logs(run.run_id)
        if event.is_dagster_event
    ]

    assert DagsterEventType.STEP_UP_FOR_RETRY in [
        event.dagster_event.event_type
        for event in dagster_instance.all_logs(run.run_id)
        if event.is_dagster_event
    ]

    assert DagsterEventType.STEP_RESTARTED in [
        event.dagster_event.event_type
        for event in dagster_instance.all_logs(run.run_id)
        if event.is_dagster_event
    ]

    assert DagsterEventType.STEP_SUCCESS in [
        event.dagster_event.event_type
        for event in dagster_instance.all_logs(run.run_id)
        if event.is_dagster_event
    ]


@pytest.mark.integration
@pytest.mark.skipif(sys.version_info < (3, 5), reason="Very slow on Python 2")
def test_execute_on_celery_k8s_with_resource_requirements(  # pylint: disable=redefined-outer-name
    dagster_docker_image, dagster_instance, helm_namespace
):
    run_config = merge_dicts(
        merge_yamls([os.path.join(test_project_environments_path(), 'env_s3.yaml'),]),
        get_celery_engine_config(
            dagster_docker_image=dagster_docker_image, helm_namespace=helm_namespace
        ),
    )

    pipeline_name = 'resources_limit_pipeline_celery'
    run = create_run_for_test(
        dagster_instance, pipeline_name=pipeline_name, run_config=run_config, mode='default',
    )

    dagster_instance.launch_run(run.run_id, get_test_project_external_pipeline(pipeline_name))

    result = wait_for_job_and_get_logs(
        job_name='dagster-run-%s' % run.run_id, namespace=helm_namespace
    )

    assert not result.get('errors')
    assert result['data']
    assert (
        result['data']['executeRunInProcess']['__typename'] == 'ExecuteRunInProcessSuccess'
    ), 'no match, result: {}'.format(result)


@pytest.mark.skipif(sys.version_info < (3, 5), reason="Very slow on Python 2")
def test_execute_on_celery_k8s_with_termination(  # pylint: disable=redefined-outer-name
    dagster_docker_image, dagster_instance, helm_namespace
):
    run_config = merge_dicts(
        merge_yamls([os.path.join(test_project_environments_path(), 'env_s3.yaml'),]),
        get_celery_engine_config(
            dagster_docker_image=dagster_docker_image, helm_namespace=helm_namespace
        ),
    )

    pipeline_name = 'resource_pipeline'
    run = create_run_for_test(
        dagster_instance, pipeline_name=pipeline_name, run_config=run_config, mode='default',
    )

    dagster_instance.launch_run(run.run_id, get_test_project_external_pipeline(pipeline_name))
    assert isinstance(dagster_instance.run_launcher, CeleryK8sRunLauncher)

    # Wait for pipeline run to start
    timeout = datetime.timedelta(0, 120)
    start_time = datetime.datetime.now()
    can_terminate = False
    while datetime.datetime.now() < start_time + timeout:
        if dagster_instance.run_launcher.can_terminate(run_id=run.run_id):
            can_terminate = True
            break
        time.sleep(5)
    assert can_terminate

    # Wait for step to start
    step_start_found = False
    start_time = datetime.datetime.now()
    while datetime.datetime.now() < start_time + timeout:
        event_records = dagster_instance.all_logs(run.run_id)
        for event_record in event_records:
            if (
                event_record.dagster_event
                and event_record.dagster_event.event_type == DagsterEventType.STEP_START
            ):
                step_start_found = True
                break
        time.sleep(5)
    assert step_start_found

    # Terminate run
    assert dagster_instance.run_launcher.can_terminate(run_id=run.run_id)
    assert dagster_instance.run_launcher.terminate(run_id=run.run_id)

    # Check that pipeline run is marked as failed
    pipeline_run_status_failure = False
    start_time = datetime.datetime.now()
    while datetime.datetime.now() < start_time + timeout:
        pipeline_run = dagster_instance.get_run_by_id(run.run_id)
        if pipeline_run.status == PipelineRunStatus.FAILURE:
            pipeline_run_status_failure = True
            break
        time.sleep(5)
    assert pipeline_run_status_failure

    # Check that terminate cannot be called again
    assert not dagster_instance.run_launcher.can_terminate(run_id=run.run_id)
    assert not dagster_instance.run_launcher.terminate(run_id=run.run_id)

    # Check for step failure and resource tear down
    expected_events_found = False
    start_time = datetime.datetime.now()
    while datetime.datetime.now() < start_time + timeout:
        step_failures_count = 0
        resource_tear_down_count = 0
        resource_init_count = 0
        event_records = dagster_instance.all_logs(run.run_id)
        for event_record in event_records:
            if event_record.dagster_event:
                if event_record.dagster_event.event_type == DagsterEventType.STEP_FAILURE:
                    step_failures_count += 1
            elif event_record.message:
                if 'initializing s3_resource_with_context_manager' in event_record.message:
                    resource_init_count += 1
                if 'tearing down s3_resource_with_context_manager' in event_record.message:
                    resource_tear_down_count += 1
        if step_failures_count == 1 and resource_init_count == 1 and resource_tear_down_count == 1:
            expected_events_found = True
            break
        time.sleep(5)
    assert expected_events_found

    s3 = boto3.resource('s3', region_name='us-west-1', use_ssl=True, endpoint_url=None).meta.client
    bucket = 'dagster-scratch-80542c2'
    key = 'resource_termination_test/{}'.format(run.run_id)
    assert s3.get_object(Bucket=bucket, Key=key)
