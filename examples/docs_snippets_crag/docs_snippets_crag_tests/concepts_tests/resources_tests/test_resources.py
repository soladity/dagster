from dagster import build_init_resource_context, build_op_context
from docs_snippets_crag.concepts.resources.resources import (
    cereal_fetcher,
    connect_job,
    db_resource,
    op_requires_resources,
    test_cm_resource,
    test_my_resource,
    test_my_resource_with_context,
)


def test_cereal_fetcher():
    assert cereal_fetcher(None)


def test_database_resource():
    class BasicDatabase:
        def execute_query(self, query):
            pass

    op_requires_resources(build_op_context(resources={"database": BasicDatabase()}))


def test_resource_testing_examples():
    test_my_resource()
    test_my_resource_with_context()
    test_cm_resource()


def test_resource_deps_job():
    result = connect_job.execute_in_process()
    assert result.success


def test_resource_config_example():
    dbconn = db_resource(build_init_resource_context(config={"connection": "foo"}))
    assert dbconn.connection == "foo"
