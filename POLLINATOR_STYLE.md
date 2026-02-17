# Pollinator Project Style

A practical, opinionated style guide for building small Go server-side binaries with a CLI and HTTP API, prioritizing clean, human-readable code and minimal dependencies.

## Core principles
- Prefer the Go standard library; add external dependencies only when they clearly remove significant code or risk. Libraries under `git.sr.ht/~jakintosh` are first-class.
- Keep architecture shallow: CLI -> service -> database. The service layer owns business logic and HTTP handlers.
- Make dependencies explicit via options and constructors; avoid package-level state for new code.
- Favor clarity over cleverness: simple data flow, direct error handling, minimal indirection.
- Keep the API and CLI aligned: subcommands map to API resources and paths.

## Repository layout
```
project/
├── cmd/<bin>/             # CLI entry point and subcommands
├── internal/
│   ├── service/           # Business logic + HTTP handlers + router
│   ├── database/          # SQLite persistence + migrations
│   ├── app/               # (optional) HTML UI server + templates
│   └── testutil/          # Test helpers for internal packages
├── pkg/                   # (optional) Public reusable libraries
├── scripts/               # build/package/deploy helpers
├── testdata/              # fixtures (JSON, scenarios, etc.)
├── Makefile
├── go.mod
└── README.md
```
Notes:
- `internal/` is the default home for app code. `pkg/` is used only for APIs intended for external consumption.
- If HTML is required, keep it in `internal/app` with embedded templates.

### Domain-oriented naming and file split
- A "domain" is one business area (examples: `ledger`, `patrons`, `campaigns`, `services`, `auth`).
- Name files by domain so engineers can find logic quickly.
- Canonical split for one domain:

```
internal/
├── service/
│   ├── store.go              # shared Store interface (all domain persistence contracts)
│   ├── service.go            # Service struct, options, router composition
│   ├── ledger.go             # ledger types + business methods + ledger HTTP handlers
│   └── ledger_test.go        # ledger behavior tests
└── database/
    ├── database.go           # open/init DB connection and shared DB struct
    ├── migrations.go         # schema migration list and runner
    ├── ledger.go             # Store method implementations for ledger
    └── ledger_test.go        # DB-level tests for ledger persistence
```

- If a domain file grows too large, split by concern but keep the domain prefix:
  - `ledger_types.go`
  - `ledger_service.go`
  - `ledger_api.go`
- Do not split into many tiny files unless the split improves readability immediately.

## Dependency policy
- Default to stdlib (`net/http`, `database/sql`, `encoding/json`, `time`, `log`, `errors`).
- Acceptable core deps:
  - `git.sr.ht/~jakintosh/command-go` for CLI (`args`, `envs`), HTTP helpers (`wire`), auth (`keys`), CORS (`cors`), and versioning.
  - `modernc.org/sqlite` for CGO-free SQLite.
- Add other deps only when unavoidable (e.g., payment SDKs, UUIDs).

## CLI structure
- CLI is the primary entry point and includes both server and API client commands.
- Use `command-go/pkg/args` with a single root command in `cmd/<bin>/main.go`.
- The root command should:
  - Define `HelpOption` (short `-h`, long `--help`).
  - Include `envs.Command(DEFAULT_CFG)` for environment config management.
  - Include `serve` and `api` subcommands.
- Use `resolveOption` helpers to apply precedence: CLI option -> env var -> default.
- Credentials are loaded from a directory (usually `/etc/<bin>`) via small helpers like `loadCredential`.
- For versioning, use `//go:generate go run git.sr.ht/~jakintosh/command-go/pkg/version/generate` and include `version.Command`.

### Canonical CLI layout
```
cmd/<bin>/
├── main.go          # root command and helpers
├── serve.go         # server command
├── api.go           # api command root
└── <resource>.go    # per-resource subcommands
```

## Configuration and environment
- Default config directory: `~/.config/<bin>`.
- Use `envs.ConfigOptions` or `envs.ConfigOptionsAnd(...)` to add config flags.
- Required values are explicitly validated in `serve` handlers (return errors rather than silently defaulting).
- For server-side secrets, use files in `/etc/<bin>` (e.g., `api_key`, `signing_key`, etc).

## Service layer
- The service package is the core of the app: domain types, business logic, and HTTP handlers.
- Prefer a concrete `Service` struct with constructor options:

