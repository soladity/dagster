from collections import defaultdict, namedtuple
from enum import Enum
from typing import Any, Dict, Iterable, List, cast

from dagster import check
from dagster.core.definitions import AssetMaterialization, ExpectationResult, Materialization
from dagster.core.events import DagsterEventType, StepExpectationResultData, StepMaterializationData
from dagster.core.events.log import EventLogEntry
from dagster.core.storage.pipeline_run import PipelineRunStatsSnapshot
from dagster.serdes import whitelist_for_serdes
from dagster.utils import datetime_as_float


def build_run_stats_from_events(run_id, records):
    try:
        iter(records)
    except TypeError as exc:
        raise check.ParameterCheckError(
            "Invariant violation for parameter 'records'. Description: Expected iterable."
        ) from exc
    for i, record in enumerate(records):
        check.inst_param(record, f"records[{i}]", EventLogEntry)

    steps_succeeded = 0
    steps_failed = 0
    materializations = 0
    expectations = 0
    enqueued_time = None
    launch_time = None
    start_time = None
    end_time = None

    for event in records:
        if not event.is_dagster_event:
            continue
        dagster_event = event.get_dagster_event()

        event_timestamp_float = (
            event.timestamp
            if isinstance(event.timestamp, float)
            else datetime_as_float(event.timestamp)
        )
        if dagster_event.event_type == DagsterEventType.PIPELINE_START:
            start_time = event_timestamp_float
        if dagster_event.event_type == DagsterEventType.PIPELINE_STARTING:
            launch_time = event_timestamp_float
        if dagster_event.event_type == DagsterEventType.PIPELINE_ENQUEUED:
            enqueued_time = event_timestamp_float
        if dagster_event.event_type == DagsterEventType.STEP_FAILURE:
            steps_failed += 1
        if dagster_event.event_type == DagsterEventType.STEP_SUCCESS:
            steps_succeeded += 1
        if dagster_event.event_type == DagsterEventType.ASSET_MATERIALIZATION:
            materializations += 1
        if dagster_event.event_type == DagsterEventType.STEP_EXPECTATION_RESULT:
            expectations += 1
        if (
            dagster_event.event_type == DagsterEventType.PIPELINE_SUCCESS
            or dagster_event.event_type == DagsterEventType.PIPELINE_FAILURE
            or dagster_event.event_type == DagsterEventType.PIPELINE_CANCELED
        ):
            end_time = (
                event.timestamp
                if isinstance(event.timestamp, float)
                else datetime_as_float(event.timestamp)
            )

    return PipelineRunStatsSnapshot(
        run_id,
        steps_succeeded,
        steps_failed,
        materializations,
        expectations,
        enqueued_time,
        launch_time,
        start_time,
        end_time,
    )


class StepEventStatus(Enum):
    SKIPPED = "SKIPPED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


def build_run_step_stats_from_events(
    run_id: str, records: Iterable[EventLogEntry]
) -> List["RunStepKeyStatsSnapshot"]:
    by_step_key: Dict[str, Dict[str, Any]] = defaultdict(dict)
    for event in records:
        if not event.is_dagster_event:
            continue
        dagster_event = event.get_dagster_event()

        step_key = dagster_event.step_key
        if not step_key:
            continue

        if dagster_event.event_type == DagsterEventType.STEP_START:
            by_step_key[step_key]["start_time"] = event.timestamp
            by_step_key[step_key]["attempts"] = 1
        if dagster_event.event_type == DagsterEventType.STEP_FAILURE:
            by_step_key[step_key]["end_time"] = event.timestamp
            by_step_key[step_key]["status"] = StepEventStatus.FAILURE
        if dagster_event.event_type == DagsterEventType.STEP_RESTARTED:
            by_step_key[step_key]["attempts"] = int(by_step_key[step_key].get("attempts") or 0) + 1
        if dagster_event.event_type == DagsterEventType.STEP_SUCCESS:
            by_step_key[step_key]["end_time"] = event.timestamp
            by_step_key[step_key]["status"] = StepEventStatus.SUCCESS
        if dagster_event.event_type == DagsterEventType.STEP_SKIPPED:
            by_step_key[step_key]["end_time"] = event.timestamp
            by_step_key[step_key]["status"] = StepEventStatus.SKIPPED
        if dagster_event.event_type == DagsterEventType.ASSET_MATERIALIZATION:
            event_specific_data = cast(StepMaterializationData, dagster_event.event_specific_data)
            materialization = event_specific_data.materialization
            step_materializations = by_step_key[step_key].get("materializations", [])
            step_materializations.append(materialization)
            by_step_key[step_key]["materializations"] = step_materializations
        if dagster_event.event_type == DagsterEventType.STEP_EXPECTATION_RESULT:
            expectation_data = cast(StepExpectationResultData, dagster_event.event_specific_data)
            expectation_result = expectation_data.expectation_result
            step_expectation_results = by_step_key[step_key].get("expectation_results", [])
            step_expectation_results.append(expectation_result)
            by_step_key[step_key]["expectation_results"] = step_expectation_results

    return [
        RunStepKeyStatsSnapshot(run_id=run_id, step_key=step_key, **value)
        for step_key, value in by_step_key.items()
    ]


@whitelist_for_serdes
class RunStepKeyStatsSnapshot(
    namedtuple(
        "_RunStepKeyStatsSnapshot",
        (
            "run_id step_key status start_time end_time materializations expectation_results attempts"
        ),
    )
):
    def __new__(
        cls,
        run_id,
        step_key,
        status=None,
        start_time=None,
        end_time=None,
        materializations=None,
        expectation_results=None,
        attempts=None,
    ):

        return super(RunStepKeyStatsSnapshot, cls).__new__(
            cls,
            run_id=check.str_param(run_id, "run_id"),
            step_key=check.str_param(step_key, "step_key"),
            status=check.opt_inst_param(status, "status", StepEventStatus),
            start_time=check.opt_float_param(start_time, "start_time"),
            end_time=check.opt_float_param(end_time, "end_time"),
            materializations=check.opt_list_param(
                materializations, "materializations", (AssetMaterialization, Materialization)
            ),
            expectation_results=check.opt_list_param(
                expectation_results, "expectation_results", ExpectationResult
            ),
            attempts=check.opt_int_param(attempts, "attempts"),
        )
