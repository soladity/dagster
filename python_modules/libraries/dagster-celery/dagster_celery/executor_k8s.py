from dagster import Field, Noneable, StringSource, check
from dagster.core.definitions.executor import check_cross_process_constraints, executor
from dagster.core.execution.retries import Retries
from dagster.core.host_representation.handle import IN_PROCESS_NAME
from dagster.utils import merge_dicts

from .config import CeleryK8sJobConfig
from .executor import CELERY_CONFIG

CELERY_K8S_CONFIG_KEY = 'celery-k8s'


def celery_k8s_config():
    from dagster_k8s import DagsterK8sJobConfig

    # DagsterK8sJobConfig provides config schema for specifying Dagster K8s Jobs
    job_config = DagsterK8sJobConfig.config_type_pipeline_run()

    additional_config = {
        'load_incluster_config': Field(
            bool,
            is_required=False,
            default_value=True,
            description='''Set this value if you are running the launcher within a k8s cluster. If
            ``True``, we assume the launcher is running within the target cluster and load config
            using ``kubernetes.config.load_incluster_config``. Otherwise, we will use the k8s config
            specified in ``kubeconfig_file`` (using ``kubernetes.config.load_kube_config``) or fall
            back to the default kubeconfig. Default: ``True``.''',
        ),
        'kubeconfig_file': Field(
            Noneable(str),
            is_required=False,
            description='Path to a kubeconfig file to use, if not using default kubeconfig.',
        ),
        'job_namespace': Field(
            StringSource,
            is_required=False,
            default_value='default',
            description='The namespace into which to launch new jobs. Note that any '
            'other Kubernetes resources the Job requires (such as the service account) must be '
            'present in this namespace. Default: ``"default"``',
        ),
        'repo_location_name': Field(
            StringSource,
            is_required=False,
            default_value=IN_PROCESS_NAME,
            description='The repository location name to use for execution.',
        ),
    }

    cfg = merge_dicts(CELERY_CONFIG, job_config)
    cfg = merge_dicts(cfg, additional_config)
    return cfg


@executor(name=CELERY_K8S_CONFIG_KEY, config=celery_k8s_config())
def celery_k8s_job_executor(init_context):
    '''Celery-based executor which launches tasks as Kubernetes Jobs.

    The Celery executor exposes config settings for the underlying Celery app under
    the ``config_source`` key. This config corresponds to the "new lowercase settings" introduced
    in Celery version 4.0 and the object constructed from config will be passed to the
    :py:class:`celery.Celery` constructor as its ``config_source`` argument.
    (See https://docs.celeryproject.org/en/latest/userguide/configuration.html for details.)

    The executor also exposes the ``broker``, `backend`, and ``include`` arguments to the
    :py:class:`celery.Celery` constructor.

    In the most common case, you may want to modify the ``broker`` and ``backend`` (e.g., to use
    Redis instead of RabbitMQ). We expect that ``config_source`` will be less frequently
    modified, but that when solid executions are especially fast or slow, or when there are
    different requirements around idempotence or retry, it may make sense to execute pipelines
    with variations on these settings.

    If you'd like to configure a Celery Kubernetes Job executor in addition to the
    :py:class:`~dagster.default_executors`, you should add it to the ``executor_defs`` defined on a
    :py:class:`~dagster.ModeDefinition` as follows:

    .. code-block:: python

        from dagster import ModeDefinition, default_executors, pipeline
        from dagster_celery.executor_k8s import celery_k8s_job_executor

        @pipeline(mode_defs=[
            ModeDefinition(executor_defs=default_executors + [celery_k8s_job_executor])
        ])
        def celery_enabled_pipeline():
            pass

    Then you can configure the executor as follows:

    .. code-block:: YAML

        execution:
          celery-k8s:
            config:
              job_image: 'my_repo.com/image_name:latest'
              job_namespace: 'some-namespace'
              broker: 'pyamqp://guest@localhost//'  # Optional[str]: The URL of the Celery broker
              backend: 'rpc://' # Optional[str]: The URL of the Celery results backend
              include: ['my_module'] # Optional[List[str]]: Modules every worker should import
              config_source: # Dict[str, Any]: Any additional parameters to pass to the
                  #...       # Celery workers. This dict will be passed as the `config_source`
                  #...       # argument of celery.Celery().

    Note that the YAML you provide here must align with the configuration with which the Celery
    workers on which you hope to run were started. If, for example, you point the executor at a
    different broker than the one your workers are listening to, the workers will never be able to
    pick up tasks for execution.
    '''
    from dagster_k8s import DagsterK8sJobConfig, CeleryK8sRunLauncher

    check_cross_process_constraints(init_context)

    run_launcher = init_context.instance.run_launcher
    exc_cfg = init_context.executor_config

    check.inst(
        run_launcher,
        CeleryK8sRunLauncher,
        'This engine is only compatible with a CeleryK8sRunLauncher; configure the '
        'CeleryK8sRunLauncher on your instance to use it.',
    )

    job_config = DagsterK8sJobConfig(
        dagster_home=run_launcher.dagster_home,
        instance_config_map=run_launcher.instance_config_map,
        postgres_password_secret=run_launcher.postgres_password_secret,
        job_image=exc_cfg.get('job_image'),
        image_pull_policy=exc_cfg.get('image_pull_policy'),
        image_pull_secrets=exc_cfg.get('image_pull_secrets'),
        service_account_name=exc_cfg.get('service_account_name'),
        env_config_maps=exc_cfg.get('env_config_maps'),
        env_secrets=exc_cfg.get('env_secrets'),
    )

    # Set on the instance but overrideable here
    broker = run_launcher.broker or exc_cfg.get('broker')
    backend = run_launcher.backend or exc_cfg.get('backend')
    config_source = run_launcher.config_source or exc_cfg.get('config_source')
    include = run_launcher.include or exc_cfg.get('include')
    retries = run_launcher.retries or Retries.from_config(exc_cfg.get('retries'))

    return CeleryK8sJobConfig(
        broker=broker,
        backend=backend,
        config_source=config_source,
        include=include,
        retries=retries,
        job_config=job_config,
        job_namespace=exc_cfg.get('job_namespace'),
        load_incluster_config=exc_cfg.get('load_incluster_config'),
        kubeconfig_file=exc_cfg.get('kubeconfig_file'),
        repo_location_name=exc_cfg.get('repo_location_name'),
    )
