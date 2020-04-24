import abc

import six

from dagster import ExecutionTargetHandle, check
from dagster.core.definitions.partition import PartitionScheduleDefinition
from dagster.core.instance import DagsterInstance
from dagster.core.snap import ActiveRepositoryData, RepositoryIndex, active_repository_data_from_def

from .pipeline_execution_manager import PipelineExecutionManager
from .reloader import Reloader


class DagsterGraphQLContext(six.with_metaclass(abc.ABCMeta)):
    def __init__(self, active_repository_data, instance):
        self.active_repository_data = check.inst_param(
            active_repository_data, 'active_repository_data', ActiveRepositoryData
        )
        self._repository_index = RepositoryIndex(active_repository_data)
        self._instance = check.inst_param(instance, 'instance', DagsterInstance)

    def get_repository_index(self):
        return self._repository_index

    @property
    def instance(self):
        return self._instance

    @abc.abstractproperty
    def is_reload_supported(self):
        pass


class DagsterGraphQLOutOfProcessRepositoryContext(DagsterGraphQLContext):
    def __init__(self, active_repository_data, execution_manager, instance, version=None):
        super(DagsterGraphQLOutOfProcessRepositoryContext, self).__init__(
            active_repository_data=active_repository_data, instance=instance
        )
        self.execution_manager = check.inst_param(
            execution_manager, 'pipeline_execution_manager', PipelineExecutionManager
        )
        self.version = version

    @property
    def is_reload_supported(self):
        return False


class DagsterGraphQLInProcessRepositoryContext(DagsterGraphQLContext):
    def __init__(self, handle, execution_manager, instance, reloader=None, version=None):
        self.repository_definition = handle.build_repository_definition()
        super(DagsterGraphQLInProcessRepositoryContext, self).__init__(
            active_repository_data=active_repository_data_from_def(self.repository_definition),
            instance=instance,
        )
        self._handle = check.inst_param(handle, 'handle', ExecutionTargetHandle)
        self.reloader = check.opt_inst_param(reloader, 'reloader', Reloader)
        self.execution_manager = check.inst_param(
            execution_manager, 'pipeline_execution_manager', PipelineExecutionManager
        )
        self.version = version

        self._cached_pipelines = {}

    def get_handle(self):
        return self._handle

    def get_partition_set(self, partition_set_name):
        return next(
            (
                partition_set
                for partition_set in self.get_all_partition_sets()
                if partition_set.name == partition_set_name
            ),
            None,
        )

    def get_all_partition_sets(self):
        return self.repository_definition.partition_set_defs + [
            schedule_def.get_partition_set()
            for schedule_def in self.repository_definition.schedule_defs
            if isinstance(schedule_def, PartitionScheduleDefinition)
        ]

    def get_repository(self):
        return self.repository_definition

    def get_pipeline(self, pipeline_name):
        if not pipeline_name in self._cached_pipelines:
            self._cached_pipelines[pipeline_name] = self._build_pipeline(pipeline_name)

        return self._cached_pipelines[pipeline_name]

    def _build_pipeline(self, pipeline_name):
        orig_handle = self.get_handle()
        if orig_handle.is_resolved_to_pipeline:
            pipeline_def = orig_handle.build_pipeline_definition()
            check.invariant(
                pipeline_def.name == pipeline_name,
                '''Dagster GraphQL Context resolved pipeline with name {handle_pipeline_name},
                couldn't resolve {pipeline_name}'''.format(
                    handle_pipeline_name=pipeline_def.name, pipeline_name=pipeline_name
                ),
            )
            return pipeline_def
        return self.get_handle().with_pipeline_name(pipeline_name).build_pipeline_definition()

    @property
    def is_reload_supported(self):
        return self.reloader and self.reloader.is_reload_supported
