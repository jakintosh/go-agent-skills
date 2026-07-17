---
name: work-with-go-web-uis
description: Guide server-rendered Go web UIs. Use for design, implementation, debugging, testing, or review of internal/web, templates, view models, HTMX, forms, flash messages, assets, browser routes, handlers, or web tests; exclude JSON-only APIs.
---

# Work with Go Web UIs

Use this skill as the knowledge layer for a server-rendered browser surface, not only when creating `internal/web`. Inspect the requested change, trace its full-page and enhanced request paths, and load only the references that govern the affected UI concerns.

## Preserve the boundary

- Keep `internal/web` responsible for browser-facing HTML, UI route groups, request handling, view models, rendering, forms, flash state, HTMX behavior, and static assets.
- Keep domain behavior in the service, JSON contracts in the API, production mounting in the server, and identity-provider integration in the Consent user boundary.
- Render ordinary, usable HTML first and treat HTMX as progressive enhancement of the same routes.
- Rebuild visible mutation results from authoritative service state rather than inferred browser state.
- Keep handlers thin, view builders pure and display-ready, templates declarative, and renderer methods explicit.
- Keep browser behavior resource-local while sharing package-wide request-context, rendering, form, and status conventions.

## Consult the knowledge base

1. Inspect the target repository's web constructor, router, handlers, service calls, view models, templates, assets, and relevant tests.
2. Trace each affected route for ordinary requests and any HTMX branch, including invalid and successful mutations.
3. Classify the affected concerns and read every matching reference before editing or concluding a review.
4. Re-evaluate the selection when implementation reveals additional rendering, form, fragment, asset, auth, or test implications.
5. Apply the guidance as a strong default while preserving coherent local conventions outside the requested scope.
6. Explain any material deviation when repository constraints make the default unsuitable.

## Select references

- Read [web-ui-shape.md](references/web-ui-shape.md) for package ownership, constructors, resource locality, root route composition, and the canonical read and mutation flows.
- Read [view-models.md](references/view-models.md) whenever adding or changing display-ready data, URLs, labels, formatting, selected state, page composition, or template inputs.
- Read [renderer-and-templates.md](references/renderer-and-templates.md) whenever parsing or executing templates, adding renderer methods, defining full pages or fragments, or changing swap roots.
- Read [htmx-request-flow.md](references/htmx-request-flow.md) whenever a route branches on HTMX headers, supports boosted navigation, returns fragments, or updates multiple regions.
- Read [forms-and-mutations.md](references/forms-and-mutations.md) whenever parsing forms, validating request-local shape, mapping service errors, redirecting after writes, or rendering mutation status.
- Read [static-assets.md](references/static-assets.md) whenever adding CSS, JavaScript, static serving, cache behavior, or frontend build tooling.
- Read [testing.md](references/testing.md) whenever observable web behavior, routes, forms, HTMX branches, view builders, templates, assets, or web test infrastructure change. Use it to plan validation even when tests were not requested explicitly.

Read multiple references when concerns overlap. A new HTMX form normally requires the package shape, view models, renderer and templates, HTMX flow, forms and mutations, and testing references.

## Include adjacent domains

- Consult [Go service guidance](../work-with-go-services/SKILL.md) when handlers require new domain operations, service inputs, errors, or store contracts.
- Consult [Go HTTP routing guidance](../compose-go-http-routes/SKILL.md) when route trees, package subrouters, middleware, or mount paths change.
- Consult [Go server guidance](../work-with-go-servers/SKILL.md) when production mounting, composition, serving, or lifecycle changes.
- Consult [Consent user guidance](../work-with-consent-users/SKILL.md) when pages or mutations require login state, local account resolution, Consent cookies, CSRF, or account scoping.
- Consult [Go API guidance](../work-with-go-http-apis/SKILL.md) when the same behavior also changes JSON endpoints or API contracts.
- Consult [Go database guidance](../work-with-go-databases/SKILL.md) when browser behavior introduces or changes durable persistence.

## Validate the result

- Prefer the repository's documented formatting, test, lint, and check commands.
- Run focused view, form, handler, and renderer tests first, then the broader relevant suite.
- Exercise ordinary and HTMX paths for routes that support both, including validation and redirect behavior.
- Confirm fragment roots match their targets and successful mutations render newly fetched service state.
- Verify direct links, refreshes, browser navigation, and no-JavaScript form submissions remain coherent.
- For reviews, report concrete user-flow, boundary, rendering, or security risks rather than harmless markup variation.

## Keep the skill current

When repeated web work exposes a missing rule, unclear branch, or stale example, update the narrowest applicable reference. Change `SKILL.md` only when activation, universal boundaries, consultation behavior, adjacent routing, or reference selection needs to change.
