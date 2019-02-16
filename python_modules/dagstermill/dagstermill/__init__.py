from __future__ import absolute_import, division, print_function, unicode_literals
from builtins import *  # pylint: disable=W0622,W0401
from collections import namedtuple

import base64
import copy
import json
import os
import subprocess
import uuid

import nbformat

import six

from future.utils import raise_from

import papermill as pm
from papermill.translators import translate_parameters
from papermill.iorw import load_notebook_node, write_ipynb
from dagster import (
    DagsterRuntimeCoercionError,
    InputDefinition,
    OutputDefinition,
    RepositoryDefinition,
    Result,
    PipelineDefinition,
    SolidDefinition,
    check,
    types,
)

from dagster.core.types.marshal import serialize_to_file, deserialize_from_file
from dagster.core.types.runtime import RuntimeType

from dagster.core.definitions.dependency import Solid
from dagster.core.events import construct_json_event_logger, EventRecord, EventType
from dagster.core.definitions.environment_configs import construct_environment_config
from dagster.core.execution import yield_pipeline_execution_context
from dagster.core.execution_context import (
    DagsterLog,
    ExecutionMetadata,
    PipelineExecutionContext,
    TransformExecutionContext,
    AbstractTransformExecutionContext,
)

# magic incantation for syncing up notebooks to enclosing virtual environment.
# I don't claim to understand it.
# ipython kernel install --name "dagster" --user
# python3 -m ipykernel install --user


class DagstermillInNotebookExecutionContext(AbstractTransformExecutionContext):
    def __init__(self, pipeline_context):
        self._pipeline_context = pipeline_context

    def has_tag(self, key):
        return self._pipeline_context.has_tag(key)

    def get_tag(self, key):
        return self._pipeline_context.get_tag(key)

    @property
    def run_id(self):
        return self._pipeline_context.run_id

    @property
    def event_callback(self):
        return self._pipeline_context.event_callback

    def has_event_callback(self):
        return self._pipeline_context.has_event_callback

    @property
    def environment_config(self):
        return self._pipeline_context.environment_config

    @property
    def pipeline_def(self):
        return self._pipeline_context.pipeline_def

    @property
    def resources(self):
        return self._pipeline_context.resources

    @property
    def log(self):
        return self._pipeline_context.log

    @property
    def context(self):
        return self._pipeline_context.context

    @property
    def config(self):
        check.not_implemented('Cannot access solid config in dagstermill exploratory context')

    @property
    def step(self):
        check.not_implemented('Cannot access step in dagstermill exploratory context')

    @property
    def solid_def(self):
        check.not_implemented('Cannot access solid_def in dagstermill exploratory context')

    @property
    def solid(self):
        check.not_implemented('Cannot access solid in dagstermill exploratory context')


class DagstermillError(Exception):
    pass


