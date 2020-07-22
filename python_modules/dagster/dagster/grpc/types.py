from collections import namedtuple

from dagster import check
from dagster.core.code_pointer import (
    CodePointer,
    FileCodePointer,
    FileInDirectoryCodePointer,
    ModuleCodePointer,
    PackageCodePointer,
)
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.instance.ref import InstanceRef
from dagster.core.origin import PipelinePythonOrigin, RepositoryOrigin, RepositoryPythonOrigin
from dagster.serdes import whitelist_for_serdes
from dagster.utils.error import SerializableErrorInfo


class LoadableTargetOrigin(
    namedtuple(
        'LoadableTargetOrigin',
        'executable_path python_file module_name working_directory attribute',
    )
):
    def __new__(
        cls,
        executable_path=None,
        python_file=None,
        module_name=None,
        working_directory=None,
        attribute=None,
    ):
        return super(LoadableTargetOrigin, cls).__new__(
            cls,
            executable_path=check.opt_str_param(executable_path, 'executable_path'),
            python_file=check.opt_str_param(python_file, 'python_file'),
            module_name=check.opt_str_param(module_name, 'module_name'),
            working_directory=check.opt_str_param(working_directory, 'working_directory'),
            attribute=check.opt_str_param(attribute, 'attribute'),
        )

    @staticmethod
    def from_python_origin(repository_python_origin):
        check.inst_param(
            repository_python_origin, 'repository_python_origin', RepositoryPythonOrigin
        )
        executable_path = repository_python_origin.executable_path
        code_pointer = repository_python_origin.code_pointer
        if isinstance(code_pointer, FileCodePointer):
            return LoadableTargetOrigin(
                executable_path=executable_path,
                python_file=code_pointer.python_file,
                attribute=code_pointer.fn_name,
            )
        elif isinstance(code_pointer, FileInDirectoryCodePointer):
            return LoadableTargetOrigin(
                executable_path=executable_path,
                python_file=code_pointer.python_file,
                attribute=code_pointer.fn_name,
                working_directory=code_pointer.working_directory,
            )
        elif isinstance(code_pointer, ModuleCodePointer):
            return LoadableTargetOrigin(
                executable_path=executable_path,
                module_name=code_pointer.module,
                attribute=code_pointer.fn_name,
            )
        elif isinstance(code_pointer, PackageCodePointer):
            return LoadableTargetOrigin(
                executable_path=executable_path,
                module_name=code_pointer.module,
                attribute=code_pointer.attribute,
            )
        else:
            raise DagsterInvariantViolationError(
                "Unexpected code pointer {code_pointer_name}".format(
                    code_pointer_name=type(code_pointer).__name__
                )
            )


@whitelist_for_serdes
class ExecutionPlanSnapshotArgs(
    namedtuple(
        '_ExecutionPlanSnapshotArgs',
        'pipeline_origin solid_selection run_config mode step_keys_to_execute pipeline_snapshot_id',
    )
):
    def __new__(
        cls,
        pipeline_origin,
        solid_selection,
        run_config,
        mode,
        step_keys_to_execute,
        pipeline_snapshot_id,
    ):
        return super(ExecutionPlanSnapshotArgs, cls).__new__(
            cls,
            pipeline_origin=check.inst_param(
                pipeline_origin, 'pipeline_origin', PipelinePythonOrigin
            ),
            solid_selection=check.opt_list_param(solid_selection, 'solid_selection', of_type=str),
            run_config=check.dict_param(run_config, 'run_config'),
            mode=check.str_param(mode, 'mode'),
            step_keys_to_execute=check.opt_list_param(
                step_keys_to_execute, 'step_keys_to_execute', of_type=str
            ),
            pipeline_snapshot_id=check.str_param(pipeline_snapshot_id, 'pipeline_snapshot_id'),
        )


@whitelist_for_serdes
class ExecuteRunArgs(namedtuple('_ExecuteRunArgs', 'pipeline_origin pipeline_run_id instance_ref')):
    def __new__(cls, pipeline_origin, pipeline_run_id, instance_ref):
        return super(ExecuteRunArgs, cls).__new__(
            cls,
            pipeline_origin=check.inst_param(
                pipeline_origin, 'pipeline_origin', PipelinePythonOrigin
            ),
            pipeline_run_id=check.str_param(pipeline_run_id, 'pipeline_run_id'),
            instance_ref=check.inst_param(instance_ref, 'instance_ref', InstanceRef),
        )


