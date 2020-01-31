import uuid

import pytest
import yaml

from dagster.core.definitions.pipeline import PipelineRunsFilter
from dagster.core.events import DagsterEvent, DagsterEventType
from dagster.core.instance import DagsterInstance
from dagster.core.storage.pipeline_run import PipelineRun, PipelineRunStatus
from dagster.utils.test.run_storage import TestRunStorage

TestRunStorage.__test__ = False


class TestPostgresRunStorage(TestRunStorage):
    __test__ = True

    @pytest.fixture(scope='function', name='storage')
    def run_storage(self, clean_storage):  # pylint: disable=arguments-differ
        return clean_storage


def build_run(
    run_id, pipeline_name, mode='default', tags=None, status=PipelineRunStatus.NOT_STARTED
):
    from dagster.core.definitions.pipeline import ExecutionSelector

    return PipelineRun(
        pipeline_name=pipeline_name,
        run_id=run_id,
        environment_dict=None,
        mode=mode,
        selector=ExecutionSelector(pipeline_name),
        step_keys_to_execute=None,
        tags=tags,
        status=status,
    )


def test_add_get_postgres_run_storage(clean_storage):
    run_storage = clean_storage
    run_id = str(uuid.uuid4())
    run_to_add = build_run(pipeline_name='pipeline_name', run_id=run_id)
    added = run_storage.add_run(run_to_add)
    assert added

    fetched_run = run_storage.get_run_by_id(run_id)

    assert run_to_add == fetched_run

    assert run_storage.has_run(run_id)
    assert not run_storage.has_run(str(uuid.uuid4()))

    assert run_storage.get_runs() == [run_to_add]
    assert run_storage.get_runs(PipelineRunsFilter(pipeline_name='pipeline_name')) == [run_to_add]
    assert run_storage.get_runs(PipelineRunsFilter(pipeline_name='nope')) == []

    run_storage.wipe()
    assert run_storage.get_runs() == []


def test_handle_run_event_pipeline_success_test(clean_storage):
    run_storage = clean_storage

    run_id = str(uuid.uuid4())
    run_to_add = build_run(pipeline_name='pipeline_name', run_id=run_id)
    run_storage.add_run(run_to_add)

    dagster_pipeline_start_event = DagsterEvent(
        message='a message',
        event_type_value=DagsterEventType.PIPELINE_START.value,
        pipeline_name='pipeline_name',
        step_key=None,
        solid_handle=None,
        step_kind_value=None,
        logging_tags=None,
    )

    run_storage.handle_run_event(run_id, dagster_pipeline_start_event)

    assert run_storage.get_run_by_id(run_id).status == PipelineRunStatus.STARTED

    run_storage.handle_run_event(
        str(uuid.uuid4()),  # diff run
        DagsterEvent(
            message='a message',
            event_type_value=DagsterEventType.PIPELINE_SUCCESS.value,
            pipeline_name='pipeline_name',
            step_key=None,
            solid_handle=None,
            step_kind_value=None,
            logging_tags=None,
        ),
    )

    assert run_storage.get_run_by_id(run_id).status == PipelineRunStatus.STARTED

    run_storage.handle_run_event(
        run_id,  # correct run
        DagsterEvent(
            message='a message',
            event_type_value=DagsterEventType.PIPELINE_SUCCESS.value,
            pipeline_name='pipeline_name',
            step_key=None,
            solid_handle=None,
            step_kind_value=None,
            logging_tags=None,
        ),
    )

    assert run_storage.get_run_by_id(run_id).status == PipelineRunStatus.SUCCESS


def test_load_from_config(hostname):
    url_cfg = '''
      run_storage:
        module: dagster_postgres.run_storage
        class: PostgresRunStorage
        config:
            postgres_url: postgresql://test:test@{hostname}:5432/test
    '''.format(
        hostname=hostname
    )

    explicit_cfg = '''
      run_storage:
        module: dagster_postgres.run_storage
        class: PostgresRunStorage
        config:
            postgres_db:
              username: test
              password: test
              hostname: {hostname}
              db_name: test
    '''.format(
        hostname=hostname
    )

    # pylint: disable=protected-access
    from_url = DagsterInstance.local_temp(overrides=yaml.safe_load(url_cfg))._run_storage
    from_explicit = DagsterInstance.local_temp(overrides=yaml.safe_load(explicit_cfg))._run_storage

    assert from_url.postgres_url == from_explicit.postgres_url
