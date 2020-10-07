import csv
import os

from dagster import (
    DagsterType,
    InputDefinition,
    OutputDefinition,
    String,
    execute_pipeline,
    pipeline,
    solid,
)

SimpleDataFrame = DagsterType(
    name="SimpleDataFrame",
    type_check_fn=lambda _, value: isinstance(value, list),
    description="A naive representation of a data frame, e.g., as returned by csv.DictReader.",
)

# start_custom_types_mypy_verbose_marker_0
@solid(
    input_defs=[InputDefinition("csv_path", String)],
    output_defs=[OutputDefinition(SimpleDataFrame)],
)
def read_csv(context, csv_path: str) -> list:
    csv_path = os.path.join(os.path.dirname(__file__), csv_path)
    with open(csv_path, "r") as fd:
        lines = [row for row in csv.DictReader(fd)]

    context.log.info("Read {n_lines} lines".format(n_lines=len(lines)))
    return lines


@solid(input_defs=[InputDefinition("cereals", SimpleDataFrame)])
def sort_by_calories(context, cereals: list):
    sorted_cereals = sorted(cereals, key=lambda cereal: cereal["calories"])
    context.log.info(
        "Least caloric cereal: {least_caloric}".format(
            least_caloric=sorted_cereals[0]["name"]
        )
    )
    context.log.info(
        "Most caloric cereal: {most_caloric}".format(
            most_caloric=sorted_cereals[-1]["name"]
        )
    )


# end_custom_types_mypy_verbose_marker_0


@pipeline
def custom_type_pipeline():
    sort_by_calories(read_csv())


if __name__ == "__main__":
    run_config = {
        "solids": {
            "read_csv": {"inputs": {"csv_path": {"value": "cereal.csv"}}}
        }
    }
    result = execute_pipeline(custom_type_pipeline, run_config=run_config)
    assert result.success
