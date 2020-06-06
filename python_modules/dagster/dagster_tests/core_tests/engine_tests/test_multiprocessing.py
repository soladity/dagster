import os
import time

from dagster import (
    Field,
    InputDefinition,
    Nothing,
    Output,
    OutputDefinition,
    PresetDefinition,
    String,
    execute_pipeline,
    lambda_solid,
    pipeline,
    reconstructable,
    solid,
)
from dagster.core.instance import DagsterInstance
from dagster.utils import safe_tempfile_path


def test_diamond_simple_execution():
    result = execute_pipeline(define_diamond_pipeline())
    assert result.success
    assert result.result_for_solid('adder').output_value() == 11


def compute_event(result, solid_name):
    return result.result_for_solid(solid_name).compute_step_events[0]


def test_diamond_multi_execution():
    pipe = reconstructable(define_diamond_pipeline)
    result = execute_pipeline(
        pipe,
        environment_dict={'storage': {'filesystem': {}}, 'execution': {'multiprocess': {}}},
        instance=DagsterInstance.local_temp(),
    )
    assert result.success

    assert result.result_for_solid('adder').output_value() == 11

    # https://github.com/dagster-io/dagster/issues/1875
    # pids_by_solid = {}
    # for solid in pipeline.solids:
    #     pids_by_solid[solid.name] = compute_event(result, solid.name).logging_tags['pid']

    # # guarantee that all solids ran in their own process
    # assert len(set(pids_by_solid.values())) == len(pipeline.solids)


def define_diamond_pipeline():
    @lambda_solid
    def return_two():
        return 2

    @lambda_solid(input_defs=[InputDefinition('num')])
    def add_three(num):
        return num + 3

    @lambda_solid(input_defs=[InputDefinition('num')])
    def mult_three(num):
        return num * 3

    @lambda_solid(input_defs=[InputDefinition('left'), InputDefinition('right')])
    def adder(left, right):
        return left + right

    @pipeline(
        preset_defs=[
            PresetDefinition(
                'just_adder',
                {
                    'storage': {'filesystem': {}},
                    'execution': {'multiprocess': {}},
                    'solids': {'adder': {'inputs': {'left': {'value': 1}, 'right': {'value': 1}}}},
                },
                solid_selection=['adder'],
            )
        ],
    )
    def diamond_pipeline():
        two = return_two()
        adder(left=add_three(two), right=mult_three(two))

    return diamond_pipeline


def define_error_pipeline():
    @lambda_solid
    def should_never_execute(_x):
        assert False  # this should never execute

    @lambda_solid
    def throw_error():
        raise Exception('bad programmer')

    @pipeline
    def error_pipeline():
        should_never_execute(throw_error())

    return error_pipeline


def test_error_pipeline():
    pipe = define_error_pipeline()
    result = execute_pipeline(pipe, raise_on_error=False)
    assert not result.success


def test_error_pipeline_multiprocess():
    result = execute_pipeline(
        reconstructable(define_error_pipeline),
        environment_dict={'storage': {'filesystem': {}}, 'execution': {'multiprocess': {}}},
        instance=DagsterInstance.local_temp(),
    )
    assert not result.success


def test_mem_storage_error_pipeline_multiprocess():
    result = execute_pipeline(
        reconstructable(define_diamond_pipeline),
        environment_dict={'execution': {'multiprocess': {}}},
        instance=DagsterInstance.local_temp(),
        raise_on_error=False,
    )
    assert not result.success
    assert len(result.event_list) == 1
    assert result.event_list[0].is_failure


def test_invalid_instance():
    result = execute_pipeline(
        reconstructable(define_diamond_pipeline),
        environment_dict={'storage': {'filesystem': {}}, 'execution': {'multiprocess': {}}},
        instance=DagsterInstance.ephemeral(),
        raise_on_error=False,
    )
    assert not result.success
    assert len(result.event_list) == 1
    assert result.event_list[0].is_failure
    assert (
        result.event_list[0].pipeline_init_failure_data.error.cls_name
        == 'DagsterUnmetExecutorRequirementsError'
    )
    assert 'non-ephemeral instance' in result.event_list[0].pipeline_init_failure_data.error.message


