# Go Persistence Boundary

A persisted operation is the unit of design:

```text
caller intent → store contract → durable enforcement → adapter tests
```

The service defines the operation's meaning. The service-owned store interface expresses the persisted capability it needs. The schema and database adapter enforce that contract. Adapter tests prove the guarantee.

## Boundary Rules

- Define store methods as complete domain operations, not CRUD fragments callers must sequence correctly.
- Keep input validation, authorization, key generation, time capture, external coordination, and application sequencing in the service.
- Enforce every persisted precondition in the schema or adapter. Do not check it first in the service.
- Pass every service-produced input needed by the operation, including one captured `now` when durable state is time-sensitive.
- Return values produced or identified by the persisted operation instead of making the service reconstruct them with later reads.
- Give lifecycle transitions dedicated methods. Use generic diffs only for independently editable fields.
- Define retry behavior and meaningful domain errors as part of the store contract.

The service may read persisted state when the value itself is needed for application behavior. That read must not stand in for enforcement of a later mutation.

## Store Comment Standard

Every store method starts with a normal Go summary. Every stateful mutation then uses these sections:

```go
// ConfirmPeer confirms a provisional peer.
//
// Persisted preconditions:
//   - The peer belongs to an unexpired, redeemed registration.
//
// Atomic effects:
//   - Registration groups become peer groups.
//   - The peer and registration become confirmed.
//
// Retry:
//   - Repeating the operation after confirmation succeeds unchanged.
//
// Errors:
//   - ErrNotFound when no provisional peer exists.
//   - ErrRegistrationExpired when the registration has expired.
ConfirmPeer(network, peer string, now time.Time) error
```

All four sections are required for stateful mutations; write `None.` when that is the contract. Persisted preconditions are facts about current durable state, not input validation or schema shape. Describe a transaction-produced result in the summary. Describe domain state, not tables, SQL, or helper calls.

Reads use ordinary Go documentation. Mention semantic errors and observable ordering only when they are not clear from the signature.

## Source Of Truth

The store declaration is the human-readable source of truth for persisted operation semantics. The schema and adapter are the source of truth for enforcement. Adapter tests are the executable proof.

Keep service orchestration in service source and tests. Put a short lifecycle comment beside the domain type when several operations form one state machine. Use system design documents only for behavior that crosses several operations or external systems, and ADRs only when the rationale and rejected alternatives must survive.

## Complete Contract

A persisted operation is complete when its signature and comment define its inputs, durable preconditions, atomic effects, result, retry behavior, and semantic errors; the adapter enforces that definition directly; and focused tests prove both success and unchanged state after rejection.
