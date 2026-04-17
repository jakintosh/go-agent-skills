# HTMX + Go Front-End Style Guide

This guide describes a reusable way to structure and render a server-first HTMX UI in Go.  
It focuses on transferable rendering and templating patterns rather than project-specific features.

## Core principles

- Render HTML on the server; use HTMX to request/replace HTML fragments.
- Keep progressive enhancement: every interaction has a non-HTMX fallback.
- Treat the server as the source of truth; re-render from domain state after writes.
- Keep client JavaScript minimal and focused on enhancement, not business state.
- Use explicit view models between domain and templates.
- Organize UI by ownership boundaries; each panel/section manages one coherent concern.

## Recommended package shape

- `server.go`: routes and handlers.
- `renderer.go` (or `templates.go`): template parsing/embedding and `Renderer` initialization.
- `view_*.go`: per-concern presentation modules (`XView`, `NewXView`, renderer methods).
- `presentation.go` (optional): shared formatting/presentation utilities used across views.
- `context.go`: request-context parsing (especially HTMX headers).
- `templates/`: page templates + reusable fragments.
- `static/`: CSS and small JS enhancement code.

The key idea is separation: handlers orchestrate, view builders shape data, templates render.

## View module contract

Treat each `view_*.go` file as a small presentation module for one UI concern.

- Define typed view model(s) (`XView`) and helper view types for repeated fragments.
- Define `NewXView(...)` mappers from domain data to display-ready template data.
- Keep mapper functions pure presentation mapping (no store/network access).
- Keep template-control flags and action metadata (URLs, labels, confirm text, OOB flags) in view models.
- Implement concern-specific `Renderer` methods in these modules (fragments/details/OOB as needed).
- Keep one renderer boundary: handlers call render methods, never template names or `ExecuteTemplate` directly.
- When one detail slot supports multiple entities, dispatch in the renderer and reuse the same detail fragments for HTMX and deep-link page rendering.

Handler usage should stay predictable: load domain state -> build view model(s) -> call renderer.

## Rendering architecture

### Full page + partial fragments

- Maintain one full-page render path for normal browser navigation.
- Maintain fragment render paths for HTMX swaps.
- For detail panes/panels, support both:
  - inline rendering in full-page responses (deep-link friendly), and
  - HTMX-loaded fragment rendering into a target region.

### View-model-first templates

- Do not pass domain entities directly to templates.
- Keep templates declarative: field reads, simple conditionals, and template composition.
- Keep formatting decisions in Go.

### Fragment composition

- Break templates into small named fragments.
- Reuse the same fragment for normal rendering and OOB rendering.
- Use stable element IDs on replaceable DOM nodes so targeted swaps stay reliable.
- When using `hx-swap="outerHTML"`, return fragments with the same root element ID as the target.

## HTMX request handling pattern

Parse HTMX headers into a request context struct so handlers can branch cleanly.

Common headers to capture:

- `HX-Request` (is this an HTMX request?)
- `HX-Current-URL`
- `HX-Target`
- `HX-Trigger`
- `HX-Trigger-Name`
- `HX-Boosted`

In practice, most handler decisions only need `HX-Request`, but capturing the rest helps debugging and future behavior.

## Canonical handler flows

### Read handlers

1. Load data from store/service.
2. Build view model(s).
3. If HTMX request: return fragment/details HTML.
4. Else: return full page HTML.

For detail endpoints, keep deep-link parity: HTMX returns the detail fragment; non-HTMX returns full page HTML with that detail pre-rendered/open.

### Mutation handlers

1. Parse/validate input.
2. Persist mutation (usually through service).
3. If non-HTMX: redirect to canonical page URL.
4. If HTMX: return HTML updates (often OOB + optional targeted content).

After writes, prefer re-fetching affected state and re-rendering the smallest authoritative container.

This keeps one handler serving both classic and enhanced UX paths.

Server-side mutations should follow load→mutate→persist: load current state, apply the intended change, persist. This keeps clients simple and ensures updates are non-destructive to unrelated fields.

### State management

Favor immediate persistence for admin-style operations to reduce unsaved local state and user confusion. Use UI-only HTMX states (edit modes, form visibility) for transient interactions, but persist only on explicit submit.

## Partial update strategy

Prefer **authoritative re-rendering** over many tiny DOM patches.

- After a mutation, re-fetch affected server state.
- Re-render the smallest authoritative container that guarantees consistency.
- Use OOB swaps when multiple disconnected regions must update in one response.
- Compose multi-fragment responses intentionally when two regions must stay in sync (for example, list + details panel).

Why this works well:

- prevents client/server state drift,
- reduces edge cases from incremental patch logic,
- keeps handler logic understandable.

## Template conventions

- Use named templates for reusable pieces (rows, metadata, details sections, footer actions).
- Keep markup declarative: `hx-get`, `hx-post`, `hx-patch`, `hx-delete`, `hx-target`, `hx-swap`.
- Use `hx-swap="none"` when a request is write-only and visual updates come from OOB fragments.
- Keep fragments idempotent: the same render call should always produce valid UI from current state.
- Make templates resilient to partial data (empty states, nil/zero values).

## Progressive enhancement contract

For each interactive route, define both behaviors:

- **Non-HTMX**: full-page/redirect flow.
- **HTMX**: fragment/OOB flow.

This dual contract gives robust behavior for:

- direct links/bookmarks,
- refreshes and back/forward navigation,
- graceful degradation if HTMX is unavailable.

## Static assets guidance

- Keep CSS and JS in `static/` and serve it directly.
- Use JavaScript for enhancement hooks only (initializing behavior after swaps, minor UI affordances).
- Re-run enhancement wiring on HTMX lifecycle events for swapped-in nodes.
- Avoid putting core rendering/state transitions in JS when server-rendered HTML can represent them.

## Data-to-UI structuring patterns

- Build parent view models that own nested children; render hierarchical UI from one root model.
- Replace long positional loader arguments with grouped state structs (`PageState`, `PanelState`) that carry pagination, selection, and form-state together.

## Practical guardrails

- Keep handlers thin; push mapping/render decisions into view/presentation helpers.
- Avoid custom JSON endpoints if HTML fragment responses already satisfy the interaction.
- Avoid per-route ad hoc response styles; standardize on a small set of response patterns.
- Make each response safe to replay: rendering should always reflect persisted state, not client assumptions.

## Testing

Add focused view-mapping tests to lock in rendering contracts:

- Route→template path coverage (correct template for each handler/request type).
- Pagination and selection state carryover across requests.
- Form-state preservation on validation errors.
- HTMX vs. non-HTMX response behavior parity.
