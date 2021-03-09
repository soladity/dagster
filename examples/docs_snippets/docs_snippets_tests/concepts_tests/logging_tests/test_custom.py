import yaml
from dagster import execute_pipeline
from dagster.utils import file_relative_path
from docs_snippets.concepts.logging.custom_logger import demo_pipeline


def test_json_logger():
    with open(
        file_relative_path(
            __file__, "../../../docs_snippets/concepts/logging/config_custom_logger.yaml"
        ),
        "r",
    ) as fd:
        run_config = yaml.safe_load(fd.read())
    assert execute_pipeline(demo_pipeline, run_config=run_config).success
