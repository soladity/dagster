import pendulum
import pytest

from dagster.core.scheduler import ScheduleTickStatus
from dagster.scheduler.scheduler import get_default_scheduler_logger, launch_scheduled_runs

from .test_scheduler_run import (
    default_repo,
    grpc_repo,
    instance_with_schedules,
    validate_run_started,
    validate_tick,
    wait_for_all_runs_to_start,
)


@pytest.mark.parametrize("external_repo_context", [default_repo, grpc_repo])
def test_different_timezone_run(external_repo_context, capfd):
    # Verify that schedule runs at the expected time in a non-UTC timezone (in this
    # case, the instance is configured to run in US/Central on a server that is in US/Pacific)
    with instance_with_schedules(external_repo_context, timezone="US/Central") as (
        instance,
        external_repo,
    ):
        freeze_datetime = pendulum.create(2019, 2, 27, 23, 59, 59, tz="US/Central").in_tz(
            "US/Pacific"
        )
        with pendulum.test(freeze_datetime):
            external_schedule = external_repo.get_external_schedule("simple_schedule")

            schedule_origin = external_schedule.get_origin()

            instance.start_schedule_and_update_storage_state(external_schedule)

            assert instance.get_runs_count() == 0
            ticks = instance.get_schedule_ticks(schedule_origin.get_id())
            assert len(ticks) == 0

            launch_scheduled_runs(
                instance, get_default_scheduler_logger(), pendulum.now("UTC"),
            )
            assert instance.get_runs_count() == 0
            ticks = instance.get_schedule_ticks(schedule_origin.get_id())
            assert len(ticks) == 0

            captured = capfd.readouterr()

            assert (
                captured.out
                == """2019-02-27 21:59:59 - dagster-scheduler - INFO - Checking for new runs for the following schedules: simple_schedule
2019-02-27 21:59:59 - dagster-scheduler - INFO - No new runs for simple_schedule
"""
            )
        freeze_datetime = freeze_datetime.add(seconds=2)
        with pendulum.test(freeze_datetime):
            launch_scheduled_runs(
                instance, get_default_scheduler_logger(), pendulum.now("UTC"),
            )

            assert instance.get_runs_count() == 1
            ticks = instance.get_schedule_ticks(schedule_origin.get_id())
            assert len(ticks) == 1

            expected_datetime = pendulum.create(year=2019, month=2, day=28, tz="US/Central").in_tz(
                "UTC"
            )

            validate_tick(
                ticks[0],
                external_schedule,
                expected_datetime,
                ScheduleTickStatus.SUCCESS,
                instance.get_runs()[0].run_id,
            )

            wait_for_all_runs_to_start(instance)
            validate_run_started(instance.get_runs()[0], expected_datetime, "2019-02-27")

            captured = capfd.readouterr()

            assert (
                captured.out
                == """2019-02-27 22:00:01 - dagster-scheduler - INFO - Checking for new runs for the following schedules: simple_schedule
2019-02-27 22:00:01 - dagster-scheduler - INFO - Launching run for simple_schedule at 2019-02-28 00:00:00-0600
2019-02-27 22:00:01 - dagster-scheduler - INFO - Completed scheduled launch of run {run_id} for simple_schedule
""".format(
                    run_id=instance.get_runs()[0].run_id
                )
            )

            # Verify idempotence
            launch_scheduled_runs(
                instance, get_default_scheduler_logger(), pendulum.now("UTC"),
            )
            assert instance.get_runs_count() == 1
            ticks = instance.get_schedule_ticks(schedule_origin.get_id())
            assert len(ticks) == 1
            assert ticks[0].status == ScheduleTickStatus.SUCCESS


