import csv

import requests
from dagster import pipeline, solid


@solid
def download_cereals(_):
    response = requests.get(
        "https://raw.githubusercontent.com/dagster-io/dagster/master/examples/docs_snippets/docs_snippets/intro_tutorial/cereal.csv"
    )
    lines = response.text.split("\n")
    return [row for row in csv.DictReader(lines)]


@solid
def find_sugariest(context, cereals):
    sorted_by_sugar = sorted(cereals, key=lambda cereal: cereal["sugars"])
    context.log.info(f'{sorted_by_sugar[-1]["name"]} is the sugariest cereal')


@pipeline
def serial_pipeline():
    find_sugariest(download_cereals())
