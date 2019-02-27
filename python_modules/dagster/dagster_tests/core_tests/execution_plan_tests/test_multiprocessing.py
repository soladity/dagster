from dagster import (
    DependencyDefinition,
    InputDefinition,
    PipelineDefinition,
    execute_pipeline,
    lambda_solid,
)

from dagster.core.execution import InProcessExecutorConfig, MultiprocessExecutorConfig


def test_diamond_simple_execution():
    result = execute_pipeline(define_diamond_pipeline(), executor_config=InProcessExecutorConfig())
    assert result.success
    assert result.result_for_solid('adder').transformed_value() == 11


def transform_event(result, solid_name):
    return result.result_for_solid(solid_name).transforms[0]


def test_diamond_multi_execution():
    pipeline = define_diamond_pipeline()
    result = execute_pipeline(
        pipeline, executor_config=MultiprocessExecutorConfig(define_diamond_pipeline)
    )
    assert result.success
    assert result.result_for_solid('adder').transformed_value() == 11

    pids_by_solid = {}
    for solid in pipeline.solids:
        pids_by_solid[solid.name] = transform_event(result, solid.name).tags['pid']

    # guarantee that all solids ran in their own process
    assert len(set(pids_by_solid.values())) == len(pipeline.solids)


def define_diamond_pipeline():
    @lambda_solid
    def return_two():
        return 2

    @lambda_solid(inputs=[InputDefinition('num')])
    def add_three(num):
        return num + 3

    @lambda_solid(inputs=[InputDefinition('num')])
    def mult_three(num):
        return num * 3

    @lambda_solid(inputs=[InputDefinition('left'), InputDefinition('right')])
    def adder(left, right):
        return left + right

    return PipelineDefinition(
        name='diamond_execution',
        solids=[return_two, add_three, mult_three, adder],
        dependencies={
            'add_three': {'num': DependencyDefinition('return_two')},
            'mult_three': {'num': DependencyDefinition('return_two')},
            'adder': {
                'left': DependencyDefinition('add_three'),
                'right': DependencyDefinition('mult_three'),
            },
        },
    )


def define_error_pipeline():
    @lambda_solid
    def throw_error():
        raise Exception('bad programmer')

    return PipelineDefinition(name='error_pipeline', solids=[throw_error])


def test_error_pipeline():
    pipeline = define_error_pipeline()
    result = execute_pipeline(
        pipeline, throw_on_user_error=False, executor_config=InProcessExecutorConfig()
    )
    assert not result.success


def test_error_pipeline_multiprocess():
    pipeline = define_error_pipeline()
    result = execute_pipeline(
        pipeline,
        throw_on_user_error=False,
        executor_config=MultiprocessExecutorConfig(define_error_pipeline),
    )
    assert not result.success
