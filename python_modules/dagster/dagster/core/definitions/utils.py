import keyword
import os
import re
from glob import glob

import pkg_resources
import six
import yaml

from dagster import check, seven
from dagster.core.errors import DagsterInvalidDefinitionError, DagsterInvariantViolationError
from dagster.seven import FileNotFoundError, ModuleNotFoundError  # pylint:disable=redefined-builtin
from dagster.utils import frozentags
from dagster.utils.yaml_utils import merge_yaml_strings, merge_yamls

DEFAULT_OUTPUT = "result"

DISALLOWED_NAMES = set(
    [
        "context",
        "conf",
        "config",
        "meta",
        "arg_dict",
        "dict",
        "input_arg_dict",
        "output_arg_dict",
        "int",
        "str",
        "float",
        "bool",
        "input",
        "output",
        "type",
    ]
    + keyword.kwlist  # just disallow all python keywords
)

VALID_NAME_REGEX_STR = r"^[A-Za-z0-9_]+$"
VALID_NAME_REGEX = re.compile(VALID_NAME_REGEX_STR)


def has_valid_name_chars(name):
    return bool(VALID_NAME_REGEX.match(name))


def check_valid_name(name):
    check.str_param(name, "name")
    if name in DISALLOWED_NAMES:
        raise DagsterInvalidDefinitionError("{name} is not allowed.".format(name=name))

    if not has_valid_name_chars(name):
        raise DagsterInvalidDefinitionError(
            "{name} must be in regex {regex}".format(name=name, regex=VALID_NAME_REGEX_STR)
        )
    return name


def _kv_str(key, value):
    return '{key}="{value}"'.format(key=key, value=repr(value))


def struct_to_string(name, **kwargs):
    # Sort the kwargs to ensure consistent representations across Python versions
    props_str = ", ".join([_kv_str(key, value) for key, value in sorted(kwargs.items())])
    return "{name}({props_str})".format(name=name, props_str=props_str)


def validate_tags(tags):
    valid_tags = {}
    for key, value in check.opt_dict_param(tags, "tags", key_type=str).items():
        if not check.is_str(value):
            valid = False
            err_reason = 'Could not JSON encode value "{}"'.format(value)
            try:
                str_val = seven.json.dumps(value)
                err_reason = 'JSON encoding "{json}" of value "{val}" is not equivalent to original value'.format(
                    json=str_val, val=value
                )

                valid = seven.json.loads(str_val) == value
            except Exception:  # pylint: disable=broad-except
                pass

            if not valid:
                raise DagsterInvalidDefinitionError(
                    'Invalid value for tag "{key}", {err_reason}. Tag values must be strings '
                    "or meet the constraint that json.loads(json.dumps(value)) == value.".format(
                        key=key, err_reason=err_reason
                    )
                )

            valid_tags[key] = str_val
        else:
            valid_tags[key] = value

    return frozentags(valid_tags)


def config_from_files(config_files):
    """Constructs run config from YAML files.

    Args:
        config_files (List[str]): List of paths or glob patterns for yaml files
            to load and parse as the run config.

    Returns:
        Dict[Str, Any]: A run config dictionary constructed from provided YAML files.

    Raises:
        FileNotFoundError: When a config file produces no results
        DagsterInvariantViolationError: When one of the YAML files is invalid and has a parse
            error.
    """
    config_files = check.opt_list_param(config_files, "config_files")

    filenames = []
    for file_glob in config_files or []:
        globbed_files = glob(file_glob)
        if not globbed_files:
            raise DagsterInvariantViolationError(
                'File or glob pattern "{file_glob}" for "config_files"'
                "produced no results.".format(file_glob=file_glob)
            )

        filenames += [os.path.realpath(globbed_file) for globbed_file in globbed_files]

    try:
        run_config = merge_yamls(filenames)
    except yaml.YAMLError as err:
        six.raise_from(
            DagsterInvariantViolationError(
                "Encountered error attempting to parse yaml. Parsing files {file_set} "
                "loaded by file/patterns {files}.".format(file_set=filenames, files=config_files)
            ),
            err,
        )

    return run_config


def config_from_yaml_strings(yaml_strings):
    """Static constructor for run configs from YAML strings.

    Args:
        yaml_strings (List[str]): List of yaml strings to parse as the run config.

    Returns:
        Dict[Str, Any]: A run config dictionary constructed from the provided yaml strings

    Raises:
        DagsterInvariantViolationError: When one of the YAML documents is invalid and has a
            parse error.
    """
    yaml_strings = check.opt_list_param(yaml_strings, "yaml_strings", of_type=str)

    try:
        run_config = merge_yaml_strings(yaml_strings)
    except yaml.YAMLError as err:
        six.raise_from(
            DagsterInvariantViolationError(
                "Encountered error attempting to parse yaml. Parsing YAMLs {yaml_strings} ".format(
                    yaml_strings=yaml_strings
                )
            ),
            err,
        )

    return run_config


def config_from_pkg_resources(pkg_resource_defs):
    """Load a run config from a package resource, using :py:func:`pkg_resources.resource_string`.

    Example:

    .. code-block:: python

        config_from_pkg_resources(
            pkg_resource_defs=[
                ('dagster_examples.airline_demo.environments', 'local_base.yaml'),
                ('dagster_examples.airline_demo.environments', 'local_warehouse.yaml'),
            ],
        )


    Args:
        pkg_resource_defs (List[(str, str)]): List of pkg_resource modules/files to
            load as the run config.

    Returns:
        Dict[Str, Any]: A run config dictionary constructed from the provided yaml strings

    Raises:
        DagsterInvariantViolationError: When one of the YAML documents is invalid and has a
            parse error.
    """
    pkg_resource_defs = check.opt_list_param(pkg_resource_defs, "pkg_resource_defs", of_type=tuple)

    try:
        yaml_strings = [
            six.ensure_str(pkg_resources.resource_string(*pkg_resource_def))
            for pkg_resource_def in pkg_resource_defs
        ]
    except (ModuleNotFoundError, FileNotFoundError, UnicodeDecodeError) as err:
        six.raise_from(
            DagsterInvariantViolationError(
                "Encountered error attempting to parse yaml. Loading YAMLs from "
                "package resources {pkg_resource_defs}.".format(pkg_resource_defs=pkg_resource_defs)
            ),
            err,
        )

    return config_from_yaml_strings(yaml_strings=yaml_strings)
