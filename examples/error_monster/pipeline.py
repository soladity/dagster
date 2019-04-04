import logging

from dagster import (
    DependencyDefinition,
    Field,
    InputDefinition,
    Int,
    Bool,
    String,
    Dict,
    OutputDefinition,
    PipelineDefinition,
    SolidInstance,
    RunConfig,
    execute_pipeline,
    solid,
    ResourceDefinition,
    PipelineContextDefinition,
    ExecutionContext,
)


class ErrorableResource:
    pass


def resource_init(init_context):
    if init_context.resource_config['throw_on_resource_init']:
        raise Exception('throwing from in resource_fn')
    return ErrorableResource()


def define_errorable_resource():
    return ResourceDefinition(
        resource_fn=resource_init, config_field=Field(Dict({'throw_on_resource_init': Field(Bool)}))
    )


solid_throw_config = Field(Dict(fields={'throw_in_solid': Field(Bool)}))


@solid(name='start', outputs=[OutputDefinition(Int)], config_field=solid_throw_config)
def emit_num(context):
    if context.solid_config['throw_in_solid']:
        raise Exception('throwing from in the solid')

    return 13


@solid(
    name='middle',
    inputs=[InputDefinition('num', Int)],
    outputs=[OutputDefinition(String)],
    config_field=solid_throw_config,
)
def num_to_str(context, num):
    if context.solid_config['throw_in_solid']:
        raise Exception('throwing from in the solid')

    return str(num)


@solid(
    name='end',
    inputs=[InputDefinition('string', String)],
    outputs=[OutputDefinition(Int)],
    config_field=solid_throw_config,
)
def str_to_num(context, string):
    if context.solid_config['throw_in_solid']:
        raise Exception('throwing from in the solid')

    return int(string)


def context_init(init_context):
    if init_context.context_config['throw_on_context_init']:
        raise Exception('throwing from context_fn')
    return ExecutionContext.console_logging(log_level=logging.DEBUG)


def define_pipeline():
    return PipelineDefinition(
        name="error_monster",
        solids=[emit_num, num_to_str, str_to_num],
        dependencies={
            SolidInstance('start'): {},
            SolidInstance('middle'): {'num': DependencyDefinition('start')},
            SolidInstance('end'): {'string': DependencyDefinition('middle')},
        },
        context_definitions={
            'errorable_context': PipelineContextDefinition(
                config_field=Field(Dict({'throw_on_context_init': Field(Bool)})),
                context_fn=context_init,
                resources={'errorable_resource': define_errorable_resource()},
            )
        },
    )


if __name__ == '__main__':
    result = execute_pipeline(
        define_pipeline(),
        {
            'context': {
                'errorable_context': {
                    'config': {'throw_on_context_init': False},
                    'resources': {
                        'errorable_resource': {'config': {'throw_on_resource_init': True}}
                    },
                }
            },
            'solids': {
                'start': {'config': {'throw_in_solid': False}},
                'middle': {'config': {'throw_in_solid': False}},
                'end': {'config': {'throw_in_solid': False}},
            },
        },
        RunConfig.nonthrowing_in_process(),
    )
    print('Pipeline Success: ', result.success)