# Verify that a schedule that runs in US/Central late enough in the day that it executes on
# a different day in UTC still runs and creates its partition names based on the US/Central time
@pytest.mark.parametrize("external_repo_context", [default_repo, grpc_repo])
def test_different_days_in_different_timezones(external_repo_context):
    with instance_with_schedules(external_repo_context, timezone="US/Central") as (
        instance,
        external_repo,
    ):
        freeze_datetime = pendulum.create(2019, 2, 27, 22, 59, 59, tz="US/Central").in_tz(
            "US/Pacific"
        )
        with pendulum.test(freeze_datetime):
            # Runs every day at 11PM (CST)
            external_schedule = external_repo.get_external_schedule("daily_late_schedule")
            schedule_origin = external_schedule.get_origin()
            instance.start_schedule_and_update_storage_state(external_schedule)

            assert instance.get_runs_count() == 0
            ticks = instance.get_schedule_ticks(schedule_origin.get_id())
            assert len(ticks) == 0

            launch_scheduled_runs(
                instance, get_default_scheduler_logger(), pendulum.now("UTC"),
            )
            assert instance.get_runs_count() == 0
            ticks = instance.get_schedule_ticks(schedule_origin.get_id())
            assert len(ticks) == 0

        freeze_datetime = freeze_datetime.add(seconds=2)
        with pendulum.test(freeze_datetime):
            launch_scheduled_runs(
                instance, get_default_scheduler_logger(), pendulum.now("UTC"),
            )

            assert instance.get_runs_count() == 1
            ticks = instance.get_schedule_ticks(schedule_origin.get_id())
            assert len(ticks) == 1

            expected_datetime = pendulum.create(
                year=2019, month=2, day=27, hour=23, tz="US/Central"
            ).in_tz("UTC")

            validate_tick(
                ticks[0],
                external_schedule,
                expected_datetime,
                ScheduleTickStatus.SUCCESS,
                instance.get_runs()[0].run_id,
            )

            wait_for_all_runs_to_start(instance)
            validate_run_started(instance.get_runs()[0], expected_datetime, "2019-02-26")

            # Verify idempotence
            launch_scheduled_runs(
                instance, get_default_scheduler_logger(), pendulum.now("UTC"),
            )
            assert instance.get_runs_count() == 1
            ticks = instance.get_schedule_ticks(schedule_origin.get_id())
            assert len(ticks) == 1
            assert ticks[0].status == ScheduleTickStatus.SUCCESS


@pytest.mark.parametrize(
    "external_repo_context", [default_repo, grpc_repo],
)
def test_hourly_dst_spring_forward(external_repo_context):
    # Verify that an hourly schedule still runs hourly during the spring DST transition
    with instance_with_schedules(external_repo_context, timezone="US/Central") as (
        instance,
        external_repo,
    ):
        # 1AM CST
        freeze_datetime = pendulum.create(2019, 3, 10, 1, 0, 0, tz="US/Central").in_tz("US/Pacific")

        with pendulum.test(freeze_datetime):
            external_schedule = external_repo.get_external_schedule("simple_hourly_schedule")
            schedule_origin = external_schedule.get_origin()
            instance.start_schedule_and_update_storage_state(external_schedule)

            assert instance.get_runs_count() == 0
            ticks = instance.get_schedule_ticks(schedule_origin.get_id())
            assert len(ticks) == 0

        freeze_datetime = freeze_datetime.add(hours=2)

        # DST has now happened, 2 hours later it is 4AM CST
        # Should be 3 runs: 1AM CST, 3AM CST, 4AM CST
        with pendulum.test(freeze_datetime):
            launch_scheduled_runs(
                instance, get_default_scheduler_logger(), pendulum.now("UTC"),
            )

            wait_for_all_runs_to_start(instance)

            assert instance.get_runs_count() == 3
            ticks = instance.get_schedule_ticks(schedule_origin.get_id())
            assert len(ticks) == 3

            expected_datetimes_utc = [
                pendulum.create(2019, 3, 10, 4, 0, 0, tz="US/Central").in_tz("UTC"),
                pendulum.create(2019, 3, 10, 3, 0, 0, tz="US/Central").in_tz("UTC"),
                pendulum.create(2019, 3, 10, 1, 0, 0, tz="US/Central").in_tz("UTC"),
            ]

            for i in range(3):
                validate_tick(
                    ticks[i],
                    external_schedule,
                    expected_datetimes_utc[i],
                    ScheduleTickStatus.SUCCESS,
                    instance.get_runs()[i].run_id,
                )

                validate_run_started(
                    instance.get_runs()[i],
                    expected_datetimes_utc[i],
                    expected_datetimes_utc[i].subtract(hours=1).strftime("%Y-%m-%d-%H:%M"),
                )

            # Verify idempotence
            launch_scheduled_runs(
                instance, get_default_scheduler_logger(), pendulum.now("UTC"),
            )
            assert instance.get_runs_count() == 3
            ticks = instance.get_schedule_ticks(schedule_origin.get_id())
            assert len(ticks) == 3