def test_no_handle():
    result = execute_pipeline(
        define_diamond_pipeline(),
        environment_dict={'storage': {'filesystem': {}}, 'execution': {'multiprocess': {}}},
        instance=DagsterInstance.ephemeral(),
        raise_on_error=False,
    )
    assert not result.success
    assert len(result.event_list) == 1
    assert result.event_list[0].is_failure
    assert (
        result.event_list[0].pipeline_init_failure_data.error.cls_name
        == 'DagsterUnmetExecutorRequirementsError'
    )
    assert 'is not reconstructable' in result.event_list[0].pipeline_init_failure_data.error.message


def test_solid_selection():
    pipe = reconstructable(define_diamond_pipeline)

    result = execute_pipeline(pipe, preset='just_adder', instance=DagsterInstance.local_temp())

    assert result.success

    assert result.result_for_solid('adder').output_value() == 2


def define_subdag_pipeline():
    @solid(config=Field(String))
    def waiter(context):
        done = False
        while not done:
            time.sleep(0.15)
            if os.path.isfile(context.solid_config):
                return

    @solid(
        input_defs=[InputDefinition('after', Nothing)], config=Field(String),
    )
    def writer(context):
        with open(context.solid_config, 'w') as fd:
            fd.write('1')
        return

    @lambda_solid(
        input_defs=[InputDefinition('after', Nothing)], output_def=OutputDefinition(Nothing),
    )
    def noop():
        pass

    @pipeline
    def separate():
        waiter()
        a = noop.alias('noop_1')()
        b = noop.alias('noop_2')(a)
        c = noop.alias('noop_3')(b)
        writer(c)

    return separate


def test_separate_sub_dags():
    pipe = reconstructable(define_subdag_pipeline)

    with safe_tempfile_path() as filename:
        result = execute_pipeline(
            pipe,
            environment_dict={
                'storage': {'filesystem': {}},
                'execution': {'multiprocess': {'config': {'max_concurrent': 2}}},
                'solids': {'waiter': {'config': filename}, 'writer': {'config': filename},},
            },
            instance=DagsterInstance.local_temp(),
        )

    assert result.success

    # this test is to ensure that the chain of noop -> noop -> noop -> writer is not blocked by waiter
    order = [str(event.solid_handle) for event in result.step_event_list if event.is_step_success]

    # the writer and waiter my finish in different orders so just ensure the proceeding chain
    assert order[0:3] == ['noop_1', 'noop_2', 'noop_3']


def test_ephemeral_event_log():
    pipe = reconstructable(define_diamond_pipeline)
    # override event log to in memory
    instance = DagsterInstance.local_temp(
        overrides={
            'event_log_storage': {
                'module': 'dagster.core.storage.event_log',
                'class': 'InMemoryEventLogStorage',
            }
        }
    )

    result = execute_pipeline(
        pipe,
        environment_dict={'storage': {'filesystem': {}}, 'execution': {'multiprocess': {}}},
        instance=instance,
    )
    assert result.success

    assert result.result_for_solid('adder').output_value() == 11


@solid(
    output_defs=[
        OutputDefinition(name='option_1', is_required=False),
        OutputDefinition(name='option_2', is_required=False),
    ]
)
def either_or(_context):
    yield Output(1, 'option_1')


@lambda_solid
def echo(x):
    return x


@pipeline
def optional_stuff():
    option_1, option_2 = either_or()
    echo(echo(option_1))
    echo(echo(option_2))


def test_optional_outputs():
    single_result = execute_pipeline(optional_stuff)
    assert single_result.success
    assert not [event for event in single_result.step_event_list if event.is_step_failure]
    assert len([event for event in single_result.step_event_list if event.is_step_skipped]) == 2

    multi_result = execute_pipeline(
        reconstructable(optional_stuff),
        environment_dict={'storage': {'filesystem': {}}, 'execution': {'multiprocess': {}}},
        instance=DagsterInstance.local_temp(),
    )
    assert multi_result.success
    assert not [event for event in multi_result.step_event_list if event.is_step_failure]
    assert len([event for event in multi_result.step_event_list if event.is_step_skipped]) == 2
