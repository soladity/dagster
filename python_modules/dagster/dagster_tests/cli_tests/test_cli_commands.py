from __future__ import print_function

import os
import re
import string
from contextlib import contextmanager

import mock
import pytest
from click import UsageError
from click.testing import CliRunner

from dagster import (
    DagsterInvariantViolationError,
    PartitionSetDefinition,
    ScheduleDefinition,
    check,
    lambda_solid,
    pipeline,
    repository,
    seven,
    solid,
)
from dagster.cli.pipeline import (
    execute_backfill_command,
    execute_execute_command,
    execute_list_command,
    execute_print_command,
    execute_scaffold_command,
    pipeline_backfill_command,
    pipeline_execute_command,
    pipeline_launch_command,
    pipeline_list_command,
    pipeline_print_command,
    pipeline_scaffold_command,
)
from dagster.cli.run import run_list_command, run_wipe_command
from dagster.cli.schedule import (
    schedule_list_command,
    schedule_logs_command,
    schedule_restart_command,
    schedule_start_command,
    schedule_stop_command,
    schedule_up_command,
    schedule_wipe_command,
)
from dagster.config.field_utils import Shape
from dagster.core.instance import DagsterInstance, InstanceType
from dagster.core.launcher import RunLauncher
from dagster.core.launcher.sync_in_memory_run_launcher import SyncInMemoryRunLauncher
from dagster.core.storage.event_log import InMemoryEventLogStorage
from dagster.core.storage.noop_compute_log_manager import NoOpComputeLogManager
from dagster.core.storage.root import LocalArtifactStorage
from dagster.core.storage.runs import InMemoryRunStorage
from dagster.core.storage.schedules import SqliteScheduleStorage
from dagster.serdes import ConfigurableClass
from dagster.utils import file_relative_path
from dagster.utils.test import FilesystemTestScheduler


def no_print(_):
    return None


@lambda_solid
def do_something():
    return 1


@lambda_solid
def do_input(x):
    return x


@pipeline(name='foo')
def foo_pipeline():
    do_input(do_something())


def define_foo_pipeline():
    return foo_pipeline


@pipeline(name='baz', description='Not much tbh')
def baz_pipeline():
    do_input()


def define_bar_schedules():
    return {
        'foo_schedule': ScheduleDefinition(
            "foo_schedule",
            cron_schedule="* * * * *",
            pipeline_name="test_pipeline",
            environment_dict={},
        )
    }


def define_baz_partitions():
    return {
        'baz_partitions': PartitionSetDefinition(
            name='baz_partitions',
            pipeline_name='baz',
            partition_fn=lambda: string.ascii_lowercase,
            environment_dict_fn_for_partition=lambda partition: {
                'solids': {'do_input': {'inputs': {'x': {'value': partition.value}}}}
            },
        )
    }


@repository
def bar():
    return {
        'pipelines': {'foo': foo_pipeline, 'baz': baz_pipeline},
        'schedules': define_bar_schedules(),
        'partition_sets': define_baz_partitions(),
    }


@solid
def spew(context):
    context.log.info('HELLO WORLD')


@solid
def fail(context):
    raise Exception('I AM SUPPOSED TO FAIL')


@pipeline
def stdout_pipeline():
    spew()


@pipeline
def stderr_pipeline():
    fail()


def assert_correct_hello_cereal_output(result):
    assert result.exit_code == 0
    assert result.output == (
        'Repository hello_cereal_repository\n'
        '**********************************\n'
        'Pipeline: complex_pipeline\n'
        'Solids: (Execution Order)\n'
        '    load_cereals\n'
        '    sort_by_calories\n'
        '    sort_by_protein\n'
        '    display_results\n'
        '*******************************\n'
        'Pipeline: hello_cereal_pipeline\n'
        'Solids: (Execution Order)\n'
        '    hello_cereal\n'
    )


def assert_correct_bar_repository_output(result):
    assert result.exit_code == 0
    assert result.output == (
        'Repository bar\n'
        '**************\n'
        'Pipeline: baz\n'
        'Description:\n'
        'Not much tbh\n'
        'Solids: (Execution Order)\n'
        '    do_input\n'
        '*************\n'
        'Pipeline: foo\n'
        'Solids: (Execution Order)\n'
        '    do_something\n'
        '    do_input\n'
    )


