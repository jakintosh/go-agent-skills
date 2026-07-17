---
name: compose-go-http-routes
description: Guide Go HTTP route-tree composition. Use for design, implementation, debugging, testing, or review of net/http routers, wire.Subrouter mounts, package handlers, public paths, or middleware boundaries; exclude endpoint payload behavior.
---

# Compose Go HTTP routes

## Preserve the routing boundary

- Treat routing as in-process composition of a complete `http.Handler` tree.
- Let each HTTP surface own one readable root composition point and let coherent areas own mountable route-group builders.
- Register direct routes with explicit method-and-path patterns.
- Mount child routers additively with `wire.Subrouter` instead of flattening unrelated routes into one function.
- Apply middleware at the highest safe boundary while keeping the protection visible at the registration or mount site.
- Keep deployment base paths, listener behavior, and process lifecycle outside local API or web route registration.

## Compose or revise a route tree

1. Trace the complete public path from the server mount through every child router to the direct route or package handler.
2. Inspect the root composition function, the owning route-group builder, middleware constructors, package handlers, and in-process tests before editing.
3. Load the relevant references:
   - Read [router composition](references/router-composition.md) for the root mux, route-group builders, and additive mounting pattern.
   - Read [middleware boundaries](references/middleware-boundaries.md) when choosing between subtree and direct-route wrappers.
   - Read [mounting package handlers](references/mounting-package-handlers.md) when a dependency already exposes `http.Handler`.
4. Decide which package owns the public location, which package owns handler behavior, and which boundary owns cross-cutting middleware.
5. Change the smallest coherent composition layer. Do not recreate routes owned by a mounted package.
6. Test the completed handler in process, including public paths and negative middleware cases.

## Route adjacent work

- Use [work-with-go-http-apis](../work-with-go-http-apis/SKILL.md) for JSON handlers, DTOs, response envelopes, error mapping, keys, CORS, and API tests.
- Use [work-with-go-web-uis](../work-with-go-web-uis/SKILL.md) for server-rendered pages, HTMX flows, forms, templates, and web view models.
- Use [work-with-go-servers](../work-with-go-servers/SKILL.md) for process-level mounting, deployment prefixes, serving, and lifecycle.
- Use [work-with-consent-users](../work-with-consent-users/SKILL.md) for Consent auth handlers and account integration.
- Use [work-with-go-clis](../work-with-go-clis/SKILL.md) when a mounted management handler's public collection path is passed to a remote command.

## Validate the route tree

- Verify every intended method and full path through the built handler.
- Test that public groups remain public and protected groups reject missing or insufficient authorization.
- Cover CORS preflight and non-preflight `OPTIONS` behavior where browser-facing routes use CORS.
- Confirm package-owned handlers remain mounted directly and receive the intended containing middleware.
- Confirm any CLI collection path matches the final path after all server and local mounts.

## Maintain this skill

- Keep reusable composition principles here and detailed examples in the references.
- Update the narrowest routing reference when a mounting or middleware convention changes.
- Keep API-, web-, server-, and auth-specific behavior in their adjacent skills instead of expanding this skill into a general HTTP guide.
