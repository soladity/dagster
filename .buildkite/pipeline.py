import yaml

DOCKER_PLUGIN = "docker#v3.1.0"


# This should be an enum once we make our own buildkite AMI with py3
class SupportedPython:
    V3_7 = "3.7"
    V3_6 = "3.6"
    V3_5 = "3.5"
    V2_7 = "2.7"


SupportedPythons = [
    SupportedPython.V3_7,
    SupportedPython.V3_6,
    SupportedPython.V3_5,
    SupportedPython.V2_7,
]

IMAGE_MAP = {
    SupportedPython.V3_7: "python:3.7",
    SupportedPython.V3_6: "python:3.6",
    SupportedPython.V3_5: "python:3.5",
    SupportedPython.V2_7: "python:2.7",
}

TOX_MAP = {
    SupportedPython.V3_7: "py37",
    SupportedPython.V3_6: "py36",
    SupportedPython.V3_5: "py35",
    SupportedPython.V2_7: "py27",
}


class StepBuilder:
    def __init__(self, label):
        self._step = {"label": label}

    def run(self, *argc):
        self._step["command"] = "\n".join(argc)
        return self

    def on_docker_image(self, img, env=None):
        if img in IMAGE_MAP:
            img = IMAGE_MAP[img]

        docker = {"image": img, "always-pull": True}
        if env:
            docker['environment'] = env

        self._step["plugins"] = [{DOCKER_PLUGIN: docker}]
        return self

    def build(self):
        return self._step


def wait_step():
    return "wait"


def python_modules_tox_tests(directory, prereqs=None):
    label = directory.replace("/", "-")
    tests = []
    for version in SupportedPythons:
        coverage = ".coverage.{label}.{version}.$BUILDKITE_BUILD_ID".format(
            label=label, version=version
        )
        tox_command = []
        if prereqs:
            tox_command += prereqs
        tox_command += [
            "pip install tox;",
            "cd python_modules/{directory}".format(directory=directory),
            "tox -e {ver}".format(ver=TOX_MAP[version]),
            "mv .coverage {file}".format(file=coverage),
            "buildkite-agent artifact upload {file}".format(file=coverage),
        ]
        tests.append(
            StepBuilder("{label} tests ({ver})".format(label=label, ver=TOX_MAP[version]))
            .run(*tox_command)
            .on_docker_image(version)
            .build()
        )

    return tests


if __name__ == "__main__":
    steps = [
        StepBuilder("pylint")
        .run("make dev_install", "make pylint")
        .on_docker_image(SupportedPython.V3_7)
        .build(),
        StepBuilder("black")
        # black 18.9b0 doesn't support py27-compatible formatting of the below invocation (omitting
        # the trailing comma after **check.opt_dict_param...) -- black 19.3b0 supports multiple python
        # versions, but currently doesn't know what to do with from __future__ import print_function --
        # see https://github.com/ambv/black/issues/768
        .run("pip install black==18.9b0", "make check_black")
        .on_docker_image(SupportedPython.V3_7)
        .build(),
        StepBuilder("docs snapshot test")
        .run(
            "pip install -r python_modules/dagster/dev-requirements.txt -qqq",
            "pip install -e python_modules/dagster -qqq",
            "pytest -vv python_modules/dagster/docs",
        )
        .on_docker_image(SupportedPython.V3_7)
        .build(),
        StepBuilder("dagit webapp tests")
        .run(
            "pip install -r python_modules/dagster/dev-requirements.txt -qqq",
            "pip install -e python_modules/dagster -qqq",
            "pip install -e python_modules/dagster-graphql -qqq",
            "pip install -e python_modules/dagit -qqq",
            "pip install -r python_modules/dagit/dev-requirements.txt -qqq",
            "cd js_modules/dagit",
            "yarn install --offline",
            "yarn run ts",
            "yarn run jest",
            "yarn run check-prettier",
            "yarn generate-types",
            "git diff --exit-code",
        )
        .on_docker_image("nikolaik/python-nodejs:python3.7-nodejs11")
        .build(),
    ]
    steps += python_modules_tox_tests("dagster")
    steps += python_modules_tox_tests("dagit", ["apt-get update", "apt-get install -y xdg-utils"])
    steps += python_modules_tox_tests("dagster-graphql")
    steps += python_modules_tox_tests("dagstermill")
    steps += python_modules_tox_tests("libraries/dagster-pandas")
    steps += python_modules_tox_tests("libraries/dagster-ge")
    steps += python_modules_tox_tests("libraries/dagster-aws")
    steps += python_modules_tox_tests("libraries/dagster-snowflake")
    steps += python_modules_tox_tests("libraries/dagster-spark")

    steps += [
        wait_step(),  # wait for all previous steps to finish
        StepBuilder("coverage")
        .run(
            "pip install coverage coveralls",
            "mkdir -p tmp",
            'buildkite-agent artifact download ".coverage*" tmp/',
            "cd tmp",
            "coverage combine",
            "coveralls",
        )
        .on_docker_image(
            SupportedPython.V3_7,
            # COVERALLS_REPO_TOKEN exported by /env in ManagedSecretsBucket
            ['COVERALLS_REPO_TOKEN', 'BUILDKITE_PULL_REQUEST', 'BUILDKITE_JOB_ID', 'BUILDKITE'],
        )
        .build(),
    ]

    print(yaml.dump({"steps": steps}, default_flow_style=False, default_style="|"))