def test_list_command():
    runner = CliRunner()

    execute_list_command(
        {
            'repository_yaml': None,
            'python_file': file_relative_path(__file__, 'test_cli_commands.py'),
            'module_name': None,
            'fn_name': 'bar',
        },
        no_print,
    )

    result = runner.invoke(
        pipeline_list_command,
        ['-f', file_relative_path(__file__, 'test_cli_commands.py'), '-a', 'bar'],
    )

    assert_correct_bar_repository_output(result)

    execute_list_command(
        {
            'repository_yaml': None,
            'python_file': None,
            'module_name': 'dagster_examples.intro_tutorial.repos',
            'fn_name': 'hello_cereal_repository',
        },
        no_print,
    )

    result = runner.invoke(
        pipeline_list_command,
        ['-m', 'dagster_examples.intro_tutorial.repos', '-a', 'hello_cereal_repository'],
    )
    assert_correct_hello_cereal_output(result)

    execute_list_command(
        {
            'repository_yaml': file_relative_path(__file__, 'repository_module.yaml'),
            'python_file': None,
            'module_name': None,
            'fn_name': None,
        },
        no_print,
    )

    result = runner.invoke(
        pipeline_list_command, ['-w', file_relative_path(__file__, 'repository_module.yaml')]
    )
    assert_correct_hello_cereal_output(result)

    with pytest.raises(UsageError):
        execute_list_command(
            {
                'repository_yaml': None,
                'python_file': 'foo.py',
                'module_name': 'dagster_examples.intro_tutorial.repos',
                'fn_name': 'hello_cereal_repository',
            },
            no_print,
        )

    result = runner.invoke(
        pipeline_list_command,
        [
            '-f',
            'foo.py',
            '-m',
            'dagster_examples.intro_tutorial.repos',
            '-a',
            'hello_cereal_repository',
        ],
    )
    assert result.exit_code == 2

    result = runner.invoke(pipeline_list_command, ['-m', 'dagster_examples.intro_tutorial.repos'])
    assert_correct_hello_cereal_output(result)

    result = runner.invoke(
        pipeline_list_command, ['-f', file_relative_path(__file__, 'test_cli_commands.py')]
    )
    assert_correct_bar_repository_output(result)


def valid_execute_args():
    return [
        {
            'workspace': file_relative_path(__file__, 'repository_file.yaml'),
            'pipeline': 'foo',
            'python_file': None,
            'module_name': None,
            'attribute': None,
        },
        {
            'workspace': file_relative_path(__file__, 'repository_module.yaml'),
            'pipeline': 'hello_cereal_pipeline',
            'python_file': None,
            'module_name': None,
            'attribute': None,
        },
        {
            'workspace': None,
            'pipeline': 'foo',
            'python_file': file_relative_path(__file__, 'test_cli_commands.py'),
            'module_name': None,
            'attribute': 'bar',
        },
        {
            'workspace': None,
            'pipeline': 'hello_cereal_pipeline',
            'python_file': None,
            'module_name': 'dagster_examples.intro_tutorial.repos',
            'attribute': 'hello_cereal_repository',
        },
        {
            'workspace': None,
            'pipeline': None,
            'python_file': None,
            'module_name': 'dagster_examples.intro_tutorial.repos',
            'attribute': 'hello_cereal_pipeline',
        },
        {
            'workspace': None,
            'pipeline': None,
            'python_file': file_relative_path(__file__, 'test_cli_commands.py'),
            'module_name': None,
            'attribute': 'define_foo_pipeline',
        },
        {
            'workspace': None,
            'pipeline': None,
            'python_file': file_relative_path(__file__, 'test_cli_commands.py'),
            'module_name': None,
            'attribute': 'foo_pipeline',
        },
    ]


def valid_cli_args():
    return [
        ['-w', file_relative_path(__file__, 'repository_file.yaml'), '-p', 'foo'],
        [
            '-w',
            file_relative_path(__file__, 'repository_module.yaml'),
            '-p',
            'hello_cereal_pipeline',
        ],
        ['-f', file_relative_path(__file__, 'test_cli_commands.py'), '-a', 'bar', '-p', 'foo',],
        [
            '-m',
            'dagster_examples.intro_tutorial.repos',
            '-a',
            'hello_cereal_repository',
            '-p',
            'hello_cereal_pipeline',
        ],
        ['-m', 'dagster_examples.intro_tutorial.repos', '-a', 'hello_cereal_pipeline'],
        ['-f', file_relative_path(__file__, 'test_cli_commands.py'), '-a', 'define_foo_pipeline'],
    ]