@pytest.mark.parametrize(
    "external_repo_context", [default_repo, grpc_repo],
)
def test_hourly_dst_fall_back(external_repo_context):
    # Verify that an hourly schedule still runs hourly during the fall DST transition
    with instance_with_schedules(external_repo_context, timezone="US/Central") as (
        instance,
        external_repo,
    ):
        # 12:30 AM CST
        freeze_datetime = pendulum.create(2019, 11, 3, 0, 30, 0, tz="US/Central").in_tz(
            "US/Pacific"
        )

        with pendulum.test(freeze_datetime):
            external_schedule = external_repo.get_external_schedule("simple_hourly_schedule")
            schedule_origin = external_schedule.get_origin()
            instance.start_schedule_and_update_storage_state(external_schedule)

            assert instance.get_runs_count() == 0
            ticks = instance.get_schedule_ticks(schedule_origin.get_id())
            assert len(ticks) == 0

        freeze_datetime = freeze_datetime.add(hours=4)

        # DST has now happened, 4 hours later it is 3:30AM CST
        # Should be 4 runs: 1AM CST, 2AM CST (part 1), 2AM CST (part 2), 3AM CST
        with pendulum.test(freeze_datetime):
            launch_scheduled_runs(
                instance, get_default_scheduler_logger(), pendulum.now("UTC"),
            )

            wait_for_all_runs_to_start(instance)

            assert instance.get_runs_count() == 4
            ticks = instance.get_schedule_ticks(schedule_origin.get_id())
            assert len(ticks) == 4

            expected_datetimes_utc = [
                pendulum.create(2019, 11, 3, 9, 0, 0, tz="UTC"),
                pendulum.create(2019, 11, 3, 8, 0, 0, tz="UTC"),
                pendulum.create(2019, 11, 3, 7, 0, 0, tz="UTC"),
                pendulum.create(2019, 11, 3, 6, 0, 0, tz="UTC"),
            ]

            expected_ct_times = [
                "2019-11-03T03:00:00-06:00",
                "2019-11-03T02:00:00-06:00",
                "2019-11-03T01:00:00-06:00",
                "2019-11-03T01:00:00-05:00",
            ]

            for i in range(4):
                assert (
                    expected_datetimes_utc[i].in_tz("US/Central").isoformat()
                    == expected_ct_times[i]
                )

                validate_tick(
                    ticks[i],
                    external_schedule,
                    expected_datetimes_utc[i],
                    ScheduleTickStatus.SUCCESS,
                    instance.get_runs()[i].run_id,
                )

                validate_run_started(
                    instance.get_runs()[i],
                    expected_datetimes_utc[i],
                    expected_datetimes_utc[i].subtract(hours=1).strftime("%Y-%m-%d-%H:%M"),
                )

            # Verify idempotence
            launch_scheduled_runs(
                instance, get_default_scheduler_logger(), pendulum.now("UTC"),
            )
            assert instance.get_runs_count() == 4
            ticks = instance.get_schedule_ticks(schedule_origin.get_id())
            assert len(ticks) == 4


