# API Test Style Guide
This guide defines the standard style for HTTP API tests across internal Go services.
Priority order: 1) Readability, 2) Fast test execution.
Goal: tests are easy to scan, easy to debug, and fast in local/CI runs.

## Scope
Apply this guide to in-process API tests at the service/router boundary.

These tests verify:
- route wiring
- middleware behavior
- input parsing and validation
- status mapping
- response envelope and payload shape
- state transitions across requests

These are not browser tests and not cross-process end-to-end tests.

## Core principles
- Test observable HTTP behavior, not private internals.
- Keep each test focused on one scenario.
- Use Arrange -> Act -> Assert order.
- Assert status first, then payload/error, then side effects.
- Cover happy paths and meaningful failure paths.
- Keep setup deterministic and local.
- Use helpers to remove boilerplate, not to hide intent.
- Use table-driven tests only when they improve readability.
- Use `t.Parallel()` only when isolation is clearly safe.

## Standard packages and helpers
- `testing`: lifecycle, assertions, `t.Run`, cleanup.
- `net/http`: status constants.
- `git.sr.ht/~jakintosh/command-go/pkg/wire`: request helpers and typed response assertions.
- `internal/testutil`: service setup, auth header helpers, fixture seeding.

Preferred `wire` helpers:
- `wire.TestGet[T]`
- `wire.TestPost[T]`
- `wire.TestPut[T]`
- `wire.TestDelete[T]`
- `wire.TestOptions[T]`

Preferred `wire` assertions:
- `result.ExpectStatus(t, code)`
- `result.ExpectOK(t)`
- `result.ExpectError(t)`

## internal/testutil responsibilities

`internal/testutil` is the test composition root for API tests.

Use it to make tests shorter and more consistent, while keeping each test's intent obvious.

### What belongs in `internal/testutil`

- test environment setup (`SetupTestEnv`) with deterministic defaults
- lifecycle ownership (`t.Cleanup`) for service/process/database shutdown
- auth/header helpers (header defaults/helpers)
- small domain seed helpers for common Arrange steps
- narrow scenario setup helpers for multi-request workflows

### What should not go in `internal/testutil`

- helpers that perform endpoint assertions
- giant one-call setup helpers that seed unrelated domains
- random/non-deterministic fixture generation by default
- shared mutable globals that leak across tests
- wrappers that hide request URL/body/header construction

### Recommended `internal/testutil` layout

- `internal/testutil/utils.go`: `TestEnv`, `SetupTestEnv`, lifecycle, common headers
- `internal/testutil/seed_<domain>.go`: deterministic domain seeding helpers
- `internal/testutil/scenario_<domain>.go`: multi-step setup helpers for transition tests

### Recommended `TestEnv` shape

Expose only what tests need regularly.

```go
const TEST_TOKEN = "test-id.0123456789abcdef0123456789abcdef"

type TestEnv struct {
	DB      *database.DB
	Service *service.Service
}

func SetupTestEnv(t *testing.T) *TestEnv {
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
		KeysOptions: &keys.Options{
			Store:          db.KeysStore,
			BootstrapToken: TEST_TOKEN,
		},
	}
	svc, err := service.New(svcOpts)
	if err != nil {
		t.Fatalf("create service: %v", err)
	}
	svc.Start()

	t.Cleanup(func() {
		svc.Stop()
		_ = db.Close()
	})

	return &TestEnv{DB: db, Service: svc}
}
```

### Header helpers should stay tiny

```go
const TEST_TOKEN = "test-id.0123456789abcdef0123456789abcdef"

var AuthHeader = wire.TestHeader{
	Key:   "Authorization",
	Value: "Bearer " + TEST_TOKEN,
}

var JSONHeader = wire.TestHeader{
	Key:   "Content-Type",
	Value: "application/json",
}
```

### Seed helpers should encode intent

Keep these helpers deterministic and domain-specific.

