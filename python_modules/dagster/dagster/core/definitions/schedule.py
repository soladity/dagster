from collections import namedtuple

from dagster import check
from dagster.core.serdes import whitelist_for_serdes


@whitelist_for_serdes
class ScheduleDefinitionData(
    namedtuple('ScheduleDefinitionData', 'name cron_schedule environment_vars')
):
    def __new__(cls, name, cron_schedule, environment_vars=None):
        return super(ScheduleDefinitionData, cls).__new__(
            cls,
            check.str_param(name, 'name'),
            check.str_param(cron_schedule, 'cron_schedule'),
            check.opt_dict_param(environment_vars, 'environment_vars'),
        )


class ScheduleDefinition(object):
    '''Define a schedule that targets a repository

    Args:
        name (str): The name of the schedule.
        cron_schedule (str): The cron schedule for the schedule
        execution_params (dict): The execution params for the schedule
        should_execute (function): Function that returns True/False
        environment_vars (dict): The environment variables to set for the schedule
    '''

    __slots__ = ['_schedule_definition_data', '_execution_params', '_should_execute']

    def __init__(
        self,
        name,
        cron_schedule,
        pipeline_name,
        environment_dict=None,
        tags=None,
        mode="default",
        should_execute=lambda: True,
        environment_vars=None,
    ):
        self._schedule_definition_data = ScheduleDefinitionData(
            name=check.str_param(name, 'name'),
            cron_schedule=check.str_param(cron_schedule, 'cron_schedule'),
            environment_vars=check.opt_dict_param(environment_vars, 'environment_vars'),
        )

        check.str_param(pipeline_name, 'pipeline_name')
        environment_dict = check.opt_dict_param(environment_dict, 'environment_dict')
        tags = check.opt_list_param(tags, 'tags')
        check.str_param(mode, 'mode')

        self._execution_params = {
            'environmentConfigData': environment_dict,
            'selector': {'name': pipeline_name},
            'executionMetadata': {"tags": tags},
            'mode': mode,
        }

        self._should_execute = check.fn_param(should_execute, 'should_execute')

    @property
    def schedule_definition_data(self):
        return self._schedule_definition_data

    @property
    def name(self):
        return self._schedule_definition_data.name

    @property
    def cron_schedule(self):
        return self._schedule_definition_data.cron_schedule

    @property
    def environment_vars(self):
        return self._schedule_definition_data.environment_vars

    @property
    def execution_params(self):
        return self._execution_params

    @property
    def should_execute(self):
        return self._should_execute
