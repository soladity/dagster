import tempfile

from dagster import execute_pipeline
from memoized_development.repo import my_pipeline


def test_memoized_development():
    with tempfile.TemporaryDirectory() as temp_dir:
        result = execute_pipeline(
            my_pipeline,
            run_config={
                "solids": {
                    "emit_dog": {"config": {"dog_breed": "poodle"}},
                    "emit_tree": {"config": {"tree_species": "weeping_willow"}},
                },
                "resources": {"io_manager": {"config": {"base_dir": temp_dir}}},
            },
        )
        assert result.success
