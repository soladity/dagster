import os

import pytest
from dagster_k8s import get_celery_engine_config
from dagster_test.test_project import (
    get_test_project_external_pipeline,
    test_project_environments_path,
)

from dagster.core.test_utils import create_run_for_test
from dagster.utils import load_yaml_from_path, merge_dicts
from dagster.utils.yaml_utils import merge_yamls

from .utils import wait_for_job_and_get_logs


@pytest.mark.integration
def test_k8s_run_launcher_default(dagster_instance, helm_namespace):
    environment_dict = load_yaml_from_path(
        os.path.join(test_project_environments_path(), 'env.yaml')
    )
    pipeline_name = 'demo_pipeline'
    tags = {'key': 'value'}
    run = create_run_for_test(
        dagster_instance,
        pipeline_name=pipeline_name,
        environment_dict=environment_dict,
        tags=tags,
        mode='default',
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
def test_k8s_run_launcher_celery(dagster_instance, helm_namespace):

    environment_dict = merge_dicts(
        merge_yamls(
            [
                os.path.join(test_project_environments_path(), 'env.yaml'),
                os.path.join(test_project_environments_path(), 'env_s3.yaml'),
            ]
        ),
        get_celery_engine_config(),
    )

    assert 'celery-k8s' in environment_dict['execution']

    pipeline_name = 'demo_pipeline_celery'
    tags = {'key': 'value'}
    run = create_run_for_test(
        dagster_instance,
        pipeline_name=pipeline_name,
        environment_dict=environment_dict,
        tags=tags,
        mode='default',
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
def test_failing_k8s_run_launcher(dagster_instance, helm_namespace):
    environment_dict = {'blah blah this is wrong': {}}
    pipeline_name = 'demo_pipeline'
    run = create_run_for_test(
        dagster_instance, pipeline_name=pipeline_name, environment_dict=environment_dict
    )

    dagster_instance.launch_run(run.run_id, get_test_project_external_pipeline(pipeline_name))
    result = wait_for_job_and_get_logs(
        job_name='dagster-run-%s' % run.run_id, namespace=helm_namespace
    )

    assert not result.get('errors')
    assert result['data']
    assert result['data']['executeRunInProcess']['__typename'] == 'PipelineConfigValidationInvalid'
    assert len(result['data']['executeRunInProcess']['errors']) == 2

    assert set(error['reason'] for error in result['data']['executeRunInProcess']['errors']) == {
        'FIELD_NOT_DEFINED',
        'MISSING_REQUIRED_FIELD',
    }
