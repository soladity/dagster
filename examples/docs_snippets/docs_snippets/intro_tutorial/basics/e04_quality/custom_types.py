import csv

import requests
from dagster import (
    DagsterType,
    InputDefinition,
    OutputDefinition,
    execute_pipeline,
    pipeline,
    solid,
)


# start_custom_types_marker_0
def is_list_of_dicts(_, value):
    return isinstance(value, list) and all(
        isinstance(element, dict) for element in value
    )


SimpleDataFrame = DagsterType(
    name="SimpleDataFrame",
    type_check_fn=is_list_of_dicts,
    description="A naive representation of a data frame, e.g., as returned by csv.DictReader.",
)
# end_custom_types_marker_0


# start_custom_types_marker_1


@solid(output_defs=[OutputDefinition(SimpleDataFrame)])
def download_csv(context, url):
    response = requests.get(url)
    lines = response.text.split("\n")
    context.log.info("Read {n_lines} lines".format(n_lines=len(lines)))
    return [row for row in csv.DictReader(lines)]


@solid(input_defs=[InputDefinition("cereals", SimpleDataFrame)])
def sort_by_calories(context, cereals):
    sorted_cereals = sorted(cereals, key=lambda cereal: cereal["calories"])
    context.log.info(f'Most caloric cereal: {sorted_cereals[-1]["name"]}')


# end_custom_types_marker_1


@pipeline
def custom_type_pipeline():
    sort_by_calories(download_csv())


if __name__ == "__main__":
    run_config = {
        "solids": {
            "download_csv": {
                "inputs": {
                    "url": {
                        "value": "https://raw.githubusercontent.com/dagster-io/dagster/master/examples/docs_snippets/docs_snippets/intro_tutorial/cereal.csv"
                    }
                }
            }
        }
    }
    result = execute_pipeline(custom_type_pipeline, run_config=run_config)
    assert result.success
