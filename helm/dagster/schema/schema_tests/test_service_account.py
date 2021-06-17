import subprocess

import pytest
from kubernetes.client import models
from schema.charts.dagster.subschema.global_ import Global
from schema.charts.dagster.subschema.service_account import ServiceAccount
from schema.charts.dagster.values import DagsterHelmValues

from .helm_template import HelmTemplate


@pytest.fixture(name="template")
def umbrella_helm_template() -> HelmTemplate:
    return HelmTemplate(
        output="templates/serviceaccount.yaml",
        model=models.V1ServiceAccount,
    )


@pytest.fixture(name="subchart_template")
def subchart_helm_template() -> HelmTemplate:
    return HelmTemplate(
        output="charts/dagster-user-deployments/templates/serviceaccount.yaml",
        model=models.V1ServiceAccount,
    )


def test_service_account_name(template: HelmTemplate):
    service_account_name = "service-account-name"
    service_account_values = DagsterHelmValues.construct(
        serviceAccount=ServiceAccount.construct(name=service_account_name, create=True)
    )

    service_account_templates = template.render(service_account_values)

    assert len(service_account_templates) == 1

    service_account_template = service_account_templates[0]

    assert service_account_template.metadata.name == service_account_name


def test_service_account_global_name(template: HelmTemplate):
    global_service_account_name = "global-service-account-name"
    service_account_values = DagsterHelmValues.construct(
        global_=Global.construct(serviceAccountName=global_service_account_name),
    )

    service_account_templates = template.render(service_account_values)

    assert len(service_account_templates) == 1

    service_account_template = service_account_templates[0]

    assert service_account_template.metadata.name == global_service_account_name


def test_subchart_service_account_global_name(subchart_template: HelmTemplate, capsys):
    with pytest.raises(subprocess.CalledProcessError):
        global_service_account_name = "global-service-account-name"
        service_account_values = DagsterHelmValues.construct(
            global_=Global.construct(serviceAccountName=global_service_account_name),
        )

        subchart_template.render(service_account_values)

        _, err = capsys.readouterr()

        assert "Error: could not find template" in err


def test_service_account_does_not_render(template: HelmTemplate, capsys):
    with pytest.raises(subprocess.CalledProcessError):
        service_account_values = DagsterHelmValues.construct(
            serviceAccount=ServiceAccount.construct(name="service-account-name", create=False),
        )

        template.render(service_account_values)

        _, err = capsys.readouterr()

        assert "Error: could not find template" in err


def test_service_account_annotations(template: HelmTemplate):
    service_account_name = "service-account-name"
    service_account_annotations = {"hello": "world"}
    service_account_values = DagsterHelmValues.construct(
        serviceAccount=ServiceAccount.construct(
            name=service_account_name, create=True, annotations=service_account_annotations
        )
    )

    service_account_templates = template.render(service_account_values)

    assert len(service_account_templates) == 1

    service_account_template = service_account_templates[0]

    assert service_account_template.metadata.name == service_account_name
    assert service_account_template.metadata.annotations == service_account_annotations