def test_print_command():
    for cli_args in valid_execute_args():
        execute_print_command(verbose=True, cli_args=cli_args, print_fn=no_print)

    for cli_args in valid_execute_args():
        execute_print_command(verbose=False, cli_args=cli_args, print_fn=no_print)

    runner = CliRunner()

    for cli_args in valid_cli_args():

        result = runner.invoke(pipeline_print_command, cli_args)
        assert result.exit_code == 0, result.stdout

        result = runner.invoke(pipeline_print_command, ['--verbose'] + cli_args)
        assert result.exit_code == 0, result.stdout

    res = runner.invoke(
        pipeline_print_command,
        [
            '--verbose',
            '-f',
            file_relative_path(__file__, 'test_cli_commands.py'),
            '-a',
            'bar',
            '-p',
            'baz',
        ],
    )
    assert res.exit_code == 0, res.stdout


def test_execute_mode_command():
    runner = CliRunner()

    add_result = runner_pipeline_execute(
        runner,
        [
            '-w',
            file_relative_path(__file__, '../repository.yaml'),
            '--config',
            file_relative_path(__file__, '../environments/multi_mode_with_resources/add_mode.yaml'),
            '-d',
            'add_mode',
            '-p',
            'multi_mode_with_resources',  # pipeline name
        ],
    )

    assert add_result

    mult_result = runner_pipeline_execute(
        runner,
        [
            '-w',
            file_relative_path(__file__, '../repository.yaml'),
            '--config',
            file_relative_path(
                __file__, '../environments/multi_mode_with_resources/mult_mode.yaml'
            ),
            '-d',
            'mult_mode',
            '-p',
            'multi_mode_with_resources',  # pipeline name
        ],
    )

    assert mult_result

    double_adder_result = runner_pipeline_execute(
        runner,
        [
            '-w',
            file_relative_path(__file__, '../repository.yaml'),
            '--config',
            file_relative_path(
                __file__, '../environments/multi_mode_with_resources/double_adder_mode.yaml'
            ),
            '-d',
            'double_adder_mode',
            '-p',
            'multi_mode_with_resources',  # pipeline name
        ],
    )

    assert double_adder_result


def test_execute_preset_command():
    runner = CliRunner()
    add_result = runner_pipeline_execute(
        runner,
        [
            '-w',
            file_relative_path(__file__, '../repository.yaml'),
            '--preset',
            'add',
            '-p',
            'multi_mode_with_resources',  # pipeline name
        ],
    )

    assert 'PIPELINE_SUCCESS' in add_result.output

    # Can't use --preset with --config
    bad_res = runner.invoke(
        pipeline_execute_command,
        [
            '-w',
            file_relative_path(__file__, '../repository.yaml'),
            '--preset',
            'add',
            '--config',
            file_relative_path(
                __file__, '../environments/multi_mode_with_resources/double_adder_mode.yaml'
            ),
            '-p',
            'multi_mode_with_resources',  # pipeline name
        ],
    )
    assert bad_res.exit_code == 2


def test_execute_command():
    for cli_args in valid_execute_args():
        execute_execute_command(env=None, cli_args=cli_args)

    for cli_args in valid_execute_args():
        execute_execute_command(
            env=[file_relative_path(__file__, 'default_log_error_env.yaml')], cli_args=cli_args
        )

    runner = CliRunner()

    for cli_args in valid_cli_args():
        runner_pipeline_execute(runner, cli_args)

        runner_pipeline_execute(
            runner,
            ['--config', file_relative_path(__file__, 'default_log_error_env.yaml')] + cli_args,
        )


def test_stdout_execute_command():
    runner = CliRunner()
    result = runner_pipeline_execute(
        runner,
        ['-f', file_relative_path(__file__, 'test_cli_commands.py'), '-a', 'stdout_pipeline'],
    )
    assert result.exit_code == 0, result.stdout
    assert 'HELLO WORLD' in result.output


def test_stderr_execute_command():
    runner = CliRunner()
    result = runner.invoke(
        pipeline_execute_command,
        ['-f', file_relative_path(__file__, 'test_cli_commands.py'), '-a', 'stderr_pipeline'],
    )
    assert result.exit_code != 0
    assert 'I AM SUPPOSED TO FAIL' in result.output


def test_more_than_one_pipeline():
    with pytest.raises(
        UsageError,
        match=re.escape(
            "Must provide --pipeline as there is more than one pipeline in bar. "
            "Options are: ['baz', 'foo']."
        ),
    ):
        execute_execute_command(
            env=None,
            cli_args={
                'repository_yaml': None,
                'pipeline': None,
                'python_file': file_relative_path(__file__, 'test_cli_commands.py'),
                'module_name': None,
                'attribute': None,
            },
        )


def test_attribute_not_found():
    with pytest.raises(
        DagsterInvariantViolationError, match=re.escape('nope not found at module scope in file')
    ):
        execute_execute_command(
            env=None,
            cli_args={
                'repository_yaml': None,
                'pipeline': None,
                'python_file': file_relative_path(__file__, 'test_cli_commands.py'),
                'module_name': None,
                'attribute': 'nope',
            },
        )


