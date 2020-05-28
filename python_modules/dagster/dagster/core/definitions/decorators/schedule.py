import datetime
import warnings

from dateutil.relativedelta import relativedelta

from dagster import check
from dagster.core.definitions.partition import PartitionSetDefinition
from dagster.core.errors import DagsterInvalidDefinitionError
from dagster.utils.partitions import date_partition_range

from ..mode import DEFAULT_MODE_NAME
from ..schedule import ScheduleDefinition

# Error messages are long
# pylint: disable=C0301


def schedule(
    cron_schedule,
    pipeline_name,
    name=None,
    tags=None,
    tags_fn=None,
    solid_subset=None,
    mode="default",
    should_execute=None,
    environment_vars=None,
):
    '''Create a schedule.

    The decorated function will be called as the ``environment_dict_fn`` of the underlying
    :py:class:`~dagster.ScheduleDefinition` and should take a
    :py:class:`~dagster.ScheduleExecutionContext` as its only argument, returning the environment
    dict for the scheduled execution.

    Args:
        cron_schedule (str): A valid cron string specifying when the schedule will run, e.g.,
            ``'45 23 * * 6'`` for a schedule that runs at 11:45 PM every Saturday.
        pipeline_name (str): The name of the pipeline to execute when the schedule runs.
        name (Optional[str]): The name of the schedule to create.
        tags (Optional[Dict[str, str]]): A dictionary of tags (string key-value pairs) to attach
            to the scheduled runs.
        tags_fn (Optional[Callable[[ScheduleExecutionContext], Optional[Dict[str, str]]]]): A function
            that generates tags to attach to the schedules runs. Takes a
            :py:class:`~dagster.ScheduleExecutionContext` and returns a dictionary of tags (string
            key-value pairs). You may set only one of ``tags`` and ``tags_fn``.
        solid_subset (Optional[List[str]]): Optionally, a list of the names of solid invocations
            (names of unaliased solids or aliases of aliased solids) to execute when the schedule
            runs.
        mode (Optional[str]): The pipeline mode in which to execute this schedule.
            (Default: 'default')
        should_execute (Optional[Callable[[ScheduleExecutionContext], bool]]): A function that runs at
            schedule execution tie to determine whether a schedule should execute or skip. Takes a
            :py:class:`~dagster.ScheduleExecutionContext` and returns a boolean (``True`` if the
            schedule should execute). Defaults to a function that always returns ``True``.
        environment_vars (Optional[Dict[str, str]]): Any environment variables to set when executing
            the schedule.
    '''

    def inner(fn):
        check.callable_param(fn, 'fn')

        schedule_name = name or fn.__name__

        return ScheduleDefinition(
            name=schedule_name,
            cron_schedule=cron_schedule,
            pipeline_name=pipeline_name,
            environment_dict_fn=fn,
            tags=tags,
            tags_fn=tags_fn,
            solid_subset=solid_subset,
            mode=mode,
            should_execute=should_execute,
            environment_vars=environment_vars,
        )

    return inner


