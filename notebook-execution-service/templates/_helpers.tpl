{{/* Chart name */}}
{{- define "notebook-execution-service.name" -}}
notebook-execution-service
{{- end -}}

{{/* Fully qualified name: <release>-<name> */}}
{{- define "notebook-execution-service.fullname" -}}
{{- printf "%s-%s" .Release.Name (include "notebook-execution-service.name" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/* Standard labels used across resources */}}
{{- define "notebook-execution-service.labels" -}}
app.kubernetes.io/name: {{ include "notebook-execution-service.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version | replace "+" "_" }}
{{- end -}}
