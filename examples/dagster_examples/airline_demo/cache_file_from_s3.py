from dagster import (
    Dict,
    EventMetadataEntry,
    ExpectationResult,
    Field,
    FileHandle,
    InputDefinition,
    OutputDefinition,
    Output,
    String,
    solid,
)
from dagster.utils.test import get_temp_file_name

from dagster_aws.s3.solids import S3BucketData


@solid(
    inputs=[InputDefinition('bucket_data', S3BucketData)],
    outputs=[OutputDefinition(FileHandle)],
    config_field=Field(
        Dict(
            {
                'file_key': Field(
                    String,
                    is_optional=True,
                    description=(
                        'Optionally specify the key for the file to be ingested '
                        'into the keyed store. Defaults to the last path component '
                        'of the downloaded s3 key.'
                    ),
                )
            }
        )
    ),
    required_resources={'file_cache', 's3'},
    description='''This is a solid which caches a file in s3 into file cache.

The `file_cache` is a resource type that allows a solid author to save files
and assign a key to them. The keyed file store can be backed by local file or any
object store (currently we support s3). This keyed file store can be configured
to be at an external location so that is persists in a well known spot between runs.
It is designed for the case where there is an expensive download step that should not
occur unless the downloaded file does not exist. Redownload can be instigated either
by configuring the source to overwrite files or to just delete the file in the underlying
storage manually.

This works by downloading the file to a temporary file, and then ingesting it into
the file cache. In the case of a filesystem-backed file cache, this is a file
copy. In the case of a object-store-backed file cache, this is an upload.

In order to work this must be executed within a mode that provides an `s3`
and `file_cache` resource.
    ''',
)
def cache_file_from_s3(context, bucket_data):
    target_key = context.solid_config.get('file_key', bucket_data['key'].split('/')[-1])

    file_cache = context.resources.file_cache

    file_handle = file_cache.get_file_handle(target_key)

    if file_cache.overwrite or not file_cache.has_file_object(target_key):

        with get_temp_file_name() as tmp_file:
            context.resources.s3.session.download_file(
                Bucket=bucket_data['bucket'], Key=bucket_data['key'], Filename=tmp_file
            )

            context.log.info('File downloaded to {}'.format(tmp_file))

            with open(tmp_file, 'rb') as tmp_file_object:
                file_cache.write_file_object(target_key, tmp_file_object)
                context.log.info('File handle written at : {}'.format(file_handle.path_desc))
    else:
        context.log.info('File {} already present in cache'.format(file_handle.path_desc))

    yield ExpectationResult(
        success=file_cache.has_file_object(target_key),
        label='file_handle_exists',
        metadata_entries=[EventMetadataEntry.path(path=file_handle.path_desc, label=target_key)],
    )
    yield Output(file_handle)