def not_a_repo_or_pipeline_fn():
    return 'kdjfkjdf'


not_a_repo_or_pipeline = 123


def test_attribute_is_wrong_thing():
    with pytest.raises(
        DagsterInvariantViolationError,
        match=re.escape(
            'Loadable attributes must be either a PipelineDefinition or a '
            'RepositoryDefinition. Got 123.'
        ),
    ):
        execute_execute_command(
            env=[],
            cli_args={
                'repository_yaml': None,
                'pipeline': None,
                'python_file': file_relative_path(__file__, 'test_cli_commands.py'),
                'module_name': None,
                'attribute': 'not_a_repo_or_pipeline',
            },
        )


def test_attribute_fn_returns_wrong_thing():
    with pytest.raises(
        DagsterInvariantViolationError,
        match=re.escape(
            "Loadable attributes must be either a PipelineDefinition or a "
            "RepositoryDefinition. Got 'kdjfkjdf'."
        ),
    ):
        execute_execute_command(
            env=[],
            cli_args={
                'repository_yaml': None,
                'pipeline': None,
                'python_file': file_relative_path(__file__, 'test_cli_commands.py'),
                'module_name': None,
                'attribute': 'not_a_repo_or_pipeline_fn',
            },
        )


def runner_pipeline_execute(runner, cli_args):
    result = runner.invoke(pipeline_execute_command, cli_args)
    if result.exit_code != 0:
        # CliRunner captures stdout so printing it out here
        raise Exception(
            (
                'dagster pipeline execute commands with cli_args {cli_args} '
                'returned exit_code {exit_code} with stdout:\n"{stdout}" and '
                '\nresult as string: "{result}"'
            ).format(
                cli_args=cli_args, exit_code=result.exit_code, stdout=result.stdout, result=result
            )
        )
    return result


def test_scaffold_command():
    for cli_args in valid_execute_args():
        cli_args['print_only_required'] = True
        execute_scaffold_command(cli_args=cli_args, print_fn=no_print)

        cli_args['print_only_required'] = False
        execute_scaffold_command(cli_args=cli_args, print_fn=no_print)

    runner = CliRunner()

    for cli_args in valid_cli_args():
        result = runner.invoke(pipeline_scaffold_command, cli_args)
        assert result.exit_code == 0

        result = runner.invoke(pipeline_scaffold_command, ['--print-only-required'] + cli_args)
        assert result.exit_code == 0


def test_default_memory_run_storage():
    cli_args = {
        'workspace': file_relative_path(__file__, 'repository_file.yaml'),
        'pipeline': 'foo',
        'python_file': None,
        'module_name': None,
        'attribute': None,
    }
    result = execute_execute_command(env=None, cli_args=cli_args)
    assert result.success


def test_override_with_in_memory_storage():
    cli_args = {
        'workspace': file_relative_path(__file__, 'repository_file.yaml'),
        'pipeline': 'foo',
        'python_file': None,
        'module_name': None,
        'attribute': None,
    }
    result = execute_execute_command(
        env=[file_relative_path(__file__, 'in_memory_env.yaml')], cli_args=cli_args
    )
    assert result.success


def test_override_with_filesystem_storage():
    cli_args = {
        'workspace': file_relative_path(__file__, 'repository_file.yaml'),
        'pipeline': 'foo',
        'python_file': None,
        'module_name': None,
        'attribute': None,
    }
    result = execute_execute_command(
        env=[file_relative_path(__file__, 'filesystem_env.yaml')], cli_args=cli_args
    )
    assert result.success


def test_run_list():
    runner = CliRunner()
    result = runner.invoke(run_list_command)
    assert result.exit_code == 0


def test_run_wipe_correct_delete_message():
    runner = CliRunner()
    result = runner.invoke(run_wipe_command, input="DELETE\n")
    assert 'Deleted all run history and event logs' in result.output
    assert result.exit_code == 0


def test_run_wipe_incorrect_delete_message():
    runner = CliRunner()
    result = runner.invoke(run_wipe_command, input="WRONG\n")
    assert 'Exiting without deleting all run history and event logs' in result.output
    assert result.exit_code == 0


