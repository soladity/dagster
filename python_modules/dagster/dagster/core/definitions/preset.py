from collections import namedtuple

import pkg_resources
import six
import yaml

from dagster import check
from dagster.core.definitions.utils import config_from_files, config_from_yaml_strings
from dagster.core.errors import DagsterInvariantViolationError
from dagster.seven import FileNotFoundError, ModuleNotFoundError  # pylint:disable=redefined-builtin
from dagster.utils import merge_dicts
from dagster.utils.backcompat import canonicalize_backcompat_args

from .mode import DEFAULT_MODE_NAME


class PresetDefinition(
    namedtuple("_PresetDefinition", "name run_config solid_selection mode tags")
):
    """Defines a preset configuration in which a pipeline can execute.

    Presets can be used in Dagit to load predefined configurations into the tool.

    Presets may also be used from the Python API (in a script, or in test) as follows:

    .. code-block:: python

        execute_pipeline(pipeline_def, preset='example_preset')

    Presets may also be used with the command line tools:

    .. code-block:: shell

        $ dagster pipeline execute example_pipeline --preset example_preset

    Args:
        name (str): The name of this preset. Must be unique in the presets defined on a given
            pipeline.
        run_config (Optional[dict]): A dict representing the config to set with the preset.
            This is equivalent to the ``run_config`` argument to :py:func:`execute_pipeline`.
        solid_selection (Optional[List[str]]): A list of solid subselection (including single
            solid names) to execute with the preset. e.g. ``['*some_solid+', 'other_solid']``
        mode (Optional[str]): The mode to apply when executing this preset. (default: 'default')
        tags (Optional[Dict[str, Any]]): The tags to apply when executing this preset.
    """

    def __new__(
        cls, name, run_config=None, solid_selection=None, mode=None, tags=None,
    ):

        return super(PresetDefinition, cls).__new__(
            cls,
            name=check.str_param(name, "name"),
            run_config=run_config,
            solid_selection=check.opt_nullable_list_param(
                solid_selection, "solid_selection", of_type=str
            ),
            mode=check.opt_str_param(mode, "mode", DEFAULT_MODE_NAME),
            tags=check.opt_dict_param(tags, "tags", key_type=str),
        )

    @staticmethod
    def from_files(
        name, environment_files=None, config_files=None, solid_selection=None, mode=None, tags=None
    ):
        """Static constructor for presets from YAML files.

        Args:
            name (str): The name of this preset. Must be unique in the presets defined on a given
                pipeline.
            config_files (Optional[List[str]]): List of paths or glob patterns for yaml files
                to load and parse as the environment config for this preset.
            solid_selection (Optional[List[str]]): A list of solid subselection (including single
                solid names) to execute with the preset. e.g. ``['*some_solid+', 'other_solid']``
            mode (Optional[str]): The mode to apply when executing this preset. (default:
                'default')
            tags (Optional[Dict[str, Any]]): The tags to apply when executing this preset.

        Returns:
            PresetDefinition: A PresetDefinition constructed from the provided YAML files.

        Raises:
            DagsterInvariantViolationError: When one of the YAML files is invalid and has a parse
                error.
        """
        check.str_param(name, "name")
        config_files = canonicalize_backcompat_args(
            config_files, "config_files", environment_files, "environment_files", "0.9.0"
        )
        config_files = check.opt_list_param(config_files, "config_files")
        solid_selection = check.opt_nullable_list_param(
            solid_selection, "solid_selection", of_type=str
        )
        mode = check.opt_str_param(mode, "mode", DEFAULT_MODE_NAME)

        merged = config_from_files(config_files)

        return PresetDefinition(name, merged, solid_selection, mode, tags)

    @staticmethod
    def from_yaml_strings(name, yaml_strings=None, solid_selection=None, mode=None, tags=None):
        """Static constructor for presets from YAML strings.

        Args:
            name (str): The name of this preset. Must be unique in the presets defined on a given
                pipeline.
            yaml_strings (Optional[List[str]]): List of yaml strings to parse as the environment
                config for this preset.
            solid_selection (Optional[List[str]]): A list of solid subselection (including single
                solid names) to execute with the preset. e.g. ``['*some_solid+', 'other_solid']``
            mode (Optional[str]): The mode to apply when executing this preset. (default:
                'default')
            tags (Optional[Dict[str, Any]]): The tags to apply when executing this preset.

        Returns:
            PresetDefinition: A PresetDefinition constructed from the provided YAML strings

        Raises:
            DagsterInvariantViolationError: When one of the YAML documents is invalid and has a
                parse error.
        """
        check.str_param(name, "name")
        yaml_strings = check.opt_list_param(yaml_strings, "yaml_strings", of_type=str)
        solid_selection = check.opt_nullable_list_param(
            solid_selection, "solid_selection", of_type=str
        )
        mode = check.opt_str_param(mode, "mode", DEFAULT_MODE_NAME)

        merged = config_from_yaml_strings(yaml_strings)

        return PresetDefinition(name, merged, solid_selection, mode, tags)

    @staticmethod
    def from_pkg_resources(
        name, pkg_resource_defs=None, solid_selection=None, mode=None, tags=None
    ):
        """Load a preset from a package resource, using :py:func:`pkg_resources.resource_string`.

        Example:

        .. code-block:: python

            PresetDefinition.from_pkg_resources(
                name='local',
                mode='local',
                pkg_resource_defs=[
                    ('dagster_examples.airline_demo.environments', 'local_base.yaml'),
                    ('dagster_examples.airline_demo.environments', 'local_warehouse.yaml'),
                ],
            )


        Args:
            name (str): The name of this preset. Must be unique in the presets defined on a given
                pipeline.
            pkg_resource_defs (Optional[List[(str, str)]]): List of pkg_resource modules/files to
                load as environment config for this preset.
            solid_selection (Optional[List[str]]): A list of solid subselection (including single
                solid names) to execute with this partition. e.g.
                ``['*some_solid+', 'other_solid']``
            mode (Optional[str]): The mode to apply when executing this preset. (default:
                'default')
            tags (Optional[Dict[str, Any]]): The tags to apply when executing this preset.

        Returns:
            PresetDefinition: A PresetDefinition constructed from the provided YAML strings

        Raises:
            DagsterInvariantViolationError: When one of the YAML documents is invalid and has a
                parse error.
        """
        pkg_resource_defs = check.opt_list_param(
            pkg_resource_defs, "pkg_resource_defs", of_type=tuple
        )

        try:
            yaml_strings = [
                six.ensure_str(pkg_resources.resource_string(*pkg_resource_def))
                for pkg_resource_def in pkg_resource_defs
            ]
        except (ModuleNotFoundError, FileNotFoundError, UnicodeDecodeError) as err:
            six.raise_from(
                DagsterInvariantViolationError(
                    "Encountered error attempting to parse yaml. Loading YAMLs from "
                    "package resources {pkg_resource_defs} "
                    'on preset "{name}".'.format(pkg_resource_defs=pkg_resource_defs, name=name)
                ),
                err,
            )

        return PresetDefinition.from_yaml_strings(name, yaml_strings, solid_selection, mode, tags)

    def get_environment_yaml(self):
        """Get the environment dict set on a preset as YAML.

        Returns:
            str: The environment dict as YAML.
        """
        return yaml.dump(self.run_config or {}, default_flow_style=False)

    def with_additional_config(self, run_config):
        """Return a new PresetDefinition with additional config merged in to the existing config."""

        check.opt_nullable_dict_param(run_config, "run_config")
        if run_config is None:
            return self
        else:
            return PresetDefinition(
                name=self.name,
                solid_selection=self.solid_selection,
                mode=self.mode,
                tags=self.tags,
                run_config=merge_dicts(self.run_config, run_config),
            )
