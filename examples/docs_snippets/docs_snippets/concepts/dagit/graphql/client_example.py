"""isort:skip_file"""
# pylint: disable=W0404
# start_setup_marker
from dagster_graphql import DagsterGraphQLClient

client = DagsterGraphQLClient("localhost", port_number=3000)

# end_setup_marker

RUN_ID = "foo"
REPO_NAME = "bar"
PIPELINE_NAME = "baz"
REPO_NAME = "quux"
REPO_LOCATION_NAME = "corge"
PRESET_NAME = "waldo"


def do_something_on_success(some_arg=None):  # pylint: disable=W0613
    pass


def do_something_else():
    pass


def do_something_with_exc(some_exception):  # pylint: disable=W0613
    pass


# start_submit_marker_default
from dagster_graphql import DagsterGraphQLClientError

try:
    new_run_id: str = client.submit_pipeline_execution(
        PIPELINE_NAME,
        repository_location_name=REPO_LOCATION_NAME,
        repository_name=REPO_NAME,
        run_config={},
        mode="default",
    )
    do_something_on_success(new_run_id)
except DagsterGraphQLClientError as exc:
    do_something_with_exc(exc)
    raise exc
# end_submit_marker_default


# start_submit_marker_preset
from dagster_graphql import DagsterGraphQLClientError

try:
    new_run_id: str = client.submit_pipeline_execution(
        PIPELINE_NAME,
        repository_location_name=REPO_LOCATION_NAME,
        repository_name=REPO_NAME,
        preset=PRESET_NAME,
    )
    do_something_on_success(new_run_id)
except DagsterGraphQLClientError as exc:
    do_something_with_exc(exc)
    raise exc
# end_submit_marker_preset


# start_submit_marker_pipeline_name_only
from dagster_graphql import DagsterGraphQLClientError

try:
    new_run_id: str = client.submit_pipeline_execution(
        PIPELINE_NAME,
        run_config={},
        mode="default",
    )
    do_something_on_success(new_run_id)
except DagsterGraphQLClientError as exc:
    do_something_with_exc(exc)
    raise exc
# end_submit_marker_pipeline_name_only


# start_run_status_marker
from dagster_graphql import DagsterGraphQLClientError
from dagster.core.storage.pipeline_run import PipelineRunStatus

try:
    status: PipelineRunStatus = client.get_run_status(RUN_ID)
    if status == PipelineRunStatus.SUCCESS:
        do_something_on_success()
    else:
        do_something_else()
except DagsterGraphQLClientError as exc:
    do_something_with_exc(exc)
    raise exc
# end_run_status_marker


# start_reload_repo_location_marker
from dagster_graphql import (
    ReloadRepositoryLocationInfo,
    ReloadRepositoryLocationStatus,
)

reload_info: ReloadRepositoryLocationInfo = client.reload_repository_location(REPO_NAME)
if reload_info.status == ReloadRepositoryLocationStatus.SUCCESS:
    do_something_on_success()
else:
    raise Exception(f"Repository location reload failed with message: {reload_info.message}")
# end_reload_repo_location_marker
