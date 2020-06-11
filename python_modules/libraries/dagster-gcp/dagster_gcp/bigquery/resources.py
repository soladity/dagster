from google.cloud import bigquery

from dagster import resource

from .configs import bq_resource_config


@resource(config=bq_resource_config(), description='Dagster resource for connecting to BigQuery')
def bigquery_resource(context):
    return bigquery.Client(**context.resource_config)