@pytest.mark.parametrize(
    "external_repo_context", [default_repo, grpc_repo],
)
def test_daily_dst_spring_forward(external_repo_context):
    # Verify that a daily schedule still runs once per day during the spring DST transition
    with instance_with_schedules(external_repo_context, timezone="US/Central") as (
        instance,
        external_repo,
    ):
        # Night before DST
        freeze_datetime = pendulum.create(2019, 3, 10, 0, 0, 0, tz="US/Central").in_tz("US/Pacific")

        with pendulum.test(freeze_datetime):
            external_schedule = external_repo.get_external_schedule("simple_schedule")
            schedule_origin = external_schedule.get_origin()
            instance.start_schedule_and_update_storage_state(external_schedule)

            assert instance.get_runs_count() == 0
            ticks = instance.get_schedule_ticks(schedule_origin.get_id())
            assert len(ticks) == 0

        freeze_datetime = freeze_datetime.add(days=2)

        with pendulum.test(freeze_datetime):
            launch_scheduled_runs(
                instance, get_default_scheduler_logger(), pendulum.now("UTC"),
            )

            wait_for_all_runs_to_start(instance)

            assert instance.get_runs_count() == 3
            ticks = instance.get_schedule_ticks(schedule_origin.get_id())
            assert len(ticks) == 3

            # UTC time changed by one hour after the transition, still running daily at the same
            # time in CT
            expected_datetimes_utc = [
                pendulum.create(2019, 3, 12, 5, 0, 0, tz="UTC"),
                pendulum.create(2019, 3, 11, 5, 0, 0, tz="UTC"),
                pendulum.create(2019, 3, 10, 6, 0, 0, tz="UTC"),
            ]

            for i in range(3):
                validate_tick(
                    ticks[i],
                    external_schedule,
                    expected_datetimes_utc[i],
                    ScheduleTickStatus.SUCCESS,
                    instance.get_runs()[i].run_id,
                )

                validate_run_started(
                    instance.get_runs()[i],
                    expected_datetimes_utc[i],
                    expected_datetimes_utc[i].subtract(days=1).strftime("%Y-%m-%d"),
                )

            # Verify idempotence
            launch_scheduled_runs(
                instance, get_default_scheduler_logger(), pendulum.now("UTC"),
            )
            assert instance.get_runs_count() == 3
            ticks = instance.get_schedule_ticks(schedule_origin.get_id())
            assert len(ticks) == 3


@pytest.mark.parametrize("external_repo_context", [default_repo, grpc_repo])
def test_daily_dst_fall_back(external_repo_context):
    # Verify that a daily schedule still runs once per day during the fall DST transition
    with instance_with_schedules(external_repo_context, timezone="US/Central") as (
        instance,
        external_repo,
    ):
        # Night before DST
        freeze_datetime = pendulum.create(2019, 11, 3, 0, 0, 0, tz="US/Central").in_tz("US/Pacific")

        with pendulum.test(freeze_datetime):
            external_schedule = external_repo.get_external_schedule("simple_schedule")
            schedule_origin = external_schedule.get_origin()
            instance.start_schedule_and_update_storage_state(external_schedule)

            assert instance.get_runs_count() == 0
            ticks = instance.get_schedule_ticks(schedule_origin.get_id())
            assert len(ticks) == 0

        freeze_datetime = freeze_datetime.add(days=2)

        with pendulum.test(freeze_datetime):
            launch_scheduled_runs(
                instance, get_default_scheduler_logger(), pendulum.now("UTC"),
            )

            wait_for_all_runs_to_start(instance)

            assert instance.get_runs_count() == 3
            ticks = instance.get_schedule_ticks(schedule_origin.get_id())
            assert len(ticks) == 3

            # UTC time changed by one hour after the transition, still running daily at the same
            # time in CT
            expected_datetimes_utc = [
                pendulum.create(2019, 11, 5, 6, 0, 0, tz="UTC"),
                pendulum.create(2019, 11, 4, 6, 0, 0, tz="UTC"),
                pendulum.create(2019, 11, 3, 5, 0, 0, tz="UTC"),
            ]

            for i in range(3):
                validate_tick(
                    ticks[i],
                    external_schedule,
                    expected_datetimes_utc[i],
                    ScheduleTickStatus.SUCCESS,
                    instance.get_runs()[i].run_id,
                )

                validate_run_started(
                    instance.get_runs()[i],
                    expected_datetimes_utc[i],
                    expected_datetimes_utc[i].subtract(days=1).strftime("%Y-%m-%d"),
                )

            # Verify idempotence
            launch_scheduled_runs(
                instance, get_default_scheduler_logger(), pendulum.now("UTC"),
            )
            assert instance.get_runs_count() == 3
            ticks = instance.get_schedule_ticks(schedule_origin.get_id())
            assert len(ticks) == 3


