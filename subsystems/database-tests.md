# Database Tests

This guide defines the standard shape for database adapter tests in this style system.

It focuses on tests for SQL-backed store behavior, open and migration behavior, and the setup patterns that keep persistence tests fast, direct, and trustworthy.

The goal is to make database tests:

- behavior-focused
- isolated and deterministic
- explicit about what boundary is being verified
- careful about when to inspect raw SQL state directly

## When to use this guide

Use this guide when you are:

- writing tests in `internal/database`
- testing a runtime store layer directly
- deciding whether setup should use adapter calls, test helpers, or service-assisted seeding
- reviewing migration, open, close, health-check, or transactional behavior

## Non-goals

This guide does not define:

- store contract design
- database adapter implementation style
- service-layer business-rule tests
- HTTP API tests
- true external integration tests against remote database infrastructure

Those belong in adjacent guides.

## Core rules

- Test observable adapter behavior through public store methods by default.
- Keep database tests alongside adapter code and use external test packages by default.
- Use a real isolated SQLite database for the default suite.
- Give each test its own database state and own cleanup through setup helpers or `t.Cleanup()`.
- Keep each test focused on one behavior.
- Seed through adapter methods by default.
- Use test-only helpers only to shorten setup, not to hide the behavior under test.
- Verify durable outcomes with follow-up reads at the narrowest sensible boundary.
- Use raw SQL only when checking storage mechanics the adapter API does not expose clearly.
- Add focused tests for open, schema, migration, and transaction behavior where those concerns exist.
- Use `t.Parallel()` only when isolation is clearly safe.

## Package and file shape

Keep database tests next to the adapter they exercise.

A typical layout looks like:

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

The default package choice is external:

```go
package database_test
```

That keeps most tests at the adapter boundary and prevents quiet coupling to unexported internals.

Use an internal-package test only when the subject is intentionally internal, such as a migration runner helper that is not meaningfully testable through the public open path alone.

## Setup strategy

The default setup is a fresh, isolated SQLite database per test.

Usually that means:

- `:memory:` for ordinary adapter tests
- a temp-file path when close-and-reopen behavior is the subject
- cleanup owned by `t.Cleanup()` or a small helper

Prefer real adapter construction over mocks or `sqlmock` for the default suite. These tests are meant to validate actual schema, query, scan, and constraint behavior.

## Test helper boundary

Test helpers can help database tests, but they should stay narrow.

For `internal/database` and similar internal subsystems, `internal/testutil` is the normal shared helper location.

For public packages such as `pkg/mylib`, same-directory `_test.go` helpers are the normal shared helper location. If only one test file needs the helper, keep it file-local instead of inventing a wider helper layer.

In both cases, helpers may own:

- opening an isolated test database
- cleanup
- deterministic seed helpers
- reusable test-only dates, tokens, or fixture values

They should not own:

- the adapter call being tested
- assertions about returned records
- giant scenario builders that hide what state matters

If a helper makes it hard to see what row or condition the test depends on, the helper is too large.

For public packages, do not treat `internal/testutil` as the default home for the package's own tests, and do not create a public `pkg/mylib/testutil` API unless test utilities are intentionally part of the public product surface. That should be rare.

## Seeding policy

Seed through adapter methods by default.

That keeps database tests honest about the boundary they are exercising and avoids pulling service behavior into tests that are supposed to validate persistence behavior.

Use service-level seeding only when the state is meaningfully cross-table or domain-heavy and arranging it directly through adapter calls would obscure the scenario more than it would clarify it.

That should be treated as an optional pattern, not the baseline.

Direct one-off setup inside a single test is still fine when it is shorter and clearer than introducing a helper. The important rule is that reusable setup should be demonstrated through a helper when the guide is teaching the general pattern.

## Canonical test flow

Most database tests should follow this visible shape:

1. open isolated store state
2. seed only the records needed for the scenario
3. perform one adapter operation
4. assert the immediate return value or error
5. verify the durable storage outcome with a read-back check

When the adapter already exposes a clear read method, use that for verification.

When the thing you need to verify is more mechanical than behavioral, a narrow SQL inspection is acceptable. Good examples include:

- checking that a migration created a table
- checking `user_version`
- checking `NULL` versus non-`NULL` persistence
- checking that an upsert preserved `created_at` but updated `updated_at`

The important rule is to use the narrowest boundary that proves the behavior clearly.

## Canonical example