class Manager:
    def __init__(self):
        self.repository_def = None
        self.populated_by_papermill = False
        self.pipeline_def = None
        self.solid_def = None
        self.marshal_dir = None
        self.context = None

    def register_repository(self, repository_def):
        self.repository_def = repository_def

    def define_out_of_pipeline_context(self, context_config):
        pipeline_def = PipelineDefinition([], name='Ephemeral Notebook Pipeline')

        # BUG: If the context cleans up after itself (e.g. closes a db connection or similar)
        # This will instigate that process *before* return. We are going to have to
        # manage this manually (without an if block) in order to make this work.
        # See https://github.com/dagster-io/dagster/issues/796
        with yield_pipeline_execution_context(
            pipeline_def,
            {} if context_config is None else {'context': context_config},
            ExecutionMetadata(run_id=''),
        ) as pipeline_context:
            self.context = DagstermillInNotebookExecutionContext(pipeline_context)
        return self.context

    def yield_result(self, value, output_name):
        if not self.populated_by_papermill:
            return value

        check.invariant(
            self.solid_def is not None,
            "If Dagstermill has been run by papermill, self.solid_def should not be None",
        )
        if not self.solid_def.has_output(output_name):
            raise DagstermillError(
                'Solid {solid_name} does not have output named {output_name}'.format(
                    solid_name=self.solid_def.name, output_name=output_name
                )
            )

        runtime_type = self.solid_def.output_def_named(output_name).runtime_type

        out_file = os.path.join(self.marshal_dir, 'output-{}'.format(output_name))
        pm.record(output_name, write_value(runtime_type, value, out_file))

    def populate_context(
        self,
        run_id,
        solid_def_name,
        pipeline_def_name,
        marshal_dir,
        environment_dict,
        output_log_path,
    ):
        check.dict_param(environment_dict, 'environment_dict')
        self.populated_by_papermill = True
        check.invariant(
            self.repository_def != None,
            desc='When running Dagstermill notebook in pipeline, '
            'must register a repository within notebook by calling '
            '"dm.register_repository(repository_def)"',
        )
        self.pipeline_def = self.repository_def.get_pipeline(pipeline_def_name)
        check.invariant(self.pipeline_def.has_solid_def(solid_def_name))
        self.solid_def = self.pipeline_def.solid_def_named(solid_def_name)

        self.marshal_dir = marshal_dir
        loggers = None
        if output_log_path != 0:
            event_logger = construct_json_event_logger(output_log_path)
            loggers = [event_logger]
        # do not include event_callback in ExecutionMetadata,
        # since that'll be taken care of by side-channel established by event_logger
        execution_metadata = ExecutionMetadata(run_id, loggers=loggers)
        # See block comment above referencing this issue
        # See https://github.com/dagster-io/dagster/issues/796
        with yield_pipeline_execution_context(
            self.pipeline_def, environment_dict, execution_metadata
        ) as pipeline_context:
            self.context = DagstermillInNotebookExecutionContext(pipeline_context)

        return self.context


class DagsterTranslator(pm.translators.PythonTranslator):
    @classmethod
    def codify(cls, parameters):
        assert 'dm_context' in parameters
        content = '{}\n'.format(cls.comment('Parameters'))
        content += '{}\n'.format('import json')
        content += '{}\n'.format(
            cls.assign(
                'context',
                'dm.populate_context(json.loads(\'{dm_context}\'))'.format(
                    dm_context=parameters['dm_context']
                ),
            )
        )

        for name, val in parameters.items():
            if name == 'dm_context':
                continue
            dm_unmarshal_call = 'dm.load_parameter("{name}", {val})'.format(
                name=name, val='"{val}"'.format(val=val) if isinstance(val, str) else val
            )
            content += '{}\n'.format(cls.assign(name, dm_unmarshal_call))

        return content


MANAGER_FOR_NOTEBOOK_INSTANCE = Manager()
pm.translators.papermill_translators.register('python', DagsterTranslator)


def is_json_serializable(value):
    try:
        json.dumps(value)
        return True
    except TypeError:
        return False


def write_value(runtime_type, value, target_file):
    check.inst_param(runtime_type, 'runtime_type', RuntimeType)
    if runtime_type.is_scalar:
        return value
    elif runtime_type.is_any and is_json_serializable(value):
        return value
    elif runtime_type.serialization_strategy:
        serialize_to_file(runtime_type.serialization_strategy, value, target_file)
        return target_file
    else:
        check.failed('Unsupported type {name}'.format(name=runtime_type.name))


def register_repository(repo_def):
    return MANAGER_FOR_NOTEBOOK_INSTANCE.register_repository(repo_def)


def yield_result(value, output_name='result'):
    return MANAGER_FOR_NOTEBOOK_INSTANCE.yield_result(value, output_name)


def populate_context(dm_context_data):
    check.dict_param(dm_context_data, 'dm_context_data')
    return MANAGER_FOR_NOTEBOOK_INSTANCE.populate_context(
        dm_context_data['run_id'],
        dm_context_data['solid_def_name'],
        dm_context_data['pipeline_name'],
        dm_context_data['marshal_dir'],
        dm_context_data['environment_config'],
        dm_context_data['output_log_path'],
    )


def load_parameter(input_name, input_value):
    check.invariant(MANAGER_FOR_NOTEBOOK_INSTANCE.populated_by_papermill, 'populated_by_papermill')
    solid_def = MANAGER_FOR_NOTEBOOK_INSTANCE.solid_def
    input_def = solid_def.input_def_named(input_name)
    return read_value(input_def.runtime_type, input_value)


