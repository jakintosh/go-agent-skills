# HTMX + Go Front-End Style Guide

This guide describes a reusable way to structure and render a server-first HTMX UI in Go.  
It focuses on transferable rendering and templating patterns rather than project-specific features.

## Core principles

- Render HTML on the server; use HTMX to request/replace HTML fragments.
- Keep progressive enhancement: every interaction has a non-HTMX fallback.
- Treat the server as the source of truth; re-render from domain state after writes.
- Keep client JavaScript minimal and focused on enhancement, not business state.
- Use explicit view models between domain and templates.

## Recommended package shape

- `server.go`: routes and handlers.
- `templates.go`: template parsing/embedding and renderer initialization.
- `view_*.go`: typed view models + render helpers.
- `context.go`: request-context parsing (especially HTMX headers).
- `templates/`: page templates + reusable fragments.
- `static/`: CSS and small JS enhancement code.

The key idea is separation: handlers orchestrate, view builders shape data, templates render.

## Rendering architecture

### Full page + partial fragments

- Maintain one full-page render path for normal browser navigation.
- Maintain fragment render paths for HTMX swaps.
- For detail panes/panels, support both:
  - inline rendering in full-page responses (deep-link friendly), and
  - HTMX-loaded fragment rendering into a target region.

### View-model-first templates

- Do not pass domain entities directly to templates.
- Build view models that contain:
  - display-ready fields (formatted time/text/percentages),
  - precomputed aggregate values,
  - nested child view models,
  - template-specific flags (e.g., OOB mode).
- Keep formatting decisions in Go, not in templates.

### Fragment composition

- Break templates into small named fragments.
- Reuse the same fragment for normal rendering and OOB rendering.
- Use stable element IDs on replaceable DOM nodes so targeted swaps stay reliable.

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

### Mutation handlers

1. Parse/validate input.
2. Persist mutation (usually through service).
3. If non-HTMX: redirect to canonical page URL.
4. If HTMX: return HTML updates (often OOB + optional targeted content).

This keeps one handler serving both classic and enhanced UX paths.

## Partial update strategy

Prefer **authoritative re-rendering** over many tiny DOM patches.

- After a mutation, re-fetch affected server state.
- Re-render the smallest authoritative container that guarantees consistency.
- Use OOB swaps when multiple disconnected regions must update in one response.

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
- Use small specialized view types for repeated blocks (e.g., list entries, badges, action buttons).
- Keep URL/action strings close to view construction so templates stay mostly declarative.
- Store template control flags in the view model rather than deriving complex logic in template conditionals.

## Practical guardrails

- Keep handlers thin; push mapping/render decisions into view/presentation helpers.
- Avoid custom JSON endpoints if HTML fragment responses already satisfy the interaction.
- Avoid per-route ad hoc response styles; standardize on a small set of response patterns.
- Make each response safe to replay: rendering should always reflect persisted state, not client assumptions.
