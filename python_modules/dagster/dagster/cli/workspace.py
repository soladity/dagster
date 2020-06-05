import warnings

import six

from dagster import check
from dagster.config import Field, ScalarUnion, Selector, validate_config
from dagster.core.code_pointer import CodePointer, rebase_file
from dagster.core.definitions.reconstructable import def_from_pointer
from dagster.core.errors import DagsterInvalidConfigError, DagsterInvariantViolationError
from dagster.core.host_representation import RepositoryLocationHandle
from dagster.utils import load_yaml_from_path, merge_dicts

from .autodiscovery import (
    LoadableTarget,
    loadable_targets_from_python_file,
    loadable_targets_from_python_module,
)


class Workspace:
    def __init__(self, repository_location_handles):
        check.list_param(
            repository_location_handles,
            'repository_location_handles',
            of_type=RepositoryLocationHandle,
        )
        self._location_handle_dict = {rlh.location_name: rlh for rlh in repository_location_handles}

    @property
    def repository_location_handles(self):
        return list(self._location_handle_dict.values())

    def has_repository_location_handle(self, location_name):
        check.str_param(location_name, 'location_name')
        return location_name in self._location_handle_dict

    def get_repository_location_handle(self, location_name):
        check.str_param(location_name, 'location_name')
        return self._location_handle_dict[location_name]


def load_workspace_from_yaml_path(yaml_path):
    check.str_param(yaml_path, 'yaml_path')

    workspace_config = load_yaml_from_path(yaml_path)
    ensure_workspace_config(workspace_config, yaml_path)

    if 'repository' in workspace_config:
        warnings.warn(
            # link to docs once they exist
            'You are using the legacy repository yaml format. Please update your file '
            'to abide by the new workspace file format.'
        )
        return Workspace(
            [
                RepositoryLocationHandle.create_in_process_location(
                    pointer=CodePointer.from_legacy_repository_yaml(yaml_path)
                )
            ]
        )

    location_handles = []
    for location_config in workspace_config['load_from']:
        location_handles.append(_location_handle_from_location_config(location_config, yaml_path))

    return Workspace(location_handles)


def load_def_in_module(module_name, definition):
    return def_from_pointer(CodePointer.from_module(module_name, definition))


def load_def_in_python_file(python_file, definition):
    return def_from_pointer(CodePointer.from_python_file(python_file, definition))


def _location_handle_from_module_config(python_module_config):
    module_name, definition, location_name = (
        (python_module_config, None, None)
        if isinstance(python_module_config, six.string_types)
        else (
            python_module_config['module_name'],
            python_module_config.get('definition'),
            python_module_config.get('location_name'),
        )
    )

    loadable_targets = (
        [LoadableTarget(definition, load_def_in_module(module_name, definition))]
        if definition
        else loadable_targets_from_python_module(module_name)
    )

    repository_code_pointer_dict = {}
    for loadable_target in loadable_targets:
        repository_code_pointer_dict[
            loadable_target.target_definition.name
        ] = CodePointer.from_module(module_name, loadable_target.symbol_name)

    return RepositoryLocationHandle.create_out_of_process_location(
        repository_code_pointer_dict=repository_code_pointer_dict,
        # default to the name of the repository symbol for now
        location_name=assign_location_name(location_name, repository_code_pointer_dict),
    )


def assign_location_name(location_name, repository_code_pointer_dict):
    if location_name:
        return location_name

    if len(repository_code_pointer_dict) > 1:
        raise DagsterInvariantViolationError(
            'If there is one than more repository you must provide a location name'
        )

    return next(iter(repository_code_pointer_dict.keys()))


def _location_handle_from_python_file(python_file_config, yaml_path):
    check.str_param(yaml_path, 'yaml_path')

    relative_path, definition, location_name = (
        (python_file_config, None, None)
        if isinstance(python_file_config, six.string_types)
        else (
            python_file_config['relative_path'],
            python_file_config.get('definition'),
            python_file_config.get('location_name'),
        )
    )

    absolute_path = rebase_file(relative_path, yaml_path)
    loadable_targets = (
        [LoadableTarget(definition, load_def_in_python_file(absolute_path, definition))]
        if definition
        else loadable_targets_from_python_file(absolute_path)
    )

    repository_code_pointer_dict = {}
    for loadable_target in loadable_targets:
        repository_code_pointer_dict[
            loadable_target.target_definition.name
        ] = CodePointer.from_python_file(absolute_path, loadable_target.symbol_name)

    return RepositoryLocationHandle.create_out_of_process_location(
        repository_code_pointer_dict=repository_code_pointer_dict,
        # default to the name of the repository symbol for now
        location_name=assign_location_name(location_name, repository_code_pointer_dict),
    )


def _location_handle_from_location_config(location_config, yaml_path):
    check.dict_param(location_config, 'location_config')
    check.str_param(yaml_path, 'yaml_path')

    if 'python_file' in location_config:
        return _location_handle_from_python_file(location_config['python_file'], yaml_path)

    elif 'python_module' in location_config:
        return _location_handle_from_module_config(location_config['python_module'])

    elif 'python_environment' in location_config:
        check.not_implemented('not implemented')

    else:
        check.not_implemented('Unsupported location config: {}'.format(location_config))


def _get_python_target_configs():
    return {
        'python_file': ScalarUnion(
            scalar_type=str,
            non_scalar_schema={
                'relative_path': str,
                'definition': Field(str, is_required=False),
                'location_name': Field(str, is_required=False),
            },
        ),
        'python_module': ScalarUnion(
            scalar_type=str,
            non_scalar_schema={
                'module_name': str,
                'definition': Field(str, is_required=False),
                'location_name': Field(str, is_required=False),
            },
        ),
    }


WORKSPACE_CONFIG_SCHEMA = {
    'load_from': [
        Selector(
            merge_dicts(
                _get_python_target_configs(),
                {
                    'python_environment': {
                        'pythonpath': str,
                        'target': Selector(_get_python_target_configs()),
                    },
                },
            )
        )
    ],
}

WORKSPACE_CONFIG_SCHEMA_WITH_LEGACY = Selector(
    merge_dicts(
        {
            'repository': {
                'module': Field(str, is_required=False),
                'file': Field(str, is_required=False),
                'fn': Field(str),
            },
        },
        WORKSPACE_CONFIG_SCHEMA,
    )
)


def ensure_workspace_config(workspace_config, yaml_path):
    check.dict_param(workspace_config, 'workspace_config')
    check.str_param(yaml_path, 'yaml_path')

    validation_result = validate_workspace_config(workspace_config)
    if not validation_result.success:
        raise DagsterInvalidConfigError(
            'Errors while loading workspace config at {}.'.format(yaml_path),
            validation_result.errors,
            workspace_config,
        )


def validate_workspace_config(workspace_config):
    check.dict_param(workspace_config, 'workspace_config')

    return validate_config(WORKSPACE_CONFIG_SCHEMA_WITH_LEGACY, workspace_config)
