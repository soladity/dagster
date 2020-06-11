'''
This module contains data objects meant to be serialized between
host processes and user processes. They should contain no
business logic or clever indexing. Use the classes in external.py
for that.
'''

from collections import namedtuple

from dagster import check
from dagster.core.definitions import (
    PartitionSetDefinition,
    PipelineDefinition,
    PresetDefinition,
    RepositoryDefinition,
    ScheduleDefinition,
)
from dagster.core.definitions.partition import PartitionScheduleDefinition
from dagster.core.errors import PartitionScheduleExecutionError
from dagster.core.snap import PipelineSnapshot
from dagster.serdes import whitelist_for_serdes
from dagster.utils.error import SerializableErrorInfo


@whitelist_for_serdes
class ExternalRepositoryData(
    namedtuple(
        '_ExternalRepositoryData',
        'name external_pipeline_datas external_schedule_datas external_partition_set_datas',
    )
):
    def __new__(
        cls, name, external_pipeline_datas, external_schedule_datas, external_partition_set_datas
    ):
        return super(ExternalRepositoryData, cls).__new__(
            cls,
            name=check.str_param(name, 'name'),
            external_pipeline_datas=check.list_param(
                external_pipeline_datas, 'external_pipeline_datas', of_type=ExternalPipelineData
            ),
            external_schedule_datas=check.list_param(
                external_schedule_datas, 'external_schedule_datas', of_type=ExternalScheduleData
            ),
            external_partition_set_datas=check.list_param(
                external_partition_set_datas,
                'external_parition_set_datas',
                of_type=ExternalPartitionSetData,
            ),
        )

    def get_pipeline_snapshot(self, name):
        check.str_param(name, 'name')

        for external_pipeline_data in self.external_pipeline_datas:
            if external_pipeline_data.name == name:
                return external_pipeline_data.pipeline_snapshot

        check.failed('Could not find pipeline snapshot named ' + name)

    def get_external_pipeline_data(self, name):
        check.str_param(name, 'name')

        for external_pipeline_data in self.external_pipeline_datas:
            if external_pipeline_data.name == name:
                return external_pipeline_data

        check.failed('Could not find external pipeline data named ' + name)

    def get_external_schedule_data(self, name):
        check.str_param(name, 'name')

        for external_schedule_data in self.external_schedule_datas:
            if external_schedule_data.name == name:
                return external_schedule_data

        check.failed('Could not find external schedule data named ' + name)

    def get_external_partition_set_data(self, name):
        check.str_param(name, 'name')

        for external_partition_set_data in self.external_partition_set_datas:
            if external_partition_set_data.name == name:
                return external_partition_set_data

        check.failed('Could not find external parition set data named ' + name)


@whitelist_for_serdes
class ExternalPipelineSubsetResult(
    namedtuple('_ExternalPipelineSubsetResult', 'success error external_pipeline_data')
):
    def __new__(cls, success, error=None, external_pipeline_data=None):
        return super(ExternalPipelineSubsetResult, cls).__new__(
            cls,
            success=check.bool_param(success, 'success'),
            error=check.opt_inst_param(error, 'error', SerializableErrorInfo),
            external_pipeline_data=check.opt_inst_param(
                external_pipeline_data, 'external_pipeline_data', ExternalPipelineData
            ),
        )


@whitelist_for_serdes
class ExternalPipelineData(
    namedtuple(
        '_ExternalPipelineData', 'name pipeline_snapshot active_presets parent_pipeline_snapshot'
    )
):
    def __new__(cls, name, pipeline_snapshot, active_presets, parent_pipeline_snapshot):
        return super(ExternalPipelineData, cls).__new__(
            cls,
            name=check.str_param(name, 'name'),
            pipeline_snapshot=check.inst_param(
                pipeline_snapshot, 'pipeline_snapshot', PipelineSnapshot
            ),
            parent_pipeline_snapshot=check.opt_inst_param(
                parent_pipeline_snapshot, 'parent_pipeline_snapshot', PipelineSnapshot
            ),
            active_presets=check.list_param(
                active_presets, 'active_presets', of_type=ExternalPresetData
            ),
        )


@whitelist_for_serdes
class ExternalPresetData(
    namedtuple('_ExternalPresetData', 'name environment_dict solid_selection mode')
):
    def __new__(cls, name, environment_dict, solid_selection, mode):
        return super(ExternalPresetData, cls).__new__(
            cls,
            name=check.str_param(name, 'name'),
            environment_dict=check.opt_dict_param(environment_dict, 'environment_dict'),
            solid_selection=check.opt_nullable_list_param(
                solid_selection, 'solid_selection', of_type=str
            ),
            mode=check.str_param(mode, 'mode'),
        )


