# Renderer And Templates

This guide defines the renderer and template boundary for `internal/web`.

Use it when adding renderer methods, named templates, full-page layouts, fragments, or HTMX swap targets.

## Required

- Use `html/template`.
- Parse templates once during web construction.
- Keep one renderer type as the template execution boundary.
- Have handlers call renderer methods, not template names.
- Use full-page renderer methods for normal browser responses.
- Use fragment renderer methods for HTMX responses.
- Keep templates declarative.
- Use stable root IDs for replaceable fragments.
- Return the same root ID when replacing a target with `outerHTML`.

## Renderer Shape

`renderer.go` owns template parsing and shared execution helpers.

```go
type Renderer struct {
	templates *template.Template
}

func NewRenderer() (
	*Renderer,
	error,
) {
	tmpl, err := template.ParseFS(templateFS, "templates/*.html")
	if err != nil {
		return nil, fmt.Errorf("parse web templates: %w", err)
	}

	return &Renderer{templates: tmpl}, nil
}

func (r *Renderer) execute(
	w http.ResponseWriter,
	name string,
	data any,
) {
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	if err := r.templates.ExecuteTemplate(w, name, data); err != nil {
		http.Error(w, "render template", http.StatusInternalServerError)
	}
}
```

Resource files may define resource-specific renderer methods beside their handlers and views.

```go
func (r *Renderer) RenderDocumentsPage(
	w http.ResponseWriter,
	view DocumentsPageView,
) {
	r.execute(w, "documents.page", view)
}

func (r *Renderer) RenderDocumentList(
	w http.ResponseWriter,
	view DocumentsPageView,
) {
	r.execute(w, "documents.list", view)
}
```

This keeps template names out of handlers while preserving resource locality.

## Template Shape

Use named templates for pages and fragments.

```html
{{define "documents.page"}}
<!doctype html>
<html lang="en">
  <head>
    <title>Documents</title>
    <link rel="stylesheet" href="/static/styles.css">
  </head>
  <body>
    {{template "flash" .Flash}}
    {{template "documents.list" .}}
    {{template "documents.form" .Form}}
  </body>
</html>
{{end}}

{{define "documents.list"}}
<section id="documents-list">
  {{range .Rows}}
    {{template "documents.row" .}}
  {{else}}
    <p>No documents yet.</p>
  {{end}}
</section>
{{end}}
```

Templates should mostly contain:

- field reads
- simple conditionals
- ranges
- named-template composition
- ordinary links and forms
- HTMX attributes on ordinary links and forms

Move display formatting, URL assembly, status labels, and form state decisions into view models.

## Fragment Roots

Every HTMX target should have a stable root element.

```html
<section id="documents-list">
  ...
</section>
```

For `hx-swap="outerHTML"`, the returned fragment should include the same root ID.

For `hx-swap="innerHTML"`, the returned fragment should contain the target's children and leave the target itself in place.

Choose one swap style per region and keep it consistent unless the UI flow clearly needs a different behavior.

## Layouts

Keep full-page layout in templates. Keep request branching in handlers or renderer methods.

Do not hide full-page versus fragment decisions inside template complexity. A reader should be able to tell from the handler which response shape is being returned.

## Errors

Renderer methods should set `Content-Type` before executing templates. Projects may centralize render errors through a helper, but handlers should not ignore whether a render failed when the project needs explicit logging or observability.

Keep service-to-HTTP error translation outside templates.
