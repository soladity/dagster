import os

import pytest
from dagster.utils import file_relative_path
from dagster.utils.test.postgres_instance import TestPostgresInstance


@pytest.fixture(scope="function")
def postgres():  # pylint: disable=redefined-outer-name
    with TestPostgresInstance.docker_service_up(
        file_relative_path(
            __file__, os.path.join("..", "..", "..", "dbt_example", "docker-compose.yml")
        ),
        "test-postgres-db",
    ) as conn_string:
        yield conn_string
