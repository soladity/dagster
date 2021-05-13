from dagster import pipeline, schedule

# start_marker_priority


@pipeline(tags={"dagster/priority": "3"})
def important_pipeline():
    ...


@schedule(
    cron_schedule="* * * * *",
    pipeline_name="my_pipeline",
    execution_timezone="US/Central",
    tags={"dagster/priority": "-1"},
)
def less_important_schedule(_):
    ...


# end_marker_priority
