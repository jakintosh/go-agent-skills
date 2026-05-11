# Testing an API

This guide defines the default shape for in-process HTTP tests for `internal/api`.

Use it when you are testing handlers, route wiring, middleware, request decoding, response DTOs, service-error status mapping, or observable state changes through `API.Router()`.

API tests should verify the HTTP contract a caller can observe. Keep service-domain tests in `internal/service` and persistence tests in `internal/database`.

## Required

- Test observable HTTP behavior through the built router.
- Prefer in-process router tests over real network listeners.
- Use `internal/testutil` as the test composition root.
- Build service and API dependencies in test setup, then exercise `env.Router`.
- Keep each test focused on one scenario.
- Structure tests as setup, request, result assertion, and side-effect assertion chunks.
- Leave short chunk comments before each visible phase.
- Keep request URL, body, and headers visible in the test.
- Use exported `internal/api` DTOs for response assertions.
- Assert status first, then payload or error contract, then side effects.
- Use `t.Parallel()` only when isolation is clearly safe.

## Local Shape

API tests should live next to the API file they exercise.

Name one test file directly after each non-test file:

```text
internal/api/
  api.go
  api_test.go
  documents.go
  documents_test.go
  projects.go
  projects_test.go
```

Each test file should verify the functionality owned by the file it is named after. For example, `documents_test.go` tests document routes, document request decoding, document DTO behavior, and document handler outcomes.

Use test names that make the endpoint behavior obvious:

```go
func TestAPICreateDocument_Success(
	t *testing.T,
) {
	// ...
}
```

The default flow is:

1. set up the test environment
2. seed only the state needed for the scenario
3. build and send the request
4. verify the immediate HTTP result
5. verify important side effects

Use standalone tests when setup or assertions differ meaningfully. Use table-driven tests only when setup is shared, assertion shape stays the same, and a small set of inputs varies.

## Test Composition Root

`internal/testutil` should own deterministic API test wiring:

- environment setup such as `SetupTestEnv(t)`
- service and API construction
- lifecycle cleanup through `t.Cleanup()`
- small shared header helpers
- deterministic seed helpers
- narrow scenario setup helpers for multi-request arrangements

Keep endpoint assertions, request URLs, request bodies, and behavior-specific headers in the test.

```go
type TestEnv struct {
	DB      *database.DB
	Service *service.Service
	Router  http.Handler
}

func SetupTestEnv(
	t *testing.T,
) *TestEnv {
	t.Helper()

	dbOpts := database.Options{
		Path: ":memory:",
	}
	db, err := database.Open(dbOpts)
	if err != nil {
		t.Fatalf("open test db: %v", err)
	}

	svcOpts := service.Options{
		Store: db,
		Clock: fixedClock,
	}
	svc, err := service.New(svcOpts)
	if err != nil {
		t.Fatalf("create service: %v", err)
	}

	apiOpts := api.Options{
		Service: svc,
		Keys:    db.KeysStore,
	}
	apiServer, err := api.New(apiOpts)
	if err != nil {
		t.Fatalf("create api: %v", err)
	}

	t.Cleanup(func() {
		_ = db.Close()
	})

	return &TestEnv{
		DB:      db,
		Service: svc,
		Router:  apiServer.Router(),
	}
}
```

If production wiring and test wiring need to diverge more deeply, read `../server/composition-roots.md`.

## Request Shape

Keep request construction easy to scan:

- assign `url` in its own statement
- assign `body` in its own statement
- assign `headers` in their own statement when needed
- use pretty-printed raw string literals for non-empty JSON bodies
- use exactly `"{}"` for empty JSON objects

`wire` is the HTTP wire-format package from `command-go`. Import it with:

```go
import "git.sr.ht/~jakintosh/command-go/pkg/wire"
```

It provides the standard JSON response envelope, server helpers such as `wire.WriteData` and `wire.WriteError`, router mounting with `wire.Subrouter`, API clients, and typed handler-test helpers such as `wire.TestGet[T]` and `wire.TestPost[T]`.

Shared header values belong in `internal/testutil` when they are part of the normal test surface:

```go
var AuthHeader = wire.TestHeader{
	Key:   "Authorization",
	Value: "Bearer " + TestToken,
}

var JSONHeader = wire.TestHeader{
	Key:   "Content-Type",
	Value: "application/json",
}
```

## Focused Example

```go
func TestAPICreateDocument_Success(
	t *testing.T,
) {
	// setup env
	env := testutil.SetupTestEnv(t)

	// post document
	url := "/documents"
	body := `{
		"id": "doc-1",
		"title": "Guide A"
	}`
	headers := []wire.TestHeader{
		testutil.JSONHeader,
		testutil.AuthHeader,
	}
	result := wire.TestPost[api.DocumentDTO](env.Router, url, body, headers...)

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

This shape keeps the scenario visible without hiding the HTTP contract behind helpers.

## Coverage Shape

For each endpoint family, cover the relevant subset of:

- success paths
- malformed JSON or query input
- required field validation
- auth and permission failures
- domain-state failures such as `NotFound` or `Conflict`
- pagination or filter parsing
- meaningful state transitions or idempotency behavior

Include focused middleware tests where behavior matters. For CORS preflight tests, include the expected method request header on `OPTIONS` requests.

Avoid redundant tests that change only literal data values without changing behavior.
