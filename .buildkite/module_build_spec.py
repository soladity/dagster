import os
import sys
from collections import namedtuple

SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))

sys.path.append(SCRIPT_PATH)
from defines import SupportedPython, SupportedPythons, TOX_MAP  # isort:skip
from step_builder import StepBuilder  # isort:skip


class ModuleBuildSpec(
    namedtuple(
        '_ModuleBuildSpec',
        'directory env_vars supported_pythons extra_cmds_fn depends_on_fn tox_file '
        'tox_env_suffixes buildkite_label',
    )
):
    '''Main spec for testing Dagster Python modules using tox.

    Args:
        directory (str): Python directory to test, relative to the repository root. Should contain a
            tox.ini file.
        env_vars (List[str], optional): Additional environment variables to pass through to the
            test. Make sure you set these in tox.ini also, using ``passenv``! Defaults to None.
        supported_pythons (List[str], optional): Optional overrides for Python versions to test.
            Tests are generated for each version of Python listed here; each test will run in an
            integration test image for that Python version, and ``tox -e <<VERSION>>`` will be
            invoked for the corresponding Python version. Defaults to None (all supported Pythons).
        extra_cmds_fn (Callable[str, List[str]], optional): Optional callable to create more
            commands to run before the main test invocation through tox. Function takes a single
            argument, which is the Python version being invoked, and returns a list of shell
            commands to execute, one invocation per list item. Defaults to None (no additional
            commands).
        depends_on_fn (Callable[str, List[str]], optional): Optional callable to create a
            Buildkite dependency (e.g. on test image build step). Function takes a single
            argument, which is the Python version being invoked, and returns a list of names of
            other Buildkite build steps this build step should depend on. Defaults to None (no
            dependencies).
        tox_file (str, optional): The tox file to use. Defaults to None (uses the default tox.ini
            file).
        tox_env_suffixes: (List[str], optional): List of additional tox env suffixes to provide
            when invoking tox. When provided, a separate test run will be invoked per
            env x env_suffix string. For example, given Python tox version py27, the
            tox_env_suffixes ["-a", "-b"] will result in running "tox -e py27-a" and "tox -e py27-b"
            as two build steps. Defaults to None.
        buildkite_label: (str, optional): Optional label to override what's shown in Buildkite.
            Defaults to None (uses the package name as the label).

    Returns:
        List[dict]: List of test steps
    '''

    def __new__(
        cls,
        directory,
        env_vars=None,
        supported_pythons=None,
        extra_cmds_fn=None,
        depends_on_fn=None,
        tox_file=None,
        tox_env_suffixes=None,
        buildkite_label=None,
    ):
        return super(ModuleBuildSpec, cls).__new__(
            cls,
            directory,
            env_vars or [],
            supported_pythons or SupportedPythons,
            extra_cmds_fn,
            depends_on_fn,
            tox_file,
            tox_env_suffixes,
            buildkite_label,
        )

    def get_tox_build_steps(self):
        package = self.buildkite_label or self.directory.split("/")[-1]
        tests = []

        tox_env_suffixes = self.tox_env_suffixes or ['']

        for version in self.supported_pythons:
            for tox_env_suffix in tox_env_suffixes:
                label = package + tox_env_suffix

                coverage = ".coverage.{label}.{version}.$BUILDKITE_BUILD_ID".format(
                    label=label, version=version
                )

                extra_cmds = self.extra_cmds_fn(version) if self.extra_cmds_fn else []

                # See: https://github.com/dagster-io/dagster/issues/2512
                tox_file = '-c %s ' % self.tox_file if self.tox_file else ''
                tox_cmd = 'tox -vv {tox_file}-e {ver}{tox_env_suffix}'.format(
                    tox_file=tox_file, tox_env_suffix=tox_env_suffix, ver=TOX_MAP[version]
                )

                cmds = extra_cmds + [
                    'cd {directory}'.format(directory=self.directory),
                    tox_cmd,
                    'mv .coverage {file}'.format(file=coverage),
                    'buildkite-agent artifact upload {file}'.format(file=coverage),
                ]

                step = (
                    StepBuilder('{label} tests ({ver})'.format(label=label, ver=TOX_MAP[version]))
                    .run(*cmds)
                    .on_integration_image(version, self.env_vars or [])
                )

                if self.depends_on_fn:
                    step = step.depends_on(self.depends_on_fn(version))

                tests.append(step.build())

        # We expect the tox file to define a pylint testenv, and we'll construct a separate
        # buildkite build step for the pylint testenv.
        tests.append(
            StepBuilder('%s pylint' % package)
            .run('cd {directory}'.format(directory=self.directory), 'tox -vv -e pylint')
            .on_integration_image(SupportedPython.V3_7)
            .build()
        )
        return tests
