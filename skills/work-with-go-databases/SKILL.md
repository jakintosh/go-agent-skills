---
name: work-with-go-databases
description: Guide Go persistence layers. Use for design, implementation, debugging, testing, or review of schemas, migrations, database opening, SQL adapters, queries, scans, transactions, constraints, or internal/database; exclude service-only store contracts.
---

# Work with Go Databases

Use this skill as a database-domain knowledge layer, not only for greenfield implementation. Inspect the requested work, identify the affected persistence concerns, and load only the references that inform those concerns.

## Preserve the boundary

- Keep `internal/database` mechanical and storage-focused.
- Implement persistence contracts owned by `internal/service`; do not move domain policy into the adapter.
- Keep SQL, driver types, scans, and storage conversions inside the database package.
- Provide one explicit `Open(...)` entry point that returns a migrated, ready-to-use adapter.
- Enforce durable invariants with schema constraints and storage behavior.
- Use transactions for coordinated writes and consistent multi-query reads.
- Return service-owned values only after explicitly converting storage-shaped values.

## Consult the knowledge base

1. Inspect the target repository and the relevant database, service, and test files before deciding which references apply.
2. Classify every affected persistence concern, including concerns discovered only after reading the code.
3. Read each matching reference below before editing or reaching a review conclusion.
4. Re-evaluate the reference selection when the implementation reveals schema, transaction, opening, or test implications not obvious from the prompt.
5. Apply the guidance as a strong default while preserving coherent local conventions outside the requested scope.
6. Explain any material deviation when the existing architecture or task constraints make the default unsuitable.

## Select references

- Read [adapter-shape.md](references/adapter-shape.md) when creating, opening, composing, or structurally reorganizing the database adapter. Also read it when reviewing whether storage and service responsibilities are separated correctly.
- Read [migrations.md](references/migrations.md) for every schema change, migration-runner change, or review of durable schema evolution.
- Also read [migrations-with-go.md](references/migrations-with-go.md) when a migration needs reads, loops, batching, conditional repair, or a data transformation clearer in Go than SQL.
- Read [query-methods.md](references/query-methods.md) whenever adding, modifying, debugging, or reviewing ordinary reads, writes, scans, conversions, null handling, upserts, or optional filters.
- Read [transactions.md](references/transactions.md) whenever an operation spans several statements, coordinates related writes, or requires a consistent view across multiple queries.
- Read [testing.md](references/testing.md) whenever observable persistence behavior, migrations, opening behavior, transactions, test infrastructure, or database tests change. For implementation work, use it to plan validation even when the request does not explicitly mention tests.

Read multiple references when the change crosses concerns. A new persisted field normally requires migrations, query methods, and testing. A new multi-step mutation normally requires query methods, transactions, and testing.

## Include adjacent domains

- Consult [service guidance](../work-with-go-services/SKILL.md) when persistence contracts, domain values, error semantics, or initialization responsibilities change.
- Consult [config guidance](../work-with-go-config/SKILL.md) when database paths, runtime resolution, or authored configuration change.
- Consult [server guidance](../work-with-go-servers/SKILL.md) when database opening, closing, dependency composition, or lifecycle ownership changes.
- Consult [API guidance](../work-with-go-http-apis/SKILL.md) when endpoint behavior, keys, or CORS introduces schema or adapter work.
- Consult [web UI guidance](../work-with-go-web-uis/SKILL.md) when browser behavior introduces durable state.
- Consult [CLI guidance](../work-with-go-clis/SKILL.md) when commands initialize, migrate, query, or reset durable state.
- Consult [Consent user guidance](../work-with-consent-users/SKILL.md) when local accounts, ownership constraints, or account-scoped queries change.

## Validate the result

- Prefer the repository's documented formatting, test, lint, and check commands.
- Run focused database tests first, then the broader relevant suite when implementation changes are requested.
- Verify both immediate results and durable round trips for persistence changes.
- Exercise migration behavior from the oldest supported schema state affected by the change.
- Check rollback and constraint behavior when atomicity or durable invariants matter.
- For reviews, report concrete behavioral or architectural risks; do not flag harmless stylistic variation that preserves the boundary and invariants.

## Keep the skill current

When repeated database work exposes a missing rule, unclear branch, or stale example, update the narrowest applicable reference. Change `SKILL.md` only when activation, universal boundaries, consultation behavior, or reference routing needs to change.