@pytest.mark.parametrize(
    "external_repo_context", [default_repo, grpc_repo],
)
def test_execute_during_dst_transition_spring_forward(external_repo_context):
    # Verify that a daily schedule that is supposed to execute at a time that is skipped
    # by the DST transition does not execute for that day
    with instance_with_schedules(external_repo_context, timezone="US/Central") as (
        instance,
        external_repo,
    ):
        # Day before DST
        freeze_datetime = pendulum.create(2019, 3, 9, 0, 0, 0, tz="US/Central").in_tz("US/Pacific")

        with pendulum.test(freeze_datetime):
            external_schedule = external_repo.get_external_schedule("daily_dst_transition_schedule")
            schedule_origin = external_schedule.get_origin()
            instance.start_schedule_and_update_storage_state(external_schedule)

            assert instance.get_runs_count() == 0
            ticks = instance.get_schedule_ticks(schedule_origin.get_id())
            assert len(ticks) == 0

        freeze_datetime = freeze_datetime.add(days=3)

        with pendulum.test(freeze_datetime):
            launch_scheduled_runs(
                instance, get_default_scheduler_logger(), pendulum.now("UTC"),
            )

            wait_for_all_runs_to_start(instance)

            assert instance.get_runs_count() == 2
            ticks = instance.get_schedule_ticks(schedule_origin.get_id())
            assert len(ticks) == 2

            # skipped 3/10 since 2:30AM never happened
            expected_datetimes_utc = [
                pendulum.create(2019, 3, 11, 2, 30, 0, tz="US/Central").in_tz("UTC"),
                pendulum.create(2019, 3, 9, 2, 30, 0, tz="US/Central").in_tz("UTC"),
            ]

            for i in range(2):
                validate_tick(
                    ticks[i],
                    external_schedule,
                    expected_datetimes_utc[i],
                    ScheduleTickStatus.SUCCESS,
                    instance.get_runs()[i].run_id,
                )

                validate_run_started(
                    instance.get_runs()[i],
                    expected_datetimes_utc[i],
                    expected_datetimes_utc[i].subtract(days=1).strftime("%Y-%m-%d"),
                )

            # Verify idempotence
            launch_scheduled_runs(
                instance, get_default_scheduler_logger(), pendulum.now("UTC"),
            )
            assert instance.get_runs_count() == 2
            ticks = instance.get_schedule_ticks(schedule_origin.get_id())
            assert len(ticks) == 2


@pytest.mark.parametrize(
    "external_repo_context", [default_repo, grpc_repo],
)
def test_execute_during_dst_transition_fall_back(external_repo_context):
    with instance_with_schedules(external_repo_context, timezone="US/Central") as (
        instance,
        external_repo,
    ):
        # A schedule that runs daily during a time that occurs twice during a fall DST transition
        # only executes once for that day
        freeze_datetime = pendulum.create(2019, 11, 2, 0, 0, 0, tz="US/Central").in_tz("US/Pacific")

        with pendulum.test(freeze_datetime):
            external_schedule = external_repo.get_external_schedule("daily_dst_transition_schedule")
            schedule_origin = external_schedule.get_origin()
            instance.start_schedule_and_update_storage_state(external_schedule)

            assert instance.get_runs_count() == 0
            ticks = instance.get_schedule_ticks(schedule_origin.get_id())
            assert len(ticks) == 0

        freeze_datetime = freeze_datetime.add(days=3)

        with pendulum.test(freeze_datetime):
            launch_scheduled_runs(
                instance, get_default_scheduler_logger(), pendulum.now("UTC"),
            )

            wait_for_all_runs_to_start(instance)

            assert instance.get_runs_count() == 3
            ticks = instance.get_schedule_ticks(schedule_origin.get_id())
            assert len(ticks) == 3

            expected_datetimes_utc = [
                pendulum.create(2019, 11, 4, 8, 30, 0, tz="UTC"),
                pendulum.create(2019, 11, 3, 8, 30, 0, tz="UTC"),
                pendulum.create(2019, 11, 2, 7, 30, 0, tz="UTC"),
            ]

            for i in range(3):
                validate_tick(
                    ticks[i],
                    external_schedule,
                    expected_datetimes_utc[i],
                    ScheduleTickStatus.SUCCESS,
                    instance.get_runs()[i].run_id,
                )

                validate_run_started(
                    instance.get_runs()[i],
                    expected_datetimes_utc[i],
                    expected_datetimes_utc[i].subtract(days=1).strftime("%Y-%m-%d"),
                )

            # Verify idempotence
            launch_scheduled_runs(
                instance, get_default_scheduler_logger(), pendulum.now("UTC"),
            )
            assert instance.get_runs_count() == 3
            ticks = instance.get_schedule_ticks(schedule_origin.get_id())
            assert len(ticks) == 3