```go
type Options struct {
    Store Store
    KeysOptions  *keys.Options   // or non-pointer for required
    CORSOptions  *cors.Options
    Clock        func() time.Time
    HealthCheck  func() error
}

func New(opts Options) (*Service, error)
```

- Store interfaces are defined in `internal/service`, not in the database layer.
- Services should not mutate global state; dependency injection is explicit.
- Provide `Start()` / `Stop()` when background processing is needed.
- Keep business logic and HTTP handlers in the same file when they share types (e.g., `ledger.go`, `services.go`).

### Store contracts (canonical pattern)
- The service layer owns the domain model and the persistence contract.
- Define domain structs in `internal/service` first, then define store methods in terms of those structs.
- Keep the store interface focused on domain operations, not SQL concepts.

```go
// internal/service/ledger.go
type Transaction struct {
    ID     string    `json:"id"`
    Ledger string    `json:"ledger"`
    Amount int       `json:"amount"`
    Date   time.Time `json:"date"`
    Label  string    `json:"label"`
}

type LedgerSnapshot struct {
    OpeningBalance int `json:"opening_balance"`
    IncomingFunds  int `json:"incoming_funds"`
    OutgoingFunds  int `json:"outgoing_funds"`
    ClosingBalance int `json:"closing_balance"`
}

// internal/service/store.go
type Store interface {
    InsertTransaction(id, ledger string, amount int, dateUnix int64, label string) error
    GetTransactions(ledger string, limit, offset int) ([]Transaction, error)
    GetLedgerSnapshot(ledger string, sinceUnix, untilUnix int64) (*LedgerSnapshot, error)
}
```

- Naming rules for store contracts:
  - Interface name: `Store` (single app-wide interface) or `<Domain>Store` (if deliberately split).
  - Methods: `VerbNoun` with domain terms (`InsertTransaction`, `GetLedgerSnapshot`).
  - Parameter names should reveal storage representation when relevant (`dateUnix`, `sinceUnix`).
- Store interface should describe everything service needs, and nothing more:
  - no SQL rows
  - no `*sql.DB`, `*sql.Tx`, or driver-specific types
  - no transport concerns (HTTP, JSON, headers)

- Service methods are the translation boundary:
  - Validate input.
  - Convert API-level types to persistence-friendly values (e.g., `time.Time` -> unix seconds).
  - Call the store.
  - Wrap persistence failures in `DatabaseError`.

```go
func (s *Service) AddTransaction(id, ledger string, amount int, date time.Time, label string) error {
    if err := s.store.InsertTransaction(id, ledger, amount, date.Unix(), label); err != nil {
        return DatabaseError{Err: err}
    }
    return nil
}
```

- Keep handlers thin: decode -> call service method -> encode response.
- Keep domain invariants in service methods, not in HTTP handlers and not in database code.

### Error strategy
- Define sentinel errors in the service package (`ErrInvalidX`, `ErrNotFound`, etc.).
- Wrap DB errors in a typed error with `Unwrap()`:

```go
type DatabaseError struct { Err error }
func (e DatabaseError) Error() string { return fmt.Sprintf("database error: %v", e.Err) }
func (e DatabaseError) Unwrap() error { return e.Err }
```

- Map errors to HTTP status codes in a small helper.

## HTTP/API design
- Base path prefix: `/api/v1`.
- Use `http.NewServeMux()` with method patterns (Go 1.22+):
  - `mux.HandleFunc("GET /resource", ...)`
  - `mux.HandleFunc("POST /resource/{id}", ...)`
- Use `r.PathValue("id")` for path parameters.
- Prefer `command-go/pkg/wire` helpers:
  - `wire.WriteData(w, status, data)`
  - `wire.WriteError(w, status, message)`
  - `wire.ParsePagination(r)`
- Standard response format (from `wire`):
  - `{ "error": { "message": "..." }, "data": ... }`
- CORS and auth are applied as middleware using `keys` and `cors` services:
  - Auth via `Authorization: Bearer <token>` header.
  - Preflight OPTIONS handlers for CORS are explicitly registered.

### Router composition
- Build routers by resource and register in `Service.BuildRouter()`:

```go
func (s *Service) BuildRouter() http.Handler {
    mux := http.NewServeMux()
    s.buildHealthRouter(mux)
    s.buildResourceRouter(mux, mw)
    return mux
}
```

- Use `http.StripPrefix("/api/v1", ...)` in `Serve()`.

