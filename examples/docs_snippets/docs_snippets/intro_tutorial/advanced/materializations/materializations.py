import csv
import os

import requests
from dagster import (
    AssetMaterialization,
    EventMetadataEntry,
    Output,
    pipeline,
    solid,
)


@solid
def download_csv(context):
    response = requests.get("https://docs.dagster.io/assets/cereal.csv")
    lines = response.text.split("\n")
    context.log.info("Read {n_lines} lines".format(n_lines=len(lines)))
    return [row for row in csv.DictReader(lines)]


# start_materializations_marker_0
@solid
def sort_by_calories(context, cereals):
    sorted_cereals = sorted(
        cereals, key=lambda cereal: int(cereal["calories"])
    )
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
    fieldnames = list(sorted_cereals[0].keys())
    sorted_cereals_csv_path = os.path.abspath(
        "output/calories_sorted_{run_id}.csv".format(run_id=context.run_id)
    )
    os.makedirs(os.path.dirname(sorted_cereals_csv_path), exist_ok=True)
    with open(sorted_cereals_csv_path, "w") as fd:
        writer = csv.DictWriter(fd, fieldnames)
        writer.writeheader()
        writer.writerows(sorted_cereals)
    yield AssetMaterialization(
        asset_key="sorted_cereals_csv",
        description="Cereals data frame sorted by caloric content",
        metadata_entries=[
            EventMetadataEntry.path(
                sorted_cereals_csv_path, "sorted_cereals_csv_path"
            )
        ],
    )
    yield Output(None)


# end_materializations_marker_0


@pipeline
def materialization_pipeline():
    sort_by_calories(download_csv())
