import itertools
import logging
import os
import shutil
import tempfile
import uuid

from collections import defaultdict
from contextlib import contextmanager

from dagster import (
    DagsterInvariantViolationError,
    DependencyDefinition,
    ModeDefinition,
    PipelineDefinition,
    SolidInvocation,
    check,
    execute_pipeline,
    SystemStorageData,
)
from dagster.core.definitions.logger import LoggerDefinition
from dagster.core.definitions.resource import ScopedResourcesBuilder
from dagster.core.execution.api import RunConfig, scoped_pipeline_context
from dagster.core.execution.context_creation_pipeline import (
    create_log_manager,
    construct_pipeline_execution_context,
    create_context_creation_data,
)
from dagster.core.utility_solids import define_stub_solid
from dagster.core.storage.intermediates_manager import InMemoryIntermediatesManager
from dagster.core.storage.file_manager import LocalFileHandle
from dagster.core.storage.runs import InMemoryRunStorage


def create_test_pipeline_execution_context(
    loggers=None, scoped_resources_builder=None, tags=None, run_config_loggers=None
):
    run_id = str(uuid.uuid4())
    loggers = check.opt_dict_param(loggers, 'loggers', key_type=str, value_type=LoggerDefinition)
    mode_def = ModeDefinition(loggers=loggers)
    pipeline_def = PipelineDefinition(
        name='test_legacy_context', solid_defs=[], mode_definitions=[mode_def]
    )
    run_config_loggers = check.opt_list_param(
        run_config_loggers, 'run_config_loggers', of_type=logging.Logger
    )
    run_config = RunConfig(run_id, tags=tags, loggers=run_config_loggers)
    environment_dict = {'loggers': {key: {} for key in loggers}}
    creation_data = create_context_creation_data(pipeline_def, environment_dict, run_config)
    log_manager = create_log_manager(creation_data)

    scoped_resources_builder = check.opt_inst_param(
        scoped_resources_builder,
        'scoped_resources_builder',
        ScopedResourcesBuilder,
        default=ScopedResourcesBuilder(),
    )
    return construct_pipeline_execution_context(
        context_creation_data=creation_data,
        scoped_resources_builder=scoped_resources_builder,
        system_storage_data=SystemStorageData(
            run_storage=InMemoryRunStorage(), intermediates_manager=InMemoryIntermediatesManager()
        ),
        log_manager=log_manager,
    )


def _unlink_swallow_errors(path):
    check.str_param(path, 'path')
    try:
        os.unlink(path)
    except Exception:  # pylint: disable=broad-except
        pass


@contextmanager
def get_temp_file_handle_with_data(data):
    with get_temp_file_name_with_data(data) as temp_file:
        yield LocalFileHandle(temp_file)


@contextmanager
def get_temp_file_name_with_data(data):
    with get_temp_file_name() as temp_file:
        with open(temp_file, 'wb') as ff:
            ff.write(data)

        yield temp_file


@contextmanager
def get_temp_file_handle():
    with get_temp_file_name() as temp_file:
        yield LocalFileHandle(temp_file)


@contextmanager
def get_temp_file_name():
    temp_file_name = tempfile.mkstemp()[1]
    try:
        yield temp_file_name
    finally:
        _unlink_swallow_errors(temp_file_name)


@contextmanager
def get_temp_file_names(number):
    check.int_param(number, 'number')

    temp_file_names = list()
    for _ in itertools.repeat(None, number):
        temp_file_name = tempfile.mkstemp()[1]
        temp_file_names.append(temp_file_name)

    try:
        yield tuple(temp_file_names)
    finally:
        for temp_file_name in temp_file_names:
            _unlink_swallow_errors(temp_file_name)


@contextmanager
def get_temp_dir():
    temp_dir = None
    try:
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
    finally:
        if temp_dir:
            shutil.rmtree(temp_dir)


def _dep_key_of(solid):
    return SolidInvocation(solid.definition.name, solid.name)


def build_pipeline_with_input_stubs(pipeline_def, inputs):
    check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)
    check.dict_param(inputs, 'inputs', key_type=str, value_type=dict)

    deps = defaultdict(dict)
    for solid_name, dep_dict in pipeline_def.dependencies.items():
        for input_name, dep in dep_dict.items():
            deps[solid_name][input_name] = dep

    stub_solid_defs = []

    for solid_name, input_dict in inputs.items():
        if not pipeline_def.has_solid_named(solid_name):
            raise DagsterInvariantViolationError(
                (
                    'You are injecting an input value for solid {solid_name} '
                    'into pipeline {pipeline_name} but that solid was not found'
                ).format(solid_name=solid_name, pipeline_name=pipeline_def.name)
            )

        solid = pipeline_def.solid_named(solid_name)
        for input_name, input_value in input_dict.items():
            stub_solid_def = define_stub_solid(
                '__stub_{solid_name}_{input_name}'.format(
                    solid_name=solid_name, input_name=input_name
                ),
                input_value,
            )
            stub_solid_defs.append(stub_solid_def)
            deps[_dep_key_of(solid)][input_name] = DependencyDefinition(stub_solid_def.name)

    return PipelineDefinition(
        name=pipeline_def.name + '_stubbed',
        solid_defs=pipeline_def.solid_defs + stub_solid_defs,
        mode_definitions=pipeline_def.mode_definitions,
        dependencies=deps,
    )


def execute_solids(pipeline_def, solid_names, inputs=None, environment_dict=None, run_config=None):
    check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)
    check.list_param(solid_names, 'solid_names', of_type=str)
    inputs = check.opt_dict_param(inputs, 'inputs', key_type=str, value_type=dict)
    environment_dict = check.opt_dict_param(environment_dict, 'environment_dict')
    run_config = check.opt_inst_param(run_config, 'run_config', RunConfig)

    sub_pipeline = pipeline_def.build_sub_pipeline(solid_names)
    stubbed_pipeline = build_pipeline_with_input_stubs(sub_pipeline, inputs)
    result = execute_pipeline(stubbed_pipeline, environment_dict, run_config)

    return {sr.solid.name: sr for sr in result.solid_result_list}


def execute_solid(pipeline_def, solid_name, inputs=None, environment_dict=None, run_config=None):
    check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)
    check.str_param(solid_name, 'solid_name')
    inputs = check.opt_dict_param(inputs, 'inputs', key_type=str)
    environment_dict = check.opt_dict_param(environment_dict, 'environment')
    run_config = check.opt_inst_param(run_config, 'run_config', RunConfig)

    return execute_solids(
        pipeline_def,
        [solid_name],
        {solid_name: inputs} if inputs else None,
        environment_dict,
        run_config,
    )[solid_name]


@contextmanager
def yield_empty_pipeline_context(run_id=None):
    with scoped_pipeline_context(PipelineDefinition([]), {}, RunConfig(run_id=run_id)) as context:
        yield context
