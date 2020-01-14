from kubernetes import client, config

from dagster import Field
from dagster import __version__ as dagster_version
from dagster import check
from dagster.core.launcher import RunLauncher
from dagster.core.serdes import ConfigurableClass, ConfigurableClassData
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.seven import json

BACKOFF_LIMIT = 4

TTL_SECONDS_AFTER_FINISHED = 100


class K8sRunLauncher(RunLauncher, ConfigurableClass):
    def __init__(
        self,
        postgres_host,
        postgres_port,
        service_account_name,
        job_image,
        instance_config_map,
        image_pull_secrets=None,
        load_kubeconfig=False,
        kubeconfig_file=None,
        inst_data=None,
    ):
        self._inst_data = check.opt_inst_param(inst_data, 'inst_data', ConfigurableClassData)
        self.postgres_host = check.str_param(postgres_host, 'postgres_host')
        self.postgres_port = check.str_param(postgres_port, 'postgres_port')
        self.job_image = check.str_param(job_image, 'job_image')
        self.instance_config_map = check.str_param(instance_config_map, 'instance_config_map')
        self.image_pull_secrets = check.opt_list_param(image_pull_secrets, 'image_pull_secrets')
        self.service_account_name = check.str_param(service_account_name, 'service_account_name')
        check.bool_param(load_kubeconfig, 'load_kubeconfig')
        check.opt_str_param(kubeconfig_file, 'kubeconfig_file')

        if load_kubeconfig:
            config.load_kube_config(kubeconfig_file)
        else:
            config.load_incluster_config()

        self._kube_api = client.BatchV1Api()

    @classmethod
    def config_type(cls):
        return {
            'postgres_host': str,
            'postgres_port': str,
            'service_account_name': str,
            'job_image': str,
            'instance_config_map': str,
            'image_pull_secrets': Field(list, is_optional=True),
        }

    @classmethod
    def from_config_value(cls, inst_data, config_value):
        return cls(inst_data=inst_data, **config_value)

    @property
    def inst_data(self):
        return self._inst_data

    def construct_job(self, run):
        check.inst_param(run, 'run', PipelineRun)

        dagster_labels = {
            'app.kubernetes.io/name': 'dagster',
            'app.kubernetes.io/instance': 'dagster',
            'app.kubernetes.io/version': dagster_version,
        }

        init_container = client.V1Container(
            name='check-db-ready',
            image='postgres:9.6.16',
            command=[
                'sh',
                '-c',
                'until pg_isready -h {pg_host} -p {pg_port}; '
                'do echo waiting for database; sleep 2; done;'.format(
                    pg_host=self.postgres_host, pg_port=self.postgres_port,
                ),
            ],
        )

        execution_params = {
            'executionParams': {
                'selector': run.selector.to_graphql_input(),
                "environmentConfigData": run.environment_dict,
                "mode": run.mode,
            }
        }

        job_container = client.V1Container(
            name='dagster-job-%s' % run.run_id,
            image=self.job_image,
            command=['dagster-graphql'],
            args=["-p", "startPipelineExecution", "-v", json.dumps(execution_params)],
            image_pull_policy='Always',
            env=[client.V1EnvVar(name='DAGSTER_HOME', value='/opt/dagster/dagster_home')],
            volume_mounts=[
                client.V1VolumeMount(
                    name='dagster-instance',
                    mount_path='/opt/dagster/dagster_home/dagster.yaml',
                    sub_path='dagster.yaml',
                )
            ],
        )

        config_map_volume = client.V1Volume(
            name='dagster-instance',
            config_map=client.V1ConfigMapVolumeSource(name=self.instance_config_map),
        )

        template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(
                name='dagster-job-pod-%s' % run.run_id, labels=dagster_labels
            ),
            spec=client.V1PodSpec(
                image_pull_secrets=self.image_pull_secrets,
                service_account_name=self.service_account_name,
                init_containers=[init_container],
                restart_policy='Never',
                containers=[job_container],
                volumes=[config_map_volume],
            ),
        )

        job = client.V1Job(
            api_version="batch/v1",
            kind="Job",
            metadata=client.V1ObjectMeta(name='dagster-job-%s' % run.run_id, labels=dagster_labels),
            spec=client.V1JobSpec(
                template=template,
                backoff_limit=BACKOFF_LIMIT,
                ttl_seconds_after_finished=TTL_SECONDS_AFTER_FINISHED,
            ),
        )
        return job

    def launch_run(self, run):
        check.inst_param(run, 'run', PipelineRun)

        job = self.construct_job(run)
        api_response = self._kube_api.create_namespaced_job(body=job, namespace="default")
        print("Job created. status='%s'" % str(api_response.status))
        return run
