# Defining a Web UI

This guide defines the default shape for a server-rendered browser UI in `internal/web`.

Use it when a Go service binary needs to expose a small web interface alongside a CLI, JSON API, background worker, or other server-side surface.

The web package owns the browser-facing HTML surface. It defines UI route composition, handlers, typed view models, renderer methods, `html/template` templates, HTMX request handling, form responses, flash messages, and static assets. Keep domain behavior in `internal/service`, JSON API contracts in `internal/api`, and production mounting in `internal/server`.

If the UI needs logged-in users, account-scoped routes, or CSRF-protected Consent cookies, consult [`work-with-consent-users`](../../work-with-consent-users/SKILL.md) before shaping the web constructor and auth context.

## Contents

- [Required](#required)
- [Canonical Package Shape](#canonical-package-shape)
- [Constructor Pattern](#constructor-pattern)
- [Canonical Flow](#canonical-flow)
- [Canonical Resource File](#canonical-resource-file)
- [Template And HTMX Shape](#template-and-htmx-shape)
- [Static Assets](#static-assets)
- [Testing Expectations](#testing-expectations)
- [Related Guides](#related-guides)

## Required

- Use `internal/web` for the server-rendered browser UI.
- Render HTML on the server with `html/template`.
- Use HTMX as progressive enhancement, not as a separate client application.
- Keep every interactive flow usable through ordinary browser navigation or form submission.
- Treat the service as the source of truth and re-render from service state after writes.
- Keep handlers thin: parse request shape, call the service, build views, and render.
- Keep UI behavior local by grouping handlers, views, forms, and resource render methods in resource-scoped files.
- Return `http.Handler` from resource route-group builders.
- Mount child route groups with `wire.Subrouter`.
- Use typed view models between service data and templates.
- Keep templates declarative and move display formatting into Go view builders.
- Keep one renderer boundary so handlers call renderer methods, not template names directly.
- Use plain CSS in `static/styles.css` and no frontend build step by default.
- Use JavaScript only for small enhancement behavior that server-rendered HTML cannot express cleanly.

## Canonical Package Shape

Use resource-scoped files by default:

```text
internal/web/
  web.go
  router.go
  renderer.go
  context.go
  forms.go
  flash.go
  documents.go
  settings.go
  templates/
    layout.html
    documents.html
    settings.html
  static/
    styles.css
    app.js
```

The ownership split should stay clear:

- `web.go` owns `Web`, `Options`, and `New(...)`.
- `router.go` owns top-level UI route composition and subtree mounting.
- `renderer.go` owns template parsing, shared render helpers, and the renderer type.
- `context.go` owns request context parsing, including HTMX headers.
- `forms.go` owns shared form validation primitives.
- `flash.go` owns shared status-message primitives.
- resource files own mountable route-group builders, handlers, view models, form state, and resource-specific renderer methods.
- `templates/` holds layouts and named fragments.
- `static/` holds plain CSS and optional small enhancement JavaScript.

Resource files keep UI behavior near the markup and view state it changes. They should still use the same package-level request context, renderer, form, flash, and template conventions as the rest of `internal/web`.

## Constructor Pattern

The web package receives the service and any UI-specific dependencies.

```go
package web

import (
	"errors"
	"html/template"
	"net/http"

	"example/internal/service"
	"git.sr.ht/~jakintosh/command-go/pkg/wire"
)

type Options struct {
	Service *service.Service
}

type Web struct {
	service  *service.Service
	renderer *Renderer
}

func New(
	opts Options,
) (
	*Web,
	error,
) {
	if opts.Service == nil {
		return nil, errors.New("web: service required")
	}

	renderer, err := NewRenderer()
	if err != nil {
		return nil, err
	}

	return &Web{
		service:  opts.Service,
		renderer: renderer,
	}, nil
}

type Renderer struct {
	templates *template.Template
}

func NewRenderer() (
	*Renderer,
	error,
) {
	tmpl, err := template.ParseFS(templateFS, "templates/*.html")
	if err != nil {
		return nil, err
	}
	return &Renderer{templates: tmpl}, nil
}

func (w *Web) Router() http.Handler {
	root := http.NewServeMux()
	wire.Subrouter(root, "/documents", w.buildDocumentRouter())
	wire.Subrouter(root, "/settings", w.buildSettingsRouter())
	return root
}
```

This keeps construction explicit and lets `internal/server` decide where the web UI is mounted in the process route tree.

## Canonical Flow

The normal read flow is:

1. parse path and query inputs
2. load domain state through the service
3. build typed view models
4. parse request context
5. render a full page for normal requests
6. render a fragment for HTMX requests

The normal mutation flow is:

1. parse submitted form inputs
2. validate request-local shape
3. render the form with validation state when input is invalid
4. call the service when input is valid
5. redirect after success for normal requests
6. re-fetch affected state after success for HTMX requests
7. render the smallest authoritative container, plus flash/status fragments when needed

This preserves direct links, refreshes, browser back and forward behavior, and no-JavaScript operation.

## Canonical Resource File

A resource file may keep the route-group builder, handlers, views, forms, and local render methods together.

```go
package web

import (
	"net/http"

	"example/internal/service"
)

type DocumentRowView struct {
	ID         string
	Title      string
	DetailURL  string
	IsSelected bool
}

func NewDocumentRowView(
	doc service.Document,
	selectedID string,
) DocumentRowView {
	return DocumentRowView{
		ID:         doc.ID,
		Title:      doc.Title,
		DetailURL:  "/documents/" + doc.ID,
		IsSelected: doc.ID == selectedID,
	}
}

type DocumentListView struct {
	Rows []DocumentRowView
}

func NewDocumentListView(
	docs []service.Document,
	selectedID string,
) DocumentListView {
	rows := make([]DocumentRowView, 0, len(docs))
	for _, doc := range docs {
		row := NewDocumentRowView(doc, selectedID)
		rows = append(rows, row)
	}

	return DocumentListView{
		Rows: rows,
	}
}

type DocumentsPageView struct {
	List  DocumentListView
	Form  DocumentFormView
	Flash *FlashView
}

func NewDocumentsPageView(
	list DocumentListView,
	form DocumentFormView,
	flash *FlashView,
) DocumentsPageView {
	return DocumentsPageView{
		List:  list,
		Form:  form,
		Flash: flash,
	}
}

func (r *Renderer) RenderDocumentsPage(
	rw http.ResponseWriter,
	view DocumentsPageView,
) {
	r.execute(rw, "documents.page", view)
}

func (r *Renderer) RenderDocumentList(
	rw http.ResponseWriter,
	view DocumentListView,
) {
	r.execute(rw, "documents.list", view)
}

func (r *Renderer) RenderDocumentListUpdate(
	rw http.ResponseWriter,
	list DocumentListView,
	flash *FlashView,
) {
	r.execute(rw, "documents.list", list)
	r.execute(rw, "flash.oob", flash)
}

func (w *Web) buildDocumentRouter() http.Handler {
	mux := http.NewServeMux()

	mux.HandleFunc("GET /", w.handleListDocuments)
	mux.HandleFunc("GET /{document_id}", w.handleShowDocument)
	mux.HandleFunc("POST /", w.handleCreateDocument)

	return mux
}

func (w *Web) handleListDocuments(
	rw http.ResponseWriter,
	r *http.Request,
) {
	// parse request
	req := ParseRequestContext(r)

	// call model
	docs, err := w.service.ListDocuments()
	if err != nil {
		w.writeError(rw, err)
		return
	}

	// build fragment
	list := NewDocumentListView(docs, "")
	if req.IsHTMX {
		w.renderer.RenderDocumentList(rw, list)
		return
	}

	// build page
	form := DocumentFormView{
		SubmitLabel: "Create document",
	}
	page := NewDocumentsPageView(list, form, nil)
	w.renderer.RenderDocumentsPage(rw, page)
}

func (w *Web) handleCreateDocument(
	rw http.ResponseWriter,
	r *http.Request,
) {
	// parse request
	req := ParseRequestContext(r)
	form := ParseDocumentForm(r)
	if !form.Validate() {
		w.renderer.RenderDocumentForm(rw, form.View())
		return
	}

	// call model
	if _, err := w.service.CreateDocument(form.Title); err != nil {
		w.writeError(rw, err)
		return
	}

	// handle full redirect
	if !req.IsHTMX {
		http.Redirect(rw, r, "/documents", http.StatusSeeOther)
		return
	}

	// handle fragment rendering
	docs, err := w.service.ListDocuments()
	if err != nil {
		w.writeError(rw, err)
		return
	}

	list := NewDocumentListView(docs, "")
	flash := NewFlashView("Document created.")
	w.renderer.RenderDocumentListUpdate(rw, list, flash)
}
```

This is the default feel to preserve:

- the resource route group is visible
- the root router mounts the resource subtree with `wire.Subrouter`
- direct registrations stay local to the resource route-group builder
- handlers orchestrate one request each
- fragment renderers receive the region view they render
- page views compose the same region views used by fragment renderers
- invalid form state renders immediately
- successful normal form submissions redirect
- successful HTMX mutations re-fetch state and render explicit update responses

Read `./view-models.md` when shaping display-ready data. Read `./forms-and-mutations.md` when implementing validation, form state, redirects, HTMX mutation responses, or flash messages.

## Template And HTMX Shape

Templates should render ordinary HTML first and add HTMX attributes to improve the same route.

Use stable IDs on replaceable containers:

```html
{{define "documents.list"}}
<section id="documents-list">
  {{range .Rows}}
    <a href="{{.DetailURL}}" hx-get="{{.DetailURL}}" hx-target="#document-detail">
      {{.Title}}
    </a>
  {{else}}
    <p>No documents yet.</p>
  {{end}}
</section>
{{end}}
```

When using `hx-swap="outerHTML"`, return a fragment with the same root element ID as the target being replaced. Use out-of-band swaps only when one request must intentionally update multiple independent regions.

Read `./renderer-and-templates.md` for renderer methods, template naming, fragment roots, and out-of-band swaps. Read `./htmx-request-flow.md` for request context and full-page/fragment parity.

## Static Assets

Serve static assets from `static/`.

Use plain CSS in `static/styles.css` by default. Prefer a small set of semantic classes and ordinary cascade structure over many single-purpose utility classes. Add `static/app.js` only when a small enhancement cannot be expressed clearly with HTML, CSS, or HTMX attributes.

Read `./static-assets.md` before adding client-side behavior or asset build tooling.

## Testing Expectations

Web UI tests should make it easy to verify:

- route handlers choose the correct full-page or fragment response
- ordinary form submissions redirect on success
- HTMX form submissions re-render authoritative HTML from service state
- invalid forms render submitted values and validation messages
- view builders produce display-ready labels, URLs, and formatted values
- renderer methods execute the expected full-page and fragment templates

Use `httptest` and focused response assertions by default. Do not add HTML parsing dependencies unless a project already has one and the extra structure is clearly worth it.

Read `./testing.md` for focused web UI test shape.

## Related Guides

- Read [`work-with-go-services`](../../work-with-go-services/SKILL.md) for domain behavior and service contracts.
- Read [`work-with-go-servers`](../../work-with-go-servers/SKILL.md) for mounting the web router into the production serving stack.
- Read [`work-with-consent-users`](../../work-with-consent-users/SKILL.md) when the web UI needs Consent-backed accounts, login/logout links, or account-scoped mutations.
- Read [`work-with-go-http-apis`](../../work-with-go-http-apis/SKILL.md) when the same application also exposes JSON HTTP endpoints.
- Read [`compose-go-http-routes`](../../compose-go-http-routes/SKILL.md) when composing route trees across packages.
