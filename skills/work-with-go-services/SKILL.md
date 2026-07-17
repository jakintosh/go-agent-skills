---
name: work-with-go-services
description: Guide Go service and store boundaries. Use for design, implementation, debugging, testing, or review of internal/service, domain behavior or types, constructors, errors, permissions, store contracts, bootstrap, or lifecycle; exclude SQL-only adapter work.
---

# Work with Go Services

Use this skill as the domain-boundary knowledge layer for ongoing service work. Inspect the repository, identify every affected service concern, and load only the references that govern those concerns.

## Preserve the boundary

- Treat `internal/service` as the application core.
- Keep domain behavior, domain types, domain errors, permission vocabulary, and persistence contracts service-owned.
- Construct a concrete `Service` with explicit options and validate required dependencies early.
- Keep transport DTOs, raw ingress normalization, config resolution, SQL mechanics, external-client setup, routing, and process serving outside the service.
- Express persistence through domain-named store interfaces defined beside the service.
- Keep mutable bootstrap work out of ordinary construction and serving.
- Add lifecycle hooks only for service-owned background work; let outer layers control process lifetime.

## Consult the knowledge base

1. Inspect the target service, its callers, its store contracts, adapter implementations, and relevant tests before choosing references.
2. Classify the affected concerns, including domain behavior, construction, persistence contracts, initialization, and background lifecycle.
3. Read every matching reference below before editing or reaching a review conclusion.
4. Re-evaluate the selection when implementation reveals adjacent API, database, user, config, routing, or server implications.
5. Apply the guidance as a strong default while preserving coherent local conventions outside the requested scope.
6. Explain any material deviation when repository constraints make the default unsuitable.

## Select references

- Read [service-shape.md](references/service-shape.md) whenever creating or reorganizing a service package, changing construction, domain types, service methods, errors, permissions, or the service's architectural boundary.
- Read [store-contracts.md](references/store-contracts.md) whenever defining, changing, or reviewing a service-owned persistence interface, persistence-shaped parameters, update types, or store-facing domain values.
- Also read [database-adapters.md](references/database-adapters.md) when implementing that contract in `internal/database` or reviewing whether its adapter stays mechanical.
- Read [bootstrap-initialization.md](references/bootstrap-initialization.md) when durable setup must run through an explicit `init` or bootstrap path rather than ordinary construction or serving.
- Read [lifecycle-hooks.md](references/lifecycle-hooks.md) only when the service owns long-lived background work requiring coordinated startup and shutdown.

Read multiple references when a change crosses concerns. A new persisted domain feature normally requires the service shape, store contract, database adapter, and adjacent database guidance. A background worker that requires durable setup normally requires lifecycle and bootstrap guidance as separate concerns.

## Include adjacent domains

- Consult [database guidance](../work-with-go-databases/SKILL.md) for schemas, migrations, SQL methods, transactions, scans, and adapter tests.
- Consult [API guidance](../work-with-go-http-apis/SKILL.md) when a domain change affects JSON contracts, error mapping, permissions, keys, or CORS behavior.
- Consult [web UI guidance](../work-with-go-web-uis/SKILL.md) when browser handlers, forms, view models, or rendered behavior consume the service change.
- Consult [Consent user guidance](../work-with-consent-users/SKILL.md) for local accounts, account-scoped inputs, authentication, and CSRF behavior.
- Consult [config guidance](../work-with-go-config/SKILL.md) when service dependencies or initialization require authored or resolved configuration.
- Consult [routing guidance](../compose-go-http-routes/SKILL.md) for route-tree and middleware composition.
- Consult [server guidance](../work-with-go-servers/SKILL.md) for production dependency construction, mounting, serving, cleanup, and lifecycle control.
- Consult [CLI guidance](../work-with-go-clis/SKILL.md) when commands expose or initialize service behavior.

## Validate the result

- Prefer the repository's documented formatting, test, lint, and check commands.
- Run focused service tests first, then adapter and transport tests affected by contract changes.
- Verify dependency validation, domain-error behavior, store-call inputs, and service-side conversions.
- Test bootstrap idempotence and separation from normal startup when initialization changes.
- Test startup, cancellation, and shutdown when lifecycle hooks change.
- For reviews, report concrete boundary or behavior risks rather than harmless local variation.

## Keep the skill current

Update the narrowest reference when repeated service work exposes missing or stale guidance. Change `SKILL.md` only when activation, universal boundaries, consultation behavior, or reference routing needs to change.
