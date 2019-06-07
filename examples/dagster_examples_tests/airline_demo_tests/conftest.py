import os
import subprocess
import sys

import pytest

from dagster.utils import script_relative_path, pushd


CIRCLECI = os.getenv('CIRCLECI')


# Spins up a database using docker-compose and tears it down after tests complete.
# We disable this on CircleCI when running the py37 tests -- airflow is not compatible with
# py37; as a consequence, on this build we use the Circle docker executor, rather than the
# machine executor, and spin the database up directly from circleci/postgres:9.6.2-alpine.
@pytest.fixture(scope='session')
def docker_compose_db():
    if sys.version_info.major == 3 and sys.version_info.minor == 7 and CIRCLECI:
        yield
        return

    with pushd(script_relative_path('../')):
        try:
            subprocess.check_output(['docker-compose', 'stop', 'airline-demo-db'])
            subprocess.check_output(['docker-compose', 'rm', '-f', 'airline-demo-db'])
        except Exception:  # pylint: disable=broad-except
            pass
        subprocess.check_output(['docker-compose', 'up', '-d', 'airline-demo-db'])

    yield

    with pushd(script_relative_path('../')):
        subprocess.check_output(['docker-compose', 'stop', 'airline-demo-db'])
        subprocess.check_output(['docker-compose', 'rm', '-f', 'airline-demo-db'])

    return
