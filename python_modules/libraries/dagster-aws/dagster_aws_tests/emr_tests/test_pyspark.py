import os
import subprocess
import sys

import pytest
from dagster_aws.emr import EmrJobRunner
from dagster_aws.emr.pyspark_step_launcher import emr_pyspark_step_launcher
from dagster_aws.s3 import s3_plus_default_storage_defs, s3_resource
from dagster_pyspark import DataFrame, pyspark_resource
from moto import mock_emr
from pyspark.sql import Row
from pyspark.sql.types import IntegerType, StringType, StructField, StructType

from dagster import (
    InputDefinition,
    ModeDefinition,
    OutputDefinition,
    execute_pipeline,
    pipeline,
    reconstructable,
    solid,
)
from dagster.core.definitions.no_step_launcher import no_step_launcher
from dagster.core.errors import DagsterSubprocessError
from dagster.seven import mock
from dagster.utils.merger import deep_merge_dicts
from dagster.utils.test import create_test_pipeline_execution_context

S3_BUCKET = "dagster-scratch-80542c2"

BASE_EMR_PYSPARK_STEP_LAUNCHER_CONFIG = {
    "local_pipeline_package_path": os.path.abspath(os.path.dirname(__file__)),
    "cluster_id": os.environ.get("EMR_CLUSTER_ID"),
    "staging_bucket": S3_BUCKET,
    "region_name": "us-west-1",
    "deploy_local_pipeline_package": True,
}


@solid(
    output_defs=[OutputDefinition(DataFrame)],
    required_resource_keys={"pyspark_step_launcher", "pyspark"},
)
def make_df_solid(context):
    schema = StructType([StructField("name", StringType()), StructField("age", IntegerType())])
    rows = [Row(name="John", age=19), Row(name="Jennifer", age=29), Row(name="Henry", age=50)]
    return context.resources.pyspark.spark_session.createDataFrame(rows, schema)


@solid(
    name="blah",
    description="this is a test",
    config_schema={"foo": str, "bar": int},
    input_defs=[InputDefinition("people", DataFrame)],
    output_defs=[OutputDefinition(DataFrame)],
    required_resource_keys={"pyspark_step_launcher"},
)
def filter_df_solid(_, people):
    return people.filter(people["age"] < 30)


MODE_DEFS = [
    ModeDefinition(
        "prod",
        resource_defs={
            "pyspark_step_launcher": emr_pyspark_step_launcher,
            "pyspark": pyspark_resource,
            "s3": s3_resource,
        },
        system_storage_defs=s3_plus_default_storage_defs,
    ),
    ModeDefinition(
        "local",
        resource_defs={"pyspark_step_launcher": no_step_launcher, "pyspark": pyspark_resource},
    ),
]


@pipeline(mode_defs=MODE_DEFS)
def pyspark_pipe():
    filter_df_solid(make_df_solid())


def define_pyspark_pipe():
    return pyspark_pipe


@solid(
    output_defs=[OutputDefinition(DataFrame)],
    required_resource_keys={"pyspark_step_launcher", "pyspark"},
)
def do_nothing_solid(_):
    pass


@pipeline(mode_defs=MODE_DEFS)
def do_nothing_pipe():
    do_nothing_solid()


def define_do_nothing_pipe():
    return do_nothing_pipe


def test_local():
    result = execute_pipeline(
        pipeline=pyspark_pipe,
        mode="local",
        run_config={"solids": {"blah": {"config": {"foo": "a string", "bar": 123}}}},
    )
    assert result.success


@mock_emr
@mock.patch("dagster_aws.emr.emr.EmrJobRunner.is_emr_step_complete")
def test_pyspark_emr(mock_is_emr_step_complete):
    run_job_flow_args = dict(
        Instances={
            "InstanceCount": 1,
            "KeepJobFlowAliveWhenNoSteps": True,
            "MasterInstanceType": "c3.medium",
            "Placement": {"AvailabilityZone": "us-west-1a"},
            "SlaveInstanceType": "c3.xlarge",
        },
        JobFlowRole="EMR_EC2_DefaultRole",
        LogUri="s3://mybucket/log",
        Name="cluster",
        ServiceRole="EMR_DefaultRole",
        VisibleToAllUsers=True,
    )

    # Doing cluster setup outside of a solid here, because run_job_flow is not yet plumbed through
    # to the pyspark EMR resource.
    job_runner = EmrJobRunner(region="us-west-1")
    context = create_test_pipeline_execution_context()
    cluster_id = job_runner.run_job_flow(context.log, run_job_flow_args)

    result = execute_pipeline(
        pipeline=reconstructable(define_do_nothing_pipe),
        mode="prod",
        run_config={
            "resources": {
                "pyspark_step_launcher": {
                    "config": deep_merge_dicts(
                        BASE_EMR_PYSPARK_STEP_LAUNCHER_CONFIG, {"cluster_id": cluster_id}
                    ),
                }
            },
        },
    )
    assert result.success
    assert mock_is_emr_step_complete.called


def sync_code():
    # Sync remote dagster packages with local dagster code
    sync_code_command = [
        "rsync",
        "-av",
        "-progress",
        "--exclude='scala_modules/'",
        "--exclude='js_modules/'",
        "--exclude='.git/'",
        "--exclude='docs/'",
        "-e",
        '"ssh -i {aws_emr_pem_file}"'.format(aws_emr_pem_file=os.environ["AWS_EMR_PEM_FILE"]),
        os.environ["DAGSTER_DIR"],
        os.environ["AWS_EMR_NODE_ADDRESS"] + ":~/",
    ]
    if (
        subprocess.call(
            " ".join(sync_code_command), stdout=sys.stdout, stderr=sys.stderr, shell=True
        )
        != 0
    ):
        raise DagsterSubprocessError("Failed to sync code to EMR")

    # Install dagster packages on remote node
    remote_install_dagster_packages_command = ["sudo", "python3", "-m", "pip", "install"] + [
        token
        for package_subpath in ["dagster", "libraries/dagster-pyspark"]
        for token in ["-e", "/home/hadoop/dagster/python_modules/" + package_subpath]
    ]

    install_dagster_packages_command = [
        "ssh",
        "-i",
        os.environ["AWS_EMR_PEM_FILE"],
        os.environ["AWS_EMR_NODE_ADDRESS"],
        "'" + " ".join(remote_install_dagster_packages_command) + "'",
    ]
    if (
        subprocess.call(
            " ".join(install_dagster_packages_command),
            stdout=sys.stdout,
            stderr=sys.stderr,
            shell=True,
        )
        != 0
    ):
        raise DagsterSubprocessError("Failed to install dagster packages on EMR")


@pytest.mark.skipif(
    "AWS_EMR_TEST_DO_IT_LIVE" not in os.environ,
    reason="This test is slow and requires a live EMR cluster; run only upon explicit request",
)
def test_do_it_live_emr():
    sync_code()

    result = execute_pipeline(
        reconstructable(define_pyspark_pipe),
        mode="prod",
        run_config={
            "solids": {"blah": {"config": {"foo": "a string", "bar": 123}}},
            "resources": {
                "pyspark_step_launcher": {"config": BASE_EMR_PYSPARK_STEP_LAUNCHER_CONFIG},
            },
            "storage": {"s3": {"config": {"s3_bucket": S3_BUCKET, "s3_prefix": "test_pyspark"}}},
        },
    )
    assert result.success
