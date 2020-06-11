import os

import yaml
from dagster_k8s import construct_dagster_graphql_k8s_job
from dagster_k8s.job import K8S_RESOURCE_REQUIREMENTS_KEY, get_k8s_resource_requirements
from dagster_test.test_project import (
    get_test_project_external_pipeline,
    test_project_docker_image,
    test_project_environments_path,
)

from dagster import __version__ as dagster_version
from dagster import seven
from dagster.core.definitions.utils import validate_tags
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.core.test_utils import create_run_for_test
from dagster.utils import load_yaml_from_path

from .utils import image_pull_policy, remove_none_recursively, wait_for_job_and_get_logs

EXPECTED_JOB_SPEC = '''
api_version: batch/v1
kind: Job
metadata:
  labels:
    app.kubernetes.io/component: runmaster
    app.kubernetes.io/instance: dagster
    app.kubernetes.io/name: dagster
    app.kubernetes.io/part-of: dagster
    app.kubernetes.io/version: {dagster_version}
  name: dagster-run-{run_id}
spec:
  backoff_limit: 4
  template:
    metadata:
      labels:
        app.kubernetes.io/component: runmaster
        app.kubernetes.io/instance: dagster
        app.kubernetes.io/name: dagster
        app.kubernetes.io/part-of: dagster
        app.kubernetes.io/version: {dagster_version}
      name: dagster-run-{run_id}
    spec:
      containers:
      - args:
        - -p
        - executeRunInProcess
        - -v
        - '{{"runId": "{run_id}"}}'
        command:
        - dagster-graphql
        env:
        - name: DAGSTER_HOME
          value: /opt/dagster/dagster_home
        - name: DAGSTER_PG_PASSWORD
          value_from:
            secret_key_ref:
              key: postgresql-password
              name: dagster-postgresql-secret
        env_from:
        - config_map_ref:
            name: dagster-pipeline-env
        - config_map_ref:
            name: test-env-configmap
        - secret_ref:
            name: test-env-secret
        image: {job_image}
        image_pull_policy: {image_pull_policy}
        name: dagster-run-{run_id}{resources}
        volume_mounts:
        - mount_path: /opt/dagster/dagster_home/dagster.yaml
          name: dagster-instance
          sub_path: dagster.yaml
      image_pull_secrets:
      - name: element-dev-key
      restart_policy: Never
      service_account_name: dagit-admin
      volumes:
      - config_map:
          name: dagster-instance
        name: dagster-instance
  ttl_seconds_after_finished: 86400
'''


def test_valid_job_format(run_launcher):
    docker_image = test_project_docker_image()

    environment_dict = load_yaml_from_path(
        os.path.join(test_project_environments_path(), 'env.yaml')
    )
    pipeline_name = 'demo_pipeline'
    run = PipelineRun(pipeline_name=pipeline_name, environment_dict=environment_dict)

    job_name = 'dagster-run-%s' % run.run_id
    pod_name = 'dagster-run-%s' % run.run_id
    job = construct_dagster_graphql_k8s_job(
        run_launcher.job_config,
        args=['-p', 'executeRunInProcess', '-v', seven.json.dumps({'runId': run.run_id}),],
        job_name=job_name,
        pod_name=pod_name,
        component='runmaster',
    )

    assert (
        yaml.dump(remove_none_recursively(job.to_dict()), default_flow_style=False).strip()
        == EXPECTED_JOB_SPEC.format(
            run_id=run.run_id,
            job_image=docker_image,
            image_pull_policy=image_pull_policy(),
            dagster_version=dagster_version,
            resources='',
        ).strip()
    )


def test_valid_job_format_with_resources(run_launcher):
    docker_image = test_project_docker_image()

    environment_dict = load_yaml_from_path(
        os.path.join(test_project_environments_path(), 'env.yaml')
    )
    pipeline_name = 'demo_pipeline'
    run = PipelineRun(pipeline_name=pipeline_name, environment_dict=environment_dict)

    tags = validate_tags(
        {
            K8S_RESOURCE_REQUIREMENTS_KEY: (
                {
                    'requests': {'cpu': '250m', 'memory': '64Mi'},
                    'limits': {'cpu': '500m', 'memory': '2560Mi'},
                }
            )
        }
    )
    resources = get_k8s_resource_requirements(tags)
    job_name = 'dagster-run-%s' % run.run_id
    pod_name = 'dagster-run-%s' % run.run_id
    job = construct_dagster_graphql_k8s_job(
        run_launcher.job_config,
        args=['-p', 'executeRunInProcess', '-v', seven.json.dumps({'runId': run.run_id}),],
        job_name=job_name,
        resources=resources,
        pod_name=pod_name,
        component='runmaster',
    )

    assert (
        yaml.dump(remove_none_recursively(job.to_dict()), default_flow_style=False).strip()
        == EXPECTED_JOB_SPEC.format(
            run_id=run.run_id,
            job_image=docker_image,
            image_pull_policy=image_pull_policy(),
            dagster_version=dagster_version,
            resources='''
        resources:
          limits:
            cpu: 500m
            memory: 2560Mi
          requests:
            cpu: 250m
            memory: 64Mi''',
        ).strip()
    )


def test_k8s_run_launcher(dagster_instance, helm_namespace):
    environment_dict = load_yaml_from_path(
        os.path.join(test_project_environments_path(), 'env.yaml')
    )
    pipeline_name = 'demo_pipeline'
    run = create_run_for_test(
        dagster_instance,
        pipeline_name=pipeline_name,
        environment_dict=environment_dict,
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
