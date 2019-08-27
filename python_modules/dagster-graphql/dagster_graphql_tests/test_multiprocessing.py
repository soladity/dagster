import csv
import os
from collections import OrderedDict
from copy import deepcopy

from dagster_graphql.implementation.pipeline_execution_manager import (
    MultiprocessingExecutionManager,
)

from dagster import (
    ExecutionTargetHandle,
    Field,
    InputDefinition,
    Int,
    Materialization,
    OutputDefinition,
    Path,
    String,
    as_dagster_type,
    composite_solid,
    input_hydration_config,
    lambda_solid,
    output_materialization_config,
    pipeline,
    solid,
)
from dagster.core.events import DagsterEventType
from dagster.core.execution.api import ExecutionSelector
from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.core.storage.runs import InMemoryRunStorage
from dagster.core.utils import make_new_run_id
from dagster.utils import script_relative_path


class PoorMansDataFrame_(list):
    pass


@input_hydration_config(Path)
def df_input_schema(_context, path):
    with open(path, 'r') as fd:
        return PoorMansDataFrame_(
            [OrderedDict(sorted(x.items(), key=lambda x: x[0])) for x in csv.DictReader(fd)]
        )


@output_materialization_config(Path)
def df_output_schema(_context, path, value):
    with open(path, 'w') as fd:
        writer = csv.DictWriter(fd, fieldnames=value[0].keys())
        writer.writeheader()
        writer.writerows(rowdicts=value)

    return Materialization.file(path)


PoorMansDataFrame = as_dagster_type(
    PoorMansDataFrame_,
    input_hydration_config=df_input_schema,
    output_materialization_config=df_output_schema,
)


def get_events_of_type(events, event_type):
    return [
        event
        for event in events
        if event.is_dagster_event and event.dagster_event.event_type == event_type
    ]


def test_running():
    run_id = make_new_run_id()
    handle = ExecutionTargetHandle.for_pipeline_python_file(__file__, 'passing_pipeline')
    env_config = {
        'solids': {'sum_solid': {'inputs': {'num': script_relative_path('data/num.csv')}}}
    }
    selector = ExecutionSelector('csv_hello_world')
    run_storage = InMemoryRunStorage()
    pipeline_run = run_storage.create_run(
        pipeline_name=passing_pipeline.name,
        run_id=run_id,
        selector=selector,
        env_config=env_config,
        mode='default',
        reexecution_config=None,
        step_keys_to_execute=None,
    )
    execution_manager = MultiprocessingExecutionManager()
    execution_manager.execute_pipeline(handle, passing_pipeline, pipeline_run, raise_on_error=False)
    execution_manager.join()
    assert pipeline_run.status == PipelineRunStatus.SUCCESS
    events = pipeline_run.all_logs()
    assert events

    process_start_events = get_events_of_type(events, DagsterEventType.PIPELINE_PROCESS_START)
    assert len(process_start_events) == 1

    process_started_events = get_events_of_type(events, DagsterEventType.PIPELINE_PROCESS_STARTED)
    assert len(process_started_events) == 1


def test_failing():
    run_id = make_new_run_id()
    handle = ExecutionTargetHandle.for_pipeline_python_file(__file__, 'failing_pipeline')
    env_config = {
        'solids': {'sum_solid': {'inputs': {'num': script_relative_path('data/num.csv')}}}
    }
    selector = ExecutionSelector('csv_hello_world')
    run_storage = InMemoryRunStorage()
    pipeline_run = run_storage.create_run(
        run_storage=run_storage,
        pipeline_name=failing_pipeline.name,
        run_id=run_id,
        selector=selector,
        env_config=env_config,
        mode='default',
        reexecution_config=None,
        step_keys_to_execute=None,
    )
    execution_manager = MultiprocessingExecutionManager()
    execution_manager.execute_pipeline(handle, failing_pipeline, pipeline_run, raise_on_error=False)
    execution_manager.join()
    assert pipeline_run.status == PipelineRunStatus.FAILURE
    assert pipeline_run.all_logs()


def test_execution_crash():
    run_id = make_new_run_id()
    handle = ExecutionTargetHandle.for_pipeline_python_file(__file__, 'crashy_pipeline')
    env_config = {
        'solids': {'sum_solid': {'inputs': {'num': script_relative_path('data/num.csv')}}}
    }
    selector = ExecutionSelector('csv_hello_world')
    run_storage = InMemoryRunStorage()
    pipeline_run = run_storage.create_run(
        run_storage=run_storage,
        pipeline_name=crashy_pipeline.name,
        run_id=run_id,
        selector=selector,
        env_config=env_config,
        mode='default',
        reexecution_config=None,
        step_keys_to_execute=None,
    )
    execution_manager = MultiprocessingExecutionManager()
    execution_manager.execute_pipeline(handle, crashy_pipeline, pipeline_run, raise_on_error=False)
    execution_manager.join()
    assert pipeline_run.status == PipelineRunStatus.FAILURE
    last_log = pipeline_run.all_logs()[-1]
    print(last_log.message)
    assert last_log.message.startswith(
        'Exception: Pipeline execution process for {run_id} unexpectedly exited\n'.format(
            run_id=run_id
        )
    )


@lambda_solid(
    input_defs=[InputDefinition('num', PoorMansDataFrame)],
    output_def=OutputDefinition(PoorMansDataFrame),
)
def sum_solid(num):
    sum_df = deepcopy(num)
    for x in sum_df:
        x['sum'] = x['num1'] + x['num2']
    return PoorMansDataFrame(sum_df)


