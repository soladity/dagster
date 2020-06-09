from collections import namedtuple

import kubernetes
import yaml

from dagster import Array, DagsterInvariantViolationError, Field, Noneable, StringSource
from dagster import __version__ as dagster_version
from dagster import check
from dagster.config.field_utils import Shape
from dagster.serdes import whitelist_for_serdes
from dagster.utils import frozentags, merge_dicts

K8S_JOB_BACKOFF_LIMIT = 4

K8S_JOB_TTL_SECONDS_AFTER_FINISHED = 24 * 60 * 60  # 1 day

DAGSTER_HOME_DEFAULT = '/opt/dagster/dagster_home'

# The Kubernetes Secret containing the PG password will be exposed as this env var in the job
# container.
DAGSTER_PG_PASSWORD_ENV_VAR = 'DAGSTER_PG_PASSWORD'

# We expect the PG secret to have this key.
#
# For an example, see:
# python_modules/libraries/dagster-k8s/helm/dagster/templates/secret-postgres.yaml
DAGSTER_PG_PASSWORD_SECRET_KEY = 'postgresql-password'

# Kubernetes Job object names cannot be longer than 63 characters
MAX_K8S_NAME_LEN = 63

K8S_RESOURCE_REQUIREMENTS_KEY = 'dagster-k8s/resource_requirements'
K8s_RESOURCE_REQUIREMENTS_VALID_KEYS = set(['limits', 'requests'])


def get_k8s_resource_requirements(tags):
    check.inst_param(tags, 'tags', frozentags)
    req_str = tags.get(K8S_RESOURCE_REQUIREMENTS_KEY)
    if req_str is not None:
        req_dict = yaml.safe_load(req_str)

        req_keys = set(req_dict.keys())
        if len(req_keys.difference(K8s_RESOURCE_REQUIREMENTS_VALID_KEYS)) > 0:
            raise DagsterInvariantViolationError(
                'Invalid K8s resource specification. {resource} expected to only contain keys in '
                'set {valid_keys} but found extra keys {extra_keys}'.format(
                    resource=req_dict,
                    valid_keys=K8s_RESOURCE_REQUIREMENTS_VALID_KEYS,
                    extra_keys=req_keys.difference(K8s_RESOURCE_REQUIREMENTS_VALID_KEYS),
                )
            )

        req = kubernetes.client.V1ResourceRequirements(**req_dict)
        return req

    return None


