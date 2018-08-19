import pytest
import dagster
from dagster import (
    ArgumentDefinition,
    DependencyDefinition,
    InputDefinition,
    OutputDefinition,
    PipelineDefinition,
    config,
    execute_pipeline,
    types,
)
from dagster.core.errors import DagsterInvalidDefinitionError
from dagster.core.decorators import (
    materialization,
    solid,
    with_context,
)
from dagster.core.execution import (
    output_single_solid,
    execute_single_solid,
    ExecutionContext,
)
from dagster.core.utility_solids import define_pass_mem_value

# This file tests a lot of parameter name stuff
# So these warnings are spurious
# unused variables, unused arguments
# pylint: disable=W0612, W0613


def create_test_context():
    return ExecutionContext()


def create_empty_test_env():
    return config.Environment()


def test_solid():
    @solid()
    def hello_world():
        return {'foo': 'bar'}

    result = execute_single_solid(
        create_test_context(),
        hello_world,
        environment=create_empty_test_env(),
    )

    assert result.success

    assert result.transformed_value['foo'] == 'bar'


def test_solid_with_name():
    @solid(name="foobar")
    def hello_world():
        return {'foo': 'bar'}

    result = execute_single_solid(
        create_test_context(),
        hello_world,
        environment=create_empty_test_env(),
    )

    assert result.success

    assert result.transformed_value['foo'] == 'bar'


def test_solid_with_context():
    @solid(name="foobar")
    @with_context
    def hello_world(_context):
        return {'foo': 'bar'}

    result = execute_single_solid(
        create_test_context(),
        hello_world,
        environment=create_empty_test_env(),
    )

    assert result.success

    assert result.transformed_value['foo'] == 'bar'


def test_solid_with_input():
    @solid(inputs=[InputDefinition(name="foo_to_foo")])
    def hello_world(foo_to_foo):
        return foo_to_foo

    pipeline = PipelineDefinition(
        solids=[define_pass_mem_value('test_value', {'foo': 'bar'}), hello_world],
        dependencies={'hello_world': {
            'foo_to_foo': DependencyDefinition('test_value'),
        }}
    )

    pipeline_result = execute_pipeline(
        pipeline,
        environment=config.Environment(),
    )

    result = pipeline_result.result_named('hello_world')

    assert result.success

    assert result.transformed_value['foo'] == 'bar'


def test_materializations():
    test_output = {}

    @materialization(name="CONTEXT", argument_def_dict={'foo': ArgumentDefinition(types.String)})
    @with_context
    def materialization_with_context(_context, data, foo):
        test_output['test'] = data

    @materialization(name="NO_CONTEXT", argument_def_dict={'foo': ArgumentDefinition(types.String)})
    def materialization_no_context(data, foo):
        test_output['test'] = data

    @solid(
        output=OutputDefinition(
            materializations=[materialization_with_context, materialization_no_context]
        )
    )
    def hello():
        return {'foo': 'bar'}

    output_single_solid(
        create_test_context(),
        hello,
        environment=config.Environment(),
        name='CONTEXT',
        arg_dict={'foo': 'bar'}
    )

    assert test_output['test'] == {'foo': 'bar'}

    test_output = {}

    output_single_solid(
        create_test_context(),
        hello,
        environment=config.Environment(),
        name='NO_CONTEXT',
        arg_dict={'foo': 'bar'}
    )

    assert test_output['test'] == {'foo': 'bar'}