@lambda_solid(
    input_defs=[InputDefinition('sum_df', PoorMansDataFrame)],
    output_def=OutputDefinition(PoorMansDataFrame),
)
def error_solid(sum_df):  # pylint: disable=W0613
    raise Exception('foo')


@lambda_solid(
    input_defs=[InputDefinition('sum_df', PoorMansDataFrame)],
    output_def=OutputDefinition(PoorMansDataFrame),
)
def crashy_solid(sum_df):  # pylint: disable=W0613
    os._exit(1)  # pylint: disable=W0212


@pipeline
def passing_pipeline():
    return sum_solid()  # pylint: disable=no-value-for-parameter


@pipeline
def failing_pipeline():
    return error_solid(sum_solid())  # pylint: disable=no-value-for-parameter


@pipeline
def crashy_pipeline():
    crashy_solid(sum_solid())  # pylint: disable=no-value-for-parameter


@solid(config={'foo': Field(String)})
def node_a(context):
    return context.solid_config['foo']


@solid(config={'bar': Field(Int)})
def node_b(context, input_):
    return input_ * context.solid_config['bar']


@composite_solid
def composite_with_nested_config_solid():
    return node_b(node_a())  # pylint: disable=no-value-for-parameter


@pipeline
def composite_pipeline():
    return composite_with_nested_config_solid()


@composite_solid(
    config_fn=lambda _, cfg: {
        'node_a': {'config': {'foo': cfg['foo']}},
        'node_b': {'config': {'bar': cfg['bar']}},
    },
    config={'foo': Field(String), 'bar': Field(Int)},
)
def composite_with_nested_config_solid_and_config_mapping():
    return node_b(node_a())  # pylint: disable=no-value-for-parameter


@pipeline
def composite_pipeline_with_config_mapping():
    return composite_with_nested_config_solid_and_config_mapping()


def test_multiprocessing_execution_for_composite_solid():
    environment_dict = {
        'solids': {
            'composite_with_nested_config_solid': {
                'solids': {'node_a': {'config': {'foo': 'baz'}}, 'node_b': {'config': {'bar': 3}}}
            }
        }
    }

    run_id = make_new_run_id()
    handle = ExecutionTargetHandle.for_pipeline_python_file(__file__, 'composite_pipeline')
    run_storage = InMemoryRunStorage()
    pipeline_run = run_storage.create_run(
        run_storage=run_storage,
        pipeline_name=composite_pipeline.name,
        run_id=run_id,
        selector=ExecutionSelector('nonce'),
        env_config=environment_dict,
        mode='default',
        reexecution_config=None,
        step_keys_to_execute=None,
    )
    execution_manager = MultiprocessingExecutionManager()
    execution_manager.execute_pipeline(
        handle, composite_pipeline, pipeline_run, raise_on_error=False
    )
    execution_manager.join()
    assert pipeline_run.status == PipelineRunStatus.SUCCESS

    environment_dict = {
        'solids': {
            'composite_with_nested_config_solid': {
                'solids': {'node_a': {'config': {'foo': 'baz'}}, 'node_b': {'config': {'bar': 3}}}
            }
        },
        'execution': {'multiprocess': {}},
        'storage': {'filesystem': {}},
    }

    run_id = make_new_run_id()
    pipeline_run = run_storage.create_run(
        run_storage=run_storage,
        pipeline_name=composite_pipeline.name,
        run_id=run_id,
        selector=ExecutionSelector('nonce'),
        env_config=environment_dict,
        mode='default',
        reexecution_config=None,
        step_keys_to_execute=None,
    )
    execution_manager = MultiprocessingExecutionManager()
    execution_manager.execute_pipeline(
        handle, composite_pipeline, pipeline_run, raise_on_error=False
    )
    execution_manager.join()


def test_multiprocessing_execution_for_composite_solid_with_config_mapping():
    environment_dict = {
        'solids': {
            'composite_with_nested_config_solid_and_config_mapping': {
                'config': {'foo': 'baz', 'bar': 3}
            }
        }
    }

    run_id = make_new_run_id()
    handle = ExecutionTargetHandle.for_pipeline_python_file(
        __file__, 'composite_pipeline_with_config_mapping'
    )
    run_storage = InMemoryRunStorage()
    pipeline_run = run_storage.create_run(
        run_storage=run_storage,
        pipeline_name=composite_pipeline_with_config_mapping.name,
        run_id=run_id,
        selector=ExecutionSelector('nonce'),
        env_config=environment_dict,
        mode='default',
        reexecution_config=None,
        step_keys_to_execute=None,
    )
    execution_manager = MultiprocessingExecutionManager()
    execution_manager.execute_pipeline(
        handle, composite_pipeline_with_config_mapping, pipeline_run, raise_on_error=False
    )
    execution_manager.join()
    assert pipeline_run.status == PipelineRunStatus.SUCCESS

    environment_dict = {
        'solids': {
            'composite_with_nested_config_solid_and_config_mapping': {
                'config': {'foo': 'baz', 'bar': 3}
            }
        },
        'execution': {'multiprocess': {}},
        'storage': {'filesystem': {}},
    }

    run_id = make_new_run_id()
    pipeline_run = run_storage.create_run(
        run_storage=run_storage,
        pipeline_name=composite_pipeline.name,
        run_id=run_id,
        selector=ExecutionSelector('nonce'),
        env_config=environment_dict,
        mode='default',
        reexecution_config=None,
        step_keys_to_execute=None,
    )
    execution_manager = MultiprocessingExecutionManager()
    execution_manager.execute_pipeline(
        handle, composite_pipeline, pipeline_run, raise_on_error=False
    )

    execution_manager.join()
    assert pipeline_run.status == PipelineRunStatus.SUCCESS