def monthly_schedule(
    pipeline_name,
    start_date,
    name=None,
    execution_day_of_month=1,
    execution_time=datetime.time(0, 0),
    tags_fn_for_date=None,
    solid_subset=None,
    mode="default",
    should_execute=None,
    environment_vars=None,
):
    '''Create a schedule that runs monthly.

    The decorated function will be called as the ``environment_dict_fn`` of the underlying
    :py:class:`~dagster.ScheduleDefinition` and should take a
    :py:class:`~dagster.ScheduleExecutionContext` as its only argument, returning the environment
    dict for the scheduled execution.

    Args:
        pipeline_name (str): The name of the pipeline to execute when the schedule runs.
        start_date (datetime.datetime): The date from which to run the schedule.
        name (Optional[str]): The name of the schedule to create.
        execution_day_of_month (int): The day of the month on which to run the schedule (must be
            between 0 and 31).
        execution_time (datetime.time): The time at which to execute the schedule.
        tags_fn_for_date (Optional[Callable[[datetime.datetime], Optional[Dict[str, str]]]]): A
            function that generates tags to attach to the schedules runs. Takes the date of the
            schedule run and returns a dictionary of tags (string key-value pairs).
        solid_subset (Optional[List[str]]): Optionally, a list of the names of solid invocations
            (names of unaliased solids or aliases of aliased solids) to execute when the schedule
            runs.
        mode (Optional[str]): The pipeline mode in which to execute this schedule.
            (Default: 'default')
        should_execute (Optional[Callable[ScheduleExecutionContext, bool]]): A function that runs at
            schedule execution tie to determine whether a schedule should execute or skip. Takes a
            :py:class:`~dagster.ScheduleExecutionContext` and returns a boolean (``True`` if the
            schedule should execute). Defaults to a function that always returns ``True``.
        environment_vars (Optional[Dict[str, str]]): Any environment variables to set when executing
            the schedule.
    '''
    check.opt_str_param(name, 'name')
    check.inst_param(start_date, 'start_date', datetime.datetime)
    check.opt_callable_param(tags_fn_for_date, 'tags_fn_for_date')
    check.opt_nullable_list_param(solid_subset, 'solid_subset', of_type=str)
    mode = check.opt_str_param(mode, 'mode', DEFAULT_MODE_NAME)
    check.opt_callable_param(should_execute, 'should_execute')
    check.opt_dict_param(environment_vars, 'environment_vars', key_type=str, value_type=str)
    check.str_param(pipeline_name, 'pipeline_name')
    check.int_param(execution_day_of_month, 'execution_day')
    check.inst_param(execution_time, 'execution_time', datetime.time)

    if execution_day_of_month <= 0 or execution_day_of_month > 31:
        raise DagsterInvalidDefinitionError(
            "`execution_day_of_month={}` is not valid for monthly schedule. Execution day must be between 1 and 31".format(
                execution_day_of_month
            )
        )

    cron_schedule = '{minute} {hour} {day} * *'.format(
        minute=execution_time.minute, hour=execution_time.hour, day=execution_day_of_month
    )

    partition_fn = date_partition_range(start_date, delta=relativedelta(months=1), fmt="%Y-%m")

    def inner(fn):
        check.callable_param(fn, 'fn')

        schedule_name = name or fn.__name__

        tags_fn_for_partition_value = lambda partition: {}
        if tags_fn_for_date:
            tags_fn_for_partition_value = lambda partition: tags_fn_for_date(partition.value)

        partition_set = PartitionSetDefinition(
            name='{}_monthly'.format(pipeline_name),
            pipeline_name=pipeline_name,
            partition_fn=partition_fn,
            environment_dict_fn_for_partition=lambda partition: fn(partition.value),
            solid_subset=solid_subset,
            tags_fn_for_partition=tags_fn_for_partition_value,
            mode=mode,
        )

        return partition_set.create_schedule_definition(
            schedule_name,
            cron_schedule,
            should_execute=should_execute,
            environment_vars=environment_vars,
        )

    return inner


def weekly_schedule(
    pipeline_name,
    start_date,
    name=None,
    execution_day_of_week=0,
    execution_time=datetime.time(0, 0),
    tags_fn_for_date=None,
    solid_subset=None,
    mode="default",
    should_execute=None,
    environment_vars=None,
):
    '''Create a schedule that runs weekly.

    The decorated function will be called as the ``environment_dict_fn`` of the underlying
    :py:class:`~dagster.ScheduleDefinition` and should take a
    :py:class:`~dagster.ScheduleExecutionContext` as its only argument, returning the environment
    dict for the scheduled execution.

    Args:
        pipeline_name (str): The name of the pipeline to execute when the schedule runs.
        start_date (datetime.datetime): The date from which to run the schedule.
        name (Optional[str]): The name of the schedule to create.
        execution_day_of_week (int): The day of the week on which to run the schedule. Must be
            between 0 (Monday) and 6 (Sunday).
        execution_time (datetime.time): The time at which to execute the schedule.
        tags_fn_for_date (Optional[Callable[[datetime.datetime], Optional[Dict[str, str]]]]): A
            function that generates tags to attach to the schedules runs. Takes the date of the
            schedule run and returns a dictionary of tags (string key-value pairs).
        solid_subset (Optional[List[str]]): Optionally, a list of the names of solid invocations
            (names of unaliased solids or aliases of aliased solids) to execute when the schedule
            runs.
        mode (Optional[str]): The pipeline mode in which to execute this schedule.
            (Default: 'default')
        should_execute (Optional[Callable[ScheduleExecutionContext, bool]]): A function that runs at
            schedule execution tie to determine whether a schedule should execute or skip. Takes a
            :py:class:`~dagster.ScheduleExecutionContext` and returns a boolean (``True`` if the
            schedule should execute). Defaults to a function that always returns ``True``.
        environment_vars (Optional[Dict[str, str]]): Any environment variables to set when executing
            the schedule.
    '''
    check.opt_str_param(name, 'name')
    check.inst_param(start_date, 'start_date', datetime.datetime)
    check.opt_callable_param(tags_fn_for_date, 'tags_fn_for_date')
    check.opt_nullable_list_param(solid_subset, 'solid_subset', of_type=str)
    mode = check.opt_str_param(mode, 'mode', DEFAULT_MODE_NAME)
    check.opt_callable_param(should_execute, 'should_execute')
    check.opt_dict_param(environment_vars, 'environment_vars', key_type=str, value_type=str)
    check.str_param(pipeline_name, 'pipeline_name')
    check.int_param(execution_day_of_week, 'execution_day_of_week')
    check.inst_param(execution_time, 'execution_time', datetime.time)

    if execution_day_of_week < 0 or execution_day_of_week >= 7:
        raise DagsterInvalidDefinitionError(
            "`execution_day_of_week={}` is not valid for weekly schedule. Execution day must be between 0 [Sunday] and 6 [Saturday]".format(
                execution_day_of_week
            )
        )

    cron_schedule = '{minute} {hour} * * {day}'.format(
        minute=execution_time.minute, hour=execution_time.hour, day=execution_day_of_week
    )

    partition_fn = date_partition_range(start_date, delta=relativedelta(weeks=1), fmt="%Y-%m-%d")

    def inner(fn):
        check.callable_param(fn, 'fn')

        schedule_name = name or fn.__name__

        tags_fn_for_partition_value = lambda partition: {}
        if tags_fn_for_date:
            tags_fn_for_partition_value = lambda partition: tags_fn_for_date(partition.value)

        partition_set = PartitionSetDefinition(
            name='{}_weekly'.format(pipeline_name),
            pipeline_name=pipeline_name,
            partition_fn=partition_fn,
            environment_dict_fn_for_partition=lambda partition: fn(partition.value),
            solid_subset=solid_subset,
            tags_fn_for_partition=tags_fn_for_partition_value,
            mode=mode,
        )

        return partition_set.create_schedule_definition(
            schedule_name,
            cron_schedule,
            should_execute=should_execute,
            environment_vars=environment_vars,
        )

    return inner


