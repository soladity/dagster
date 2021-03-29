from typing import List

from pydantic import BaseModel, Field  # pylint: disable=no-name-in-module

from ..dagster_user_deployments.subschema.user_deployments import UserDeployments
from ..utils import kubernetes
from . import subschema


class DagsterHelmValues(BaseModel):
    """
    Schema for Helm values.
    """

    dagit: subschema.Dagit
    dagsterUserDeployments: UserDeployments = Field(..., alias="dagster-user-deployments")
    postgresql: subschema.PostgreSQL
    generatePostgresqlPasswordSecret: bool
    rabbitmq: subschema.RabbitMQ
    redis: subschema.Redis
    flower: subschema.Flower
    ingress: subschema.Ingress
    imagePullSecrets: List[kubernetes.SecretRef]
    computeLogManager: subschema.ComputeLogManager
    scheduler: subschema.Scheduler
    runLauncher: subschema.RunLauncher
    dagsterDaemon: subschema.Daemon
    busybox: subschema.Busybox
    migrate: subschema.Migrate
    serviceAccount: subschema.ServiceAccount
    global_: subschema.Global = Field(..., alias="global")
