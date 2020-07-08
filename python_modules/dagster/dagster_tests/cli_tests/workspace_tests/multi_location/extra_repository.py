from dagster import pipeline, repository, solid


@solid
def extra_solid(_):
    pass


@pipeline
def extra_pipeline():
    extra_solid()


@repository
def extra_repository():
    return [extra_pipeline]
