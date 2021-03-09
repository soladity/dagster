import os

from dagster.core.instance.config import dagster_instance_config


def test_instance_yaml(docs_snippets_folder, snapshot):
    # Before updating the snapshot for this test, please make sure that you
    # update the dagster.yaml at the path below to include the new addition
    # to the dagster.yaml configuration options.

    intance_yaml_folder = os.path.join(
        docs_snippets_folder,
        "deploying",
        "dagster_instance",
    )

    config = dagster_instance_config(intance_yaml_folder)
    keys = sorted(list(config.keys()))
    snapshot.assert_match(keys)