def test_solid_definition_errors():
    with pytest.raises(DagsterInvalidDefinitionError):

        @solid(inputs=[InputDefinition(name="foo")], output=OutputDefinition())
        @with_context
        def vargs(_context, foo, *args):
            pass

    with pytest.raises(DagsterInvalidDefinitionError):

        @solid(inputs=[InputDefinition(name="foo")], output=OutputDefinition())
        def wrong_name(bar):
            pass

    with pytest.raises(DagsterInvalidDefinitionError):

        @solid(
            inputs=[InputDefinition(name="foo"),
                    InputDefinition(name="bar")],
            output=OutputDefinition()
        )
        def wrong_name_2(foo):
            pass

    with pytest.raises(DagsterInvalidDefinitionError):

        @solid(inputs=[InputDefinition(name="foo")], output=OutputDefinition())
        @with_context
        def no_context(foo):
            pass

    with pytest.raises(DagsterInvalidDefinitionError):

        @solid(inputs=[InputDefinition(name="foo")], output=OutputDefinition())
        def yes_context(_context, foo):
            pass

    with pytest.raises(DagsterInvalidDefinitionError):

        @solid(inputs=[InputDefinition(name="foo")], output=OutputDefinition())
        def extras(foo, bar):
            pass

    @solid(
        inputs=[InputDefinition(name="foo"),
                InputDefinition(name="bar")],
        output=OutputDefinition()
    )
    def valid_kwargs(**kwargs):
        pass

    @solid(
        inputs=[InputDefinition(name="foo"),
                InputDefinition(name="bar")],
        output=OutputDefinition()
    )
    def valid(foo, bar):
        pass

    @solid(
        inputs=[InputDefinition(name="foo"),
                InputDefinition(name="bar")],
        output=OutputDefinition()
    )
    @with_context
    def valid_rontext(context, foo, bar):
        pass

    @solid(
        inputs=[InputDefinition(name="foo"),
                InputDefinition(name="bar")],
        output=OutputDefinition()
    )
    @with_context
    def valid_context_2(_context, foo, bar):
        pass


def test_materialization_definition_errors():
    with pytest.raises(DagsterInvalidDefinitionError):

        @materialization(argument_def_dict={'foo': ArgumentDefinition(types.String)})
        @with_context
        def no_data(context, foo):
            pass

    with pytest.raises(DagsterInvalidDefinitionError):

        @materialization(argument_def_dict={'foo': ArgumentDefinition(types.String)})
        @with_context
        def vargs(context, data, foo, *args):
            pass

    with pytest.raises(DagsterInvalidDefinitionError):

        @materialization(argument_def_dict={'foo': ArgumentDefinition(types.String)})
        def wrong_name(data, bar):
            pass

    with pytest.raises(DagsterInvalidDefinitionError):

        @materialization(
            argument_def_dict={
                'foo': ArgumentDefinition(types.String),
                'bar': ArgumentDefinition(types.String)
            }
        )
        def wrong_name_2(data, foo):
            pass

    with pytest.raises(DagsterInvalidDefinitionError):

        @materialization(argument_def_dict={'foo': ArgumentDefinition(types.String)})
        @with_context
        def no_context(data, foo):
            pass

    with pytest.raises(DagsterInvalidDefinitionError):

        @materialization(argument_def_dict={'foo': ArgumentDefinition(types.String)})
        def yes_context(context, data, foo):
            pass

    with pytest.raises(DagsterInvalidDefinitionError):

        @materialization(argument_def_dict={'foo': ArgumentDefinition(types.String)})
        def extras(data, foo, bar):
            pass

    @materialization(argument_def_dict={'foo': ArgumentDefinition(types.String)})
    def valid_kwargs(data, **kwargs):
        pass

    @materialization(
        argument_def_dict={
            'foo': ArgumentDefinition(types.String),
            'bar': ArgumentDefinition(types.String)
        }
    )
    def valid(data, foo, bar):
        pass

    @materialization(
        argument_def_dict={
            'foo': ArgumentDefinition(types.String),
            'bar': ArgumentDefinition(types.String)
        }
    )
    @with_context
    def valid_rontext(context, data, foo, bar):
        pass

    @materialization(
        argument_def_dict={
            'foo': ArgumentDefinition(types.String),
            'bar': ArgumentDefinition(types.String)
        }
    )
    @with_context
    def valid_context_2(_context, _data, foo, bar):
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

    @materialization(description='baaz')
    def materialization_desc():
        pass

    assert materialization_desc.description == 'baaz'