@pytest.fixture(name="scheduler_instance")
def define_scheduler_instance():
    with seven.TemporaryDirectory() as temp_dir:
        yield DagsterInstance(
            instance_type=InstanceType.EPHEMERAL,
            local_artifact_storage=LocalArtifactStorage(temp_dir),
            run_storage=InMemoryRunStorage(),
            event_storage=InMemoryEventLogStorage(),
            schedule_storage=SqliteScheduleStorage.from_local(temp_dir),
            scheduler=FilesystemTestScheduler(temp_dir),
            compute_log_manager=NoOpComputeLogManager(),
            run_launcher=SyncInMemoryRunLauncher(),
        )


@pytest.fixture(name="_patch_scheduler_instance")
def mock_scheduler_instance(mocker, scheduler_instance):
    mocker.patch(
        'dagster.core.instance.DagsterInstance.get', return_value=scheduler_instance,
    )


def test_schedules_list(_patch_scheduler_instance):
    runner = CliRunner()

    result = runner.invoke(
        schedule_list_command, ['-w', file_relative_path(__file__, 'workspace.yaml')]
    )

    if result.exception:
        raise result.exception

    assert result.exit_code == 0
    assert result.output == ('Repository bar\n' '**************\n')


def test_schedules_up(_patch_scheduler_instance):
    runner = CliRunner()

    result = runner.invoke(
        schedule_up_command, ['-w', file_relative_path(__file__, 'workspace.yaml')]
    )
    assert result.exit_code == 0
    assert 'Changes:\n  + foo_schedule (add)' in result.output


def test_schedules_up_and_list(_patch_scheduler_instance):
    runner = CliRunner()

    result = runner.invoke(
        schedule_up_command, ['-w', file_relative_path(__file__, 'workspace.yaml')]
    )

    result = runner.invoke(
        schedule_list_command, ['-w', file_relative_path(__file__, 'workspace.yaml')]
    )

    assert result.exit_code == 0
    assert (
        result.output == 'Repository bar\n'
        '**************\n'
        'Schedule: foo_schedule [STOPPED]\n'
        'Cron Schedule: * * * * *\n'
    )


def test_schedules_start_and_stop(_patch_scheduler_instance):
    runner = CliRunner()

    result = runner.invoke(
        schedule_up_command, ['-w', file_relative_path(__file__, 'workspace.yaml')],
    )

    result = runner.invoke(
        schedule_start_command,
        ['-w', file_relative_path(__file__, 'workspace.yaml'), 'foo_schedule'],
    )

    assert result.exit_code == 0
    assert 'Started schedule foo_schedule\n' == result.output

    result = runner.invoke(
        schedule_stop_command,
        ['-w', file_relative_path(__file__, 'workspace.yaml'), 'foo_schedule'],
    )

    assert result.exit_code == 0
    assert 'Stopped schedule foo_schedule\n' == result.output


def test_schedules_start_empty(_patch_scheduler_instance):
    runner = CliRunner()

    result = runner.invoke(
        schedule_start_command, ['-w', file_relative_path(__file__, 'workspace.yaml')],
    )

    assert result.exit_code == 0
    assert 'Noop: dagster schedule start was called without any arguments' in result.output


def test_schedules_start_all(_patch_scheduler_instance):
    runner = CliRunner()

    result = runner.invoke(
        schedule_up_command, ['-w', file_relative_path(__file__, 'workspace.yaml')]
    )

    result = runner.invoke(
        schedule_start_command,
        ['-w', file_relative_path(__file__, 'workspace.yaml'), '--start-all'],
    )

    assert result.exit_code == 0
    assert result.output == 'Started all schedules for repository bar\n'


def test_schedules_wipe_correct_delete_message(_patch_scheduler_instance):
    runner = CliRunner()

    result = runner.invoke(
        schedule_up_command, ['-w', file_relative_path(__file__, 'workspace.yaml')]
    )

    result = runner.invoke(
        schedule_wipe_command,
        ['-w', file_relative_path(__file__, 'workspace.yaml')],
        input="DELETE\n",
    )

    if result.exception:
        raise result.exception

    assert result.exit_code == 0
    assert 'Wiped all schedules and schedule cron jobs' in result.output

    result = runner.invoke(
        schedule_up_command, ['-w', file_relative_path(__file__, 'workspace.yaml'), '--preview'],
    )

    # Verify schedules were wiped
    assert result.exit_code == 0
    assert 'Planned Schedule Changes:\n  + foo_schedule (add)' in result.output


def test_schedules_wipe_incorrect_delete_message(_patch_scheduler_instance):
    runner = CliRunner()

    result = runner.invoke(
        schedule_up_command, ['-w', file_relative_path(__file__, 'workspace.yaml')]
    )

    result = runner.invoke(
        schedule_wipe_command,
        ['-w', file_relative_path(__file__, 'workspace.yaml')],
        input="WRONG\n",
    )

    assert result.exit_code == 0
    assert 'Exiting without deleting all schedules and schedule cron jobs' in result.output

    result = runner.invoke(
        schedule_up_command, ['-w', file_relative_path(__file__, 'workspace.yaml'), '--preview'],
    )

    # Verify schedules were not wiped
    assert result.exit_code == 0
    assert result.output == 'No planned changes to schedules.\n1 schedules will remain unchanged\n'


