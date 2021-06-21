import pytest
import yaml
from dagster_aws.s3.compute_log_manager import S3ComputeLogManager
from dagster_azure.blob.compute_log_manager import AzureBlobComputeLogManager
from dagster_gcp.gcs.compute_log_manager import GCSComputeLogManager
from kubernetes.client import models
from schema.charts.dagster.subschema.compute_log_manager import (
    AzureBlobComputeLogManager as AzureBlobComputeLogManagerModel,
)
from schema.charts.dagster.subschema.compute_log_manager import (
    GCSComputeLogManager as GCSComputeLogManagerModel,
)
from schema.charts.dagster.subschema.compute_log_manager import (
    S3ComputeLogManager as S3ComputeLogManagerModel,
)
from schema.charts.dagster.subschema.daemon import Daemon, QueuedRunCoordinator
from schema.charts.dagster.subschema.postgresql import PostgreSQL, Service
from schema.charts.dagster.values import DagsterHelmValues
from schema.utils.helm_template import HelmTemplate


def to_camel_case(s: str) -> str:
    components = s.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


@pytest.fixture(name="template")
def helm_template() -> HelmTemplate:
    return HelmTemplate(
        helm_dir_path="helm/dagster",
        subchart_paths=["charts/dagster-user-deployments"],
        output="templates/configmap-instance.yaml",
        model=models.V1ConfigMap,
    )


@pytest.mark.parametrize("storage", ["schedule_storage", "run_storage", "event_log_storage"])
def test_storage_postgres_db_config(template: HelmTemplate, storage: str):
    postgresql_username = "username"
    postgresql_host = "1.1.1.1"
    postgresql_database = "database"
    postgresql_params = {
        "connect_timeout": 10,
        "application_name": "myapp",
        "options": "-c synchronous_commit=off",
    }
    postgresql_port = 8080
    helm_values = DagsterHelmValues.construct(
        postgresql=PostgreSQL.construct(
            postgresqlUsername=postgresql_username,
            postgresqlHost=postgresql_host,
            postgresqlDatabase=postgresql_database,
            postgresqlParams=postgresql_params,
            service=Service(port=postgresql_port),
        )
    )

    configmaps = template.render(helm_values)

    assert len(configmaps) == 1

    instance = yaml.full_load(configmaps[0].data["dagster.yaml"])

    assert instance[storage]

    postgres_db = instance[storage]["config"]["postgres_db"]

    assert postgres_db["username"] == postgresql_username
    assert postgres_db["password"] == {"env": "DAGSTER_PG_PASSWORD"}
    assert postgres_db["hostname"] == postgresql_host
    assert postgres_db["db_name"] == postgresql_database
    assert postgres_db["port"] == postgresql_port
    assert postgres_db["params"] == postgresql_params


@pytest.mark.parametrize("enabled", [True, False])
def test_run_coordinator_config(template: HelmTemplate, enabled: bool):
    module_name = "dagster.core.run_coordinator"
    class_name = "QueuedRunCoordinator"

    helm_values = DagsterHelmValues.construct(
        dagsterDaemon=Daemon.construct(
            queuedRunCoordinator=QueuedRunCoordinator.construct(
                enabled=enabled, module=module_name, class_name=class_name
            )
        )
    )
    configmaps = template.render(helm_values)
    assert len(configmaps) == 1

    instance = yaml.full_load(configmaps[0].data["dagster.yaml"])

    assert ("run_coordinator" in instance) == enabled
    if enabled:
        assert instance["run_coordinator"]["module"] == module_name
        assert instance["run_coordinator"]["class"] == class_name


@pytest.mark.parametrize(
    argnames=["json_schema_model", "compute_log_manager_class"],
    argvalues=[
        (AzureBlobComputeLogManagerModel, AzureBlobComputeLogManager),
        (GCSComputeLogManagerModel, GCSComputeLogManager),
        (S3ComputeLogManagerModel, S3ComputeLogManager),
    ],
)
def test_compute_log_manager_has_schema(json_schema_model, compute_log_manager_class):
    json_schema_fields = json_schema_model.schema()["properties"].keys()
    compute_log_manager_fields = set(
        map(to_camel_case, compute_log_manager_class.config_type().keys())
    )

    assert json_schema_fields == compute_log_manager_fields
