import string

from dagster import (
    InputDefinition,
    Int,
    OutputDefinition,
    PartitionSetDefinition,
    ScheduleDefinition,
    lambda_solid,
    pipeline,
    repository,
    solid,
    usable_as_dagster_type,
)
from dagster.core.definitions.decorators import triggered_execution


@lambda_solid
def do_something():
    return 1


@lambda_solid
def do_input(x):
    return x


@pipeline(name="foo")
def foo_pipeline():
    do_input(do_something())


@pipeline(name="baz", description="Not much tbh")
def baz_pipeline():
    do_input()


def define_foo_pipeline():
    return foo_pipeline


@pipeline(name="bar")
def bar_pipeline():
    @usable_as_dagster_type(name="InputTypeWithoutHydration")
    class InputTypeWithoutHydration(int):
        pass

    @solid(output_defs=[OutputDefinition(InputTypeWithoutHydration)])
    def one(_):
        return 1

    @solid(
        input_defs=[InputDefinition("some_input", InputTypeWithoutHydration)],
        output_defs=[OutputDefinition(Int)],
    )
    def fail_subset(_, some_input):
        return some_input

    return fail_subset(one())


def define_bar_schedules():
    return {
        "foo_schedule": ScheduleDefinition(
            "foo_schedule",
            cron_schedule="* * * * *",
            pipeline_name="test_pipeline",
            run_config={"fizz": "buzz"},
        ),
        "foo_schedule_never_execute": ScheduleDefinition(
            "foo_schedule_never_execute",
            cron_schedule="* * * * *",
            pipeline_name="test_pipeline",
            run_config={"fizz": "buzz"},
            should_execute=lambda _context: False,
        ),
    }


def error_partition_fn():
    raise Exception("womp womp")


def error_partition_config_fn():
    raise Exception("womp womp")


def error_partition_tags_fn(_partition):
    raise Exception("womp womp")


def define_baz_partitions():
    return {
        "baz_partitions": PartitionSetDefinition(
            name="baz_partitions",
            pipeline_name="baz",
            partition_fn=lambda: string.ascii_lowercase,
            run_config_fn_for_partition=lambda partition: {
                "solids": {"do_input": {"inputs": {"x": {"value": partition.value}}}}
            },
            tags_fn_for_partition=lambda _partition: {"foo": "bar"},
        ),
        "error_partitions": PartitionSetDefinition(
            name="error_partitions",
            pipeline_name="baz",
            partition_fn=error_partition_fn,
            run_config_fn_for_partition=lambda partition: {},
        ),
        "error_partition_config": PartitionSetDefinition(
            name="error_partition_config",
            pipeline_name="baz",
            partition_fn=lambda: string.ascii_lowercase,
            run_config_fn_for_partition=error_partition_config_fn,
        ),
        "error_partition_tags": PartitionSetDefinition(
            name="error_partition_tags",
            pipeline_name="baz",
            partition_fn=lambda: string.ascii_lowercase,
            run_config_fn_for_partition=lambda partition: {},
            tags_fn_for_partition=error_partition_tags_fn,
        ),
    }


@triggered_execution(pipeline_name="foo_pipeline")
def triggered_foo(_):
    return {"foo": "FOO"}


@triggered_execution(pipeline_name="baz_pipeline")
def triggered_error(_):
    raise Exception("womp womp")


@repository
def bar_repo():
    return {
        "pipelines": {
            "foo": define_foo_pipeline,
            "bar": lambda: bar_pipeline,
            "baz": lambda: baz_pipeline,
        },
        "schedules": define_bar_schedules(),
        "partition_sets": define_baz_partitions(),
        "triggered_executions": {
            "triggered_foo": triggered_foo,
            "triggered_error": lambda: triggered_error,
        },
    }
