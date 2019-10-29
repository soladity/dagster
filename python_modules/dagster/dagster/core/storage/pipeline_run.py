from collections import namedtuple
from enum import Enum

from dagster import check
from dagster.core.execution.config import IRunConfig
from dagster.core.serdes import whitelist_for_serdes


@whitelist_for_serdes
class PipelineRunStatus(Enum):
    NOT_STARTED = 'NOT_STARTED'
    MANAGED = 'MANAGED'
    STARTED = 'STARTED'
    SUCCESS = 'SUCCESS'
    FAILURE = 'FAILURE'


@whitelist_for_serdes
class PipelineRunStatsSnapshot(
    namedtuple(
        '_PipelineRunStatsSnapshot',
        (
            'run_id steps_succeeded steps_failed materializations '
            'expectations start_time end_time'
        ),
    )
):
    def __new__(
        cls,
        run_id,
        steps_succeeded,
        steps_failed,
        materializations,
        expectations,
        start_time,
        end_time,
    ):
        return super(PipelineRunStatsSnapshot, cls).__new__(
            cls,
            run_id=check.str_param(run_id, 'run_id'),
            steps_succeeded=check.int_param(steps_succeeded, 'steps_succeeded'),
            steps_failed=check.int_param(steps_failed, 'steps_failed'),
            materializations=check.int_param(materializations, 'materializations'),
            expectations=check.int_param(expectations, 'expectations'),
            start_time=check.opt_float_param(start_time, 'start_time'),
            end_time=check.opt_float_param(end_time, 'end_time'),
        )


@whitelist_for_serdes
class PipelineRun(
    namedtuple(
        '_PipelineRun',
        (
            'pipeline_name run_id environment_dict mode selector reexecution_config '
            'step_keys_to_execute status tags'
        ),
    ),
    IRunConfig,
):
    @staticmethod
    def create_empty_run(pipeline_name, run_id, environment_dict=None, tags=None):
        from dagster.core.definitions.pipeline import ExecutionSelector

        return PipelineRun(
            pipeline_name=pipeline_name,
            run_id=run_id,
            environment_dict=environment_dict,
            mode='default',
            selector=ExecutionSelector(pipeline_name),
            reexecution_config=None,
            step_keys_to_execute=None,
            tags=tags,
            status=PipelineRunStatus.NOT_STARTED,
        )

    def __new__(
        cls,
        pipeline_name,
        run_id,
        environment_dict,
        mode,
        selector=None,
        reexecution_config=None,
        step_keys_to_execute=None,
        status=None,
        tags=None,
    ):
        from dagster.core.definitions.pipeline import ExecutionSelector
        from dagster.core.execution.config import ReexecutionConfig

        tags = check.opt_dict_param(tags, 'tags', key_type=str)
        selector = check.opt_inst_param(selector, 'selector', ExecutionSelector)
        if not selector:
            selector = ExecutionSelector(pipeline_name)

        if not status:
            status = PipelineRunStatus.NOT_STARTED

        return super(PipelineRun, cls).__new__(
            cls,
            pipeline_name=check.str_param(pipeline_name, 'pipeline_name'),
            run_id=check.str_param(run_id, 'run_id'),
            environment_dict=check.opt_dict_param(
                environment_dict, 'environment_dict', key_type=str
            ),
            mode=check.str_param(mode, 'mode'),
            selector=selector,
            reexecution_config=check.opt_inst_param(
                reexecution_config, 'reexecution_config', ReexecutionConfig
            ),
            step_keys_to_execute=None
            if step_keys_to_execute is None
            else check.list_param(step_keys_to_execute, 'step_keys_to_execute', of_type=str),
            status=status,
            tags=check.opt_dict_param(tags, 'tags', key_type=str),
        )

    def run_with_status(self, status):
        return PipelineRun(
            pipeline_name=self.pipeline_name,
            run_id=self.run_id,
            environment_dict=self.environment_dict,
            mode=self.mode,
            selector=self.selector,
            reexecution_config=self.reexecution_config,
            step_keys_to_execute=self.step_keys_to_execute,
            tags=self.tags,
            status=status,
        )

    @property
    def is_finished(self):
        return self.status == PipelineRunStatus.SUCCESS or self.status == PipelineRunStatus.FAILURE
