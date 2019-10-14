from dagster_examples.intro_tutorial.composition import (
    complex_pipeline,
    composed_pipeline,
    compute_three_auto,
    compute_three_explicit,
    compute_two,
    multiple_outputs,
)

from dagster import execute_pipeline


def test_pipelines_execute():

    assert execute_pipeline(compute_two).success
    assert execute_pipeline(compute_three_auto).success
    assert execute_pipeline(compute_three_explicit).success
    assert execute_pipeline(multiple_outputs).success
    assert execute_pipeline(complex_pipeline).success
    assert execute_pipeline(composed_pipeline).success
