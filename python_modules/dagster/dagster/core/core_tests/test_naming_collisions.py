import dagster

from dagster import (
    ArgumentDefinition,
    ConfigDefinition,
    DependencyDefinition,
    InputDefinition,
    OutputDefinition,
    PipelineDefinition,
    Result,
    SolidDefinition,
    check,
    config,
    execute_pipeline,
    types,
)


def define_pass_value_solid(name, description=None):
    check.str_param(name, 'name')
    check.opt_str_param(description, 'description')

    def _value_t_fn(_context, _inputs, config_dict):
        yield Result(config_dict['value'])

    return SolidDefinition(
        name=name,
        description=description,
        inputs=[],
        outputs=[OutputDefinition(dagster_type=types.String)],
        config_def=ConfigDefinition({
            'value': ArgumentDefinition(types.String)
        }),
        transform_fn=_value_t_fn,
    )


def test_execute_solid_with_input_same_name():
    a_thing_solid = SolidDefinition.single_output_transform(
        'a_thing',
        inputs=[InputDefinition(name='a_thing')],
        transform_fn=lambda context, args: args['a_thing'] + args['a_thing'],
        output=dagster.OutputDefinition(),
    )

    pipeline = PipelineDefinition(
        solids=[define_pass_value_solid('pass_value'), a_thing_solid],
        dependencies={'a_thing': {
            'a_thing': DependencyDefinition('pass_value')
        }},
    )

    result = execute_pipeline(
        pipeline,
        config.Environment(solids={'pass_value': config.Solid(config_dict={'value': 'foo'})}),
    )

    assert result.result_named('a_thing').transformed_value == 'foofoo'


def test_execute_two_solids_with_same_input_name():
    input_def = InputDefinition(name='a_thing')

    solid_one = SolidDefinition.single_output_transform(
        'solid_one',
        inputs=[input_def],
        transform_fn=lambda context, args: args['a_thing'] + args['a_thing'],
        output=dagster.OutputDefinition(),
    )

    solid_two = SolidDefinition.single_output_transform(
        'solid_two',
        inputs=[input_def],
        transform_fn=lambda context, args: args['a_thing'] + args['a_thing'],
        output=dagster.OutputDefinition(),
    )

    pipeline = dagster.PipelineDefinition(
        solids=[
            define_pass_value_solid('pass_to_one'),
            define_pass_value_solid('pass_to_two'),
            solid_one,
            solid_two,
        ],
        dependencies={
            'solid_one': {
                'a_thing': DependencyDefinition('pass_to_one')
            },
            'solid_two': {
                'a_thing': DependencyDefinition('pass_to_two')
            }
        }
    )

    result = execute_pipeline(
        pipeline,
        environment=config.Environment(
            solids={
                'pass_to_one': config.Solid({
                    'value': 'foo'
                }),
                'pass_to_two': config.Solid({
                    'value': 'bar'
                }),
            }
        )
    )

    assert result.success

    assert result.result_named('solid_one').transformed_value == 'foofoo'
    assert result.result_named('solid_two').transformed_value == 'barbar'


def test_execute_dep_solid_different_input_name():
    pass_to_first = define_pass_value_solid('pass_to_first')

    first_solid = SolidDefinition.single_output_transform(
        'first_solid',
        inputs=[InputDefinition(name='a_thing')],
        transform_fn=lambda context, args: args['a_thing'] + args['a_thing'],
        output=dagster.OutputDefinition(),
    )

    second_solid = SolidDefinition.single_output_transform(
        'second_solid',
        inputs=[
            InputDefinition(name='an_input'),
        ],
        transform_fn=lambda context, args: args['an_input'] + args['an_input'],
        output=dagster.OutputDefinition(),
    )

    pipeline = dagster.PipelineDefinition(
        solids=[pass_to_first, first_solid, second_solid],
        dependencies={
            'first_solid': {
                'a_thing': DependencyDefinition('pass_to_first'),
            },
            'second_solid': {
                'an_input': DependencyDefinition('first_solid'),
            },
        }
    )

    result = dagster.execute_pipeline(
        pipeline,
        environment=config.Environment(solids={'pass_to_first': config.Solid({
            'value': 'bar'
        })})
    )

    assert result.success
    assert len(result.result_list) == 3
    assert result.result_list[0].transformed_value == 'bar'
    assert result.result_list[1].transformed_value == 'barbar'
    assert result.result_list[2].transformed_value == 'barbarbarbar'
