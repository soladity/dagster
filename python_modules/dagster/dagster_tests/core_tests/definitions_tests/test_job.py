import pytest
from dagster import (
    DagsterInvariantViolationError,
    execute_pipeline,
    graph,
    job,
    op,
    reconstructable,
)
from dagster.core.test_utils import instance_for_test


def define_the_job():
    @op
    def my_op():
        return 5

    @job
    def call_the_op():
        for _ in range(10):
            my_op()

    return call_the_op


def test_job_execution_multiprocess_config():
    with instance_for_test() as instance:
        result = execute_pipeline(
            reconstructable(define_the_job),
            instance=instance,
            run_config={"execution": {"config": {"multiprocess": {"max_concurrent": 4}}}},
        )

        assert result.success
        assert result.output_for_solid("my_op") == 5


results_lst = []


def define_in_process_job():
    @op
    def my_op():
        results_lst.append("entered")

    @job
    def call_the_op():
        for _ in range(10):
            my_op()

    return call_the_op


def test_switch_to_in_process_execution():
    result = execute_pipeline(
        define_in_process_job(),
        run_config={"execution": {"config": {"in_process": {}}}},
    )
    assert result.success
    assert len(results_lst) == 10


@graph
def basic_graph():
    pass


basic_job = basic_graph.to_job()  # type: ignore[union-attr]


def test_non_reconstructable_job_error():
    with pytest.raises(
        DagsterInvariantViolationError,
        match="you must wrap the ``to_job`` call in a function at module scope",
    ):
        reconstructable(basic_job)
