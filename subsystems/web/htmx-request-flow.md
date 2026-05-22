# HTMX Request Flow

This guide defines the request-flow rules for HTMX-enhanced routes in `internal/web`.

Use it when a handler needs to choose between full-page rendering, fragment rendering, boosted navigation behavior, or multi-region updates.

## Required

- Parse HTMX headers into a typed request context.
- Keep every HTMX route backed by an ordinary browser route.
- Use the same service calls and view builders for full-page and fragment paths.
- Return full pages for normal requests.
- Return fragments only when the request context calls for a fragment response.
- Preserve direct-link, refresh, and back/forward behavior.
- Use out-of-band swaps only when one response must intentionally update multiple regions.

## Request Context

Use one request context type for web handlers.

```go
type RequestContext struct {
	IsHTMX    bool
	Boosted   bool
	Target    string
	Trigger   string
	CurrentURL string
}

func ParseRequestContext(
	r *http.Request,
) RequestContext {
	return RequestContext{
		IsHTMX:    r.Header.Get("HX-Request") == "true",
		Boosted:   r.Header.Get("HX-Boosted") == "true",
		Target:    r.Header.Get("HX-Target"),
		Trigger:   r.Header.Get("HX-Trigger"),
		CurrentURL: r.Header.Get("HX-Current-URL"),
	}
}
```

Most handlers only need `IsHTMX`. Keeping the rest typed avoids scattered ad hoc header reads when a route later needs target-aware behavior.

## Read Flow

Read handlers usually follow this shape:

1. parse path and query inputs
2. load service state
3. build view models
4. return the target fragment for HTMX requests
5. return a full page for normal requests

```go
func (w *Web) handleShowDocument(
	rw http.ResponseWriter,
	r *http.Request,
) {
	req := ParseRequestContext(r)
	id := r.PathValue("document_id")

	doc, err := w.service.GetDocument(id)
	if err != nil {
		w.writeError(rw, err)
		return
	}

	view := NewDocumentDetailView(*doc)
	if req.IsHTMX {
		w.renderer.RenderDocumentDetail(rw, view)
		return
	}

	page := NewDocumentsPageViewWithDetail(view)
	w.renderer.RenderDocumentsPage(rw, page)
}
```

The normal request path should render the same detail content in the page that the HTMX path would swap into the page.

## Mutation Flow

Mutation handlers usually follow this shape:

1. parse and validate form input
2. render validation state when input is invalid
3. call the service when input is valid
4. redirect for normal requests
5. re-fetch affected state for HTMX requests
6. render the smallest authoritative container

Do not build mutation responses from guessed client-side state. Re-read the service state that defines the visible result.

Read `./forms-and-mutations.md` for validation and flash-message details.

## Fragment Targets

Use stable IDs for replaceable regions.

```html
<section id="document-detail">
  {{template "documents.detail" .Detail}}
</section>
```

If a request uses `hx-target="#document-detail"` with `hx-swap="outerHTML"`, return a fragment rooted at `id="document-detail"`.

```html
{{define "documents.detail"}}
<section id="document-detail">
  <h2>{{.Title}}</h2>
  <p>{{.UpdatedText}}</p>
</section>
{{end}}
```

This keeps repeated swaps stable.

## Out-Of-Band Updates

Use out-of-band swaps when one action must update more than one independent region, such as a list, a detail panel, and a flash message.

Keep OOB responses intentional and small. If many regions must change after most mutations, consider whether a larger containing region should be the stable target instead.

## Boosted Navigation

Treat boosted requests as enhanced navigation of ordinary links or forms.

The destination must still work as a normal page. When boosted behavior needs a partial response, keep the branch explicit in the handler or renderer method and reuse the same view models as the full-page path.
