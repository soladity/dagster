from dagster import check
from dagster.core.storage.file_manager import LocalFileManager, FileManager
from dagster.core.storage.intermediate_store import FileSystemIntermediateStore
from dagster.core.storage.intermediates_manager import (
    IntermediatesManager,
    InMemoryIntermediatesManager,
    IntermediateStoreIntermediatesManager,
)
from dagster.core.storage.runs import RunStorage, InMemoryRunStorage, FileSystemRunStorage
from dagster.core.types.field_utils import check_user_facing_opt_field_param
from dagster.core.types import Field, Dict, String


class SystemStorageDefinition:
    '''
    Dagster stores run metadata and intermediate data on the user's behalf.
    The SystemStorageDefinition exists is in order to configure and customized
    those behaviors.

    Example storage definitions are the mem_system_storage in this module,
    which storages all intermediates and run data in memory. and the fs_system_storage,
    which stores all that data in the local filesystem.

    In dagster_aws there is the S3SystemStorageDefinition. We anticipated having
    system storage for every major cloud provider. And it is user customizable
    for users with custom infrastructure needs.

    The storage definitions pass into the ModeDefinition determinees the config
    schema of the "storage" section of the environment configuration.

    Args:
        name (str): Name of the storage mode.
        is_persistent (bool): Does storage def persist in way that can cross process/node
            boundaries. Execution with, for example, the multiprocess executor or within
            the context of dagster-airflow require a persistent storage mode.
        config_field (Field): Configuration field for its section of the storage config.
        system_storage_creation_fn: (Callable[InitSystemStorageContext, SystemStorageData])
            Called by the system. The author of the StorageSystemDefinition must provide this function,
            which consumes the init context and then emits the SystemStorageData.
    '''

    def __init__(
        self,
        name,
        is_persistent,
        config_field=None,
        system_storage_creation_fn=None,
        required_resources=None,
    ):
        self.name = check.str_param(name, 'name')
        self.is_persistent = check.bool_param(is_persistent, 'is_persistent')
        self.config_field = check_user_facing_opt_field_param(
            config_field,
            'config_field',
            'of a SystemStorageDefinition named {name}'.format(name=name),
        )
        self.system_storage_creation_fn = check.opt_callable_param(
            system_storage_creation_fn, 'system_storage_creation_fn'
        )
        self.required_resources = check.opt_set_param(
            required_resources, 'required_resources', of_type=str
        )


class SystemStorageData:
    def __init__(self, run_storage, intermediates_manager, file_manager=None):
        self.run_storage = check.inst_param(run_storage, 'run_storage', RunStorage)
        self.intermediates_manager = check.inst_param(
            intermediates_manager, 'intermediates_manager', IntermediatesManager
        )
        # TODO: Make required when https://github.com/dagster-io/dagster/issues/1456 is complete
        self.file_manager = check.opt_inst_param(file_manager, 'file_manager', FileManager)


def system_storage(name=None, is_persistent=True, config_field=None, required_resources=None):
    if callable(name):
        check.invariant(name is None)
        check.invariant(is_persistent is True)
        check.invariant(config_field is None)
        check.invariant(required_resources is None)
        return _SystemStorageDecoratorCallable()(name)

    return _SystemStorageDecoratorCallable(
        name=name,
        is_persistent=is_persistent,
        config_field=config_field,
        required_resources=required_resources,
    )


class _SystemStorageDecoratorCallable:
    def __init__(self, name=None, is_persistent=True, config_field=None, required_resources=None):
        self.name = check.opt_str_param(name, 'name')
        self.is_persistent = check.bool_param(is_persistent, 'is_persistent')
        self.config_field = config_field  # type check in definition
        self.required_resources = required_resources  # type check in definition

    def __call__(self, fn):
        check.callable_param(fn, 'fn')

        if not self.name:
            self.name = fn.__name__

        return SystemStorageDefinition(
            name=self.name,
            is_persistent=self.is_persistent,
            config_field=self.config_field,
            system_storage_creation_fn=fn,
            required_resources=self.required_resources,
        )


def create_mem_system_storage_data(init_context):
    return SystemStorageData(
        run_storage=InMemoryRunStorage(),
        intermediates_manager=InMemoryIntermediatesManager(),
        file_manager=LocalFileManager(
            LocalFileManager.default_base_dir(init_context.run_config.run_id)
        ),
    )


@system_storage(name='in_memory', is_persistent=False)
def mem_system_storage(init_context):
    return create_mem_system_storage_data(init_context)


@system_storage(
    name='filesystem',
    is_persistent=True,
    config_field=Field(Dict({'base_dir': Field(String, is_optional=True)})),
)
def fs_system_storage(init_context):
    base_dir = init_context.system_storage_config.get('base_dir')
    return SystemStorageData(
        file_manager=LocalFileManager(
            LocalFileManager.default_base_dir(init_context.run_config.run_id)
        ),
        run_storage=FileSystemRunStorage(base_dir=base_dir),
        intermediates_manager=IntermediateStoreIntermediatesManager(
            FileSystemIntermediateStore(
                run_id=init_context.run_config.run_id,
                type_storage_plugin_registry=init_context.type_storage_plugin_registry,
                base_dir=base_dir,
            )
        ),
    )
