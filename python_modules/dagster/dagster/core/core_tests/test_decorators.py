import pytest
import dagster
from dagster import (
    ConfigDefinition,
    DagsterInvalidDefinitionError,
    DependencyDefinition,
    ExecutionContext,
    InputDefinition,
    MultipleResults,
    OutputDefinition,
    PipelineDefinition,
    Result,
    config,
    execute_pipeline,
    solid,
)

from dagster.core.test_utils import execute_single_solid
from dagster.core.utility_solids import define_stub_solid

# This file tests a lot of parameter name stuff
# So these warnings are spurious
# unused variables, unused arguments
# pylint: disable=W0612, W0613


def create_test_context():
    return ExecutionContext()


def create_empty_test_env():
    return config.Environment()


def test_no_parens_solid():
    called = {}

    @solid
    def hello_world(_context, _conf):
        called['yup'] = True

    result = execute_single_solid(
        create_test_context(),
        hello_world,
        environment=create_empty_test_env(),
    )

    assert called['yup']


def test_empty_solid():
    called = {}

    @solid()
    def hello_world(_context, _conf):
        called['yup'] = True

    result = execute_single_solid(
        create_test_context(),
        hello_world,
        environment=create_empty_test_env(),
    )

    assert called['yup']


def test_solid():
    @solid(outputs=[OutputDefinition()])
    def hello_world(_context, _conf):
        return {'foo': 'bar'}

    result = execute_single_solid(
        create_test_context(),
        hello_world,
        environment=create_empty_test_env(),
    )

    assert result.success
    assert len(result.result_list) == 1
    assert result.result_list[0].transformed_value()['foo'] == 'bar'


def test_solid_one_output():
    @solid(output=OutputDefinition())
    def hello_world(_context, _conf):
        return {'foo': 'bar'}

    result = execute_single_solid(
        create_test_context(),
        hello_world,
        environment=create_empty_test_env(),
    )

    assert result.success
    assert len(result.result_list) == 1
    assert result.result_list[0].transformed_value()['foo'] == 'bar'


def test_solid_yield():
    @solid(output=OutputDefinition())
    def hello_world(_context, _conf):
        yield Result(value={'foo': 'bar'})

    result = execute_single_solid(
        create_test_context(),
        hello_world,
        environment=create_empty_test_env(),
    )

    assert result.success
    assert len(result.result_list) == 1
    assert result.result_list[0].transformed_value()['foo'] == 'bar'


def test_solid_result_return():
    @solid(output=OutputDefinition())
    def hello_world(_context, _conf):
        return Result(value={'foo': 'bar'})

    result = execute_single_solid(
        create_test_context(),
        hello_world,
        environment=create_empty_test_env(),
    )

    assert result.success
    assert len(result.result_list) == 1
    assert result.result_list[0].transformed_value()['foo'] == 'bar'


def test_solid_multiple_outputs():
    @solid(outputs=[
        OutputDefinition(name="left"),
        OutputDefinition(name="right"),
    ])
    def hello_world(_context, _conf):
        return MultipleResults(
            Result(value={'foo': 'left'}, output_name='left'),
            Result(value={'foo': 'right'}, output_name='right')
        )

    result = execute_single_solid(
        create_test_context(),
        hello_world,
        environment=create_empty_test_env(),
    )

    assert result.success
    assert len(result.result_list) == 1
    solid_result = result.result_list[0]
    assert solid_result.transformed_value('left')['foo'] == 'left'
    assert solid_result.transformed_value('right')['foo'] == 'right'


def test_dict_multiple_outputs():
    @solid(outputs=[
        OutputDefinition(name="left"),
        OutputDefinition(name="right"),
    ])
    def hello_world(_context, _conf):
        return MultipleResults.from_dict({
            'left': {
                'foo': 'left'
            },
            'right': {
                'foo': 'right'
            },
        })

    result = execute_single_solid(
        create_test_context(),
        hello_world,
        environment=create_empty_test_env(),
    )

    assert result.success
    assert len(result.result_list) == 1
    solid_result = result.result_list[0]
    assert solid_result.transformed_value('left')['foo'] == 'left'
    assert solid_result.transformed_value('right')['foo'] == 'right'