@whitelist_for_serdes
class DagsterK8sJobConfig(
    namedtuple(
        '_K8sJobTaskConfig',
        'job_image dagster_home image_pull_policy image_pull_secrets service_account_name '
        'instance_config_map postgres_password_secret env_config_maps env_secrets',
    )
):
    '''Configuration parameters for launching Dagster Jobs on Kubernetes.

    Params:
        job_image (str): The docker image to use. The Job container will be launched with this
            image.
        dagster_home (str): The location of DAGSTER_HOME in the Job container; this is where the
            ``dagster.yaml`` file will be mounted from the instance ConfigMap specified here.
        image_pull_policy (Optional[str]): Allows the image pull policy to be overridden, e.g. to
            facilitate local testing with `kind <https://kind.sigs.k8s.io/>`_. Default:
            ``"Always"``. See:
            https://kubernetes.io/docs/concepts/containers/images/#updating-images.
        image_pull_secrets (Optional[List[Dict[str, str]]]): Optionally, a list of dicts, each of
            which corresponds to a Kubernetes ``LocalObjectReference`` (e.g.,
            ``{'name': 'myRegistryName'}``). This allows you to specify the ```imagePullSecrets`` on
            a pod basis. Typically, these will be provided through the service account, when needed,
            and you will not need to pass this argument. See:
            https://kubernetes.io/docs/concepts/containers/images/#specifying-imagepullsecrets-on-a-pod
            and https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.17/#podspec-v1-core
        service_account_name (Optional[str]): The name of the Kubernetes service account under which
            to run the Job. Defaults to "default"
        instance_config_map (str): The ``name`` of an existing Volume to mount into the pod in
            order to provide a ConfigMap for the Dagster instance. This Volume should contain a
            ``dagster.yaml`` with appropriate values for run storage, event log storage, etc.
        postgres_password_secret (str): The name of the Kubernetes Secret where the postgres
            password can be retrieved. Will be mounted and supplied as an environment variable to
            the Job Pod.
        env_config_maps (Optional[List[str]]): A list of custom ConfigMapEnvSource names from which to
            draw environment variables (using ``envFrom``) for the Job. Default: ``[]``. See:
        https://kubernetes.io/docs/tasks/inject-data-application/define-environment-variable-container/#define-an-environment-variable-for-a-container
        env_secrets (Optional[List[str]]): A list of custom Secret names from which to
            draw environment variables (using ``envFrom``) for the Job. Default: ``[]``. See:
        https://kubernetes.io/docs/tasks/inject-data-application/distribute-credentials-secure/#configure-all-key-value-pairs-in-a-secret-as-container-environment-variables

    '''

    def __new__(
        cls,
        job_image,
        dagster_home=None,
        image_pull_policy=None,
        image_pull_secrets=None,
        service_account_name=None,
        instance_config_map=None,
        postgres_password_secret=None,
        env_config_maps=None,
        env_secrets=None,
    ):
        return super(DagsterK8sJobConfig, cls).__new__(
            cls,
            job_image=check.str_param(job_image, 'job_image'),
            dagster_home=check.opt_str_param(
                dagster_home, 'dagster_home', default=DAGSTER_HOME_DEFAULT
            ),
            image_pull_policy=check.opt_str_param(image_pull_policy, 'image_pull_policy'),
            image_pull_secrets=check.opt_list_param(
                image_pull_secrets, 'image_pull_secrets', of_type=dict
            ),
            service_account_name=check.opt_str_param(service_account_name, 'service_account_name'),
            instance_config_map=check.str_param(instance_config_map, 'instance_config_map'),
            postgres_password_secret=check.str_param(
                postgres_password_secret, 'postgres_password_secret'
            ),
            env_config_maps=check.opt_list_param(env_config_maps, 'env_config_maps', of_type=str),
            env_secrets=check.opt_list_param(env_secrets, 'env_secrets', of_type=str),
        )

    @classmethod
    def config_type(cls):
        '''Combined config type which includes both run launcher and pipeline run config.
        '''
        cfg_run_launcher = DagsterK8sJobConfig.config_type_run_launcher()
        cfg_pipeline_run = DagsterK8sJobConfig.config_type_pipeline_run()
        return merge_dicts(cfg_run_launcher, cfg_pipeline_run)

    @classmethod
    def config_type_run_launcher(cls):
        '''Configuration intended to be set on the Dagster instance.
        '''
        return {
            'instance_config_map': Field(
                StringSource,
                is_required=True,
                description='The ``name`` of an existing Volume to mount into the pod in order to '
                'provide a ConfigMap for the Dagster instance. This Volume should contain a '
                '``dagster.yaml`` with appropriate values for run storage, event log storage, etc.',
            ),
            'postgres_password_secret': Field(
                StringSource,
                is_required=True,
                description='The name of the Kubernetes Secret where the postgres password can be '
                'retrieved. Will be mounted and supplied as an environment variable to the Job Pod.'
                'Secret must contain the key ``"postgresql-password"`` which will be exposed in '
                'the Job environment as the environment variable ``DAGSTER_PG_PASSWORD``.',
            ),
            'dagster_home': Field(
                StringSource,
                is_required=False,
                default_value=DAGSTER_HOME_DEFAULT,
                description='The location of DAGSTER_HOME in the Job container; this is where the '
                '``dagster.yaml`` file will be mounted from the instance ConfigMap specified here. '
                'Defaults to /opt/dagster/dagster_home.',
            ),
        }

    @classmethod
    def config_type_pipeline_run(cls):
        '''Configuration intended to be set at pipeline execution time.
        '''
        return {
            'job_image': Field(
                StringSource,
                is_required=True,
                description='Docker image to use for launched task Jobs '
                '(e.g. "mycompany.com/dagster-k8s-image:latest").',
            ),
            'image_pull_policy': Field(
                StringSource,
                is_required=False,
                default_value='IfNotPresent',
                description='Image pull policy to set on the launched task Job Pods. Defaults to '
                '"IfNotPresent".',
            ),
            'image_pull_secrets': Field(
                Array(Shape({'name': StringSource})),
                is_required=False,
                description='(Advanced) Specifies that Kubernetes should get the credentials from '
                'the Secrets named in this list.',
            ),
            'service_account_name': Field(
                Noneable(StringSource),
                is_required=False,
                description='(Advanced) Override the name of the Kubernetes service account under '
                'which to run the Job.',
            ),
            'env_config_maps': Field(
                Noneable(Array(StringSource)),
                is_required=False,
                description='A list of custom ConfigMapEnvSource names from which to draw '
                'environment variables (using ``envFrom``) for the Job. Default: ``[]``. See:'
                'https://kubernetes.io/docs/tasks/inject-data-application/define-environment-variable-container/#define-an-environment-variable-for-a-container',
            ),
            'env_secrets': Field(
                Noneable(Array(StringSource)),
                is_required=False,
                description='A list of custom Secret names from which to draw environment '
                'variables (using ``envFrom``) for the Job. Default: ``[]``. See:'
                'https://kubernetes.io/docs/tasks/inject-data-application/distribute-credentials-secure/#configure-all-key-value-pairs-in-a-secret-as-container-environment-variables',
            ),
        }

    @property
    def env_from_sources(self):
        '''This constructs a list of env_from sources. Along with a default base environment
        config map which we always load, the ConfigMaps and Secrets specified via
        env_config_maps and env_secrets will be pulled into the job construction here.
        '''
        config_maps = [
            kubernetes.client.V1EnvFromSource(
                config_map_ref=kubernetes.client.V1ConfigMapEnvSource(name=config_map)
            )
            for config_map in self.env_config_maps
        ]

        secrets = [
            kubernetes.client.V1EnvFromSource(
                secret_ref=kubernetes.client.V1SecretEnvSource(name=secret)
            )
            for secret in self.env_secrets
        ]

        return config_maps + secrets

    def to_dict(self):
        return self._asdict()

    @staticmethod
    def from_dict(config=None):
        check.opt_dict_param(config, 'config')
        return DagsterK8sJobConfig(**config)


