{{/* vim: set filetype=mustache: */}}
{{/*
Expand the name of the chart.
*/}}
{{- define "dagster.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "dagster.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- if contains $name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end -}}

# Dagit image e.g. repo/foo:bar
{{- define "dagster.dagit_image" -}}
{{ required "Dagit image repository .Values.dagit.image.repository is required" .Values.dagit.image.repository -}}
:
{{- required "Dagit image tag .Values.dagit.image.tag is required" .Values.dagit.image.tag }}
{{- end -}}

# Dagster Celery worker image e.g. repo/foo:bar
{{- define "dagster.celery_image" -}}
{{ required "Celery worker image repository .Values.celery.image.repository is required" .Values.celery.image.repository -}}
:
{{- required "Celery worker image tag .Values.celery.image.tag is required" .Values.celery.image.tag }}
{{- end -}}

# Dagster job image e.g. repo/foo:bar
{{- define "dagster.pipeline_run_image" -}}
{{ required "Pipeline run image repository .Values.pipeline_run.image.repository is required" .Values.pipeline_run.image.repository -}}
:
{{- required "Pipeline run image tag .Values.pipeline_run.image.tag is required" .Values.pipeline_run.image.tag }}
{{- end -}}


{{- define "dagster.dagit.fullname" -}}
{{- $name := default "dagit" .Values.dagit.nameOverride -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "dagster.dagit.dagster_home" -}}
{{- if .Values.dagit.dagster_home -}}
{{ .Values.dagit.dagster_home }}
{{- else -}}
{{ .Values.dagster_home }}
{{- end -}}
{{- end -}}

{{- define "dagster.celery.dagster_home" -}}
{{- if .Values.celery.dagster_home -}}
{{ .Values.celery.dagster_home }}
{{- else -}}
{{ .Values.dagster_home }}
{{- end -}}
{{- end -}}

{{- define "dagster.pipeline_run.dagster_home" -}}
{{- if .Values.pipeline_run.dagster_home -}}
{{ .Values.pipeline_run.dagster_home }}
{{- else -}}
{{ .Values.dagster_home }}
{{- end -}}
{{- end -}}

{{- define "dagster.workers.fullname" -}}
{{- $name := default "celery-workers" .Values.celery.workers.nameOverride -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "dagster.flower.fullname" -}}
{{- $name := default "flower" .Values.flower.nameOverride -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "dagster.rabbitmq.fullname" -}}
{{- $name := default "rabbitmq" .Values.rabbitmq.nameOverride -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Create a default fully qualified postgresql name or use the `postgresqlHost` value if defined.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
*/}}
{{- define "dagster.postgresql.fullname" -}}
{{- if .Values.postgresql.postgresqlHost }}
    {{- .Values.postgresql.postgresqlHost -}}
{{- else }}
    {{- $name := default "postgresql" .Values.postgresql.nameOverride -}}
    {{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "dagster.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Common labels
*/}}
{{- define "dagster.labels" -}}
helm.sh/chart: {{ include "dagster.chart" . }}
{{ include "dagster.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{/*
Selector labels
*/}}
{{- define "dagster.selectorLabels" -}}
app.kubernetes.io/name: {{ include "dagster.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{/*
Create the name of the service account to use
*/}}
{{- define "dagster.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
    {{ default (include "dagster.fullname" .) .Values.serviceAccount.name }}
{{- else -}}
    {{ default "default" .Values.serviceAccount.name }}
{{- end -}}
{{- end -}}

{{/*
Set postgres host
See: https://github.com/helm/charts/blob/61c2cc0db49b06b948f90c8e44e9143d7bab430d/stable/sentry/templates/_helpers.tpl#L59-L68
*/}}
{{- define "dagster.postgresql.host" -}}
{{- if .Values.postgresql.enabled -}}
{{- template "dagster.postgresql.fullname" . -}}
{{- else -}}
{{- .Values.postgresql.postgresqlHost | quote -}}
{{- end -}}
{{- end -}}

{{/*
Celery options
*/}}
{{- define "dagster.celery.broker_url" -}}
{{- if .Values.rabbitmq.enabled -}}
"pyamqp://{{ .Values.rabbitmq.rabbitmq.username }}:{{ .Values.rabbitmq.rabbitmq.password }}@{{ include "dagster.rabbitmq.fullname" . }}:{{ .Values.rabbitmq.service.port }}//"
{{- else if .Values.redis.enabled -}}
"redis://{{ .Values.redis.host }}:{{ .Values.redis.port }}/{{ .Values.redis.brokerDbNumber | default 0}}"
{{- end -}}
{{- end -}}

{{- define "dagster.celery.backend_url" -}}
{{- if .Values.rabbitmq.enabled -}}
"amqp"
{{- else if .Values.redis.enabled -}}
"redis://{{ .Values.redis.host }}:{{ .Values.redis.port }}/{{ .Values.redis.backendDbNumber | default 0}}"
{{- end -}}
{{- end -}}