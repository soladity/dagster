import warnings
from base64 import b64decode
from json import JSONDecodeError, loads
from typing import Optional

from dagster.core.host_representation import ExternalPipeline
from dagster.core.run_coordinator import QueuedRunCoordinator
from dagster.core.storage.pipeline_run import PipelineRun
from flask import has_request_context, request


class CustomRunCoordinator(QueuedRunCoordinator):

    # start_email_marker
    def get_email(self, jwt_claims_header: Optional[str]) -> Optional[str]:
        if not jwt_claims_header:
            return None

        split_header_tokens = jwt_claims_header.split(".")
        if len(split_header_tokens) < 2:
            return None

        decoded_claims_json_str = b64decode(split_header_tokens[1])
        try:
            claims_json = loads(decoded_claims_json_str)
            return claims_json.get("email")
        except JSONDecodeError:
            return None

    # end_email_marker

    # start_submit_marker
    def submit_run(
        self, pipeline_run: PipelineRun, external_pipeline: ExternalPipeline
    ) -> PipelineRun:
        jwt_claims_header = (
            request.headers.get("X-Amzn-Oidc-Data", None) if has_request_context() else None
        )
        email = self.get_email(jwt_claims_header)
        if email:
            self._instance.add_run_tags(pipeline_run.run_id, {"user": email})
        else:
            warnings.warn(f"Couldn't decode JWT header {jwt_claims_header}")
        return super().submit_run(pipeline_run, external_pipeline)

    # end_submit_marker
