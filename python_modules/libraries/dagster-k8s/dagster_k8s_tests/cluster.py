import os
import subprocess
import time
from collections import namedtuple
from contextlib import contextmanager

import kubernetes
import psycopg2
import pytest
from dagster_k8s.launcher import K8sRunLauncher
from dagster_k8s.utils import wait_for_pod
from dagster_postgres import PostgresEventLogStorage, PostgresRunStorage
from dagster_test.test_project import build_and_tag_test_image, test_project_docker_image

from dagster import check
from dagster.core.instance import DagsterInstance, InstanceType
from dagster.core.storage.noop_compute_log_manager import NoOpComputeLogManager
from dagster.core.storage.root import LocalArtifactStorage

from .utils import IS_BUILDKITE, check_output, find_free_port, image_pull_policy

# How long to wait before giving up on trying to establish postgres port forwarding
PG_PORT_FORWARDING_TIMEOUT = 60  # 1 minute


class ClusterConfig(namedtuple('_ClusterConfig', 'name kubeconfig_file')):
    '''Used to represent a cluster, returned by the cluster_provider fixture below.
    '''

    def __new__(cls, name, kubeconfig_file):
        return super(ClusterConfig, cls).__new__(
            cls,
            name=check.str_param(name, 'name'),
            kubeconfig_file=check.str_param(kubeconfig_file, 'kubeconfig_file'),
        )


def define_cluster_provider_fixture(additional_kind_images=None):
    @pytest.fixture(scope='session')
    def _cluster_provider(request):
        from .kind import kind_cluster_exists, kind_cluster, kind_load_images

        if IS_BUILDKITE:
            print('Installing ECR credentials...')
            check_output('aws ecr get-login --no-include-email --region us-west-1 | sh', shell=True)

        provider = request.config.getoption('--cluster-provider')

        # Use a kind cluster
        if provider == 'kind':
            cluster_name = request.config.getoption('--kind-cluster')

            # Cluster will be deleted afterwards unless this is set.
            # This is to allow users to reuse an existing cluster in local test by running
            # `pytest --kind-cluster my-cluster --no-cleanup` -- this avoids the per-test run
            # overhead of cluster setup and teardown
            should_cleanup = not request.config.getoption('--no-cleanup')

            existing_cluster = kind_cluster_exists(cluster_name)

            with kind_cluster(cluster_name, should_cleanup=should_cleanup) as cluster_config:
                if not IS_BUILDKITE and not existing_cluster:
                    docker_image = test_project_docker_image()
                    build_and_tag_test_image(docker_image)
                    kind_load_images(
                        cluster_name=cluster_config.name,
                        local_dagster_test_image=docker_image,
                        additional_images=additional_kind_images,
                    )
                yield cluster_config

        # Use cluster from kubeconfig
        elif provider == 'kubeconfig':
            kubeconfig_file = os.getenv('KUBECONFIG', os.path.expandvars('${HOME}/.kube/config'))
            kubernetes.config.load_kube_config(config_file=kubeconfig_file)
            yield ClusterConfig(name='from_system_kubeconfig', kubeconfig_file=kubeconfig_file)

        else:
            raise Exception('unknown cluster provider %s' % provider)

    return _cluster_provider


@pytest.fixture(scope='session')
def run_launcher(
    cluster_provider, helm_namespace
):  # pylint: disable=redefined-outer-name,unused-argument

    return K8sRunLauncher(
        image_pull_secrets=[{'name': 'element-dev-key'}],
        service_account_name='dagit-admin',
        instance_config_map='dagster-instance',
        postgres_password_secret='dagster-postgresql-secret',
        dagster_home='/opt/dagster/dagster_home',
        job_image=test_project_docker_image(),
        load_incluster_config=False,
        kubeconfig_file=cluster_provider.kubeconfig_file,
        image_pull_policy=image_pull_policy(),
        job_namespace=helm_namespace,
        env_config_maps=['dagster-pipeline-env', 'test-env-configmap'],
        env_secrets=['test-env-secret'],
    )


@pytest.fixture(scope='session')
def dagster_instance(helm_namespace, run_launcher):  # pylint: disable=redefined-outer-name
    @contextmanager
    def local_port_forward_postgres():
        print('Port-forwarding postgres')
        postgres_pod_name = (
            check_output(
                [
                    'kubectl',
                    'get',
                    'pods',
                    '--namespace',
                    helm_namespace,
                    '-l',
                    'app=postgresql,release=dagster',
                    '-o',
                    'jsonpath="{.items[0].metadata.name}"',
                ]
            )
            .decode('utf-8')
            .strip('"')
        )
        forward_port = find_free_port()

        wait_for_pod(postgres_pod_name, namespace=helm_namespace)

        try:
            p = subprocess.Popen(
                [
                    'kubectl',
                    'port-forward',
                    '--namespace',
                    helm_namespace,
                    postgres_pod_name,
                    '{forward_port}:5432'.format(forward_port=forward_port),
                ]
            )

            # Validate port forwarding works
            start = time.time()

            while True:
                if time.time() - start > PG_PORT_FORWARDING_TIMEOUT:
                    raise Exception('Timed out while waiting for postgres port forwarding')

                print(
                    'Waiting for port forwarding from k8s pod %s:5432 to localhost:%d to be'
                    ' available...' % (postgres_pod_name, forward_port)
                )
                try:
                    conn = psycopg2.connect(
                        database='test',
                        user='test',
                        password='test',
                        host='localhost',
                        port=forward_port,
                    )
                    conn.close()
                    break
                except:  # pylint: disable=bare-except, broad-except
                    time.sleep(1)
                    continue

            yield forward_port

        finally:
            print('Terminating port-forwarding')
            p.terminate()

    tempdir = DagsterInstance.temp_storage()

    with local_port_forward_postgres() as local_forward_port:
        postgres_url = 'postgresql://test:test@localhost:{local_forward_port}/test'.format(
            local_forward_port=local_forward_port
        )
        print('Local Postgres forwarding URL: ', postgres_url)

        instance = DagsterInstance(
            instance_type=InstanceType.EPHEMERAL,
            local_artifact_storage=LocalArtifactStorage(tempdir),
            run_storage=PostgresRunStorage(postgres_url),
            event_storage=PostgresEventLogStorage(postgres_url),
            compute_log_manager=NoOpComputeLogManager(),
            run_launcher=run_launcher,
        )
        yield instance
