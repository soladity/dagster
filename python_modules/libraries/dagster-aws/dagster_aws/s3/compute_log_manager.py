import os

from dagster import check
from dagster.core.storage.compute_log_manager import (
    MAX_BYTES_FILE_READ,
    ComputeIOType,
    ComputeLogData,
    ComputeLogFileData,
    ComputeLogManager,
)
from dagster.core.storage.local_compute_log_manager import IO_TYPE_EXTENSION, LocalComputeLogManager
from dagster.utils import ensure_dir, ensure_file

from .utils import create_s3_session


class S3ComputeLogManager(ComputeLogManager):
    def __init__(self, local_dir, bucket=''):
        self._s3_session = create_s3_session()
        self._s3_bucket = check.str_param(bucket, 'bucket')
        self._download_urls = {}

        # proxy calls to local compute log manager (for subscriptions, etc)
        self.local_manager = LocalComputeLogManager(local_dir)

    def get_local_path(self, run_id, step_key, io_type):
        return self.local_manager.get_local_path(run_id, step_key, io_type)

    def on_compute_start(self, step_context):
        self.local_manager.on_compute_start(step_context)

    def on_compute_finish(self, step_context):
        self.local_manager.on_compute_finish(step_context)
        self._upload_from_local(step_context.run_id, step_context.step.key, ComputeIOType.STDOUT)
        self._upload_from_local(step_context.run_id, step_context.step.key, ComputeIOType.STDERR)

    def is_compute_completed(self, run_id, step_key):
        return self.local_manager.is_compute_completed(run_id, step_key)

    def download_url(self, run_id, step_key, io_type):
        if not self.is_compute_completed(run_id, step_key):
            return self.local_manager.download_url(run_id, step_key, io_type)
        key = self._bucket_key(run_id, step_key, io_type)
        if key in self._download_urls:
            return self._download_urls[key]
        url = self._s3_session.generate_presigned_url(
            ClientMethod='get_object', Params={'Bucket': self._s3_bucket, 'Key': key}
        )
        self._download_urls[key] = url
        return url

    def read_logs(self, run_id, step_key, cursor=None, max_bytes=MAX_BYTES_FILE_READ):
        # Need to wrap the log data from the local manager to use the current manager methods
        if self._should_download(run_id, step_key, ComputeIOType.STDOUT):
            self._download_to_local(run_id, step_key, ComputeIOType.STDOUT)
        if self._should_download(run_id, step_key, ComputeIOType.STDERR):
            self._download_to_local(run_id, step_key, ComputeIOType.STDERR)
        data = self.local_manager.read_logs(run_id, step_key, cursor, max_bytes)
        return ComputeLogData(
            self._from_local_file_data(run_id, step_key, ComputeIOType.STDOUT, data.stdout),
            self._from_local_file_data(run_id, step_key, ComputeIOType.STDERR, data.stderr),
            data.cursor,
        )

    def on_subscribe(self, subscription):
        self.local_manager.on_subscribe(subscription)

    def _should_download(self, run_id, step_key, io_type):
        local_path = self.get_local_path(run_id, step_key, io_type)
        if os.path.exists(local_path):
            return False
        s3_objects = self._s3_session.list_objects(
            Bucket=self._s3_bucket, Prefix=self._bucket_key(run_id, step_key, io_type)
        )
        return len(s3_objects) > 0

    def _from_local_file_data(self, run_id, step_key, io_type, local_file_data):
        is_complete = self.is_compute_completed(run_id, step_key)
        path = (
            's3://{}/{}'.format(self._s3_bucket, self._bucket_key(run_id, step_key, io_type))
            if is_complete
            else local_file_data.path
        )

        return ComputeLogFileData(
            path,
            local_file_data.data,
            local_file_data.cursor,
            local_file_data.size,
            self.download_url(run_id, step_key, io_type),
        )

    def _upload_from_local(self, run_id, step_key, io_type):
        path = self.get_local_path(run_id, step_key, io_type)
        ensure_file(path)
        key = self._bucket_key(run_id, step_key, io_type)
        with open(path, 'rb') as data:
            self._s3_session.upload_fileobj(data, self._s3_bucket, key)

    def _download_to_local(self, run_id, step_key, io_type):
        path = self.get_local_path(run_id, step_key, io_type)
        ensure_dir(os.path.dirname(path))
        with open(path, 'wb') as fileobj:
            self._s3_session.download_fileobj(
                self._s3_bucket, self._bucket_key(run_id, step_key, io_type), fileobj
            )

    def _bucket_key(self, run_id, step_key, io_type):
        check.inst_param(io_type, 'io_type', ComputeIOType)
        extension = IO_TYPE_EXTENSION[io_type]
        paths = ['dagster', 'runs', run_id, 'compute_logs', '{}.{}'.format(step_key, extension)]
        return '/'.join(paths)  # s3 path delimiter
