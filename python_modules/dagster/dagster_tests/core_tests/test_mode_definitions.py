import pytest

from dagster import (
    DagsterInvariantViolationError,
    ModeDefinition,
    PipelineDefinition,
    RunConfig,
    execute_pipeline,
)

from ..test_repository import (
    define_modeless_pipeline,
    define_multi_mode_pipeline,
    define_multi_mode_with_resources_pipeline,
    define_single_mode_pipeline,
)


def test_basic_mode_definition():
    pipeline_def = PipelineDefinition(
        name='takes a mode', solids=[], mode_definitions=[ModeDefinition()]
    )
    assert pipeline_def


def test_mode_takes_a_name():
    pipeline_def = PipelineDefinition(
        name='takes a mode', solids=[], mode_definitions=[ModeDefinition(name='a_mode')]
    )
    assert pipeline_def


def test_execute_modeless():
    pipeline_result = execute_pipeline(define_modeless_pipeline())
    assert pipeline_result.result_for_solid('return_one').transformed_value() == 1


def test_execute_single_mode():
    single_mode_pipeline = define_single_mode_pipeline()
    assert single_mode_pipeline.is_modeless is False
    assert single_mode_pipeline.is_single_mode is True

    assert (
        execute_pipeline(single_mode_pipeline).result_for_solid('return_two').transformed_value()
        == 2
    )

    assert (
        execute_pipeline(single_mode_pipeline, run_config=RunConfig(mode='the_mode'))
        .result_for_solid('return_two')
        .transformed_value()
        == 2
    )


def test_wrong_single_mode():
    with pytest.raises(DagsterInvariantViolationError):
        assert (
            execute_pipeline(define_single_mode_pipeline(), run_config=RunConfig(mode='wrong_mode'))
            .result_for_solid('return_two')
            .transformed_value()
            == 2
        )


def test_execute_multi_mode():
    multi_mode_pipeline = define_multi_mode_pipeline()

    assert (
        execute_pipeline(multi_mode_pipeline, run_config=RunConfig(mode='mode_one'))
        .result_for_solid('return_three')
        .transformed_value()
        == 3
    )

    assert (
        execute_pipeline(multi_mode_pipeline, run_config=RunConfig(mode='mode_two'))
        .result_for_solid('return_three')
        .transformed_value()
        == 3
    )


def test_execute_multi_mode_errors():
    multi_mode_pipeline = define_multi_mode_pipeline()

    with pytest.raises(DagsterInvariantViolationError):
        execute_pipeline(multi_mode_pipeline)

    with pytest.raises(DagsterInvariantViolationError):
        execute_pipeline(multi_mode_pipeline, run_config=RunConfig(mode='wrong_mode'))


def test_execute_multi_mode_with_resources():
    pipeline_def = define_multi_mode_with_resources_pipeline()

    add_mode_result = execute_pipeline(
        pipeline_def,
        run_config=RunConfig(mode='add_mode'),
        environment_dict={'resources': {'op': {'config': 2}}},
    )

    assert add_mode_result.result_for_solid('apply_to_three').transformed_value() == 5

    mult_mode_result = execute_pipeline(
        pipeline_def,
        run_config=RunConfig(mode='mult_mode'),
        environment_dict={'resources': {'op': {'config': 3}}},
    )

    assert mult_mode_result.result_for_solid('apply_to_three').transformed_value() == 9
