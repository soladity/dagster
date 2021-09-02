import json
import os

import docker
from dagster import Array, Field, Permissive, StringSource, check
from dagster.core.launcher.base import LaunchRunContext, RunLauncher
from dagster.core.storage.tags import DOCKER_IMAGE_TAG
from dagster.grpc.types import ExecuteRunArgs
from dagster.serdes import ConfigurableClass, serialize_dagster_namedtuple
from docker_image import reference

DOCKER_CONTAINER_ID_TAG = "docker/container_id"


class DockerRunLauncher(RunLauncher, ConfigurableClass):
    """Launches runs in a Docker container.

    Args:
        image (Optional[str]): The docker image to be used if the repository does not specify one.
        registry (Optional[Dict[str, str]]): Information for using a non-local docker registry.
            If set, should include ``url``, ``username``, and ``password`` keys.
        env_vars (Optional[List[str]]): The list of environment variables names to forward to the
            docker container.
        network (Optional[str]): Name of the network this container to which to connect the
            launched container at creation time. DEPRECATED, prefer networks
        networks (Optional[List[str]]): List of networks to which to connect the
            launched container at creation time.
        container_kwargs(Optional[Dict[str, Any]]): Additional kwargs to pass into
            containers.create. See https://docker-py.readthedocs.io/en/stable/containers.html
            for the full list of available options.
    """

    def __init__(
        self,
        inst_data=None,
        image=None,
        registry=None,
        env_vars=None,
        network=None,
        networks=None,
        container_kwargs=None,
    ):
        self._inst_data = inst_data
        self._image = image
        self._registry = registry
        self._env_vars = env_vars
        if network:
            check.invariant(not networks, "cannot set both `network` and `networks`")
            self._networks = [network]
        elif networks:
            self._networks = networks
        else:
            self._networks = []

        self._container_kwargs = check.opt_dict_param(
            container_kwargs, "container_kwargs", key_type=str
        )

        if "image" in self._container_kwargs:
            raise Exception(
                "'image' cannot be used in 'container_kwargs'. Use the 'image' config key instead."
            )

        if "environment" in self._container_kwargs and env_vars:
            raise Exception(
                "Cannot specify both `env_vars` in DockerRunLauncher config and `environment` in `container_kwargs`. Choose one or the other."
            )

        if "network" in self._container_kwargs and self._networks:
            raise Exception(
                "Cannot specify both `networks` in DockerRunLauncher config and `network` in `container_kwargs`. Choose one or the other."
            )

        super().__init__()

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return {
            "image": Field(
                StringSource,
                is_required=False,
                description="The docker image to be used if the repository does not specify one.",
            ),
            "registry": Field(
                {
                    "url": Field(StringSource),
                    "username": Field(StringSource),
                    "password": Field(StringSource),
                },
                is_required=False,
                description="Information for using a non local/public docker registry",
            ),
            "env_vars": Field(
                [str],
                is_required=False,
                description="The list of environment variables names to forward to the docker container",
            ),
            "network": Field(
                StringSource,
                is_required=False,
                description="Name of the network to which to connect the launched container at creation time",
            ),
            "networks": Field(
                Array(StringSource),
                is_required=False,
                description="Names of the networks to which to connect the launched container at creation time",
            ),
            "container_kwargs": Field(
                Permissive(),
                is_required=False,
                description="key-value pairs that can be passed into containers.create. See "
                "https://docker-py.readthedocs.io/en/stable/containers.html for the full list "
                "of available options.",
            ),
        }

    @staticmethod
    def from_config_value(inst_data, config_value):
        return DockerRunLauncher(inst_data=inst_data, **config_value)

    def _get_client(self):
        client = docker.client.from_env()
        if self._registry:
            client.login(
                registry=self._registry["url"],
                username=self._registry["username"],
                password=self._registry["password"],
            )
        return client

    def launch_run(self, context: LaunchRunContext) -> None:

        run = context.pipeline_run

        pipeline_code_origin = context.pipeline_code_origin

        docker_image = pipeline_code_origin.repository_origin.container_image

        if not docker_image:
            docker_image = self._image

        if not docker_image:
            raise Exception("No docker image specified by the instance config or repository")

        try:
            # validate that the docker image name is valid
            reference.Reference.parse(docker_image)
        except Exception as e:
            raise Exception(
                "Docker image name {docker_image} is not correctly formatted".format(
                    docker_image=docker_image
                )
            ) from e

        input_json = serialize_dagster_namedtuple(
            ExecuteRunArgs(
                pipeline_origin=pipeline_code_origin,
                pipeline_run_id=run.run_id,
                instance_ref=self._instance.get_ref(),
            )
        )

        command = "dagster api execute_run {}".format(json.dumps(input_json))

        docker_env = (
            {env_name: os.getenv(env_name) for env_name in self._env_vars} if self._env_vars else {}
        )

        client = self._get_client()

        try:
            container = client.containers.create(
                image=docker_image,
                command=command,
                detach=True,
                environment=docker_env,
                network=self._networks[0] if len(self._networks) else None,
                **self._container_kwargs,
            )

        except docker.errors.ImageNotFound:
            client.images.pull(docker_image)
            container = client.containers.create(
                image=docker_image,
                command=command,
                detach=True,
                environment=docker_env,
                network=self._networks[0] if len(self._networks) else None,
                **self._container_kwargs,
            )

        if len(self._networks) > 1:
            for network_name in self._networks[1:]:
                network = client.networks.get(network_name)
                network.connect(container)

        self._instance.report_engine_event(
            message="Launching run in a new container {container_id} with image {docker_image}".format(
                container_id=container.id,
                docker_image=docker_image,
            ),
            pipeline_run=run,
            cls=self.__class__,
        )

        self._instance.add_run_tags(
            run.run_id,
            {DOCKER_CONTAINER_ID_TAG: container.id, DOCKER_IMAGE_TAG: docker_image},
        )

        container.start()

    def _get_container(self, run):
        if not run or run.is_finished:
            return None

        container_id = run.tags.get(DOCKER_CONTAINER_ID_TAG)

        if not container_id:
            return None

        try:
            return self._get_client().containers.get(container_id)
        except Exception:  # pylint: disable=broad-except
            return None

    def can_terminate(self, run_id):
        run = self._instance.get_run_by_id(run_id)
        return self._get_container(run) != None

    def terminate(self, run_id):
        run = self._instance.get_run_by_id(run_id)
        container = self._get_container(run)

        if not container:
            self._instance.report_engine_event(
                message="Unable to get docker container to send termination request to.",
                pipeline_run=run,
                cls=self.__class__,
            )
            return False

        self._instance.report_run_canceling(run)

        container.stop()

        return True
