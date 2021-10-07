"""isort:skip_file"""

# start_pipeline_marker

from dagster import job, op


@op
def get_name():
    return "dagster"


@op
def hello(context, name: str):
    context.log.info(f"Hello, {name}!")


@job
def hello_dagster():
    hello(get_name())


# end_pipeline_marker


# start_execute_marker
if __name__ == "__main__":
    result = hello_dagster.execute_in_process()

# end_execute_marker
