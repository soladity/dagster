import csv
import os
import time
from collections import OrderedDict
from contextlib import contextmanager
from copy import deepcopy

from dagster import (
    Field,
    InputDefinition,
    Int,
    Materialization,
    OutputDefinition,
    PythonObjectDagsterType,
    String,
    composite_solid,
    execute_pipeline,
    input_hydration_config,
    lambda_solid,
    output_materialization_config,
    pipeline,
    reconstructable,
    seven,
    solid,
)
from dagster.core.events import DagsterEventType
from dagster.core.host_representation.handle import RepositoryHandle, RepositoryLocationHandle
from dagster.core.instance import DagsterInstance
from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.utils import file_relative_path, safe_tempfile_path
from dagster.utils.hosted_user_process import external_pipeline_from_recon_pipeline


@input_hydration_config(String)
def df_input_schema(_context, path):
    with open(path, 'r') as fd:
        return [OrderedDict(sorted(x.items(), key=lambda x: x[0])) for x in csv.DictReader(fd)]


@output_materialization_config(String)
def df_output_schema(_context, path, value):
    with open(path, 'w') as fd:
        writer = csv.DictWriter(fd, fieldnames=value[0].keys())
        writer.writeheader()
        writer.writerows(rowdicts=value)

    return Materialization.file(path)


PoorMansDataFrame = PythonObjectDagsterType(
    python_type=list,
    name='PoorMansDataFrame',
    input_hydration_config=df_input_schema,
    output_materialization_config=df_output_schema,
)


@lambda_solid(
    input_defs=[InputDefinition('num', PoorMansDataFrame)],
    output_def=OutputDefinition(PoorMansDataFrame),
)
def sum_solid(num):
    sum_df = deepcopy(num)
    for x in sum_df:
        x['sum'] = x['num1'] + x['num2']
    return sum_df


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
    return sum_solid()


@pipeline
def failing_pipeline():
    return error_solid(sum_solid())


@pipeline
def crashy_pipeline():
    crashy_solid(sum_solid())


@solid(config={'foo': Field(String)})
def node_a(context):
    return context.solid_config['foo']


@solid(config={'bar': Int})
def node_b(context, input_):
    return input_ * context.solid_config['bar']


@composite_solid
def composite_with_nested_config_solid():
    return node_b(node_a())


@pipeline
def composite_pipeline():
    return composite_with_nested_config_solid()


@composite_solid(
    config_fn=lambda cfg: {
        'node_a': {'config': {'foo': cfg['foo']}},
        'node_b': {'config': {'bar': cfg['bar']}},
    },
    config={'foo': Field(String), 'bar': Int},
)
def composite_with_nested_config_solid_and_config_mapping():
    return node_b(node_a())


@pipeline
def composite_pipeline_with_config_mapping():
    return composite_with_nested_config_solid_and_config_mapping()


def get_events_of_type(events, event_type):
    return [
        event
        for event in events
        if event.is_dagster_event and event.dagster_event.event_type == event_type
    ]


@contextmanager
def temp_instance():
    with seven.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance.local_temp(temp_dir)
        try:
            yield instance
        finally:
            instance.run_launcher.join()


def test_works_in_memory():

    environment_dict = {
        'solids': {'sum_solid': {'inputs': {'num': file_relative_path(__file__, 'data/num.csv')}}}
    }
    assert execute_pipeline(passing_pipeline, environment_dict).success


def _external_pipeline_from_def(pipeline_def, solid_selection=None):
    recon_pipeline = reconstructable(pipeline_def)
    recon_repo = recon_pipeline.repository
    repo_def = recon_repo.get_definition()
    location_handle = RepositoryLocationHandle.create_in_process_location(recon_repo.pointer)
    repository_handle = RepositoryHandle(
        repository_name=repo_def.name,
        repository_key=repo_def.name,
        repository_location_handle=location_handle,
    )
    return external_pipeline_from_recon_pipeline(
        reconstructable(pipeline_def),
        solid_selection=solid_selection,
        repository_handle=repository_handle,
    )


def _execute_in_launcher(instance, pipeline_def, environment_dict, solid_selection=None):
    created_pipeline_run = instance.create_run_for_pipeline(
        pipeline_def=pipeline_def, environment_dict=environment_dict
    )

    run = instance.launch_run(
        created_pipeline_run.run_id,
        _external_pipeline_from_def(pipeline_def, solid_selection=solid_selection),
    )

    instance.run_launcher.join()

    return run


def test_running():
    environment_dict = {
        'solids': {'sum_solid': {'inputs': {'num': file_relative_path(__file__, 'data/num.csv')}}}
    }

    with temp_instance() as instance:
        pipeline_run = _execute_in_launcher(instance, passing_pipeline, environment_dict)

        assert instance.get_run_by_id(pipeline_run.run_id).status == PipelineRunStatus.SUCCESS
        events = instance.all_logs(pipeline_run.run_id)
        assert events

        engine_events = get_events_of_type(events, DagsterEventType.ENGINE_EVENT)
        assert len(engine_events) == 5
        (
            _about_to_start,
            _started,
            _executing_step_in_process,
            _finished_steps_in_process,
            _process_exited,
        ) = engine_events


def test_failing():
    with temp_instance() as instance:
        environment_dict = {
            'solids': {
                'sum_solid': {'inputs': {'num': file_relative_path(__file__, 'data/num.csv')}}
            }
        }

        pipeline_run = _execute_in_launcher(instance, failing_pipeline, environment_dict)

        assert instance.get_run_by_id(pipeline_run.run_id).status == PipelineRunStatus.FAILURE
        assert instance.all_logs(pipeline_run.run_id)


