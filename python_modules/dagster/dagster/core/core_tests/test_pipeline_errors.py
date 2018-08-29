import pytest

from dagster import (
    DagsterInvariantViolationError,
    DependencyDefinition,
    ExecutionContext,
    InputDefinition,
    OutputDefinition,
    PipelineContextDefinition,
    PipelineDefinition,
    Result,
    SolidDefinition,
    check,
    config,
    execute_pipeline,
)

from dagster.core.test_utils import execute_single_solid
from dagster.core.errors import DagsterUserCodeExecutionError


def silencing_default_context():
    return {
        'default':
        PipelineContextDefinition(
            argument_def_dict={},
            context_fn=lambda _pipeline, _args: ExecutionContext(),
        )
    }


def silencing_pipeline(solids, dependencies=None):
    return PipelineDefinition(
        solids=solids,
        dependencies=dependencies,
        context_definitions=silencing_default_context(),
    )


def create_root_success_solid(name):
    def root_transform(_context, _args):
        passed_rows = []
        passed_rows.append({name: 'transform_called'})
        return passed_rows

    return SolidDefinition.single_output_transform(
        name=name,
        inputs=[],
        transform_fn=root_transform,
        output=OutputDefinition(),
    )


def create_root_transform_failure_solid(name):
    def failed_transform(**_kwargs):
        raise Exception('Transform failed')

    return SolidDefinition.single_output_transform(
        name=name,
        inputs=[],
        transform_fn=failed_transform,
        output=OutputDefinition(),
    )


def test_transform_failure_pipeline():
    pipeline = silencing_pipeline(solids=[create_root_transform_failure_solid('failing')])
    pipeline_result = execute_pipeline(
        pipeline, environment=config.Environment(), throw_on_error=False
    )

    assert not pipeline_result.success

    result_list = pipeline_result.result_list

    assert len(result_list) == 1
    assert not result_list[0].success
    assert result_list[0].dagster_user_exception


def test_failure_midstream():
    solid_a = create_root_success_solid('A')
    solid_b = create_root_success_solid('B')

    def transform_fn(_context, args):
        check.failed('user error')
        return [args['A'], args['B'], {'C': 'transform_called'}]

    solid_c = SolidDefinition.single_output_transform(
        name='C',
        inputs=[InputDefinition(name='A'), InputDefinition(name='B')],
        transform_fn=transform_fn,
        output=OutputDefinition(),
    )

    pipeline = silencing_pipeline(
        solids=[solid_a, solid_b, solid_c],
        dependencies={
            'C': {
                'A': DependencyDefinition(solid_a.name),
                'B': DependencyDefinition(solid_b.name),
            }
        }
    )
    pipeline_result = execute_pipeline(
        pipeline,
        environment=config.Environment(),
        throw_on_error=False,
    )

    result_list = pipeline_result.result_list
    print([r.solid.name for r in result_list])

    assert result_list[0].success
    assert result_list[1].success
    assert not result_list[2].success
    assert isinstance(result_list[2].dagster_user_exception, DagsterUserCodeExecutionError)


def test_do_not_yield_result():
    solid_inst = SolidDefinition(
        name='do_not_yield_result',
        inputs=[],
        outputs=[OutputDefinition()],
        transform_fn=lambda *_args, **_kwargs: Result('foo')
    )

    with pytest.raises(
        DagsterInvariantViolationError,
        message='Tranform for solid do_not_yield_result return a Result',
    ):
        execute_single_solid(ExecutionContext(), solid_inst, config.Environment())


def test_yield_non_result():
    def _tn(*_args, **_kwargs):
        yield 'foo'

    solid_inst = SolidDefinition(
        name='yield_wrong_thing',
        inputs=[],
        outputs=[OutputDefinition()],
        transform_fn=_tn,
    )

    with pytest.raises(
        DagsterInvariantViolationError,
        message="Tranform for solid yield_wrong_thing yielded 'foo'",
    ):
        execute_single_solid(ExecutionContext(), solid_inst, config.Environment())