```go
func SeedResourceData(t *testing.T, svc *service.Service) {
	t.Helper()

	if err := svc.CreateResource("r-1", "Example A"); err != nil {
		t.Fatalf("seed r-1: %v", err)
	}
	if err := svc.CreateResource("r-2", "Example B"); err != nil {
		t.Fatalf("seed r-2: %v", err)
	}
}
```

### Scenario helpers for multi-request setup

Use scenario helpers for setup mechanics, not for hiding assertions.

```go
func StoreRefreshToken(
	t *testing.T,
	env *TestEnv,
	userID string,
	audience []string,
) string {
	t.Helper()

	tok, err := env.Service.IssueRefreshToken(userID, audience)
	if err != nil {
		t.Fatalf("issue refresh token: %v", err)
	}
	if err := env.DB.InsertRefreshToken(tok); err != nil {
		t.Fatalf("store refresh token: %v", err)
	}

	return tok.Encoded()
}
```

### Quality rules for `internal/testutil`

- every helper has one clear purpose
- every helper starts with `t.Helper()`
- setup helpers own cleanup via `t.Cleanup()`
- helper names describe behavior (`SeedX`, `AuthHeader`, `StoreXToken`)
- prefer several small helpers over one large helper
- if a helper hides Arrange/Act/Assert intent, split or remove it

## File and naming conventions

- Place API tests in `internal/service/<domain>_api_test.go`.
- Use external package tests (`package service_test`) by default.
- Name tests `TestAPI<ActionOrEndpoint>_<Condition>`.
- Use clear condition suffixes like `Success`, `InvalidJSON`, `BadQuery`, `Unauthorized`, `NotFound`, `Conflict`.

## What to test

For each endpoint family, cover the relevant subset of:
- success path
- required field validation
- malformed JSON/body/query
- auth/middleware behavior on protected routes
- domain state errors (`NotFound`, `Conflict`, `Forbidden`)
- pagination/query semantics (valid and invalid)
- state transitions (rotation, invalidation, idempotency)

Avoid redundant tests that only change literal data values without changing behavior.

## Single-scenario vs table-driven

Use single-scenario tests when:
- setup is unique
- assertions differ materially
- the scenario is clearer as a standalone behavior

Use table-driven tests when:
- setup is shared
- assertion shape is identical
- only input permutations vary

Table-driven rules:
- keep case structs small (`name`, input, expected status)
- keep tables compact; split large tables into multiple tests
- use `t.Run` names that explain behavior

## Parallelism policy

- Readability first, speed second.
- Do not add `t.Parallel()` by default.
- Add `t.Parallel()` only when tests have isolated state and independent setup.
- Prefer per-test in-memory DB/service before enabling parallelism.
- Avoid parallel subtests if failure output gets noisy.

## Canonical test structure

Every test should follow the pattern of Arrange, Act, Assert. Arrange prepares isolated test state, Act performs the key behavior under test, and Assert verifies both the HTTP contract and any required side effects. We use fixed comment headers and chunk spacing between them so this flow is visually obvious at a glance.

1. Setup environment
	- topped with comment header `// setup env` and marks the baseline setup for the scenario
  - initialize `env := testutil.SetupTestEnv(t)` and `router := env.Service.BuildRouter()` (or equivalent)
  - keep this chunk focused on wiring test infrastructure, not request logic
2. Seed state (optional)
	- topped with comment header `// seed state`
  - seed only the minimal records/tokens/config needed for this test case
  - use `internal/testutil` helpers for repetitive seeding
  - omit this chunk when no preexisting state is required
3. Perform request
	- topped with comment header that clearly describes intent and http method (`// post resource`, `// get metrics`, `// delete key`)
  - build request inputs (`url`, `body`, `headers`) and send the request in this same chunk
  - keep request construction and request execution together; do not split into separate chunks
4. Cerify HTTP result
	- topped with comment header `// verify result`
  - assert status code first
  - then assert response envelope/payload (`ExpectOK`, `ExpectError`, field checks)
  - this chunk verifies the immediate API contract returned to clients