## Database layer
- SQLite via `modernc.org/sqlite`.
- Use a thin `database` package with:
  - `Open` / `Init` function
  - Migrations (prefer `PRAGMA user_version`)
  - DB options (`Path`, `WAL`)
  - `SetMaxOpenConns(1)` for serial writes
  - `PRAGMA foreign_keys=ON`, `PRAGMA busy_timeout=5000`, optional WAL
- SQL style:
  - Use positional parameters (`?1`, `?2`, ...).
  - Prefer explicit `INSERT ... ON CONFLICT` upserts for idempotent writes.
  - Store timestamps as Unix seconds; convert at the boundary.
- Add a short, transactional health check (`BEGIN`, temp table, read/write).

### Store implementation integration
- The database package implements the service-owned `Store` interface.
- Add a compile-time conformance check so contract drift fails at build time.
- Keep SQL and row scanning in `internal/database`; do not leak SQL types into service APIs.

```go
// internal/database/database.go
type DB struct {
    Conn *sql.DB
}

// compile-time interface conformance
var _ service.Store = (*DB)(nil)
```

```go
// internal/database/ledger_store.go
func (db *DB) GetTransactions(ledger string, limit, offset int) ([]service.Transaction, error) {
    rows, err := db.Conn.Query(
        `SELECT id, amount, date, label FROM tx
         WHERE ledger = ?1
         ORDER BY date DESC
         LIMIT ?2 OFFSET ?3`,
        ledger, limit, offset,
    )
    if err != nil {
        return nil, fmt.Errorf("query transactions: %w", err)
    }
    defer rows.Close()

    var out []service.Transaction
    for rows.Next() {
        var t service.Transaction
        var unixDate int64
        if err := rows.Scan(&t.ID, &t.Amount, &unixDate, &t.Label); err != nil {
            return nil, fmt.Errorf("scan transaction: %w", err)
        }
        t.Ledger = ledger
        t.Date = time.Unix(unixDate, 0)
        out = append(out, t)
    }
    return out, rows.Err()
}
```

- Database code should be mechanical and predictable:
  - Query/exec with parameterized SQL.
  - Scan into local variables.
  - Convert to service domain types.
  - Return wrapped errors with context.
- Naming rules for database implementations:
  - File: `<domain>_store.go`.
  - Receiver type: shared `*DB` unless there is a clear reason for separate receiver structs.
  - Method names must match the service contract exactly.
  - Migration table names can differ from Go type names, but keep a clear mapping in code comments when not obvious.

## Tests
- Unit tests live alongside source (`*_test.go`).
- Prefer external test packages (`package service_test`) to test public behavior.
- Use `internal/testutil` for setup, fixtures, and helpers:
  - `SetupTestEnv(t)` returns a ready-to-use service with in-memory SQLite.
  - Helpers for time creation and data seeding.
- HTTP tests use `command-go/pkg/wire` (`TestGet`, `TestPost`, headers).
- Add `//go:build integration` for integration tests with external dependencies, and separate integration tests from unit tests.
- Use `t.Helper()` and `t.Cleanup()` consistently.
- Use `t.Parallel()` when tests are isolated and fast.

## Public libraries (`pkg/`)
- Use `pkg/` only for reusable APIs intended for other projects.
- Provide `doc.go` with a full package comment, usage examples, and error behavior.
- Keep public interfaces small and documented.

## Build and automation conventions
- `Makefile` provides `build`, `test`, and `install` targets at minimum.
- `Makefile` also serves as the primary project action surface for local development.

## Code style and readability
- Use gofmt; keep signatures multi-line when there are multiple parameters:

```go
func (s *Service) DoThing(
    a string,
    b int,
) error {
    // ...
}
```

- Group related logic with blank lines; avoid excessive comments.
- Keep error strings lowercase and without punctuation.
- Prefer explicit names (`CreateService`, `GetServiceByName`) over abbreviations.
- JSON tags are `snake_case`.

## Canonical defaults (use unless there's a strong reason not to)
- HTTP API prefix: `/api/v1`
- Config dir: `~/.config/<bin>`
- Credentials dir: `/etc/<bin>`
- DB path default: `/var/lib/<bin>`
- SQLite WAL enabled in production
- Pagination default limit: 100

## Legacy patterns to avoid in new code
- Package-level mutable state for stores (e.g., `SetXStore` global setters). Use explicit `Service` structs and dependency injection instead.
- Deep or overly generic abstractions. Keep code direct and readable.
