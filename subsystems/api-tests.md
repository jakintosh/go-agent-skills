# API Tests

This guide defines the standard shape for HTTP API tests in this style system.

It focuses on in-process tests at the router and service boundary, the role of `internal/testutil`, and the test structure that keeps behavior obvious at a glance.

The goal is to make API tests:

- easy to scan
- fast in local and CI runs
- focused on observable behavior
- explicit about setup, requests, and assertions

## When to use this guide

Use this guide when you are:

- writing tests for HTTP handlers or router behavior
- building `internal/testutil`
- deciding how much setup should be hidden in helpers
- adding middleware, auth, validation, or response-contract coverage

## Non-goals

This guide does not define:

- browser automation
- cross-process end-to-end testing
- SQL adapter test style
- general unit testing philosophy beyond the API boundary

## Core rules

- Test observable HTTP behavior, not private internals.
- Keep each test focused on one scenario.
- Use Arrange -> Act -> Assert order with explicit chunk comments.
- Assert status first, then response payload or error, then side effects.
- Keep setup deterministic and local.
- Prefer in-process router tests over real network listeners.
- Use `internal/testutil` as the test composition root.
- Let `internal/testutil` own lifecycle and cleanup.
- Keep seed helpers deterministic and explicit about scenario intent.
- Allow scenario helpers for setup mechanics, but do not let them hide assertions.
- Keep request URL, body, and headers visible in the test.
- Use `t.Parallel()` only when isolation is clearly safe.

## Scope

These tests should verify the HTTP contract a caller can observe, including:

- route wiring
- middleware behavior
- request decoding and validation
- status mapping
- response envelope and payload shape
- state transitions across requests

They are not the right place to inspect private service fields or internal helper behavior directly.

## `internal/testutil` boundary

`internal/testutil` is the composition root for API tests.

It should own:

- environment setup such as `SetupTestEnv(t)`
- deterministic dependency wiring
- lifecycle cleanup through `t.Cleanup()`
- small shared header helpers
- domain seed helpers
- narrow scenario setup helpers for multi-step arrangements

It should not own:

- endpoint assertions
- one-call mega helpers that seed half the application
- wrappers that hide request URL, headers, or body construction
- random fixture generation by default

## Recommended `TestEnv` shape

Expose only what tests need regularly.

```go
type TestEnv struct {
	DB      *database.DB
	Service *service.Service
}

func SetupTestEnv(t *testing.T) *TestEnv {
	t.Helper()

	db, err := database.Open(database.Options{
		Path: ":memory:",
	})
	if err != nil {
		t.Fatalf("open test db: %v", err)
	}

	svc, err := service.New(service.Options{
		Store: db,
		Clock: fixedClock,
	})
	if err != nil {
		t.Fatalf("create service: %v", err)
	}

	t.Cleanup(func() {
		_ = db.Close()
	})

	return &TestEnv{
		DB:      db,
		Service: svc,
	}
}
```

The test environment should be deterministic, short-lived, and easy to understand.

## Seed and scenario helpers

Seed helpers should encode scenario intent clearly:

```go
func SeedDocuments(t *testing.T, svc *service.Service) {
	t.Helper()

	if err := svc.CreateDocument("doc-1", "Guide A"); err != nil {
		t.Fatalf("seed doc-1: %v", err)
	}
	if err := svc.CreateDocument("doc-2", "Guide B"); err != nil {
		t.Fatalf("seed doc-2: %v", err)
	}
}
```

Scenario helpers are useful for setup mechanics in multi-request flows, but they should stop before assertions.

If a helper hides the behavior under test, split it.

## Canonical test structure

Every API test should follow the same visible flow:

1. set up the environment
2. seed only the necessary state
3. build and send the request
4. verify the immediate HTTP result
5. verify any important side effects

Use explicit chunk comments so the flow is obvious on a quick skim.

```go
func TestAPICreateDocument_Success(t *testing.T) {
	// setup env
	env := testutil.SetupTestEnv(t)
	router := env.Service.BuildRouter()

	// post document
	url := "/api/v1/documents"
	body := `{"id":"doc-1","title":"Guide A"}`
	headers := []wire.TestHeader{
		testutil.JSONHeader,
		testutil.AuthHeader,
	}
	result := wire.TestPost[service.Document](t, router, url, body, headers...)

	// verify result
	result.ExpectStatus(t, http.StatusCreated)
	if result.Data.ID != "doc-1" {
		t.Fatalf("expected id %q, got %q", "doc-1", result.Data.ID)
	}

	// verify document exists in store
	doc, err := env.Service.GetDocument("doc-1")
	if err != nil {
		t.Fatalf("get document: %v", err)
	}
	if doc.Title != "Guide A" {
		t.Fatalf("expected title %q, got %q", "Guide A", doc.Title)
	}
}
```

## Request construction style

Keep request inputs visible and spelled out in the test itself.

That usually means:

- assign `url` in its own statement
- assign `body` in its own statement
- assign `headers` in their own statement when needed

For JSON request bodies:

- use raw string literals for non-empty JSON when that improves scanability
- use exactly `"{}"` for empty JSON objects when that is the clearest shape

Avoid hiding request construction in large helpers.

## Assertions

Assert in this order:

1. status code
2. payload or error contract
3. side effects

This ordering matches how a client experiences the API and makes failures easier to diagnose quickly.

Use typed `wire.TestX` helpers and response assertions when they make the test easier to read.

## Table-driven tests

Use table-driven tests only when they improve readability.

They work well when:

- setup is shared
- assertion shape stays the same
- only a small set of inputs varies

Prefer standalone tests when scenarios differ meaningfully in setup or expected behavior.

## Parallelism

Do not add `t.Parallel()` by default.

Use it only when:

- the test environment is fully isolated
- failure output remains readable
- the speed benefit is worth the extra complexity

Readability and determinism are more important than squeezing the maximum concurrency out of the default suite.

## CORS and middleware coverage

Include focused tests for middleware behavior where it matters, such as:

- protected routes rejecting missing auth
- allowed requests succeeding with the right permissions
- CORS preflight behavior on routes that require it

For modern preflight tests, include the expected method request header on `OPTIONS` requests.

## Testing expectations

For each endpoint family, cover the relevant subset of:

- success paths
- malformed JSON or query input
- required field validation
- auth and permission failures
- domain-state failures such as `NotFound` or `Conflict`
- pagination or filter parsing
- meaningful state transitions or idempotency behavior

Avoid redundant tests that change only literal data values without changing behavior.

## Anti-patterns

- tests that inspect private service internals instead of HTTP outcomes
- large helpers that hide Arrange, Act, or Assert intent
- random fixture generation in default API tests
- real network listeners for normal router coverage
- request bodies or headers assembled implicitly inside unrelated helpers
- massive tables that are harder to read than separate tests
- routine `t.Parallel()` on stateful tests

## Related guides

- `service-construction.md`
- `http-router-composition.md`
- `database-adapters.md`
