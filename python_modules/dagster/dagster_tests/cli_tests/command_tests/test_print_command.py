from __future__ import print_function

import re

import pytest
from click.testing import CliRunner

from dagster.cli.pipeline import execute_print_command, pipeline_print_command
from dagster.utils import file_relative_path

from .test_cli_commands import launch_command_contexts, valid_pipeline_target_cli_args


def no_print(_):
    return None


@pytest.mark.parametrize('gen_pipeline_args', launch_command_contexts())
def test_print_command_verbose(gen_pipeline_args):
    with gen_pipeline_args as (cli_args, uses_legacy_repository_yaml_format, instance):
        if uses_legacy_repository_yaml_format:
            with pytest.warns(
                UserWarning,
                match=re.escape(
                    'You are using the legacy repository yaml format. Please update your file '
                ),
            ):
                execute_print_command(
                    verbose=True, cli_args=cli_args, print_fn=no_print, instance=instance
                )
        else:
            execute_print_command(
                verbose=True, cli_args=cli_args, print_fn=no_print, instance=instance
            )


@pytest.mark.parametrize('gen_pipeline_args', launch_command_contexts())
def test_print_command(gen_pipeline_args):
    with gen_pipeline_args as (cli_args, uses_legacy_repository_yaml_format, instance):
        if uses_legacy_repository_yaml_format:
            with pytest.warns(
                UserWarning,
                match=re.escape(
                    'You are using the legacy repository yaml format. Please update your file '
                ),
            ):
                execute_print_command(
                    verbose=False, cli_args=cli_args, print_fn=no_print, instance=instance
                )
        else:
            execute_print_command(
                verbose=False, cli_args=cli_args, print_fn=no_print, instance=instance
            )


@pytest.mark.parametrize('pipeline_cli_args', valid_pipeline_target_cli_args())
def test_print_command_cli(pipeline_cli_args):
    runner = CliRunner()
    cli_args, uses_legacy_repository_yaml_format = pipeline_cli_args
    if uses_legacy_repository_yaml_format:
        with pytest.warns(
            UserWarning,
            match=re.escape(
                'You are using the legacy repository yaml format. Please update your file '
            ),
        ):
            result = runner.invoke(pipeline_print_command, cli_args)
            assert result.exit_code == 0, result.stdout

            result = runner.invoke(pipeline_print_command, ['--verbose'] + cli_args)
            assert result.exit_code == 0, result.stdout
    else:
        result = runner.invoke(pipeline_print_command, cli_args)
        assert result.exit_code == 0, result.stdout

        result = runner.invoke(pipeline_print_command, ['--verbose'] + cli_args)
        assert result.exit_code == 0, result.stdout


def test_print_command_baz():
    runner = CliRunner()
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
