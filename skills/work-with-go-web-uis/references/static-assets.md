# Static Assets

This guide defines the default static asset shape for `internal/web`.

Use it when adding CSS, small JavaScript enhancement code, or static file serving for a server-rendered web UI.

## Required

- Keep static web assets under `internal/web/static/`.
- Use plain CSS in `static/styles.css`.
- Do not add a frontend build step by default.
- Prefer semantic class names and ordinary cascade structure.
- Keep JavaScript optional and small.
- Do not move domain state, rendering decisions, or mutation behavior into browser-side code.
- Serve assets from the web router or production server without coupling them to service behavior.

## File Shape

```text
internal/web/
  static/
    styles.css
    app.js
```

Only add `app.js` when the UI has enhancement behavior that HTML, CSS, and HTMX attributes do not cover cleanly.

## CSS Shape

Use plain CSS with readable selectors.

```css
:root {
  color-scheme: light dark;
}

body {
  margin: 0;
  font-family: system-ui, sans-serif;
}

.document-list {
  display: grid;
  gap: 0.5rem;
}

.document-row[aria-current="page"] {
  font-weight: 600;
}
```

Prefer classes that describe UI roles over classes that encode every individual visual declaration. Use the cascade intentionally so markup stays readable.

## JavaScript Shape

Use JavaScript for enhancement only, such as:

- focusing a field after a swap
- wiring a small browser-only affordance
- integrating a native browser API
- reinitializing a local behavior after HTMX replaces a region

Do not use JavaScript as the source of truth for resource state. The server-rendered HTML should remain the visible representation of service state.

## Serving Assets

Serve static files through a narrow route.

```go
func (w *Web) mountStaticRoutes(
	mux *http.ServeMux,
) {
	files := http.FileServer(http.FS(staticFS))
	mux.Handle("GET /static/", http.StripPrefix("/static/", files))
}
```

Keep asset serving separate from resource handlers.

## Cache Behavior

Use simple cache behavior until the project has a real need for fingerprinting or long-lived immutable assets.

If cache headers are added, keep them at the static-file serving boundary. Do not introduce a build pipeline only to solve cache busting for a small server-rendered UI.
