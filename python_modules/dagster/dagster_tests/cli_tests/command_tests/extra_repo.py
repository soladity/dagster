from dagster import job, lambda_solid, pipeline, repository


@lambda_solid
def do_something():
    return 1


@pipeline(name="extra")
def extra_pipeline():
    do_something()


@job
def extra_job():
    do_something()


@repository
def extra():
    return {"pipelines": {"extra": extra_pipeline}, "jobs": {"extra_job": extra_job}}