@whitelist_for_serdes
class LoadableRepositorySymbol(
    namedtuple('_LoadableRepositorySymbol', 'repository_name attribute')
):
    def __new__(cls, repository_name, attribute):
        return super(LoadableRepositorySymbol, cls).__new__(
            cls,
            repository_name=check.str_param(repository_name, 'repository_name'),
            attribute=check.str_param(attribute, 'attribute'),
        )


@whitelist_for_serdes
class ListRepositoriesResponse(
    namedtuple(
        '_ListRepositoriesResponse',
        'repository_symbols executable_path repository_code_pointer_dict',
    )
):
    def __new__(
        cls, repository_symbols, executable_path=None, repository_code_pointer_dict=None,
    ):
        return super(ListRepositoriesResponse, cls).__new__(
            cls,
            repository_symbols=check.list_param(
                repository_symbols, 'repository_symbols', of_type=LoadableRepositorySymbol
            ),
            # These are currently only used by the GRPC Repository Location, but
            # we will need to migrate the rest of the repository locations to use this.
            executable_path=check.opt_str_param(executable_path, 'executable_path'),
            repository_code_pointer_dict=check.opt_dict_param(
                repository_code_pointer_dict,
                'repository_code_pointer_dict',
                key_type=str,
                value_type=CodePointer,
            ),
        )


@whitelist_for_serdes
class ListRepositoriesInput(
    namedtuple('_ListRepositoriesInput', 'module_name python_file working_directory')
):
    def __new__(cls, module_name, python_file, working_directory):
        check.invariant(not (module_name and python_file), 'Must set only one')
        check.invariant(module_name or python_file, 'Must set at least one')
        return super(ListRepositoriesInput, cls).__new__(
            cls,
            module_name=check.opt_str_param(module_name, 'module_name'),
            python_file=check.opt_str_param(python_file, 'python_file'),
            working_directory=check.opt_str_param(working_directory, 'working_directory'),
        )


@whitelist_for_serdes
class PartitionArgs(
    namedtuple('_PartitionArgs', 'repository_origin partition_set_name partition_name')
):
    def __new__(cls, repository_origin, partition_set_name, partition_name):
        return super(PartitionArgs, cls).__new__(
            cls,
            repository_origin=check.inst_param(
                repository_origin, 'repository_origin', RepositoryOrigin
            ),
            partition_set_name=check.str_param(partition_set_name, 'partition_set_name'),
            partition_name=check.str_param(partition_name, 'partition_name'),
        )


@whitelist_for_serdes
class PartitionNamesArgs(namedtuple('_PartitionNamesArgs', 'repository_origin partition_set_name')):
    def __new__(cls, repository_origin, partition_set_name):
        return super(PartitionNamesArgs, cls).__new__(
            cls,
            repository_origin=check.inst_param(
                repository_origin, 'repository_origin', RepositoryOrigin
            ),
            partition_set_name=check.str_param(partition_set_name, 'partition_set_name'),
        )


@whitelist_for_serdes
class PipelineSubsetSnapshotArgs(
    namedtuple('_PipelineSubsetSnapshotArgs', 'pipeline_origin solid_selection')
):
    def __new__(cls, pipeline_origin, solid_selection):
        return super(PipelineSubsetSnapshotArgs, cls).__new__(
            cls,
            pipeline_origin=check.inst_param(
                pipeline_origin, 'pipeline_origin', PipelinePythonOrigin
            ),
            solid_selection=check.list_param(solid_selection, 'solid_selection', of_type=str)
            if solid_selection
            else None,
        )


@whitelist_for_serdes
class ExternalScheduleExecutionArgs(
    namedtuple('_ExternalScheduleExecutionArgs', 'repository_origin instance_ref schedule_name')
):
    def __new__(cls, repository_origin, instance_ref, schedule_name):
        return super(ExternalScheduleExecutionArgs, cls).__new__(
            cls,
            repository_origin=check.inst_param(
                repository_origin, 'repository_origin', RepositoryOrigin
            ),
            instance_ref=check.inst_param(instance_ref, 'instance_ref', InstanceRef),
            schedule_name=check.str_param(schedule_name, 'schedule_name'),
        )


@whitelist_for_serdes
class ShutdownServerResult(namedtuple('_ShutdownServerResult', 'success serializable_error_info')):
    def __new__(cls, success, serializable_error_info):
        return super(ShutdownServerResult, cls).__new__(
            cls,
            success=check.bool_param(success, 'success'),
            serializable_error_info=check.opt_inst_param(
                serializable_error_info, 'serializable_error_info', SerializableErrorInfo
            ),
        )