def daily_schedule(
    pipeline_name,
    start_date,
    name=None,
    execution_time=datetime.time(0, 0),
    tags_fn_for_date=None,
    solid_subset=None,
    mode="default",
    should_execute=None,
    environment_vars=None,
):
    '''Create a schedule that runs daily.

    The decorated function will be called as the ``environment_dict_fn`` of the underlying
    :py:class:`~dagster.ScheduleDefinition` and should take a
    :py:class:`~dagster.ScheduleExecutionContext` as its only argument, returning the environment
    dict for the scheduled execution.

    Args:
        pipeline_name (str): The name of the pipeline to execute when the schedule runs.
        start_date (datetime.datetime): The date from which to run the schedule.
        name (Optional[str]): The name of the schedule to create.
        execution_time (datetime.time): The time at which to execute the schedule.
        tags_fn_for_date (Optional[Callable[[datetime.datetime], Optional[Dict[str, str]]]]): A
            function that generates tags to attach to the schedules runs. Takes the date of the
            schedule run and returns a dictionary of tags (string key-value pairs).
        solid_subset (Optional[List[str]]): Optionally, a list of the names of solid invocations
            (names of unaliased solids or aliases of aliased solids) to execute when the schedule
            runs.
        mode (Optional[str]): The pipeline mode in which to execute this schedule.
            (Default: 'default')
        should_execute (Optional[Callable[ScheduleExecutionContext, bool]]): A function that runs at
            schedule execution tie to determine whether a schedule should execute or skip. Takes a
            :py:class:`~dagster.ScheduleExecutionContext` and returns a boolean (``True`` if the
            schedule should execute). Defaults to a function that always returns ``True``.
        environment_vars (Optional[Dict[str, str]]): Any environment variables to set when executing
            the schedule.
    '''
    check.opt_str_param(name, 'name')
    check.inst_param(start_date, 'start_date', datetime.datetime)
    check.opt_callable_param(tags_fn_for_date, 'tags_fn_for_date')
    check.opt_nullable_list_param(solid_subset, 'solid_subset', of_type=str)
    mode = check.opt_str_param(mode, 'mode', DEFAULT_MODE_NAME)
    check.opt_callable_param(should_execute, 'should_execute')
    check.opt_dict_param(environment_vars, 'environment_vars', key_type=str, value_type=str)
    check.str_param(pipeline_name, 'pipeline_name')
    check.inst_param(execution_time, 'execution_time', datetime.time)

    cron_schedule = '{minute} {hour} * * *'.format(
        minute=execution_time.minute, hour=execution_time.hour
    )

    partition_fn = date_partition_range(start_date)

    def inner(fn):
        check.callable_param(fn, 'fn')

        schedule_name = name or fn.__name__

        tags_fn_for_partition_value = lambda partition: {}
        if tags_fn_for_date:
            tags_fn_for_partition_value = lambda partition: tags_fn_for_date(partition.value)

        partition_set = PartitionSetDefinition(
            name='{}_daily'.format(pipeline_name),
            pipeline_name=pipeline_name,
            partition_fn=partition_fn,
            environment_dict_fn_for_partition=lambda partition: fn(partition.value),
            solid_subset=solid_subset,
            tags_fn_for_partition=tags_fn_for_partition_value,
            mode=mode,
        )

        return partition_set.create_schedule_definition(
            schedule_name,
            cron_schedule,
            should_execute=should_execute,
            environment_vars=environment_vars,
        )

    return inner