def test_schedules_restart(_patch_scheduler_instance):
    runner = CliRunner()

    result = runner.invoke(
        schedule_up_command, ['-w', file_relative_path(__file__, 'workspace.yaml')]
    )

    result = runner.invoke(
        schedule_start_command,
        ['-w', file_relative_path(__file__, 'workspace.yaml'), 'foo_schedule'],
    )

    result = runner.invoke(
        schedule_restart_command,
        ['-w', file_relative_path(__file__, 'workspace.yaml'), 'foo_schedule'],
    )

    assert result.exit_code == 0
    assert 'Restarted schedule foo_schedule' in result.output


def test_schedules_restart_all(_patch_scheduler_instance):
    runner = CliRunner()

    result = runner.invoke(
        schedule_up_command, ['-w', file_relative_path(__file__, 'workspace.yaml')]
    )

    result = runner.invoke(
        schedule_start_command,
        ['-w', file_relative_path(__file__, 'workspace.yaml'), 'foo_schedule'],
    )

    result = runner.invoke(
        schedule_restart_command,
        [
            '-w',
            file_relative_path(__file__, 'workspace.yaml'),
            'foo_schedule',
            '--restart-all-running',
        ],
    )
    assert result.exit_code == 0
    assert result.output == 'Restarted all running schedules for repository bar\n'


def test_schedules_logs(_patch_scheduler_instance):
    runner = CliRunner()

    result = runner.invoke(
        schedule_logs_command,
        ['-w', file_relative_path(__file__, 'workspace.yaml'), 'foo_schedule'],
    )

    assert result.exit_code == 0
    assert result.output.endswith('scheduler.log\n')


@pytest.mark.skipif(
    os.name == 'nt', reason="multiproc directory test disabled for windows because of fs contention"
)
def test_multiproc():
    with seven.TemporaryDirectory() as temp:
        runner = CliRunner(env={'DAGSTER_HOME': temp})
        add_result = runner_pipeline_execute(
            runner,
            [
                '-w',
                file_relative_path(__file__, '../repository.yaml'),
                '--preset',
                'multiproc',
                '-p',
                'multi_mode_with_resources',  # pipeline name
            ],
        )
        assert 'PIPELINE_SUCCESS' in add_result.output


def test_multiproc_invalid():
    # force ephemeral instance by removing out DAGSTER_HOME
    runner = CliRunner(env={'DAGSTER_HOME': None})
    add_result = runner_pipeline_execute(
        runner,
        [
            '-w',
            file_relative_path(__file__, '../repository.yaml'),
            '--preset',
            'multiproc',
            '-p',
            'multi_mode_with_resources',  # pipeline name
        ],
    )
    # which is invalid for multiproc
    assert 'DagsterUnmetExecutorRequirementsError' in add_result.output


class InMemoryRunLauncher(RunLauncher, ConfigurableClass):
    def __init__(self, inst_data=None):
        self._inst_data = inst_data
        self._queue = []

    def launch_run(self, instance, run, external_pipeline):
        self._queue.append(run)
        return run

    def queue(self):
        return self._queue

    @classmethod
    def config_type(cls):
        return Shape({})

    @classmethod
    def from_config_value(cls, inst_data, config_value):
        return cls(inst_data=inst_data,)

    @property
    def inst_data(self):
        return self._inst_data

    def can_terminate(self, run_id):
        return False

    def terminate(self, run_id):
        check.not_implemented('Termintation not supported')


def backfill_cli_runner_args(execution_args):
    return [
        '-w',
        file_relative_path(__file__, 'repository_file.yaml'),
        '--noprompt',
    ] + execution_args


def run_test_backfill(execution_args, expected_count=None, error_message=None):
    runner = CliRunner()
    run_launcher = InMemoryRunLauncher()
    with seven.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance(
            instance_type=InstanceType.EPHEMERAL,
            local_artifact_storage=LocalArtifactStorage(temp_dir),
            run_storage=InMemoryRunStorage(),
            event_storage=InMemoryEventLogStorage(),
            compute_log_manager=NoOpComputeLogManager(),
            run_launcher=run_launcher,
        )
        with mock.patch('dagster.core.instance.DagsterInstance.get') as _instance:
            _instance.return_value = instance

            result = runner.invoke(
                pipeline_backfill_command, backfill_cli_runner_args(execution_args)
            )
            if error_message:
                assert result.exit_code == 2, result.stdout
            else:
                assert result.exit_code == 0, result.stdout
                if expected_count:
                    assert len(run_launcher.queue()) == expected_count