def read_value(runtime_type, value):
    check.inst_param(runtime_type, 'runtime_type', RuntimeType)
    if runtime_type.is_scalar:
        return value
    elif runtime_type.is_any and is_json_serializable(value):
        return value
    elif runtime_type.serialization_strategy:
        return deserialize_from_file(runtime_type.serialization_strategy, value)
    else:
        check.failed(
            'Unsupported type {name}: no persistence strategy defined'.format(
                name=runtime_type.name
            )
        )


def get_papermill_parameters(transform_context, inputs, output_log_path):
    check.inst_param(transform_context, 'transform_context', AbstractTransformExecutionContext)
    check.param_invariant(
        isinstance(transform_context.environment_dict, dict),
        'transform_context',
        'TransformExecutionContext must have valid environment_dict',
    )
    check.dict_param(inputs, 'inputs', key_type=six.string_types)

    run_id = transform_context.run_id

    marshal_dir = '/tmp/dagstermill/{run_id}/marshal'.format(run_id=run_id)
    if not os.path.exists(marshal_dir):
        os.makedirs(marshal_dir)

    if not transform_context.has_event_callback:
        transform_context.log.info('get_papermill_parameters.context has no event_callback!')
        output_log_path = 0  # stands for null

    dm_context_dict = {
        'run_id': run_id,
        'pipeline_name': transform_context.pipeline_def.name,
        'solid_def_name': transform_context.solid_def.name,
        'marshal_dir': marshal_dir,
        # TODO rename to environment_dict
        'environment_config': transform_context.environment_dict,
        'output_log_path': output_log_path,
    }

    parameters = dict(dm_context=json.dumps(dm_context_dict, sort_keys=True))

    input_defs = transform_context.solid_def.input_defs
    input_def_dict = {inp.name: inp for inp in input_defs}
    for input_name, input_value in inputs.items():
        assert (
            input_name != 'dm_context'
        ), 'Dagstermill solids cannot have inputs named "dm_context"'
        runtime_type = input_def_dict[input_name].runtime_type
        parameter_value = write_value(
            runtime_type, input_value, os.path.join(marshal_dir, 'input-{}'.format(input_name))
        )
        parameters[input_name] = parameter_value

    return parameters


def replace_parameters(context, nb, parameters):
    # Uma: This is a copy-paste from papermill papermill/execute.py:104 (execute_parameters).
    # Typically, papermill injects the injected-parameters cell *below* the parameters cell
    # but we want to *replace* the parameters cell, which is what this function does.

    '''Assigned parameters into the appropiate place in the input notebook
    Args:
        nb (NotebookNode): Executable notebook object
        parameters (dict): Arbitrary keyword arguments to pass to the notebook parameters.
    '''

    # Copy the nb object to avoid polluting the input
    nb = copy.deepcopy(nb)

    # Generate parameter content based on the kernel_name
    param_content = DagsterTranslator.codify(parameters)
    # papermill method choosed translator based on kernel_name and language,
    # but we just call the DagsterTranslator
    # translate_parameters(kernel_name, language, parameters)

    newcell = nbformat.v4.new_code_cell(source=param_content)
    newcell.metadata['tags'] = ['injected-parameters']

    from papermill.execute import _find_first_tagged_cell_index

    param_cell_index = _find_first_tagged_cell_index(nb, 'parameters')
    injected_cell_index = _find_first_tagged_cell_index(nb, 'injected-parameters')
    if injected_cell_index >= 0:
        # Replace the injected cell with a new version
        before = nb.cells[:injected_cell_index]
        after = nb.cells[injected_cell_index + 1 :]
        check.int_value_param(param_cell_index, -1, 'param_cell_index')
        # We should have blown away the parameters cell if there is an injected-parameters cell
    elif param_cell_index >= 0:
        # Replace the parameter cell with the injected-parameters cell
        before = nb.cells[:param_cell_index]
        after = nb.cells[param_cell_index + 1 :]
    else:
        # Inject to the top of the notebook, presumably first cell includes dagstermill import
        context.log.debug(
            (
                'Warning notebook has no parameters cell, '
                'so first cell must import dagstermill and call dm.register_repo()'
            )
        )
        before = nb.cells[:1]
        after = nb.cells[1:]

    nb.cells = before + [newcell] + after
    nb.metadata.papermill['parameters'] = parameters

    return nb


