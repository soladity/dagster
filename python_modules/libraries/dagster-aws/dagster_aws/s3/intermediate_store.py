from dagster import check
from dagster.core.storage.intermediate_store import IntermediateStore
from dagster.core.storage.type_storage import TypeStoragePluginRegistry

from .object_store import S3ObjectStore


class S3IntermediateStore(IntermediateStore):
    def __init__(self, s3_bucket, run_id, s3_session=None, type_storage_plugin_registry=None):
        check.str_param(s3_bucket, 's3_bucket')
        check.str_param(run_id, 'run_id')

        object_store = S3ObjectStore(s3_bucket, s3_session=s3_session)
        root = object_store.key_for_paths(['dagster', 'storage', run_id])

        super(S3IntermediateStore, self).__init__(
            object_store,
            root,
            type_storage_plugin_registry=check.inst_param(
                type_storage_plugin_registry
                if type_storage_plugin_registry
                else TypeStoragePluginRegistry(types_to_register={}),
                'type_storage_plugin_registry',
                TypeStoragePluginRegistry,
            ),
        )

    def copy_object_from_prev_run(
        self, context, previous_run_id, paths
    ):  # pylint: disable=unused-argument
        check.not_implemented('not supported: TODO for max. put issue number here')