def construct_dagster_graphql_k8s_job(
    job_config, args, job_name, resources=None, pod_name=None, component=None
):
    '''Constructs a Kubernetes Job object for a dagster-graphql invocation.

    Args:
        job_config (DagsterK8sJobConfig): Job configuration to use for constructing the Kubernetes
            Job object.
        args (List[str]): CLI arguments to use with dagster-graphql in this Job.
        job_name (str): The name of the Job. Note that this name must be <= 63 characters in length.
        resources (kubernetes.client.V1ResourceRequirements): The resource requirements for the
            container
        pod_name (str, optional): The name of the Pod. Note that this name must be <= 63 characters
            in length. Defaults to "<job_name>-pod".
        component (str, optional): The name of the component, used to provide the Job label
            app.kubernetes.io/component. Defaults to None.

    Returns:
        kubernetes.client.V1Job: A Kubernetes Job object.
    '''
    check.inst_param(job_config, 'job_config', DagsterK8sJobConfig)
    check.list_param(args, 'args', of_type=str)
    check.str_param(job_name, 'job_name')
    resources = check.opt_inst_param(
        resources, 'resources', kubernetes.client.V1ResourceRequirements
    )
    pod_name = check.opt_str_param(pod_name, 'pod_name', default=job_name + '-pod')
    check.opt_str_param(component, 'component')

    check.invariant(
        len(job_name) <= MAX_K8S_NAME_LEN,
        'job_name is %d in length; Kubernetes Jobs cannot be longer than %d characters.'
        % (len(job_name), MAX_K8S_NAME_LEN),
    )

    check.invariant(
        len(pod_name) <= MAX_K8S_NAME_LEN,
        'job_name is %d in length; Kubernetes Pods cannot be longer than %d characters.'
        % (len(pod_name), MAX_K8S_NAME_LEN),
    )

    # See: https://kubernetes.io/docs/concepts/overview/working-with-objects/common-labels/
    dagster_labels = {
        'app.kubernetes.io/name': 'dagster',
        'app.kubernetes.io/instance': 'dagster',
        'app.kubernetes.io/version': dagster_version,
        'app.kubernetes.io/part-of': 'dagster',
    }

    if component:
        dagster_labels['app.kubernetes.io/component'] = component

    job_container = kubernetes.client.V1Container(
        name=job_name,
        image=job_config.job_image,
        command=['dagster-graphql'],
        args=args,
        image_pull_policy=job_config.image_pull_policy,
        env=[
            kubernetes.client.V1EnvVar(name='DAGSTER_HOME', value=job_config.dagster_home),
            kubernetes.client.V1EnvVar(
                name=DAGSTER_PG_PASSWORD_ENV_VAR,
                value_from=kubernetes.client.V1EnvVarSource(
                    secret_key_ref=kubernetes.client.V1SecretKeySelector(
                        name=job_config.postgres_password_secret, key=DAGSTER_PG_PASSWORD_SECRET_KEY
                    )
                ),
            ),
        ],
        env_from=job_config.env_from_sources,
        resources=resources,
        volume_mounts=[
            kubernetes.client.V1VolumeMount(
                name='dagster-instance',
                mount_path='{dagster_home}/dagster.yaml'.format(
                    dagster_home=job_config.dagster_home
                ),
                sub_path='dagster.yaml',
            )
        ],
    )

    config_map_volume = kubernetes.client.V1Volume(
        name='dagster-instance',
        config_map=kubernetes.client.V1ConfigMapVolumeSource(name=job_config.instance_config_map),
    )

    template = kubernetes.client.V1PodTemplateSpec(
        metadata=kubernetes.client.V1ObjectMeta(name=pod_name, labels=dagster_labels),
        spec=kubernetes.client.V1PodSpec(
            image_pull_secrets=[
                kubernetes.client.V1LocalObjectReference(name=x['name'])
                for x in job_config.image_pull_secrets
            ],
            service_account_name=job_config.service_account_name,
            restart_policy='Never',
            containers=[job_container],
            volumes=[config_map_volume],
        ),
    )

    job = kubernetes.client.V1Job(
        api_version='batch/v1',
        kind='Job',
        metadata=kubernetes.client.V1ObjectMeta(name=job_name, labels=dagster_labels),
        spec=kubernetes.client.V1JobSpec(
            template=template,
            backoff_limit=K8S_JOB_BACKOFF_LIMIT,
            ttl_seconds_after_finished=K8S_JOB_TTL_SECONDS_AFTER_FINISHED,
        ),
    )
    return job