def get_context(config=None):
    if not MANAGER_FOR_NOTEBOOK_INSTANCE.populated_by_papermill:
        MANAGER_FOR_NOTEBOOK_INSTANCE.define_out_of_pipeline_context(config)
    return MANAGER_FOR_NOTEBOOK_INSTANCE.context


def _dm_solid_transform(name, notebook_path):
    check.str_param(name, 'name')
    check.str_param(notebook_path, 'notebook_path')

    do_cleanup = False  # for now

    def _t_fn(transform_context, inputs):
        check.inst_param(transform_context, 'transform_context', TransformExecutionContext)
        check.param_invariant(
            isinstance(transform_context.environment_dict, dict),
            'context',
            'TransformExecutionContext must have valid environment_dict',
        )

        base_dir = '/tmp/dagstermill/{run_id}/'.format(run_id=transform_context.run_id)
        output_notebook_dir = os.path.join(base_dir, 'output_notebooks/')

        if not os.path.exists(output_notebook_dir):
            os.makedirs(output_notebook_dir)

        temp_path = os.path.join(
            output_notebook_dir, '{prefix}-out.ipynb'.format(prefix=str(uuid.uuid4()))
        )

        output_log_path = os.path.join(base_dir, 'run.log')

        try:
            nb = load_notebook_node(notebook_path)
            nb_no_parameters = replace_parameters(
                transform_context,
                nb,
                get_papermill_parameters(transform_context, inputs, output_log_path),
            )
            intermediate_path = os.path.join(
                output_notebook_dir, '{prefix}-inter.ipynb'.format(prefix=str(uuid.uuid4()))
            )
            write_ipynb(nb_no_parameters, intermediate_path)

            with open(output_log_path, 'a') as f:
                f.close()

            process = subprocess.Popen(['papermill', intermediate_path, temp_path])

            while process.poll() is None:  # while subprocess alive
                if transform_context.event_callback:
                    with open(output_log_path, 'r') as ff:
                        current_time = os.path.getmtime(output_log_path)
                        while process.poll() is None:
                            new_time = os.path.getmtime(output_log_path)
                            if new_time != current_time:
                                line = ff.readline()
                                if not line:
                                    break
                                event_record_dict = json.loads(line)

                                event_record_dict['event_type'] = EventType(
                                    event_record_dict['event_type']
                                )
                                transform_context.event_callback(EventRecord(**event_record_dict))
                                current_time = new_time

            if process.returncode != 0:
                raise DagstermillError(
                    'There was an error when Papermill tried to execute the notebook. '
                    'The process stderr is {stderr}'.format(stderr=process.stderr)
                )

            output_nb = pm.read_notebook(temp_path)

            transform_context.log.debug(
                'Notebook execution complete for {name}. Data is {data}'.format(
                    name=name, data=output_nb.data
                )
            )

            transform_context.events.step_materialization(
                transform_context.step.key,
                '{name} output notebook'.format(name=transform_context.solid.name),
                temp_path,
            )

            for output_def in transform_context.solid_def.output_defs:
                if output_def.name in output_nb.data:

                    value = read_value(output_def.runtime_type, output_nb.data[output_def.name])

                    yield Result(value, output_def.name)

        finally:
            if do_cleanup and os.path.exists(temp_path):
                os.remove(temp_path)

    return _t_fn


def define_dagstermill_solid(name, notebook_path, inputs=None, outputs=None, config_field=None):
    check.str_param(name, 'name')
    check.str_param(notebook_path, 'notebook_path')
    inputs = check.opt_list_param(inputs, 'input_defs', of_type=InputDefinition)
    outputs = check.opt_list_param(outputs, 'output_defs', of_type=OutputDefinition)

    return SolidDefinition(
        name=name,
        inputs=inputs,
        transform_fn=_dm_solid_transform(name, notebook_path),
        outputs=outputs,
        config_field=config_field,
        description='This solid is backed by the notebook at {path}'.format(path=notebook_path),
        metadata={'notebook_path': notebook_path, 'kind': 'ipynb'},
    )
