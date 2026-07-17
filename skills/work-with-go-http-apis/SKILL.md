---
name: work-with-go-http-apis
description: Guide Go JSON HTTP APIs. Use for design, implementation, debugging, testing, or review of internal/api, constructors, endpoints, DTOs, handlers, envelopes, error or status mapping, keys, CORS, or API tests; exclude rendered HTML.
---

# Work with Go HTTP APIs

## Preserve the boundary

- Treat `internal/api` as the concrete HTTP contract boundary.
- Keep handlers focused on transport work: parse, validate request-local shape, convert, call one service operation, map errors, and encode.
- Keep API DTOs distinct from service domain types and export contract types that callers or tests reuse.
- Keep domain rules in the service layer and persistence mechanics in database or store implementations.
- Keep deployment base paths, process composition, and listener behavior in the server layer.
- Apply the routing skill when the primary decision concerns route-tree structure, middleware placement, or mounting a package-owned handler.

## Work through an API change

1. Inspect the existing API constructor, router, endpoint family, response helpers, service method, server mount, and nearby tests before editing.
2. Identify the observable contract under change: method, public path, inputs, response DTO, envelope, status codes, headers, and side effects.
3. Load only the references needed for that contract:
   - Read [API shape](references/api-shape.md) for constructors, DTOs, handlers, wire helpers, or endpoint families.
   - Read [error mapping](references/error-mapping.md) when changing service errors, response messages, or status behavior.
   - Read [API testing](references/testing.md) whenever behavior or tests change.
   - Read [API key integration](references/with-keys.md) for permissions, key middleware, management routes, bootstrap keys, or permission migrations.
   - Read [CORS integration](references/with-cors.md) for origin storage, CORS middleware, preflight behavior, management routes, or bootstrap origins.
4. Trace inputs and errors across the API-service boundary. Add domain behavior to the service instead of embedding it in the handler.
5. Make the smallest coherent API change and keep request parsing, route registration, conversion, and response behavior easy to audit.
6. Exercise the built handler in process. Assert status before payload or error details, then verify meaningful state changes.

## Route adjacent work

- Use [compose-go-http-routes](../compose-go-http-routes/SKILL.md) for route groups, subtree mounting, middleware boundaries, and package handlers.
- Use [work-with-go-services](../work-with-go-services/SKILL.md) for domain behavior, service errors, permissions, and store contracts.
- Use [work-with-go-databases](../work-with-go-databases/SKILL.md) for adapters, SQL, transactions, migrations, and persistence tests.
- Use [work-with-go-servers](../work-with-go-servers/SKILL.md) for production composition, deployment mounting, startup, and shutdown.
- Use [work-with-go-clis](../work-with-go-clis/SKILL.md) when a remote API change also changes command wiring or client behavior.
- Use [work-with-consent-users](../work-with-consent-users/SKILL.md) for Consent account resolution and auth package integration.
- Use [work-with-go-config](../work-with-go-config/SKILL.md) when API, keys, CORS, or bootstrap behavior changes authored or resolved configuration.
- Use [work-with-go-web-uis](../work-with-go-web-uis/SKILL.md) when the same domain behavior also changes a browser-facing HTML surface.

## Validate the result

- Run focused tests for the changed endpoint family and middleware integration.
- Verify malformed input, domain failures, auth boundaries, and pagination or filtering when relevant.
- Confirm the public path after server mounting, especially when a package handler also has a CLI command.
- Run the repository's broader test and formatting commands when the change crosses packages.

## Maintain this skill

- Keep detailed API examples and contracts in the references; keep this file focused on reference selection and procedure.
- Update the narrowest reference when the style changes, and update cross-links whenever ownership moves.
- Recheck all affected examples when `command-go/pkg/wire`, `keys`, or `cors` behavior changes.
