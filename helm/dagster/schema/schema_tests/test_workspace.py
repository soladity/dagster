import subprocess

import pytest
import yaml
from kubernetes.client import models
from schema.charts.dagster.subschema.dagit import Dagit, Server, Workspace
from schema.charts.dagster.values import DagsterHelmValues
from schema.charts.dagster_user_deployments.subschema.user_deployments import UserDeployments

from .helm_template import HelmTemplate
from .utils import create_simple_user_deployment


@pytest.fixture(name="template")
def helm_template() -> HelmTemplate:
    return HelmTemplate(
        output="templates/configmap-workspace.yaml",
        model=models.V1ConfigMap,
    )


def test_workspace_renders_fail(template: HelmTemplate, capsys):
    helm_values = DagsterHelmValues.construct(
        dagsterUserDeployments=UserDeployments(
            enabled=False,
            enableSubchart=True,
            deployments=[],
        )
    )

    with pytest.raises(subprocess.CalledProcessError):
        template.render(helm_values)

        _, err = capsys.readouterr()
        assert (
            "dagster-user-deployments subchart cannot be enabled if workspace.yaml is not created."
            in err
        )


def test_workspace_does_not_render(template: HelmTemplate, capsys):
    helm_values = DagsterHelmValues.construct(
        dagsterUserDeployments=UserDeployments(
            enabled=False,
            enableSubchart=False,
            deployments=[create_simple_user_deployment("deployment-one")],
        )
    )

    with pytest.raises(subprocess.CalledProcessError):
        template.render(helm_values)

        _, err = capsys.readouterr()
        assert "Error: could not find template" in err in err


def test_workspace_renders_from_helm_user_deployments(template: HelmTemplate):
    deployments = [
        create_simple_user_deployment("deployment-one"),
        create_simple_user_deployment("deployment-two"),
    ]
    helm_values = DagsterHelmValues.construct(
        dagsterUserDeployments=UserDeployments(
            enabled=True,
            enableSubchart=True,
            deployments=deployments,
        )
    )

    workspace_templates = template.render(helm_values)

    assert len(workspace_templates) == 1

    workspace_template = workspace_templates[0]

    workspace = yaml.full_load(workspace_template.data["workspace.yaml"])
    grpc_servers = workspace["load_from"]

    assert len(grpc_servers) == len(deployments)

    for grpc_server, deployment in zip(grpc_servers, deployments):
        assert grpc_server["grpc_server"]["host"] == deployment.name
        assert grpc_server["grpc_server"]["port"] == deployment.port
        assert grpc_server["grpc_server"]["location_name"] == deployment.name


def test_workspace_renders_from_helm_dagit(template: HelmTemplate):
    servers = [
        Server(host="another-deployment-one", port=4000),
        Server(host="another-deployment-two", port=4001),
        Server(host="another-deployment-three", port=4002),
    ]
    helm_values = DagsterHelmValues.construct(
        dagit=Dagit.construct(workspace=Workspace(enabled=True, servers=servers)),
        dagsterUserDeployments=UserDeployments(
            enabled=True,
            enableSubchart=True,
            deployments=[
                create_simple_user_deployment("deployment-one"),
                create_simple_user_deployment("deployment-two"),
            ],
        ),
    )

    workspace_templates = template.render(helm_values)

    assert len(workspace_templates) == 1

    workspace_template = workspace_templates[0]

    workspace = yaml.full_load(workspace_template.data["workspace.yaml"])
    grpc_servers = workspace["load_from"]

    assert len(grpc_servers) == len(servers)

    for grpc_server, server in zip(grpc_servers, servers):
        assert grpc_server["grpc_server"]["host"] == server.host
        assert grpc_server["grpc_server"]["port"] == server.port
        assert grpc_server["grpc_server"]["location_name"] == server.host
