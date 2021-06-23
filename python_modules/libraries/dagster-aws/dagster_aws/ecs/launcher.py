import os
from dataclasses import dataclass
from typing import Any, Dict, List

import boto3
import requests
from dagster.core.launcher.base import RunLauncher
from dagster.grpc.types import ExecuteRunArgs
from dagster.serdes import ConfigurableClass, serialize_dagster_namedtuple
from dagster.utils.backcompat import experimental


@dataclass
class TaskMetadata:
    cluster: str
    subnets: List[str]
    security_groups: List[str]
    task_definition: Dict[str, Any]
    container_definition: Dict[str, Any]


@experimental
class EcsRunLauncher(RunLauncher, ConfigurableClass):
    def __init__(self, inst_data=None, boto3_client=boto3.client("ecs")):

        self._inst_data = inst_data
        self.ecs = boto3_client
        self.ec2 = boto3.resource("ec2")

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return {}

    @staticmethod
    def from_config_value(inst_data, config_value):
        return EcsRunLauncher(inst_data=inst_data, **config_value)

    def _ecs_tags(self, run_id):
        return [{"key": "dagster/run_id", "value": run_id}]

    def _run_tags(self, task_arn):
        cluster = self._task_metadata().cluster
        return {"ecs/task_arn": task_arn, "ecs/cluster": cluster}

    def launch_run(self, run, external_pipeline):
        """
        Launch a run in an ECS task.

        Currently, Fargate is the only supported launchType and awsvpc is the
        only supported networkMode. These are the defaults that are set up by
        docker-compose when you use the Dagster ECS reference deployment.

        This method creates a new task definition revision for every run.
        First, the process that calls this method finds its own task
        definition. Next, it creates a new task definition based on its own
        with several important overrides:

        1. The command is replaced with a call to `dagster api execute_run`
        2. The image is overridden with the pipeline's origin's image.
        """
        metadata = self._task_metadata()
        pipeline_origin = external_pipeline.get_python_origin()
        image = pipeline_origin.repository_origin.container_image

        input_json = serialize_dagster_namedtuple(
            ExecuteRunArgs(
                pipeline_origin=pipeline_origin,
                pipeline_run_id=run.run_id,
                instance_ref=self._instance.get_ref(),
            )
        )
        command = ["dagster", "api", "execute_run", input_json]

        # Start with the current processes's tasks's definition but remove extra
        # keys that aren't useful for creating a new task definition (status,
        # revision, etc.)
        expected_keys = [
            key
            for key in self.ecs.meta.service_model.shape_for(
                "RegisterTaskDefinitionRequest"
            ).members
        ]
        task_definition = dict(
            (key, metadata.task_definition[key])
            for key in expected_keys
            if key in metadata.task_definition.keys()
        )

        # The current process might not be running in a container that has the
        # pipeline's code installed. Inherit most of the processes's container
        # definition (things like environment, dependencies, etc.) but replace
        # the image with the pipeline origin's image and give it a new name.
        # TODO: Configurable task definitions
        container_definitions = task_definition["containerDefinitions"]
        container_definitions.remove(metadata.container_definition)
        container_definitions.append(
            {**metadata.container_definition, "name": "run", "image": image}
        )
        task_definition = {
            **task_definition,
            "family": "dagster-run",
            "containerDefinitions": container_definitions,
        }

        # Register the task overridden task definition as a revision to the
        # "dagster-run" family.
        # TODO: Only register the task definition if a matching one doesn't
        # already exist. Otherwise, we risk exhausting the revisions limit
        # (1,000,000 per family) with unnecessary revisions:
        # https://docs.aws.amazon.com/AmazonECS/latest/developerguide/service-quotas.html
        self.ecs.register_task_definition(**task_definition)

        # Run a task using the new task definition and the same network
        # configuration as this processes's task.
        response = self.ecs.run_task(
            taskDefinition=task_definition["family"],
            cluster=metadata.cluster,
            overrides={"containerOverrides": [{"name": "run", "command": command}]},
            networkConfiguration={
                "awsvpcConfiguration": {
                    "subnets": metadata.subnets,
                    "assignPublicIp": "ENABLED",
                    "securityGroups": metadata.security_groups,
                }
            },
            launchType="FARGATE",
        )

        arn = response["tasks"][0]["taskArn"]
        self._instance.add_run_tags(run.run_id, self._run_tags(task_arn=arn))
        self.ecs.tag_resource(resourceArn=arn, tags=self._ecs_tags(run.run_id))
        self._instance.report_engine_event(
            message=f"Launching run in task {arn} on cluster {metadata.cluster}",
            pipeline_run=run,
            cls=self.__class__,
        )

        return run.run_id

    def can_terminate(self, run_id):
        arn = self._instance.get_run_by_id(run_id).tags.get("ecs/task_arn")
        if arn:
            cluster = self._task_metadata().cluster
            status = self.ecs.describe_tasks(tasks=[arn], cluster=cluster)["tasks"][0]["lastStatus"]
            if status != "STOPPED":
                return True

        return False

    def terminate(self, run_id):
        cluster = self._task_metadata().cluster
        arn = self._instance.get_run_by_id(run_id).tags.get("ecs/task_arn")
        status = self.ecs.describe_tasks(tasks=[arn], cluster=cluster)["tasks"][0]["lastStatus"]
        if status == "STOPPED":
            return False

        self.ecs.stop_task(task=arn, cluster=cluster)
        return True

    def _task_metadata(self):
        """
        ECS injects an environment variable into each Fargate task. The value
        of this environment variable is a url that can be queried to introspect
        information about the current processes's running task:

        https://docs.aws.amazon.com/AmazonECS/latest/userguide/task-metadata-endpoint-v4-fargate.html
        """
        container_metadata_uri = os.environ.get("ECS_CONTAINER_METADATA_URI_V4")
        name = requests.get(container_metadata_uri).json()["Name"]

        task_metadata_uri = container_metadata_uri + "/task"
        response = requests.get(task_metadata_uri).json()
        cluster = response.get("Cluster")
        task_arn = response.get("TaskARN")

        task = self.ecs.describe_tasks(tasks=[task_arn], cluster=cluster)["tasks"][0]
        enis = []
        subnets = []
        for attachment in task["attachments"]:
            if attachment["type"] == "ElasticNetworkInterface":
                for detail in attachment["details"]:
                    if detail["name"] == "subnetId":
                        subnets.append(detail["value"])
                    if detail["name"] == "networkInterfaceId":
                        enis.append(self.ec2.NetworkInterface(detail["value"]))

        security_groups = []
        for eni in enis:
            for group in eni.groups:
                security_groups.append(group["GroupId"])

        task_definition_arn = task["taskDefinitionArn"]
        task_definition = self.ecs.describe_task_definition(taskDefinition=task_definition_arn)[
            "taskDefinition"
        ]

        container_definition = next(
            iter(
                [
                    container
                    for container in task_definition["containerDefinitions"]
                    if container["name"] == name
                ]
            )
        )

        return TaskMetadata(
            cluster=cluster,
            subnets=subnets,
            security_groups=security_groups,
            task_definition=task_definition,
            container_definition=container_definition,
        )