def test_backfill_no_pipeline():
    args = ['--pipeline', 'nonexistent']
    run_test_backfill(args, error_message='No pipeline found')


def test_backfill_no_partition_sets():
    args = ['--pipeline', 'foo']
    run_test_backfill(args, error_message='No partition sets found')


def test_backfill_no_named_partition_set():
    args = ['--pipeline', 'baz', '--partition-set', 'nonexistent']
    run_test_backfill(args, error_message='No partition set found')


def test_backfill_launch():
    args = ['--pipeline', 'baz', '--partition-set', 'baz_partitions']
    run_test_backfill(args, expected_count=len(string.ascii_lowercase))


def test_backfill_partition_range():
    args = ['--pipeline', 'baz', '--partition-set', 'baz_partitions', '--from', 'x']
    run_test_backfill(args, expected_count=3)

    args = ['--pipeline', 'baz', '--partition-set', 'baz_partitions', '--to', 'c']
    run_test_backfill(args, expected_count=3)

    args = ['--pipeline', 'baz', '--partition-set', 'baz_partitions', '--from', 'c', '--to', 'f']
    run_test_backfill(args, expected_count=4)


def test_backfill_partition_enum():
    args = ['--pipeline', 'baz', '--partition-set', 'baz_partitions', '--partitions', 'c,x,z']
    run_test_backfill(args, expected_count=3)


def run_launch(execution_args, expected_count=None):
    runner = CliRunner()
    run_launcher = InMemoryRunLauncher()
    with seven.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance(
            instance_type=InstanceType.EPHEMERAL,
            local_artifact_storage=LocalArtifactStorage(temp_dir),
            run_storage=InMemoryRunStorage(),
            event_storage=InMemoryEventLogStorage(),
            compute_log_manager=NoOpComputeLogManager(),
            run_launcher=run_launcher,
        )
        with mock.patch('dagster.core.instance.DagsterInstance.get') as _instance:
            _instance.return_value = instance

            result = runner.invoke(pipeline_launch_command, execution_args)
            assert result.exit_code == 0, result.stdout
            if expected_count:
                assert len(run_launcher.queue()) == expected_count


def test_launch_pipeline():
    for cli_args in valid_cli_args():
        run_launch(cli_args, expected_count=1)


@contextmanager
def mocked_instance():
    with seven.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance(
            instance_type=InstanceType.EPHEMERAL,
            local_artifact_storage=LocalArtifactStorage(temp_dir),
            run_storage=InMemoryRunStorage(),
            event_storage=InMemoryEventLogStorage(),
            compute_log_manager=NoOpComputeLogManager(),
            run_launcher=InMemoryRunLauncher(),
        )
        with mock.patch('dagster.core.instance.DagsterInstance.get') as _instance:
            _instance.return_value = instance
            yield instance


def test_tags_pipeline():
    runner = CliRunner()
    with mocked_instance() as instance:
        result = runner.invoke(
            pipeline_execute_command,
            [
                '-w',
                file_relative_path(__file__, 'repository_module.yaml'),
                '--tags',
                '{ "foo": "bar" }',
                '-p',
                'hello_cereal_pipeline',
            ],
        )
        assert result.exit_code == 0
        runs = instance.get_runs()
        assert len(runs) == 1
        run = runs[0]
        assert len(run.tags) == 1
        assert run.tags.get('foo') == 'bar'

    with mocked_instance() as instance:
        result = runner.invoke(
            pipeline_execute_command,
            [
                '-w',
                file_relative_path(__file__, '../repository.yaml'),
                '--preset',
                'add',
                '--tags',
                '{ "foo": "bar" }',
                '-p',
                'multi_mode_with_resources',  # pipeline name
            ],
        )
        assert result.exit_code == 0
        runs = instance.get_runs()
        assert len(runs) == 1
        run = runs[0]
        assert len(run.tags) == 1
        assert run.tags.get('foo') == 'bar'

    with mocked_instance() as instance:
        result = runner.invoke(
            pipeline_backfill_command,
            [
                '-w',
                file_relative_path(__file__, 'repository_file.yaml'),
                '--noprompt',
                '--partition-set',
                'baz_partitions',
                '--partitions',
                'c',
                '--tags',
                '{ "foo": "bar" }',
                '-p',
                'baz',
            ],
        )
        assert result.exit_code == 0, result.stdout
        runs = instance.run_launcher.queue()
        assert len(runs) == 1
        run = runs[0]
        assert len(run.tags) >= 1
        assert run.tags.get('foo') == 'bar'


