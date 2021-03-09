from dagster import ModeDefinition, default_executors, fs_io_manager, pipeline, solid
from dagster_dask import dask_executor


@solid
def hello_world(_):
    return "Hello, World!"


@pipeline(
    mode_defs=[
        ModeDefinition(
            resource_defs={"io_manager": fs_io_manager},
            executor_defs=default_executors + [dask_executor],
        )
    ]
)
def dask_pipeline():
    return hello_world()
