"""isort:skip_file"""

# start_custom_run_coordinator_marker

from dagster.core.host_representation import ExternalPipeline
from dagster.core.run_coordinator import QueuedRunCoordinator
from dagster.core.storage.pipeline_run import PipelineRun


class CustomRunCoordinator(QueuedRunCoordinator):
    def submit_run(
        self, pipeline_run: PipelineRun, external_pipeline: ExternalPipeline
    ) -> PipelineRun:
        pass


# end_custom_run_coordinator_marker

CUSTOM_HEADER_NAME = "X-SOME-HEADER"

# start_flask_header_marker

from flask import has_request_context, request

desired_header = request.headers.get(CUSTOM_HEADER_NAME) if has_request_context() else None

# end_flask_header_marker
