from collections import defaultdict, namedtuple
from enum import Enum

import six

from dagster import check
from dagster.core.events import DagsterEventType
from dagster.core.events.log import EventRecord
from dagster.core.storage.pipeline_run import PipelineRunStatsSnapshot
from dagster.serdes import whitelist_for_serdes
from dagster.utils import datetime_as_float


def build_run_stats_from_events(run_id, records):
    try:
        iter(records)
    except TypeError as exc:
        six.raise_from(
            check.ParameterCheckError(
                'Invariant violation for parameter \'records\'. Description: Expected iterable.'
            ),
            from_value=exc,
        )
    for i, record in enumerate(records):
        check.inst_param(record, 'records[{i}]'.format(i=i), EventRecord)

    steps_succeeded = 0
    steps_failed = 0
    materializations = 0
    expectations = 0
    start_time = None
    end_time = None

    for event in records:
        if not event.is_dagster_event:
            continue
        if event.dagster_event.event_type == DagsterEventType.PIPELINE_START:
            start_time = datetime_as_float(event.timestamp)
        if event.dagster_event.event_type == DagsterEventType.STEP_FAILURE:
            steps_failed += 1
        if event.dagster_event.event_type == DagsterEventType.STEP_SUCCESS:
            steps_succeeded += 1
        if event.dagster_event.event_type == DagsterEventType.STEP_MATERIALIZATION:
            materializations += 1
        if event.dagster_event.event_type == DagsterEventType.STEP_EXPECTATION_RESULT:
            expectations += 1
        if (
            event.dagster_event.event_type == DagsterEventType.PIPELINE_SUCCESS
            or event.dagster_event.event_type == DagsterEventType.PIPELINE_FAILURE
        ):
            end_time = datetime_as_float(event.timestamp)

    return PipelineRunStatsSnapshot(
        run_id, steps_succeeded, steps_failed, materializations, expectations, start_time, end_time
    )


class StepEventStatus(Enum):
    SKIPPED = 'SKIPPED'
    SUCCESS = 'SUCCESS'
    FAILURE = 'FAILURE'


def build_run_step_stats_from_events(run_id, records):
    check.list_param(records, 'records', EventRecord)
    by_step_key = defaultdict(dict)
    for event in records:
        if not event.is_dagster_event:
            continue

        step_key = event.dagster_event.step_key
        if not step_key:
            continue

        if event.dagster_event.event_type == DagsterEventType.STEP_START:
            by_step_key[step_key]['start_time'] = event.timestamp
        if event.dagster_event.event_type == DagsterEventType.STEP_FAILURE:
            by_step_key[step_key]['end_time'] = event.timestamp
            by_step_key[step_key]['status'] = DagsterEventType.STEP_FAILURE
        if event.dagster_event.event_type == DagsterEventType.STEP_SUCCESS:
            by_step_key[step_key]['end_time'] = event.timestamp
            by_step_key[step_key]['status'] = DagsterEventType.STEP_SUCCESS
        if event.dagster_event.event_type == DagsterEventType.STEP_SKIPPED:
            by_step_key[step_key]['end_time'] = event.timestamp
            by_step_key[step_key]['status'] = DagsterEventType.STEP_SKIPPED

    return [
        RunStepKeyStatsSnapshot(run_id=run_id, step_key=step_key, **value)
        for step_key, value in by_step_key.items()
    ]


@whitelist_for_serdes
class RunStepKeyStatsSnapshot(
    namedtuple('_RunStepKeyStatsSnapshot', ('run_id step_key status start_time end_time'),)
):
    def __new__(
        cls, run_id, step_key, status=None, start_time=None, end_time=None,
    ):

        return super(RunStepKeyStatsSnapshot, cls).__new__(
            cls,
            run_id=check.str_param(run_id, 'run_id'),
            step_key=check.str_param(step_key, 'step_key'),
            status=check.opt_inst_param(status, 'status', StepEventStatus),
            start_time=check.opt_float_param(start_time, 'start_time'),
            end_time=check.opt_float_param(end_time, 'end_time'),
        )
