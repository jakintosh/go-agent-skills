---
name: work-with-consent-users
description: Guide Consent-backed identity in Go applications. Use for design, implementation, debugging, testing, deployment, or review of Consent authentication, local accounts, account scoping, CSRF, integration config, test verifiers, or production registration; exclude unrelated auth systems.
---

# Work with Consent Users

Use this skill as the integration-domain knowledge layer for applications that authenticate through Consent. Inspect the requested change across the provider boundary, local account boundary, request flow, and deployment surface, then load only the references that govern those concerns.

## Preserve the boundary

- Let Consent own credentials, authentication, grants, roles, sessions, token refresh, signing, and authoritative profile data.
- Let the application own local accounts, cached display fields, account-scoped domain data, and ownership enforcement.
- Use the Consent subject as the durable external identity key and a local account ID for application foreign keys and service inputs.
- Construct Consent clients, validators, manifests, and package handlers at a server composition root; pass a narrow auth shape into the web package.
- Depend on `client.Verifier` at the web boundary and validate CSRF before state-changing service calls.
- Keep production registration, runtime configuration, and local test authentication explicit and separate.

## Consult the knowledge base

1. Inspect the target repository's config resolution, server composition, route tree, web auth context, account service and store contracts, schema, deployment notes, and relevant tests.
2. Trace read authentication and mutation authentication end to end, including token verification, account resolution, profile refresh, CSRF, and account-scoped persistence.
3. Classify the affected concerns and read every matching reference before editing or concluding a review.
4. Re-evaluate the selection when implementation reveals config, routing, account, profile, test, or deployment implications not obvious from the prompt.
5. Apply the guidance as a strong default while preserving coherent local conventions outside the requested scope.
6. Explain any material deviation when the installed Consent API, repository architecture, or deployment constraints require another shape.

## Select references

- Read [consent-user-shape.md](references/consent-user-shape.md) for ownership, account data modeling, package boundaries, scopes, CSRF, canonical request flow, and overall integration shape.
- Read [account-resolution.md](references/account-resolution.md) whenever verifying request cookies, creating or refreshing local accounts, fetching scoped profiles, building auth context, protecting mutations, or passing account IDs into service methods.
- Read [integration-config.md](references/integration-config.md) whenever resolving Consent runtime inputs, loading verification keys, deriving audiences or public URLs, constructing clients and manifests, building authorize URLs, or mounting package handlers.
- Read [local-testing.md](references/local-testing.md) whenever adding authenticated route tests, account setup tests, CSRF tests, profile fakes, `TestVerifier`, or an opt-in local dev-auth mode.
- Read [production-deployment.md](references/production-deployment.md) whenever preparing runtime deployment, distributing verification keys, registering or updating an integration, configuring reverse-proxy paths, or checking production login end to end.

Read multiple references when concerns overlap. A production auth change normally requires the overall shape, integration config, account resolution, local testing, and deployment references.

## Include adjacent domains

- Consult [Go web UI guidance](../work-with-go-web-uis/SKILL.md) when auth state changes pages, forms, login and logout controls, error rendering, or account-scoped handlers.
- Consult [Go server guidance](../work-with-go-servers/SKILL.md) when constructing auth dependencies, mounting package handlers, selecting dev versus production auth, or managing startup.
- Consult [Go HTTP routing guidance](../compose-go-http-routes/SKILL.md) when reserving auth, dev, static, or well-known paths or composing the package handlers with application routers.
- Consult [Go config guidance](../work-with-go-config/SKILL.md) when Consent URLs, integration names, public URLs, modes, or verification-key paths are authored or resolved.
- Consult [Go service guidance](../work-with-go-services/SKILL.md) when account types, account-scoped inputs, authorization policy, errors, or store contracts change.
- Consult [Go database guidance](../work-with-go-databases/SKILL.md) when account schema, ownership constraints, migrations, or account-scoped queries change.

## Validate the result

- Prefer the repository's documented formatting, test, lint, and check commands.
- Run focused auth, account-resolution, route, service, and database tests first, then the broader relevant suite.
- Test unauthenticated reads, authenticated reads, first-login account setup, profile mismatch and refresh failure, valid and invalid CSRF, and account ownership boundaries as applicable.
- Keep local tests in process with Consent's testing package; do not require a live Consent server by default.
- For production changes, verify manifest URLs, audience and issuer derivation, public route reachability, key loading, authorize scopes, callback behavior, and logout behavior.
- For reviews, report concrete identity, ownership, CSRF, route, config, or deployment risks rather than harmless local naming differences.

## Keep the skill current

When repeated Consent integration work exposes a missing rule, unclear branch, or stale example, update the narrowest applicable reference. Change `SKILL.md` only when activation, universal boundaries, consultation behavior, adjacent routing, or reference selection needs to change.
