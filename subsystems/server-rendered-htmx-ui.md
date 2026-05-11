# Server-Rendered HTMX UI

This guide defines the standard shape for server-rendered HTML applications that use HTMX for fragment updates.

It focuses on the rendering flow, HTMX request handling, fragment strategy, and the boundaries between handlers, renderer methods, templates, and small enhancement code.

The goal is to make server-rendered UI:

- server-first and authoritative
- progressively enhanced instead of JS-dependent
- consistent across full-page and fragment flows
- easy to reason about during reads and mutations

## When to use this guide

Use this guide when you are:

- building a Go HTML UI that uses HTMX
- deciding how read and mutation handlers should behave for full-page and fragment requests
- defining renderer and template boundaries
- reviewing whether client-side code is taking over server responsibilities

## Non-goals

This guide does not define:

- detailed view-model mapping rules
- API-only JSON handler design
- general frontend styling choices
- SPA-style client state architecture

## Core rules

- Render HTML on the server and use HTMX for fragment updates.
- Keep progressive enhancement so every interaction has a non-HTMX fallback.
- Treat the server as the source of truth and re-render from domain state after writes.
- Keep client-side JavaScript minimal and focused on enhancement.
- Let handlers orchestrate, view builders shape data, and templates render.
- Keep one renderer boundary so handlers call renderer methods, not template names directly.
- Maintain both full-page render paths and fragment render paths.
- Break templates into reusable named fragments with stable replaceable IDs.
- Parse HTMX headers into a request-context struct.
- After mutations, prefer authoritative re-rendering of the smallest consistent container.
- Use out-of-band swaps intentionally when multiple regions must stay in sync.
- Add focused tests around render-path parity and view behavior.

## Canonical package shape

A good default UI package looks like:

```text
internal/app/
  server.go
  renderer.go
  context.go
  view_projects.go
  view_settings.go
  templates/
  static/
```

The important ownership split is:

- handlers in `server.go` orchestrate requests
- `renderer.go` owns parsed templates and render entry points
- `context.go` owns HTMX request parsing
- `view_*.go` files own presentation modules
- `templates/` holds declarative markup and fragments
- `static/` holds CSS and small enhancement JS

When a project also exposes a JSON API, `internal/server` should mount the UI router and `internal/api` router as separate route trees. The UI package may call `internal/service` directly for domain behavior, but API DTOs and JSON handlers should stay in `internal/api`.

## Rendering architecture

Maintain two coordinated render paths:

1. full-page rendering for normal browser navigation
2. fragment rendering for HTMX swaps

These paths should share the same underlying presentation logic.

For example, a details panel should support both:

- deep-link page rendering for a normal browser request
- fragment-only rendering for an HTMX request that swaps the detail region

This keeps direct links, refreshes, and boosted or non-boosted navigation aligned.

## Handler and renderer boundary

Handlers should not call template names directly.

Instead, the flow should be:

1. load domain state
2. build view model data
3. inspect request context
4. call a renderer method for the right response shape

For example:

```go
func (s *Server) handleProjectDetail(
	w http.ResponseWriter,
	r *http.Request,
) {
	reqCtx := ParseRequestContext(r)

	project, err := s.service.GetProject(r.PathValue("project_id"))
	if err != nil {
		s.writeError(w, err)
		return
	}

	view := NewProjectDetailView(project)

	if reqCtx.IsHTMX {
		s.renderer.RenderProjectDetail(w, view)
		return
	}

	pageView := ProjectPageView{
		Detail: view,
	}
	s.renderer.RenderProjectPage(w, pageView)
}
```

This keeps the handler focused on orchestration rather than template dispatch.

## HTMX request context

Parse HTMX headers into a request-context struct so handlers can branch cleanly.

A typical shape includes:

- whether the request is HTMX
- current URL
- target element
- trigger information
- whether the request was boosted

Most decisions may only need the HTMX boolean at first, but a typed context keeps later behavior and debugging cleaner than ad hoc header checks spread across handlers.

## Read-handler flow

Read handlers should usually:

1. load domain state
2. build view model data
3. return a fragment for HTMX requests
4. return a full page for non-HTMX requests

For detail views, keep deep-link parity by ensuring the non-HTMX path can render the same detail content already open or embedded in the page.

## Mutation-handler flow

Mutation handlers should usually:

1. parse and validate input
2. persist the change through the service
3. redirect on non-HTMX requests
4. re-fetch affected state
5. render authoritative HTML updates for HTMX requests

After writes, prefer to re-render the smallest consistent container rather than trying to patch many tiny DOM details from guessed client state.

This keeps the server authoritative and reduces drift between what the user sees and what actually persisted.

## Partial update strategy

Prefer authoritative re-rendering over incremental patch logic.

Good defaults:

- re-fetch server state after mutations
- re-render one stable list, panel, or detail container
- return OOB swaps only when two or more regions must update together

For example, if saving a project should update both the project list and the detail panel, return a multi-fragment response intentionally instead of hoping one region can infer the other.

## Template conventions

Templates should stay declarative.

They are a good place for:

- field reads
- simple conditionals
- named template composition
- HTMX attributes such as `hx-get`, `hx-post`, `hx-target`, and `hx-swap`

They are not a good place for:

- formatting-heavy presentation logic
- domain calculations
- transport branching hidden in template complexity

Use stable IDs on replaceable containers so targeted swaps remain reliable.

When using `hx-swap="outerHTML"`, return fragments with the same root element ID as the target being replaced.

## Static assets and JavaScript

Keep CSS and JS in `static/` and serve them directly.

Use JavaScript only for enhancement work such as:

- re-initializing UI affordances after swaps
- small interaction helpers
- DOM hooks that HTMX alone does not cover cleanly

Do not move core rendering or business state transitions into browser-side code when the server-rendered HTML can already represent the current truth.

## Progressive enhancement contract

Every interactive route should have both:

- a non-HTMX page or redirect flow
- an HTMX fragment or OOB flow

This gives robust behavior for:

- direct links
- bookmarks
- refreshes
- back and forward navigation
- temporary HTMX absence or failure

## Testing expectations

Server-rendered HTMX UI should be easy to test for:

- HTMX and non-HTMX render-path parity
- correct renderer method selection by request type
- fragment responses targeting the right stable containers
- mutation responses re-rendering authoritative state
- intentional use of OOB responses when multiple regions must stay in sync

Prefer focused tests around handler behavior and presentation contracts rather than brittle full-markup snapshot sprawl.

## Anti-patterns

- handlers that call `ExecuteTemplate` directly for each route
- HTMX-only interactions with no normal browser fallback
- mutation handlers that trust client-side state instead of re-fetching server state
- large custom JSON endpoints for interactions that only need HTML fragments
- many tiny DOM patches when one authoritative container re-render would be clearer
- JavaScript taking over state management that the server already owns

## Related guides

- `app-view-models.md`
- `api/README.md`
- `server/README.md`
- `api/testing.md`
