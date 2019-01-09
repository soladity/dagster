from __future__ import print_function
import logging
import re
import textwrap
import yaml

import click

from dagster import PipelineDefinition, check

from dagster.core.definitions import Solid
from dagster.core.execution import execute_pipeline_iterator
from dagster.core.execution_plan.create import solids_in_topological_order
from dagster.graphviz import build_graphviz_graph
from dagster.utils import load_yaml_from_glob_list
from dagster.utils.indenting_printer import IndentingPrinter

from .config_scaffolder import scaffold_pipeline_config

from .dynamic_loader import (
    PipelineTargetInfo,
    load_pipeline_from_target_info,
    load_repository_from_target_info,
    pipeline_target_command,
    repository_target_argument,
    load_target_info_from_cli_args,
)


def create_pipeline_cli():
    group = click.Group(name="pipeline")
    group.add_command(list_command)
    group.add_command(print_command)
    group.add_command(graphviz_command)
    group.add_command(execute_command)
    group.add_command(scaffold_command)
    return group


REPO_TARGET_WARNING = (
    'Can only use ONE of --repository-yaml/-y, --python-file/-f, --module-name/-m.'
)


@click.command(
    name='list',
    help="List the pipelines in a repository. {warning}".format(warning=REPO_TARGET_WARNING),
)
@repository_target_argument
def list_command(**kwargs):
    return execute_list_command(kwargs, click.echo)


def execute_list_command(cli_args, print_fn):
    repository_target_info = load_target_info_from_cli_args(cli_args)
    repository = load_repository_from_target_info(repository_target_info)

    title = 'Repository {name}'.format(name=repository.name)
    print_fn(title)
    print_fn('*' * len(title))
    first = True
    for pipeline in repository.get_all_pipelines():
        pipeline_title = 'Pipeline: {name}'.format(name=pipeline.name)

        if not first:
            print_fn('*' * len(pipeline_title))
        first = False

        print_fn(pipeline_title)
        if pipeline.description:
            print_fn('Description:')
            print_fn(format_description(pipeline.description, indent=' ' * 4))
        print_fn('Solids: (Execution Order)')
        for solid in solids_in_topological_order(pipeline):
            print_fn('    ' + solid.name)


def format_description(desc, indent):
    check.str_param(desc, 'desc')
    check.str_param(indent, 'indent')
    desc = re.sub(r'\s+', ' ', desc)
    dedented = textwrap.dedent(desc)
    wrapper = textwrap.TextWrapper(initial_indent='', subsequent_indent=indent)
    filled = wrapper.fill(dedented)
    return filled


def create_pipeline_from_cli_args(kwargs):
    check.dict_param(kwargs, 'kwargs')

    pipeline_names = list(kwargs['pipeline_name'])

    if not pipeline_names:
        pipeline_name = None
    elif len(pipeline_names) == 1:
        pipeline_name = pipeline_names[0]
    else:
        check.failed(
            'Can only handle zero or one pipeline args. Got {pipeline_names}'.format(
                pipeline_names=repr(pipeline_names)
            )
        )

    if (
        kwargs['pipeline_name']
        and kwargs['repository_yaml'] is None
        and kwargs['module_name'] is None
        and kwargs['python_file'] is None
    ):
        repository_yaml = 'repository.yml'
    else:
        repository_yaml = kwargs['repository_yaml']

    return load_pipeline_from_target_info(
        PipelineTargetInfo(
            repository_yaml=repository_yaml,
            pipeline_name=pipeline_name,
            python_file=kwargs['python_file'],
            module_name=kwargs['module_name'],
            fn_name=kwargs['fn_name'],
        )
    )


def get_pipeline_instructions(command_name):
    return (
        'This commands targets a pipeline. The pipeline can be specified in a number of ways:'
        '\n\n1. dagster {command_name} <<pipeline_name>> (works if .repository.yml exists)'
        '\n\n2. dagster {command_name} <<pipeline_name>> -y path/to/repository.yml'
        '\n\n3. dagster {command_name} -f /path/to/file.py -n define_some_pipeline'
        '\n\n4. dagster {command_name} -m a_module.submodule  -n define_some_pipeline'
        '\n\n5. dagster {command_name} -f /path/to/file.py -n define_some_repo -p pipeline_name'
        '\n\n6. dagster {command_name} -m a_module.submodule -n define_some_repo -p pipeline_name'
    ).format(command_name=command_name)


@click.command(
    name='print',
    help='Print a pipeline.\n\n{instructions}'.format(
        instructions=get_pipeline_instructions('print')
    ),
)
@click.option('--verbose', is_flag=True)
@pipeline_target_command
def print_command(verbose, **cli_args):
    return execute_print_command(verbose, cli_args, click.echo)


def execute_print_command(verbose, cli_args, print_fn):
    pipeline = create_pipeline_from_cli_args(cli_args)

    if verbose:
        print_pipeline(pipeline, full=True, print_fn=print_fn)
    else:
        print_solids(pipeline, print_fn=print_fn)


def print_solids(pipeline, print_fn):
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    check.callable_param(print_fn, 'print_fn')

    printer = IndentingPrinter(indent_level=2, printer=print_fn)
    printer.line('Pipeline: {name}'.format(name=pipeline.name))

    printer.line('Solids:')
    for solid in pipeline.solids:
        with printer.with_indent():
            printer.line('Solid: {name}'.format(name=solid.name))


