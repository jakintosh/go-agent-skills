---
name: design-go-persistence
description: Design Go service-to-database persistence boundaries. Use when creating or changing service-owned store interfaces, persisted operations, durable invariants, lifecycle transitions, atomic effects, retry semantics, or their contract tests; exclude SQL-only work against an unchanged store contract.
---

# Design Go Persistence

Design one persisted operation from caller intent through durable proof. Treat the service-owned store contract as the design artifact, not as an implementation detail discovered after coding.

## Design The Contract

1. Read [persistence-boundary.md](references/persistence-boundary.md).
2. Inspect the caller, service operation, domain types, store interface, adapter, schema, and relevant tests.
3. Identify the application intent, resource identities, lifecycle transition, and durable facts that must hold when the operation commits.
4. Draft the service-owned types, semantic errors, store signature, and standardized store comment.
5. State how the schema or adapter will enforce the contract and which adapter tests will prove it.
6. Present this source-level contract for approval before implementing a new or materially changed boundary.

Keep the proposal to decisions that need approval. Do not check store preconditions in the service. Keep input validation, authorization, key generation, time capture, external effects, and application sequencing there.

Read [example.md](references/example.md) when designing an initial boundary or when allocation, time, or retry behavior makes the contract unclear.

## Implement The Approved Contract

Write adapter tests for the documented preconditions, atomic effects, retry behavior, results, and errors. Then implement schema constraints or transactional adapter logic that makes those tests pass when the adapter is called directly.

Implement the service orchestration against the completed store capability. Add service or transport tests only for behavior those layers own.

Use [work-with-go-services](../work-with-go-services/SKILL.md) for service package conventions and [work-with-go-databases](../work-with-go-databases/SKILL.md) for schema, SQL, transaction, scan, and adapter-test conventions.

## Keep Documentation Authoritative

Keep persisted operation semantics in the store declaration. Keep enforcement in the schema and adapter, and proof in adapter tests. Add lifecycle or system prose only when several operations must be understood together.

Do not preserve planning worksheets after their decisions have moved into source, comments, and tests.

## Validate The Result

Verify that:

- the store method is one complete persisted capability
- its comment follows the boundary standard
- the service does not check persisted preconditions before the store call
- the adapter enforces the contract when called directly
- rejected operations leave durable state unchanged
- returned values and semantic errors match the contract

Run focused adapter and service tests, then the repository's broader checks in proportion to the change.
