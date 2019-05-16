from dagster import (
    PipelineDefinition,
    CompositeSolidDefinition,
    lambda_solid,
    Int,
    InputDefinition,
    ModeDefinition,
    SolidInstance,
    DependencyDefinition,
    OutputDefinition,
    Float,
)


@lambda_solid(inputs=[InputDefinition('num', Int)])
def add_one(num):
    return num + 1


@lambda_solid(inputs=[InputDefinition('num')])
def div_two(num):
    return num / 2


add_two = CompositeSolidDefinition(
    'add_two',
    solids=[add_one],
    dependencies={
        SolidInstance('add_one', 'adder_1'): {},
        SolidInstance('add_one', 'adder_2'): {'num': DependencyDefinition('adder_1')},
    },
    input_mappings=[InputDefinition('num', Int).mapping_to('adder_1', 'num')],
    output_mappings=[OutputDefinition(Int).mapping_from('adder_2')],
)

add_four = CompositeSolidDefinition(
    'add_four',
    solids=[add_two],
    dependencies={
        SolidInstance('add_two', 'adder_1'): {},
        SolidInstance('add_two', 'adder_2'): {'num': DependencyDefinition('adder_1')},
    },
    input_mappings=[InputDefinition('num', Int).mapping_to('adder_1', 'num')],
    output_mappings=[OutputDefinition(Int).mapping_from('adder_2')],
)

div_four = CompositeSolidDefinition(
    'div_four',
    solids=[div_two],
    dependencies={
        SolidInstance('div_two', 'div_1'): {},
        SolidInstance('div_two', 'div_2'): {'num': DependencyDefinition('div_1')},
    },
    input_mappings=[InputDefinition('num', Int).mapping_to('div_1', 'num')],
    output_mappings=[OutputDefinition(Float).mapping_from('div_2')],
)


def define_composition_pipeline():
    return PipelineDefinition(
        name='composition',
        solids=[add_four, div_four],
        dependencies={'div_four': {'num': DependencyDefinition('add_four')}},
        mode_definitions=[ModeDefinition()],
    )
