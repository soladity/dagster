from dagster import Bool, Field, Noneable, StringSource, check
from dagster.cli.api import ExecuteRunArgs
from dagster.core.launcher import RunLauncher
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.serdes import ConfigurableClass, ConfigurableClassData, serialize_dagster_namedtuple

from .client import ECSClient


class ECSRunLauncher(RunLauncher, ConfigurableClass):
    """
    This class is the RunLauncher for ECS tasks

    Args:
        key_id (Optional[str]): the AWS access key ID to use
        access_key (Optional[str]): the AWS access key going with that key_id
        family (Optional[str]): what task family you want this task revising
        containername (Optional[str]):  what you want the container the task is on to be called
        imagename (Optional[str]): the URI for the docker image
        memory (Optional[str]): how much memory (in MB) the task needs
        cpu (Optional[str]): how much CPU (in vCPU) the task needs
        inst_data (Optional[ConfigurableClassData]): any data specific to the instance
        region_name (Optional[str]):  which AWS region you're running on
        launch_type (Optional[str]): whether to use EC2 or FARGATE for the task
        grab_logs (Optional[Bool]): Whether to grab logs from ECS


    TODO:  get logs from ECSclient into event log storage
    """

    def __init__(
        self,
        inst_data,
        key_id,
        access_key,
        family,
        containername,
        imagename,
        memory,
        cpu,
        region_name,
        launch_type,
        grab_logs,
    ):
        self._inst_data = check.opt_inst_param(inst_data, "inst_data", ConfigurableClassData)
        self.run_id_to_task_offset = dict()
        self.client = ECSClient(
            region_name=region_name,
            key_id=key_id,
            access_key=access_key,
            launch_type=launch_type,
            grab_logs=grab_logs,
        )
        self.client.set_and_register_task(
            [],
            ["dagster"],
            family=family,
            containername=containername,
            imagename=imagename,
            memory=memory,
            cpu=cpu,
        )

    @classmethod
    def config_type(cls):
        return {
            "key_id": Field(
                Noneable(StringSource),
                is_required=False,
                default_value=None,
                description="the AWS access key ID to use, overriding environment vars",
            ),
            "access_key": Field(
                Noneable(StringSource),
                is_required=False,
                default_value=None,
                description="the AWS access key to use, overriding environment vars",
            ),
            "family": Field(
                StringSource,
                is_required=False,
                default_value="dagstertask",
                description="what family of tasks you want to be revising",
            ),
            "containername": Field(
                StringSource,
                is_required=False,
                default_value="dagstercontainer",
                description="what you want the docker container running the tasks to be called",
            ),
            "imagename": Field(
                StringSource,
                is_required=False,
                default_value="httpd:2.4",
                description="the URI for the docker image of the container",
            ),
            "memory": Field(
                StringSource,
                is_required=False,
                default_value="512",
                description="the memory in MB that the task will need",
            ),
            "cpu": Field(
                StringSource,
                is_required=False,
                default_value="256",
                description="the CPU in VCPU that the task will need",
            ),
            "region_name": Field(
                StringSource,
                is_required=False,
                default_value="us-east-2",
                description="which region the AWS cluster is on",
            ),
            "launch_type": Field(
                StringSource,
                is_required=False,
                default_value="FARGATE",
                description="whether to use EC2 or FARGATE for running the task -- currently only Fargate is supported",
            ),
            "grab_logs": Field(
                Bool,
                is_required=False,
                default_value=True,
                description="whether to pull down ECS logs for completed tasks",
            ),
        }

    @classmethod
    def from_config_value(cls, inst_data, config_value):
        return cls(inst_data=inst_data, **config_value)

    @property
    def inst_data(self):
        return self._inst_data

    def launch_run(self, instance, run, external_pipeline):
        check.inst_param(run, "run", PipelineRun)
        input_json = serialize_dagster_namedtuple(
            ExecuteRunArgs(
                pipeline_origin=external_pipeline.get_origin(),
                pipeline_run_id=run.run_id,
                instance_ref=instance.get_ref(),
            )
        )
        # this maps run configuration to task overrides
        # this way we can pass in parameters from the dagit configuration that user has entered in the UI
        overrides = self.generate_task_overrides(run)
        self.client.run_task(
            command=["api", "execute_run_with_structured_logs", input_json], overrides=overrides,
        )
        self.run_id_to_task_offset[run.run_id] = self.client.offset

    def generate_task_overrides(self, run):
        return {
            "containerOverrides": [
                {
                    "name": self.client.container_name,
                    "environment": [
                        {"name": "PIPELINE", "value": run.pipeline_name},
                        # possibly pull from run.run_config['solids'] other data that user might entered in the UI
                    ],
                },
            ],
        }

    def can_terminate(self, run_id):
        check.str_param(run_id, "run_id")
        return False

    def terminate(self, run_id):
        check.str_param(run_id, "run_id")
        check.not_implemented("Termination not yet implemented")