@whitelist_for_serdes
class ExternalScheduleData(
    namedtuple(
        '_ExternalScheduleData',
        'name cron_schedule pipeline_name solid_selection mode environment_vars partition_set_name',
    )
):
    def __new__(
        cls,
        name,
        cron_schedule,
        pipeline_name,
        solid_selection,
        mode,
        environment_vars,
        partition_set_name,
    ):
        return super(ExternalScheduleData, cls).__new__(
            cls,
            name=check.str_param(name, 'name'),
            cron_schedule=check.str_param(cron_schedule, 'cron_schedule'),
            pipeline_name=check.str_param(pipeline_name, 'pipeline_name'),
            solid_selection=check.opt_nullable_list_param(solid_selection, 'solid_selection', str),
            mode=check.opt_str_param(mode, 'mode'),
            environment_vars=check.opt_dict_param(environment_vars, 'environment_vars'),
            partition_set_name=check.opt_str_param(partition_set_name, 'partition_set_name'),
        )


@whitelist_for_serdes
class ExternalScheduleExecutionData(
    namedtuple('_ExternalScheduleExecutionData', 'run_config error')
):
    def __new__(cls, run_config=None, error=None):
        return super(ExternalScheduleExecutionData, cls).__new__(
            cls,
            run_config=check.opt_dict_param(run_config, 'run_config'),
            error=check.opt_inst_param(error, 'error', SerializableErrorInfo),
        )


@whitelist_for_serdes
class ExternalPartitionSetData(
    namedtuple(
        '_ExternalPartitionSetData', 'name partition_names pipeline_name solid_selection mode'
    )
):
    def __new__(cls, name, partition_names, pipeline_name, solid_selection, mode):
        return super(ExternalPartitionSetData, cls).__new__(
            cls,
            name=check.str_param(name, 'name'),
            partition_names=check.list_param(partition_names, 'parition_names', str),
            pipeline_name=check.str_param(pipeline_name, 'pipeline_name'),
            solid_selection=check.opt_nullable_list_param(solid_selection, 'solid_selection', str),
            mode=check.opt_str_param(mode, 'mode'),
        )


@whitelist_for_serdes
class ExternalPartitionData(namedtuple('_ExternalPartitionSetData', 'name tags run_config error')):
    def __new__(cls, name, tags=None, run_config=None, error=None):
        return super(ExternalPartitionData, cls).__new__(
            cls,
            name=check.str_param(name, 'name'),
            tags=check.opt_dict_param(tags, 'tags'),
            run_config=check.opt_dict_param(run_config, 'run_config'),
            error=check.opt_inst_param(error, 'error', PartitionScheduleExecutionError),
        )


def external_repository_data_from_def(repository_def):
    check.inst_param(repository_def, 'repository_def', RepositoryDefinition)

    return ExternalRepositoryData(
        name=repository_def.name,
        external_pipeline_datas=sorted(
            list(map(external_pipeline_data_from_def, repository_def.get_all_pipelines())),
            key=lambda pd: pd.name,
        ),
        external_schedule_datas=sorted(
            list(map(external_schedule_data_from_def, repository_def.schedule_defs)),
            key=lambda sd: sd.name,
        ),
        external_partition_set_datas=sorted(
            list(map(external_partition_set_data_from_def, repository_def.partition_set_defs)),
            key=lambda psd: psd.name,
        ),
    )


def external_pipeline_data_from_def(pipeline_def):
    check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)
    return ExternalPipelineData(
        name=pipeline_def.name,
        pipeline_snapshot=pipeline_def.get_pipeline_snapshot(),
        parent_pipeline_snapshot=pipeline_def.get_parent_pipeline_snapshot(),
        active_presets=sorted(
            list(map(external_preset_data_from_def, pipeline_def.preset_defs)),
            key=lambda pd: pd.name,
        ),
    )


def external_schedule_data_from_def(schedule_def):
    check.inst_param(schedule_def, 'schedule_def', ScheduleDefinition)
    return ExternalScheduleData(
        name=schedule_def.name,
        cron_schedule=schedule_def.cron_schedule,
        pipeline_name=schedule_def.pipeline_name,
        solid_selection=schedule_def.solid_selection,
        mode=schedule_def.mode,
        environment_vars=schedule_def.environment_vars,
        partition_set_name=schedule_def.get_partition_set().name
        if isinstance(schedule_def, PartitionScheduleDefinition)
        else None,
    )


def external_partition_set_data_from_def(partition_set_def):
    check.inst_param(partition_set_def, 'partition_set_def', PartitionSetDefinition)
    return ExternalPartitionSetData(
        name=partition_set_def.name,
        partition_names=partition_set_def.get_partition_names(),
        pipeline_name=partition_set_def.pipeline_name,
        solid_selection=partition_set_def.solid_selection,
        mode=partition_set_def.mode,
    )


def external_preset_data_from_def(preset_def):
    check.inst_param(preset_def, 'preset_def', PresetDefinition)
    return ExternalPresetData(
        name=preset_def.name,
        environment_dict=preset_def.run_config,
        solid_selection=preset_def.solid_selection,
        mode=preset_def.mode,
    )
