import os

from dagster import check
from dagster.config import Field, ScalarUnion, Selector
from dagster.config.source import IntSource, StringSource
from dagster.config.validate import process_config
from dagster.core.errors import DagsterInvalidConfigError
from dagster.utils import merge_dicts


def process_workspace_config(workspace_config):
    check.dict_param(workspace_config, "workspace_config")

    return process_config(WORKSPACE_CONFIG_SCHEMA, workspace_config)


def ensure_workspace_config(workspace_config, yaml_path):
    check.str_param(yaml_path, "yaml_path")
    check.dict_param(workspace_config, "workspace_config")

    validation_result = process_workspace_config(workspace_config)
    if not validation_result.success:
        raise DagsterInvalidConfigError(
            "Errors while loading workspace config from {yaml_path}.".format(
                yaml_path=os.path.abspath(yaml_path)
            ),
            validation_result.errors,
            workspace_config,
        )
    return validation_result.value


def _get_target_config():
    return {
        "python_file": ScalarUnion(
            scalar_type=str,
            non_scalar_schema={
                "relative_path": StringSource,
                "attribute": Field(StringSource, is_required=False),
                "location_name": Field(StringSource, is_required=False),
                "working_directory": Field(StringSource, is_required=False),
                "executable_path": Field(StringSource, is_required=False),
            },
        ),
        "python_module": ScalarUnion(
            scalar_type=str,
            non_scalar_schema={
                "module_name": StringSource,
                "attribute": Field(StringSource, is_required=False),
                "location_name": Field(StringSource, is_required=False),
                "executable_path": Field(StringSource, is_required=False),
            },
        ),
        "python_package": ScalarUnion(
            scalar_type=str,
            non_scalar_schema={
                "package_name": StringSource,
                "attribute": Field(StringSource, is_required=False),
                "location_name": Field(StringSource, is_required=False),
                "executable_path": Field(StringSource, is_required=False),
            },
        ),
    }


WORKSPACE_CONFIG_SCHEMA = {
    "load_from": Field(
        [
            Selector(
                merge_dicts(
                    _get_target_config(),
                    {
                        "grpc_server": {
                            "host": Field(StringSource, is_required=False),
                            "socket": Field(StringSource, is_required=False),
                            "port": Field(IntSource, is_required=False),
                            "location_name": Field(StringSource, is_required=False),
                            "ssl": Field(bool, is_required=False),
                        },
                    },
                )
            )
        ],
        is_required=False,
    ),
}
