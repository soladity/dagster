from typing import AbstractSet, Any, Optional

from dagster import (
    InputDefinition,
    Nothing,
    ResourceDefinition,
    SolidDefinition,
    repository,
    schedule,
    sensor,
    solid,
)
from dagster.core.definitions.decorators.graph import graph


def make_solid(
    name: str,
    required_resource_keys: Optional[AbstractSet[str]] = None,
    config_schema: Optional[Any] = None,
) -> SolidDefinition:
    @solid(
        name=name,
        input_defs=[InputDefinition("the_input", dagster_type=Nothing)],
        required_resource_keys=required_resource_keys,
        config_schema=config_schema,
    )
    def _solid(_):
        return None

    return _solid


@graph
def event_tables():
    """A graph with no resources"""
    make_raw_events = make_solid("make_raw_events")
    clean_events = make_solid("clean_events")

    raw_events = make_raw_events()
    clean_events(raw_events)


@schedule(job=event_tables, cron_schedule="0 0 * * *")
def event_tables_schedule(_):
    return {}


@graph
def event_reports():
    make_event_reports = make_solid("make_event_reports", required_resource_keys={"mode"})
    make_event_reports()


@sensor(job=event_reports.to_job(resource_defs={"mode": ResourceDefinition.none_resource()}))
def event_reports_sensor():
    pass


event_reports_dev = event_reports.to_job(resource_defs={"mode": ResourceDefinition.none_resource()})


@graph
def crm_ingest():
    """A graph with multiple production jobs"""
    ingest_users = make_solid("ingest_users", required_resource_keys={"crm"})
    ingest_interactions = make_solid("ingest_interactions", required_resource_keys={"crm"})

    ingest_users()
    ingest_interactions()


crm_ingest_dev = crm_ingest.to_job(resource_defs={"crm": ResourceDefinition.none_resource()})


@schedule(
    job=crm_ingest.to_job(
        name="crm_ingest_instance1", resource_defs={"crm": ResourceDefinition.none_resource()}
    ),
    cron_schedule="0 0 * * *",
)
def crm_ingest_instance1_schedule(_):
    return {}


@schedule(
    job=crm_ingest.to_job(
        name="crm_ingest_instance2", resource_defs={"crm": ResourceDefinition.none_resource()}
    ),
    cron_schedule="0 0 * * *",
)
def crm_ingest_instance2_schedule(_):
    return {}


@graph
def content_recommender_training():
    """A graph with a production job, but no schedule"""
    build_user_features = make_solid("build_user_features")
    build_item_features = make_solid("build_item_features")
    train_model = make_solid("train_model", required_resource_keys={"mlflow"})
    evaluate_model = make_solid("evaluate_model")

    evaluate_model(train_model([build_user_features(), build_item_features()]))


content_recommender_training_dev = content_recommender_training.to_job(
    resource_defs={"mlflow": ResourceDefinition.none_resource()}
)

content_recommender_training_prod = content_recommender_training.to_job(
    resource_defs={"mlflow": ResourceDefinition.none_resource()}
)


@graph
def process_customer_data_dump():
    """Customer success managers run this pipeline for a particular customers when those customers
    have data to upload."""
    process_customer = make_solid("process_customer", config_schema={"customer_id": str})
    process_customer()


process_customer_data_dump_dev = process_customer_data_dump.to_job(
    default_config={"solids": {"process_customer": {"config": {"customer_id": "test_customer"}}}}
)


@repository
def graph_job_dev_repo():
    return [
        event_tables,
        event_reports_dev,
        crm_ingest_dev,
        content_recommender_training_dev,
        process_customer_data_dump_dev,
    ]


@repository
def graph_job_prod_repo():
    return [
        event_tables_schedule,
        event_reports_sensor,
        crm_ingest_instance1_schedule,
        crm_ingest_instance2_schedule,
        content_recommender_training_prod,
        process_customer_data_dump,
    ]
