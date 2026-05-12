# Testing Database Adapters

This guide defines the standard shape for persistence-focused tests in `internal/database`.

Use it when you are testing SQL-backed store behavior, adapter open behavior, schema migrations, transaction behavior, or storage invariants that should hold even when callers reach the adapter directly.

## Required Instructions

- Test observable adapter behavior through public store methods by default.
- Keep database tests alongside the adapter code and use an external test package by default.
- Use a real isolated SQLite database for the default suite.
- Give each test its own database state and cleanup through `t.Cleanup()` or a small setup helper.
- Seed through adapter methods by default.
- Keep the adapter call under test visible in the test.
- Use test helpers for opening, cleanup, deterministic fixtures, and short seed helpers.
- Verify durable outcomes by roundtripping through store methods by default.
- Use raw SQL only for migration, schema, or storage mechanics the store contract cannot expose clearly.
- Add focused tests for open, schema, migration, and transaction behavior where those concerns exist.
- Use `t.Parallel()` only when database state and helpers are clearly isolated.

## Package And File Shape

Keep database tests next to the files they exercise.

```text
internal/database/
  database.go
  migrations.go
  documents.go
  database_test.go
  migrations_test.go
  documents_test.go

internal/testutil/
  db.go
  seed_documents.go
```

Use an external test package by default:

```go
package database_test
```

That keeps tests at the adapter boundary. Use an internal-package test only when the subject is intentionally internal, such as a migration runner helper that cannot be meaningfully tested through `Open(...)`.

## Setup Strategy

The default setup is a fresh SQLite database per test:

- `:memory:` for ordinary adapter tests
- a temp-file path when close-and-reopen behavior is the subject
- cleanup owned by `t.Cleanup()` or the setup helper

Prefer real adapter construction over mocks or `sqlmock`. Database adapter tests should exercise actual schema, query, scan, constraint, and migration behavior through the adapter boundary.

## Test Helper Boundary

For `internal/database` and similar internal subsystems, shared helpers belong in `internal/testutil`.

For public packages such as `pkg/mylib`, shared helpers belong in same-directory `_test.go` files unless they are intentionally part of a larger internal test environment.

Helpers may own:

- opening an isolated test database
- cleanup
- deterministic seed helpers
- reusable test-only dates, tokens, or fixture values

Tests should still own:

- the adapter call being tested
- the records or conditions that make the scenario meaningful
- assertions about returned records and durable state

If a helper hides the row, relationship, or constraint the test depends on, make the setup visible in the test.

## Seeding Policy

Seed through adapter methods by default. That keeps persistence tests at the adapter boundary without pulling service policy into database setup.

Use service-level seeding only when the state is cross-table or domain-heavy enough that direct adapter calls would make the scenario harder to read.

Direct one-off setup inside a single test is fine when it is clearer than introducing a helper.

## Canonical Flow

Most database tests should use this visible shape:

1. open isolated store state
2. seed only the records needed for the scenario
3. perform one adapter operation
4. assert the immediate return value or error
5. verify the durable outcome through a store-method read

Use another store method for verification when it proves the behavior clearly. Use narrow SQL inspection only for storage mechanics such as `user_version`, table or index existence, or columns that are intentionally not exposed by the store contract.

## Canonical Example

```go
// internal/testutil/db.go
package testutil

import (
	"testing"

	"example/internal/database"
)

func SetupTestDB(t *testing.T) *database.DB {
	t.Helper()

	opts := database.Options{
		Path: ":memory:",
	}
	db, err := database.Open(opts)
	if err != nil {
		t.Fatalf("open db: %v", err)
	}
	t.Cleanup(func() {
		_ = db.Close()
	})

	return db
}
```

```go
// internal/database/documents_test.go
package database_test

import (
	"testing"
	"time"

	"example/internal/service"
	"example/internal/testutil"
)

func TestInsertDocument_UpsertPreservesCreatedAt(t *testing.T) {
	db := testutil.SetupTestDB(t)

	createdAt := time.Date(2026, 1, 15, 12, 0, 0, 0, time.UTC)
	if err := db.InsertDocument(&service.Document{
		ID:        "doc-1",
		Title:     "Guide A",
		CreatedAt: createdAt,
	}); err != nil {
		t.Fatalf("insert document: %v", err)
	}

	doc, err := db.GetDocument("doc-1")
	if err != nil {
		t.Fatalf("get inserted document: %v", err)
	}
	if doc.Title != "Guide A" {
		t.Fatalf("title = %q, want %q", doc.Title, "Guide A")
	}
	if !doc.CreatedAt.Equal(createdAt) {
		t.Fatalf("created at = %s, want %s", doc.CreatedAt, createdAt)
	}

	if err := db.InsertDocument(&service.Document{
		ID:        "doc-1",
		Title:     "Guide A (Revised)",
		CreatedAt: createdAt.Add(time.Hour),
	}); err != nil {
		t.Fatalf("upsert document: %v", err)
	}

	doc, err = db.GetDocument("doc-1")
	if err != nil {
		t.Fatalf("get updated document: %v", err)
	}
	if doc.Title != "Guide A (Revised)" {
		t.Fatalf("title = %q, want %q", doc.Title, "Guide A (Revised)")
	}
	if !doc.CreatedAt.Equal(createdAt) {
		t.Fatalf("created at = %s, want %s", doc.CreatedAt, createdAt)
	}
}
```

This works because the setup helper owns only open and cleanup, the adapter operation stays visible, and durable behavior is verified through the same store boundary that callers use.

## Open And Migration Coverage

Cover adapter initialization through observable readiness:

- open succeeds for an isolated test database
- schema is ready for representative store operations after open
- close succeeds
- health checks succeed and fail in the expected conditions
- migrations advance `user_version` correctly
- required tables or indexes exist after migration
- reopening a file-backed database preserves durable state

Prefer store-method checks for open and schema readiness. Use SQL inspection for migration tests when the subject is version advancement, table creation, index creation, or another schema fact not exposed by a store method.

## Query And Transaction Coverage

For method-level adapter tests, cover the persistence behavior the method owns:

- inserts, updates, and deletes
- duplicate or constraint violations
- not-found cases
- idempotent upsert semantics
- partial updates preserving unspecified fields
- protected deletes and relationship constraints
- relationship updates preserving unchanged associations
- list ordering, limit, offset, and filter behavior
- null scanning and conversion behavior
- multi-step transactional effects

You do not need every category for every method. Prove database-owned invariants at the adapter boundary instead of only proving that a caller ran a separate preflight check.

## Parallelism

Use `t.Parallel()` only when each test has isolated database state, helpers do not share unsafe mutable state, cleanup is reliable, and failure output stays readable.