def print_pipeline(pipeline, full, print_fn):
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    check.bool_param(full, 'full')
    check.callable_param(print_fn, 'print_fn')

    printer = IndentingPrinter(indent_level=2, printer=print_fn)
    printer.line('Pipeline: {name}'.format(name=pipeline.name))
    print_description(printer, pipeline.description)

    if not full:
        return

    with printer.with_indent():
        printer.line('Context Definitions:')

        with printer.with_indent():

            for context_name, context_definition in pipeline.context_definitions.items():
                print_context_definition(printer, context_name, context_definition)

    printer.line('Solids:')
    for solid in pipeline.solids:
        with printer.with_indent():
            print_solid(printer, solid)


def print_description(printer, desc):
    with printer.with_indent():
        if desc:
            printer.line('Description:')
            with printer.with_indent():
                printer.line(format_description(desc, printer.current_indent_str))


def print_context_definition(printer, context_name, context_definition):
    printer.line('Name: {context_name}'.format(context_name=context_name))

    print_description(printer, context_definition.description)

    printer.line(
        'Type: {runtime_type}'.format(runtime_type=context_definition.config_field.config_type.name)
    )


def print_solid(printer, solid):
    check.inst_param(solid, 'solid', Solid)
    printer.line('Solid: {name}'.format(name=solid.name))

    with printer.with_indent():
        print_inputs(printer, solid)

        printer.line('Outputs:')

        for output_def in solid.definition.output_defs:
            printer.line(output_def.name)


def print_inputs(printer, solid):
    printer.line('Inputs:')
    for input_def in solid.definition.input_defs:
        with printer.with_indent():
            printer.line('Input: {name}'.format(name=input_def.name))


def format_argument_dict(arg_def_dict):
    return ', '.join(
        [
            '{name}: {type}'.format(name=name, type=arg_def.runtime_type.name)
            for name, arg_def in arg_def_dict.items()
        ]
    )


@click.command(
    name='graphviz',
    help=(
        'Visualize a pipeline using graphviz. Must be installed on your system '
        '(e.g. homebrew install graphviz on mac). \n\n{instructions}'.format(
            instructions=get_pipeline_instructions('graphviz')
        )
    ),
)
@click.option('--only-solids', is_flag=True)
@pipeline_target_command
def graphviz_command(only_solids, **kwargs):
    pipeline = create_pipeline_from_cli_args(kwargs)
    build_graphviz_graph(pipeline, only_solids).view(cleanup=True)


LOGGING_DICT = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARN': logging.WARN,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL,
}


@click.command(
    name='execute',
    help='Execute a pipeline.\n\n{instructions}'.format(
        instructions=get_pipeline_instructions('execute')
    ),
)
@pipeline_target_command
@click.option(
    '-e',
    '--env',
    type=click.STRING,
    multiple=True,
    help=(
        'Specify one or more environment files. These can also be file patterns. '
        'If more than one environment file is captured then those files are merged. '
        'Files listed first take precendence. They will smash the values of subsequent '
        'files at the key-level granularity. If the file is a pattern then you must '
        'enclose it in double quotes'
        '\n\nExample: '
        'dagster pipeline execute pandas_hello_world -e "pandas_hello_world/*.yml"'
        '\n\nYou can also specifiy multiple files:'
        '\n\nExample: '
        'dagster pipeline execute pandas_hello_world -e pandas_hello_world/solids.yml '
        '-e pandas_hello_world/env.yml'
    ),
)
def execute_command(env, **kwargs):
    check.invariant(isinstance(env, tuple))
    env = list(env)
    execute_execute_command(env, kwargs, click.echo)


def execute_execute_command(env, cli_args, print_fn):
    pipeline = create_pipeline_from_cli_args(cli_args)
    do_execute_command(pipeline, env, print_fn)


def do_execute_command(pipeline, env_file_list, printer):
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    env_file_list = check.opt_list_param(env_file_list, 'env_file_list', of_type=str)
    check.callable_param(printer, 'printer')

    env_config = load_yaml_from_glob_list(env_file_list) if env_file_list else {}

    pipeline_iter = execute_pipeline_iterator(pipeline, env_config)

    process_results_for_console(pipeline_iter)


@click.command(
    name='scaffold_config',
    help='Scaffold the config for a pipeline.\n\n{instructions}'.format(
        instructions=get_pipeline_instructions('scaffold_config')
    ),
)
@pipeline_target_command
@click.option('-p', '--print-only-required', default=False, is_flag=True)
def scaffold_command(**kwargs):
    execute_scaffold_command(kwargs, click.echo)


def execute_scaffold_command(cli_args, print_fn):
    pipeline = create_pipeline_from_cli_args(cli_args)
    skip_optional = cli_args['print_only_required']
    do_scaffold_command(pipeline, print_fn, skip_optional)


def do_scaffold_command(pipeline, printer, skip_optional):
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    check.callable_param(printer, 'printer')
    check.bool_param(skip_optional, 'skip_optional')

    config_dict = scaffold_pipeline_config(pipeline, skip_optional=skip_optional)
    yaml_string = yaml.dump(config_dict, default_flow_style=False)
    printer(yaml_string)


def process_results_for_console(pipeline_iter):
    results = []

    for result in pipeline_iter:
        if not result.success:
            result.reraise_user_error()
        results.append(result)

    return results