5. Verify outcome (optional)
	- topped with comment header that explains the verification, e.g. `// verify resource is not present in store`
  - verify persisted state changes, ordering effects, invalidation, or other post-conditions
  - keep this chunk only when behavior requires side-effect confirmation
  - omit this chunk for pure read-only assertions with no durable side effect

Keep one blank line between chunks. These comment headers are part of the required style, not optional decoration.

## Coding style conventions (required)

The formatting in this guide is intentional and should carry into real tests.

- Non-empty JSON request bodies should use a raw string `body` variable.
- For empty object payloads, use exactly `body := "{}"`.
- Keep JSON body indentation aligned with code indentation; do not left-align JSON to file column 1.
- When headers are required, declare them as a multi-line `[]wire.TestHeader` slice and pass with `headers...`.
- If no headers are needed, do not declare a headers variable.
- In table-driven tests, keep non-empty JSON case bodies in raw-string format and empty-object cases as `"{}"`.
- Keep request construction and request send in one chunk comment (for example `// post resource`).
- Keep chunk comments from the full examples (`setup env`, action chunk, `verify result`, `validate outcome`).

## Full examples (style-compliant)

### Single-scenario test

```go
func TestAPICreateResource_Success(t *testing.T) {
	t.Parallel()

	// setup env
	env := testutil.SetupTestEnv(t)
	router := env.Service.BuildRouter()

	// post resource
	url := "/resources"
	body := `
	{
		"id": "r-1",
		"name": "Example"
	}`
	headers := []wire.TestHeader{
		testutil.AuthHeader,
		testutil.JSONHeader,
	}
	result := wire.TestPost[any](router, url, body, headers...)

	// verify result
	result.ExpectStatus(t, http.StatusCreated)

	// validate outcome
	resource, err := env.Service.GetResourceByID("r-1")
	if err != nil {
		t.Fatalf("GetResourceByID failed: %v", err)
	}
	if resource.Name != "Example" {
		t.Fatalf("name = %q, want Example", resource.Name)
	}
}
```

### Table-driven validation test

```go
func TestAPICreateResource_InvalidBody(t *testing.T) {
	t.Parallel()

	// setup env
	env := testutil.SetupTestEnv(t)
	router := env.Service.BuildRouter()

	// build request cases
	tests := []struct {
		name       string
		body       string
		wantStatus int
	}{
		{
			name: "malformed json",
			body: "not-json",
			wantStatus: http.StatusBadRequest,
		},
		{
			name: "missing name",
			body: `
			{
				"id": "r-1"
			}`,
			wantStatus: http.StatusBadRequest,
		},
		{
			name: "empty object",
			body: "{}",
			wantStatus: http.StatusBadRequest,
		},
	}

	headers := []wire.TestHeader{
		testutil.AuthHeader,
		testutil.JSONHeader,
	}

	// post resource
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			url := "/resources"
			body := tt.body
			result := wire.TestPost[any](router, url, body, headers...)
			result.ExpectStatus(t, tt.wantStatus)
			result.ExpectError(t)
		})
	}
}
```

## Anti-patterns to avoid

- one test that checks many unrelated behaviors
- success tests that only assert status for complex payloads
- very large tables that reduce readability
- copy-pasted setup that belongs in `internal/testutil`
- real network listeners in default API test suites
- parallelism before isolation is proven

## Merge checklist

- names clearly describe endpoint and condition
- each test has one clear responsibility
- status + envelope + side effects are asserted as needed
- happy path and key failure paths are covered without duplication
- helpers keep tests concise and intention-revealing
- `internal/testutil` helpers are deterministic and narrowly scoped
- setup helpers own lifecycle/cleanup with `t.Cleanup()`
- helper APIs do not hide request intent or endpoint assertions
- non-empty JSON bodies use the mandated raw-string style
- empty-object payloads use exactly `"{}"`
- headers use `[]wire.TestHeader` + `headers...` when present, and are omitted when absent
- comment chunks and blank-line spacing follow the style-compliant examples
- table-driven tests are used where they improve readability
- parallelism choices are intentional and safe
