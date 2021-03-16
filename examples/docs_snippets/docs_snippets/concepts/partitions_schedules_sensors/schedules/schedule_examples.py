import datetime

from dagster import (
    PresetDefinition,
    daily_schedule,
    hourly_schedule,
    monthly_schedule,
    weekly_schedule,
)

# start_hourly_schedule


@hourly_schedule(
    pipeline_name="my_pipeline",
    start_date=datetime.datetime(2020, 1, 1),
    execution_time=datetime.time(hour=0, minute=25),
    execution_timezone="US/Central",
)
def my_hourly_schedule(date):
    return {"solids": {"process_data_for_date": {"config": {"date": date.strftime("%Y-%m-%d %H")}}}}


# end_hourly_schedule

# start_daily_schedule


@daily_schedule(
    pipeline_name="my_pipeline",
    start_date=datetime.datetime(2020, 1, 1),
    execution_time=datetime.time(hour=9, minute=0),
    execution_timezone="US/Central",
)
def my_daily_schedule(date):
    return {"solids": {"process_data_for_date": {"config": {"date": date.strftime("%Y-%m-%d")}}}}


# end_daily_schedule


# start_weekly_schedule


@weekly_schedule(
    pipeline_name="my_pipeline",
    start_date=datetime.datetime(2020, 1, 1),
    execution_day_of_week=1,  # Monday
    execution_timezone="US/Central",
)
def my_weekly_schedule(date):
    return {"solids": {"process_data_for_date": {"config": {"date": date.strftime("%Y-%m-%d")}}}}


# end_weekly_schedule


# start_monthly_schedule


@monthly_schedule(
    pipeline_name="my_pipeline",
    start_date=datetime.datetime(2020, 1, 1),
    execution_timezone="US/Central",
    execution_day_of_month=15,
    execution_time=datetime.time(hour=9, minute=0),
)
def my_monthly_schedule(date):
    return {"solids": {"process_data_for_date": {"config": {"date": date.strftime("%Y-%m")}}}}


# end_monthly_schedule

preset = PresetDefinition("test_preset", mode="basic", run_config={})

# start_preset


@daily_schedule(
    start_date=datetime.datetime(2020, 1, 1),
    pipeline_name="my_pipeline",
    solid_selection=preset.solid_selection,
    mode=preset.mode,
    tags_fn_for_date=lambda _: preset.tags,
)
def my_preset_schedule(_date):
    return preset.run_config


# end_preset


# start_modified_preset


@daily_schedule(
    start_date=datetime.datetime(2020, 1, 1),
    pipeline_name="my_pipeline",
    solid_selection=preset.solid_selection,
    mode=preset.mode,
    tags_fn_for_date=lambda _: preset.tags,
)
def my_modified_preset_schedule(date):
    modified_run_config = preset.run_config.copy()
    modified_run_config["date"] = date.strftime("%Y-%m-%d")
    return modified_run_config


# end_modified_preset