def hourly_schedule(
    pipeline_name,
    start_date,
    name=None,
    execution_time=datetime.time(0, 0),
    tags_fn_for_date=None,
    solid_subset=None,
    mode="default",
    should_execute=None,
    environment_vars=None,
):
    '''Create a schedule that runs hourly.

    The decorated function will be called as the ``environment_dict_fn`` of the underlying
    :py:class:`~dagster.ScheduleDefinition` and should take a
    :py:class:`~dagster.ScheduleExecutionContext` as its only argument, returning the environment
    dict for the scheduled execution.

    Args:
        pipeline_name (str): The name of the pipeline to execute when the schedule runs.
        start_date (datetime.datetime): The date from which to run the schedule.
        name (Optional[str]): The name of the schedule to create. By default, this will be the name
            of the decorated function.
        execution_time (datetime.time): The time at which to execute the schedule. Only the minutes
            component will be respected -- the hour should be 0, and will be ignored if it is not 0.
        tags_fn_for_date (Optional[Callable[[datetime.datetime], Optional[Dict[str, str]]]]): A
            function that generates tags to attach to the schedules runs. Takes the date of the
            schedule run and returns a dictionary of tags (string key-value pairs).
        solid_subset (Optional[List[str]]): Optionally, a list of the names of solid invocations
            (names of unaliased solids or aliases of aliased solids) to execute when the schedule
            runs.
        mode (Optional[str]): The pipeline mode in which to execute this schedule.
            (Default: 'default')
        should_execute (Optional[Callable[ScheduleExecutionContext, bool]]): A function that runs at
            schedule execution tie to determine whether a schedule should execute or skip. Takes a
            :py:class:`~dagster.ScheduleExecutionContext` and returns a boolean (``True`` if the
            schedule should execute). Defaults to a function that always returns ``True``.
        environment_vars (Optional[Dict[str, str]]): Any environment variables to set when executing
            the schedule.
    '''
    check.opt_str_param(name, 'name')
    check.inst_param(start_date, 'start_date', datetime.datetime)
    check.opt_callable_param(tags_fn_for_date, 'tags_fn_for_date')
    check.opt_nullable_list_param(solid_subset, 'solid_subset', of_type=str)
    mode = check.opt_str_param(mode, 'mode', DEFAULT_MODE_NAME)
    check.opt_callable_param(should_execute, 'should_execute')
    check.opt_dict_param(environment_vars, 'environment_vars', key_type=str, value_type=str)
    check.str_param(pipeline_name, 'pipeline_name')
    check.inst_param(execution_time, 'execution_time', datetime.time)

    if execution_time.hour != 0:
        warnings.warn(
            "Hourly schedule {schedule_name} created with:\n"
            "\tschedule_time=datetime.time(hour={hour}, minute={minute}, ...)."
            "Since this is a hourly schedule, the hour parameter will be ignored and the schedule "
            "will run on the {minute} mark for the previous hour interval. Replace "
            "datetime.time(hour={hour}, minute={minute}, ...) with datetime.time(minute={minute}, ...)"
            "to fix this warning."
        )

    cron_schedule = '{minute} * * * *'.format(minute=execution_time.minute)

    partition_fn = date_partition_range(
        start_date, delta=datetime.timedelta(hours=1), fmt="%Y-%m-%d-%H:%M"
    )

    def inner(fn):
        check.callable_param(fn, 'fn')

        schedule_name = name or fn.__name__

        tags_fn_for_partition_value = lambda partition: {}
        if tags_fn_for_date:
            tags_fn_for_partition_value = lambda partition: tags_fn_for_date(partition.value)

        partition_set = PartitionSetDefinition(
            name='{}_hourly'.format(pipeline_name),
            pipeline_name=pipeline_name,
            partition_fn=partition_fn,
            environment_dict_fn_for_partition=lambda partition: fn(partition.value),
            solid_subset=solid_subset,
            tags_fn_for_partition=tags_fn_for_partition_value,
            mode=mode,
        )

        return partition_set.create_schedule_definition(
            schedule_name,
            cron_schedule,
            should_execute=should_execute,
            environment_vars=environment_vars,
        )

    return inner