```go
// internal/testutil/db.go
package testutil

import (
	"testing"

	"example/internal/database"
)

func SetupTestDB(t *testing.T) *database.DB {
	t.Helper()

	db, err := database.Open(database.Options{Path: ":memory:"})
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

	"example/internal/testutil"
)

func TestInsertDocument_UpsertPreservesCreatedAt(t *testing.T) {
	db := testutil.SetupTestDB(t)

	if err := db.InsertDocument("doc-1", "Guide A"); err != nil {
		t.Fatalf("insert document: %v", err)
	}

	row := db.Conn.QueryRow(`
		SELECT created_at_unix, updated_at_unix
		FROM documents
		WHERE id = ?1
	`, "doc-1")

	var createdAt int64
	var updatedAt *int64
	if err := row.Scan(&createdAt, &updatedAt); err != nil {
		t.Fatalf("query inserted document: %v", err)
	}
	if updatedAt != nil {
		t.Fatalf("expected nil updated_at on first insert")
	}

	if err := db.InsertDocument("doc-1", "Guide A (Revised)"); err != nil {
		t.Fatalf("upsert document: %v", err)
	}

	doc, err := db.GetDocument("doc-1")
	if err != nil {
		t.Fatalf("get document: %v", err)
	}
	if doc.Title != "Guide A (Revised)" {
		t.Fatalf("unexpected title %q", doc.Title)
	}

	row = db.Conn.QueryRow(`
		SELECT created_at_unix, updated_at_unix
		FROM documents
		WHERE id = ?1
	`, "doc-1")

	var createdAgain int64
	var updatedAgain *int64
	if err := row.Scan(&createdAgain, &updatedAgain); err != nil {
		t.Fatalf("query updated document: %v", err)
	}
	if createdAgain != createdAt {
		t.Fatalf("expected created_at to stay stable")
	}
	if updatedAgain == nil {
		t.Fatalf("expected updated_at after upsert")
	}
}
```

This works because:

- the adapter method under test is obvious
- the setup helper owns only open and cleanup
- the behavioral assertion uses the adapter
- the mechanical timestamp assertion uses raw SQL only where it adds clarity

## Public package variant

If the database-backed package is public, the core testing goals do not change:

- keep tests black-box by default
- use a real isolated SQLite database
- keep the main package call visible in the test
- use raw SQL only for narrow storage mechanics

What changes is the boundary around the tests.

The default test package becomes the public-package external test package:

```go
package mylib_test
```

For helpers, prefer same-directory `_test.go` files first:

```text
pkg/mylib/
  doc.go
  store.go
  helpers_test.go
  store_test.go
```

For example:

```go
// pkg/mylib/helpers_test.go
package mylib_test

import (
	"testing"

	"example/pkg/mylib"
)

func SetupTestDB(t *testing.T) *mylib.Store {
	t.Helper()

	store, err := mylib.Open(mylib.Options{Path: ":memory:"})
	if err != nil {
		t.Fatalf("open store: %v", err)
	}
	t.Cleanup(func() {
		_ = store.Close()
	})

	return store
}
```

That keeps the helper:

- next to the public package's tests
- test-only rather than exported
- aligned with the public-package guidance that `pkg/` should not casually absorb application-only testing surface

Repo-level `internal/testutil` can still be useful when an application test needs to compose a public package into a larger internal test environment. It is just not the canonical home for the public package's own tests.

## Open and migration tests

Every database subsystem should have a few focused tests around adapter initialization itself.

Cover the relevant subset of:

- open succeeds for an isolated test database
- schema is ready for representative operations after open
- close succeeds
- health checks succeed and fail in the expected conditions
- migrations advance schema version correctly
- required tables or indexes exist after migration
- reopening a file-backed database preserves durable state

Keep these tests focused on observable readiness rather than duplicating the migration implementation line by line.

## Transaction and query-behavior coverage

For method-level adapter tests, cover the behaviors that actually matter for persistence:

- inserts and updates succeeding
- duplicate or constraint violations
- not-found cases
- idempotent upsert semantics
- list ordering, limit, offset, and filter behavior
- null scanning and conversion behavior
- multi-step transactional effects when the method owns a transaction

You do not need every category for every method. Cover the ones the method is responsible for.

## Parallelism

Use `t.Parallel()` only when:

- each test has isolated database state
- helpers do not share unsafe mutable state
- cleanup remains reliable
- failure output stays readable

Some suites can parallelize cleanly. Others are simpler and more robust without it. Isolation is the deciding factor.

## Anti-patterns

- testing unexported SQL helpers instead of adapter behavior
- sharing one mutable database across many tests by default
- using service logic for ordinary adapter setup when direct adapter calls would be clearer
- giant test helpers that hide the records or constraints that matter
- asserting only that a write returned `nil` without verifying the durable outcome
- inspecting raw SQL state for everything instead of using adapter reads where possible
- migration tests that duplicate every implementation step instead of checking observable schema results
- introducing mocks for ordinary SQLite adapter tests

## Related guides

- `database-adapters.md`
- `store-contracts.md`
- `api-tests.md`
