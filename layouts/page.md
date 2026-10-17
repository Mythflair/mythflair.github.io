# {{ .Title }}

{{ with .OutputFormats.Get "HTML" -}}
Canonical: {{ .Permalink }}
{{ end -}}
Language: {{ .Language.Locale }}
{{ range first 1 (.GetTerms "categories") -}}
Category: {{ .LinkTitle }}
{{ end -}}
{{ if not .PublishDate.IsZero -}}
Published: {{ .PublishDate.Format "2006-01-02T15:04:05Z07:00" }}
{{ end -}}
{{ if not .Lastmod.IsZero -}}
Updated: {{ .Lastmod.Format "2006-01-02T15:04:05Z07:00" }}
{{ end }}
{{ with .Description }}{{ . }}

{{ end -}}
{{ .RenderShortcodes }}
