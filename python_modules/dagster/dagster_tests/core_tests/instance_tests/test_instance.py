import re

import pytest

from dagster import PipelineDefinition, check, execute_pipeline, pipeline, solid
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.execution.api import create_execution_plan
from dagster.core.instance import DagsterInstance, _dagster_home
from dagster.core.snap import (
    create_execution_plan_snapshot_id,
    create_pipeline_snapshot_id,
    snapshot_from_execution_plan,
)
from dagster.core.test_utils import create_run_for_test, environ, instance_for_test


def test_get_run_by_id():
    instance = DagsterInstance.ephemeral()

    assert instance.get_runs() == []
    pipeline_run = create_run_for_test(instance, pipeline_name="foo_pipeline", run_id="new_run")

    assert instance.get_runs() == [pipeline_run]

    assert instance.get_run_by_id(pipeline_run.run_id) == pipeline_run


def do_test_single_write_read(instance):
    run_id = "some_run_id"
    pipeline_def = PipelineDefinition(name="some_pipeline", solid_defs=[])
    instance.create_run_for_pipeline(pipeline_def=pipeline_def, run_id=run_id)
    run = instance.get_run_by_id(run_id)
    assert run.run_id == run_id
    assert run.pipeline_name == "some_pipeline"
    assert list(instance.get_runs()) == [run]
    instance.wipe()
    assert list(instance.get_runs()) == []


def test_filesystem_persist_one_run(tmpdir):
    do_test_single_write_read(DagsterInstance.local_temp(str(tmpdir)))


def test_in_memory_persist_one_run():
    do_test_single_write_read(DagsterInstance.ephemeral())


def test_create_pipeline_snapshot():
    @solid
    def noop_solid(_):
        pass

    @pipeline
    def noop_pipeline():
        noop_solid()

    instance = DagsterInstance.local_temp()

    result = execute_pipeline(noop_pipeline, instance=instance)
    assert result.success

    run = instance.get_run_by_id(result.run_id)

    assert run.pipeline_snapshot_id == create_pipeline_snapshot_id(
        noop_pipeline.get_pipeline_snapshot()
    )


def test_create_execution_plan_snapshot():
    @solid
    def noop_solid(_):
        pass

    @pipeline
    def noop_pipeline():
        noop_solid()

    instance = DagsterInstance.local_temp()

    execution_plan = create_execution_plan(noop_pipeline)

    ep_snapshot = snapshot_from_execution_plan(
        execution_plan, noop_pipeline.get_pipeline_snapshot_id()
    )
    ep_snapshot_id = create_execution_plan_snapshot_id(ep_snapshot)

    result = execute_pipeline(noop_pipeline, instance=instance)
    assert result.success

    run = instance.get_run_by_id(result.run_id)

    assert run.execution_plan_snapshot_id == ep_snapshot_id
    assert run.execution_plan_snapshot_id == create_execution_plan_snapshot_id(ep_snapshot)


def test_dagster_home_not_set():
    with environ({"DAGSTER_HOME": ""}):
        with pytest.raises(
            DagsterInvariantViolationError,
            match=r"The environment variable \$DAGSTER_HOME is not set\.",
        ):
            _dagster_home()


def test_invalid_configurable_class():
    with pytest.raises(
        check.CheckError,
        match=re.escape(
            "Couldn't find class MadeUpRunLauncher in module when attempting to "
            "load the configurable class dagster.MadeUpRunLauncher"
        ),
    ):
        with instance_for_test(
            overrides={"run_launcher": {"module": "dagster", "class": "MadeUpRunLauncher"}}
        ):
            pass


def test_invalid_configurable_module():
    with pytest.raises(
        check.CheckError,
        match=re.escape(
            "Couldn't import module made_up_module when attempting to load "
            "the configurable class made_up_module.MadeUpRunLauncher",
        ),
    ):
        with instance_for_test(
            overrides={"run_launcher": {"module": "made_up_module", "class": "MadeUpRunLauncher"}}
        ):
            pass


@pytest.mark.parametrize("dirname", (".", ".."))
def test_dagster_home_not_abspath(dirname):
    with environ({"DAGSTER_HOME": dirname}):
        with pytest.raises(
            DagsterInvariantViolationError,
            match=re.escape('$DAGSTER_HOME "{}" must be an absolute path.'.format(dirname)),
        ):
            _dagster_home()


def test_dagster_home_not_dir():
    dirname = "/this/path/does/not/exist"

    with environ({"DAGSTER_HOME": dirname}):
        with pytest.raises(
            DagsterInvariantViolationError,
            match=re.escape(
                '$DAGSTER_HOME "{}" is not a directory or does not exist.'.format(dirname)
            ),
        ):
            _dagster_home()
