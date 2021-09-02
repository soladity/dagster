"""isort:skip_file"""

# start_solid_marker
import requests
import csv
from dagster import graph, op


@op
def hello_cereal(context):
    response = requests.get("https://docs.dagster.io/assets/cereal.csv")
    lines = response.text.split("\n")
    cereals = [row for row in csv.DictReader(lines)]
    context.log.info(f"Found {len(cereals)} cereals")

    return cereals


# end_solid_marker


# start_pipeline_marker
@graph
def hello_cereal_graph():
    hello_cereal()


# end_pipeline_marker

# start_execute_marker
if __name__ == "__main__":
    result = hello_cereal_graph.execute_in_process()

# end_execute_marker