def test_execute_subset_pipeline():
    runner = CliRunner()
    # single clause, solid name
    with mocked_instance() as instance:
        result = runner.invoke(
            pipeline_execute_command,
            [
                '-f',
                file_relative_path(__file__, 'test_cli_commands.py'),
                '-a',
                'foo_pipeline',
                '--solid-selection',
                'do_something',
            ],
        )
        assert result.exit_code == 0
        runs = instance.get_runs()
        assert len(runs) == 1
        run = runs[0]
        assert run.solid_selection == ['do_something']
        assert run.solids_to_execute == {'do_something'}

    # single clause, DSL query
    with mocked_instance() as instance:
        result = runner.invoke(
            pipeline_execute_command,
            [
                '-f',
                file_relative_path(__file__, 'test_cli_commands.py'),
                '-a',
                'foo_pipeline',
                '--solid-selection',
                '*do_something+',
            ],
        )
        assert result.exit_code == 0
        runs = instance.get_runs()
        assert len(runs) == 1
        run = runs[0]
        assert run.solid_selection == ['*do_something+']
        assert run.solids_to_execute == {'do_something', 'do_input'}

    # multiple clauses, DSL query and solid name
    with mocked_instance() as instance:
        result = runner.invoke(
            pipeline_execute_command,
            [
                '-f',
                file_relative_path(__file__, 'test_cli_commands.py'),
                '-a',
                'foo_pipeline',
                '--solid-selection',
                '*do_something+,do_input',
            ],
        )
        assert result.exit_code == 0
        runs = instance.get_runs()
        assert len(runs) == 1
        run = runs[0]
        assert set(run.solid_selection) == set(['*do_something+', 'do_input'])
        assert run.solids_to_execute == {'do_something', 'do_input'}

    # invalid value
    with mocked_instance() as instance:
        result = runner.invoke(
            pipeline_execute_command,
            [
                '-f',
                file_relative_path(__file__, 'test_cli_commands.py'),
                '-a',
                'foo_pipeline',
                '--solid-selection',
                'a, b',
            ],
        )
        assert result.exit_code == 1
        assert re.match(
            'No qualified solids to execute found for solid_selection', str(result.exception)
        )


def test_launch_subset_pipeline():
    runner = CliRunner()
    # single clause, solid name
    with mocked_instance() as instance:
        result = runner.invoke(
            pipeline_launch_command,
            [
                '-f',
                file_relative_path(__file__, 'test_cli_commands.py'),
                '-a',
                'foo_pipeline',
                '--solid-selection',
                'do_something',
            ],
        )
        assert result.exit_code == 0
        runs = instance.get_runs()
        assert len(runs) == 1
        run = runs[0]
        assert run.solid_selection == ['do_something']
        assert run.solids_to_execute == {'do_something'}

    # single clause, DSL query
    with mocked_instance() as instance:
        result = runner.invoke(
            pipeline_launch_command,
            [
                '-f',
                file_relative_path(__file__, 'test_cli_commands.py'),
                '-a',
                'foo_pipeline',
                '--solid-selection',
                '*do_something+',
            ],
        )
        assert result.exit_code == 0
        runs = instance.get_runs()
        assert len(runs) == 1
        run = runs[0]
        assert run.solid_selection == ['*do_something+']
        assert run.solids_to_execute == {'do_something', 'do_input'}

    # multiple clauses, DSL query and solid name
    with mocked_instance() as instance:
        result = runner.invoke(
            pipeline_launch_command,
            [
                '-f',
                file_relative_path(__file__, 'test_cli_commands.py'),
                '-a',
                'foo_pipeline',
                '--solid-selection',
                '*do_something+,do_input',
            ],
        )
        assert result.exit_code == 0
        runs = instance.get_runs()
        assert len(runs) == 1
        run = runs[0]
        assert set(run.solid_selection) == set(['*do_something+', 'do_input'])
        assert run.solids_to_execute == {'do_something', 'do_input'}

    # invalid value
    with mocked_instance() as instance:
        result = runner.invoke(
            pipeline_launch_command,
            [
                '-f',
                file_relative_path(__file__, 'test_cli_commands.py'),
                '-a',
                'foo_pipeline',
                '--solid-selection',
                'a, b',
            ],
        )
        assert result.exit_code == 1
        assert re.match(
            'No qualified solids to execute found for solid_selection', str(result.exception)
        )
