{{- define "dagsterYaml.runLauncher.celery" }}
{{- $celeryK8sRunLauncherConfig := .Values.runLauncher.config.celeryK8sRunLauncher }}
module: dagster_celery_k8s
class: CeleryK8sRunLauncher
config:
  dagster_home:
    env: DAGSTER_HOME
  instance_config_map:
    env: DAGSTER_K8S_INSTANCE_CONFIG_MAP
  postgres_password_secret:
    env: DAGSTER_K8S_PG_PASSWORD_SECRET
  broker: {{ include "dagster.celery.broker_url" . | quote }}
  backend: {{ include "dagster.celery.backend_url" . | quote}}

  {{- if $celeryK8sRunLauncherConfig.configSource }}
  config_source: {{- $celeryK8sRunLauncherConfig.configSource | toYaml | nindent 4 }}
  {{- end }}
{{- end }}

{{- define "dagsterYaml.runLauncher.k8s" }}
{{- $k8sRunLauncherConfig := .Values.runLauncher.config.k8sRunLauncher }}
module: dagster_k8s
class: K8sRunLauncher
config:
  load_incluster_config: {{ $k8sRunLauncherConfig.loadInclusterConfig }}

  {{- if $k8sRunLauncherConfig.kubeconfigFile }}
  kubeconfig_file: {{ $k8sRunLauncherConfig.kubeconfigFile }}
  {{- end }}
  job_namespace: {{ $k8sRunLauncherConfig.jobNamespace | default .Release.Namespace }}

  {{- if .Values.imagePullSecrets }}
  image_pull_secrets: {{- .Values.imagePullSecrets | toYaml | nindent 10 }}
  {{- end }}
  service_account_name: {{ include "dagster.serviceAccountName" . }}

  {{- if (hasKey $k8sRunLauncherConfig "image") }}
  job_image: {{ include "image.name" $k8sRunLauncherConfig.image | quote }}
  image_pull_policy: {{ $k8sRunLauncherConfig.image.pullPolicy }}
  {{- end }}
  dagster_home:
    env: DAGSTER_HOME
  instance_config_map:
    env: DAGSTER_K8S_INSTANCE_CONFIG_MAP
  postgres_password_secret:
    env: DAGSTER_K8S_PG_PASSWORD_SECRET
  env_config_maps:
    - env: DAGSTER_K8S_PIPELINE_RUN_ENV_CONFIGMAP
    {{- range $name := $k8sRunLauncherConfig.envConfigMaps }}
    {{- if $name }}
    - {{ $name }}
    {{- end }}
    {{- end }}

  {{- if $k8sRunLauncherConfig.envSecrets }}
  env_secrets:
    {{- range $name := $k8sRunLauncherConfig.envSecrets }}
    {{- if $name }}
    - {{ $name }}
    {{- end }}
    {{- end }}
  {{- end }}
{{- end }}

{{- define "dagsterYaml.runLauncher.custom" }}
{{- $customRunLauncherConfig := .Values.runLauncher.config.customRunLauncher }}
module: {{ $customRunLauncherConfig.module | quote }}
class: {{ $customRunLauncherConfig.class | quote }}
config: {{ $customRunLauncherConfig.config | toYaml | nindent 2 }}
{{- end }}
