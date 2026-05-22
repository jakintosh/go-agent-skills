# Testing Web UI

This guide defines the default test shape for server-rendered web UI in `internal/web`.

Use it when testing web route behavior, HTMX branches, form validation, view models, renderer contracts, or static serving.

## Required

- Use standard-library test tools by default.
- Test handlers with `httptest`.
- Test full-page and HTMX response paths for routes that support both.
- Test mutation handlers for redirect behavior, validation behavior, and authoritative HTMX re-rendering.
- Test view builders directly for display-ready values.
- Test stable rendering contracts, not incidental layout.
- Use renderer smoke tests sparingly to prove important templates still execute.
- Prefer direct view and handler tests over exhaustive rendered-markup tests.
- Do not add HTML parsing dependencies by default.

## Testing Strategy

Do not test every rendered view response by default. Server-rendered markup changes often, and tests that encode ordinary layout details become expensive without proving much behavior.

Prefer this order:

1. test view builders for display-ready data
2. test form parsers and validation directly
3. test handlers for branching, status codes, redirects, service effects, and HTMX versus non-HTMX behavior
4. test renderer output only where the markup is a stable integration contract
5. use a small number of smoke tests to catch broken template names or missing data paths

Stable rendering contracts include fragment root IDs, form actions, HTTP status behavior, redirect locations, out-of-band swap roots, and user-visible validation or status messages. They do not include ordinary layout wrappers, spacing elements, class names, or the exact order of unrelated markup.

## Handler Tests

Handler tests should exercise the built router when route wiring matters.

```go
func TestCreateDocument_HTMXRerendersList(t *testing.T) {
	web := newTestWeb(t)
	req := httptest.NewRequest(http.MethodPost, "/documents", strings.NewReader("title=Guide"))
	req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
	req.Header.Set("HX-Request", "true")
	req.Header.Set("HX-Target", "documents-list")

	rec := httptest.NewRecorder()
	web.Router().ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Fatalf("status = %d, want %d", rec.Code, http.StatusOK)
	}
	body := rec.Body.String()
	if !strings.Contains(body, `id="documents-list"`) {
		t.Fatalf("body does not contain documents list target:\n%s", body)
	}
	if !strings.Contains(body, "Guide") {
		t.Fatalf("body does not contain created document:\n%s", body)
	}
}
```

Use small test services or in-memory stores when they make the visible behavior clearer than mocks.

Handler tests should not prove the full layout. They should prove the response behavior that would break the user flow: the route is reachable, the handler chooses the right response family, mutations reach the service, and HTMX responses include the stable target that will be swapped.

## Non-HTMX Mutation Tests

Successful ordinary form submissions should redirect.

```go
func TestCreateDocument_RedirectsAfterSuccess(t *testing.T) {
	web := newTestWeb(t)
	req := httptest.NewRequest(http.MethodPost, "/documents", strings.NewReader("title=Guide"))
	req.Header.Set("Content-Type", "application/x-www-form-urlencoded")

	rec := httptest.NewRecorder()
	web.Router().ServeHTTP(rec, req)

	if rec.Code != http.StatusSeeOther {
		t.Fatalf("status = %d, want %d", rec.Code, http.StatusSeeOther)
	}
	if got := rec.Header().Get("Location"); got != "/documents" {
		t.Fatalf("location = %q, want %q", got, "/documents")
	}
}
```

This proves the no-JavaScript path remains a normal browser flow.

## Validation Tests

Invalid form tests should verify:

- status code
- parsed submitted values are preserved in the form view
- field or form-level messages are present
- the service mutation was not called

Test form parsing and validation directly when possible. Use a rendered response assertion only for the small visible contract the browser depends on, such as the field error text or the form region being returned.

## View Builder Tests

Test view builders without HTTP when the behavior is pure presentation mapping.

```go
func TestNewDocumentRowView(t *testing.T) {
	doc := service.Document{
		ID:    "doc-1",
		Title: "Guide",
	}

	view := NewDocumentRowView(doc, "doc-1")

	if view.DetailURL != "/documents/doc-1" {
		t.Fatalf("detail url = %q", view.DetailURL)
	}
	if !view.IsSelected {
		t.Fatalf("row should be selected")
	}
}
```

These tests are cheap and catch drift in URLs, labels, formatting, and selected state.

## Renderer Tests

Renderer tests are useful when a template or fragment is part of a stable contract. They should not become a snapshot suite for every page.

Use a `httptest.ResponseRecorder` or `bytes.Buffer` through the renderer method. Check the few strings or headers that define the contract, such as the root fragment ID, form action, or status message.

Good renderer assertions:

- a fragment response contains `id="documents-list"` when HTMX targets `#documents-list`
- an OOB response contains `hx-swap-oob="true"` on the expected flash region
- a form renders the expected `action` for the current resource
- a validation message appears in the form region

Weak renderer assertions:

- the full page contains every section in exact order
- a card, wrapper, or class name appears when it is only layout
- a test duplicates the template's full HTML structure

For large pages, prefer one smoke test that renders representative valid data without error, plus focused view-builder tests for the values the page displays.

## Request Context Tests

Test `ParseRequestContext(...)` directly.

```go
func TestParseRequestContext(t *testing.T) {
	req := httptest.NewRequest(http.MethodGet, "/documents", nil)
	req.Header.Set("HX-Request", "true")
	req.Header.Set("HX-Target", "documents-list")

	ctx := ParseRequestContext(req)

	if !ctx.IsHTMX {
		t.Fatalf("IsHTMX = false, want true")
	}
	if ctx.Target != "documents-list" {
		t.Fatalf("target = %q, want %q", ctx.Target, "documents-list")
	}
}
```

This keeps handler tests from needing to prove header parsing repeatedly.