def test_solid_with_name():
    @solid(name="foobar", outputs=[OutputDefinition()])
    def hello_world(_context, _conf):
        return {'foo': 'bar'}

    result = execute_single_solid(
        create_test_context(),
        hello_world,
        environment=create_empty_test_env(),
    )

    assert result.success
    assert len(result.result_list) == 1
    assert result.result_list[0].transformed_value()['foo'] == 'bar'


def test_solid_with_input():
    @solid(inputs=[InputDefinition(name="foo_to_foo")], outputs=[OutputDefinition()])
    def hello_world(_context, _conf, foo_to_foo):
        return foo_to_foo

    pipeline = PipelineDefinition(
        solids=[define_stub_solid('test_value', {'foo': 'bar'}), hello_world],
        dependencies={'hello_world': {
            'foo_to_foo': DependencyDefinition('test_value'),
        }}
    )

    pipeline_result = execute_pipeline(
        pipeline,
        environment=config.Environment(),
    )

    result = pipeline_result.result_for_solid('hello_world')

    assert result.success
    assert result.transformed_value()['foo'] == 'bar'


def test_solid_definition_errors():
    with pytest.raises(DagsterInvalidDefinitionError):

        @solid(inputs=[InputDefinition(name="foo")], outputs=[OutputDefinition()])
        def vargs(_context, _conf, foo, *args):
            pass

    with pytest.raises(DagsterInvalidDefinitionError):

        @solid(inputs=[InputDefinition(name="foo")], outputs=[OutputDefinition()])
        def wrong_name(_context, _conf, bar):
            pass

    with pytest.raises(DagsterInvalidDefinitionError):

        @solid(
            inputs=[InputDefinition(name="foo"),
                    InputDefinition(name="bar")],
            outputs=[OutputDefinition()]
        )
        def wrong_name_2(_context, _conf, foo):
            pass

    with pytest.raises(DagsterInvalidDefinitionError):

        @solid(inputs=[InputDefinition(name="foo")], outputs=[OutputDefinition()])
        def no_context(foo):
            pass

    with pytest.raises(DagsterInvalidDefinitionError):

        @solid(inputs=[InputDefinition(name="foo")], outputs=[OutputDefinition()])
        def no_conf(_context, foo):
            pass

    with pytest.raises(DagsterInvalidDefinitionError):

        @solid(inputs=[InputDefinition(name="foo")], outputs=[OutputDefinition()])
        def yes_context(_context, foo):
            pass

    with pytest.raises(DagsterInvalidDefinitionError):

        @solid(inputs=[InputDefinition(name="foo")], outputs=[OutputDefinition()])
        def extras(_context, _conf, foo, bar):
            pass

    @solid(
        inputs=[InputDefinition(name="foo"),
                InputDefinition(name="bar")],
        outputs=[OutputDefinition()]
    )
    def valid_kwargs(_context, _conf, **kwargs):
        pass

    @solid(
        inputs=[InputDefinition(name="foo"),
                InputDefinition(name="bar")],
        outputs=[OutputDefinition()]
    )
    def valid(_context, _conf, foo, bar):
        pass

    @solid(
        inputs=[InputDefinition(name="foo"),
                InputDefinition(name="bar")],
        outputs=[OutputDefinition()]
    )
    def valid_rontext(context, _conf, foo, bar):
        pass


def test_wrong_argument_to_pipeline():
    def non_solid_func():
        pass

    with pytest.raises(
        DagsterInvalidDefinitionError, match='You have passed a lambda or function non_solid_func'
    ):
        dagster.PipelineDefinition(solids=[non_solid_func])

    with pytest.raises(
        DagsterInvalidDefinitionError, match='You have passed a lambda or function <lambda>'
    ):
        dagster.PipelineDefinition(solids=[lambda x: x])


def test_descriptions():
    @solid(description='foo')
    def solid_desc():
        pass

    assert solid_desc.description == 'foo'


def test_any_config_definition():
    called = {}
    conf_value = 234

    @solid(config_def=ConfigDefinition())
    def hello_world(_context, conf):
        assert conf == conf_value
        called['yup'] = True

    result = execute_single_solid(
        create_test_context(),
        hello_world,
        environment=config.Environment(solids={'hello_world': config.Solid(conf_value)})
    )

    assert called['yup']