def test_execution_crash():
    environment_dict = {
        'solids': {'sum_solid': {'inputs': {'num': file_relative_path(__file__, 'data/num.csv')}}}
    }

    with temp_instance() as instance:

        pipeline_run = _execute_in_launcher(instance, crashy_pipeline, environment_dict)

        assert instance.get_run_by_id(pipeline_run.run_id).status == PipelineRunStatus.FAILURE
        crash_log = instance.all_logs(pipeline_run.run_id)[
            -2
        ]  # last message is pipeline failure, second to last is...

        assert crash_log.message.startswith(
            '[CliApiRunLauncher] Pipeline execution process for {run_id} unexpectedly exited'.format(
                run_id=pipeline_run.run_id
            )
        )


def test_multiprocessing_execution_for_composite_solid():
    environment_dict = {
        'solids': {
            'composite_with_nested_config_solid': {
                'solids': {'node_a': {'config': {'foo': 'baz'}}, 'node_b': {'config': {'bar': 3}}}
            }
        }
    }

    with temp_instance() as instance:
        pipeline_run = _execute_in_launcher(instance, composite_pipeline, environment_dict)
        assert instance.get_run_by_id(pipeline_run.run_id).status == PipelineRunStatus.SUCCESS


def test_multiprocessing_execution_for_composite_solid_multiprocess_executor():
    environment_dict = {
        'solids': {
            'composite_with_nested_config_solid': {
                'solids': {'node_a': {'config': {'foo': 'baz'}}, 'node_b': {'config': {'bar': 3}}}
            }
        },
        'execution': {'multiprocess': {}},
        'storage': {'filesystem': {}},
    }

    with temp_instance() as instance:
        second_run = _execute_in_launcher(instance, composite_pipeline, environment_dict)
        assert instance.get_run_by_id(second_run.run_id).status == PipelineRunStatus.SUCCESS


def test_multiprocessing_execution_for_composite_solid_with_config_mapping():
    environment_dict = {
        'solids': {
            'composite_with_nested_config_solid_and_config_mapping': {
                'config': {'foo': 'baz', 'bar': 3}
            }
        }
    }
    with temp_instance() as instance:
        pipeline_run = _execute_in_launcher(
            instance,
            pipeline_def=composite_pipeline_with_config_mapping,
            environment_dict=environment_dict,
        )
        assert instance.get_run_by_id(pipeline_run.run_id).status == PipelineRunStatus.SUCCESS


def test_multiprocessing_execution_for_composite_solid_with_config_mapping_with_multiprocess():
    environment_dict = {
        'solids': {
            'composite_with_nested_config_solid_and_config_mapping': {
                'config': {'foo': 'baz', 'bar': 3}
            },
        },
        'execution': {'multiprocess': {}},
        'storage': {'filesystem': {}},
    }
    with temp_instance() as instance:
        pipeline_run = _execute_in_launcher(
            instance,
            pipeline_def=composite_pipeline_with_config_mapping,
            environment_dict=environment_dict,
        )
        assert instance.get_run_by_id(pipeline_run.run_id).status == PipelineRunStatus.SUCCESS


@solid(config={'file': Field(String)})
def loop(context):
    with open(context.solid_config['file'], 'w') as ff:
        ff.write('yup')

    while True:
        time.sleep(0.1)


@pipeline
def infinite_loop_pipeline():
    loop()


def test_has_run_query_and_terminate():
    with temp_instance() as instance:
        with safe_tempfile_path() as path:
            environment_dict = {'solids': {'loop': {'config': {'file': path}}}}

            created_pipeline_run = instance.create_run_for_pipeline(
                pipeline_def=infinite_loop_pipeline, environment_dict=environment_dict,
            )

            pipeline_run = instance.launch_run(
                created_pipeline_run.run_id, _external_pipeline_from_def(infinite_loop_pipeline)
            )

            while not os.path.exists(path):
                time.sleep(0.1)

            assert os.path.exists(path)

            run_launcher = instance.run_launcher

            assert run_launcher.can_terminate(pipeline_run.run_id)
            assert run_launcher.terminate(pipeline_run.run_id)
            assert instance.get_run_by_id(pipeline_run.run_id).is_finished
            assert not run_launcher.can_terminate(pipeline_run.run_id)
            assert not run_launcher.terminate(pipeline_run.run_id)

        assert not os.path.exists(path)


def test_two_runs_running():
    with safe_tempfile_path() as file_one, safe_tempfile_path() as file_two, temp_instance() as instance:
        pipeline_run_one = instance.create_run_for_pipeline(
            pipeline_def=infinite_loop_pipeline,
            environment_dict={'solids': {'loop': {'config': {'file': file_one}}}},
        )
        instance.launch_run(
            pipeline_run_one.run_id, _external_pipeline_from_def(infinite_loop_pipeline)
        )

        pipeline_run_two = instance.create_run_for_pipeline(
            pipeline_def=infinite_loop_pipeline,
            environment_dict={'solids': {'loop': {'config': {'file': file_two}}}},
        )

        instance.launch_run(
            pipeline_run_two.run_id, _external_pipeline_from_def(infinite_loop_pipeline)
        )

        # ensure both runs have begun execution
        while not os.path.exists(file_one) and not os.path.exists(file_two):
            time.sleep(0.1)

        run_launcher = instance.run_launcher

        assert run_launcher.can_terminate(pipeline_run_one.run_id)
        assert run_launcher.can_terminate(pipeline_run_two.run_id)

        assert run_launcher.terminate(pipeline_run_one.run_id)

        assert not run_launcher.can_terminate(pipeline_run_one.run_id)
        assert run_launcher.can_terminate(pipeline_run_two.run_id)

        assert run_launcher.terminate(pipeline_run_two.run_id)

        assert not run_launcher.can_terminate(pipeline_run_one.run_id)
        assert not run_launcher.can_terminate(pipeline_run_two.run_id)
