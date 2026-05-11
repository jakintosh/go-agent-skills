# Rule Inventory Matrix

This document is the working inventory of style rules currently spread across the existing guides, with temporary source signals from `examples/` and sibling repos used only as extraction inputs.

Its job is to help us:

- identify every rule worth preserving
- separate foundational rules from subsystem rules
- decide which future guide should own each rule
- make sure temporary examples are captured before `examples/` is removed
- classify each rule as `required`, `default`, or `optional pattern`

Important constraints:

- `examples/` is temporary source material only
- sibling repos are extraction inputs, not documentation deliverables
- final documentation should use concise, generic examples rather than real project excerpts
- any rule that currently depends on a real project example must be rewritten into a generic example before the examples directory is deleted
- `COMMAND-GO-v040-MIGRATION.md` is used here only as a source of updated library behavior, not as a framing model for the final doc system

## Matrix conventions

Columns:

- `ID`: stable inventory identifier
- `Rule`: concise statement of the rule
- `Scope`: `foundation`, `subsystem`, or `reference`
- `Future Owner`: the document that should own the rule
- `Designation`: `required`, `default`, or `optional pattern`
- `Current Source`: where the rule currently lives
- `Example Signal`: temporary extraction evidence from current code
- `Capture`: whether the rule is already documented well enough or still needs extraction/rewrite

Designation meanings:

- `required`: should be treated as a standard unless there is a specific documented exception
- `default`: preferred normal approach, but deviations may be fine when justified
- `optional pattern`: a useful pattern that should be documented, but is not the baseline expectation for all projects

Capture states:

- `keep`: current guide already contains the rule in a reusable form
- `extract`: move rule into a narrower guide
- `rewrite`: preserve the rule, but rewrite it substantially
- `decide`: keep only if we confirm it belongs in the final system

## Foundations

| ID | Rule | Scope | Future Owner | Designation | Current Source | Example Signal | Capture |
| --- | --- | --- | --- | --- | --- | --- | --- |
| F-01 | Prefer the standard library unless an external dependency removes meaningful code or risk. | foundation | `foundations/philosophy.md` | required | `POLLINATOR_STYLE.md` Core principles | visible across all Go examples | extract |
| F-02 | Keep architecture shallow and direct. | foundation | `foundations/philosophy.md` | required | `POLLINATOR_STYLE.md` Core principles | repeated `cmd -> service -> database/app` shapes | extract |
| F-03 | Separate composition from behavior. | foundation | `foundations/philosophy.md` | required | `POLLINATOR_STYLE.md` Core principles | service constructors and outer `Serve()` patterns | extract |
| F-04 | Make dependencies explicit via options and constructors, not package globals. | foundation | `foundations/philosophy.md` | required | `POLLINATOR_STYLE.md` Core principles | `New(opts)` patterns in service/app/web packages | extract |
| F-05 | Favor clarity over cleverness and keep data flow obvious. | foundation | `foundations/philosophy.md` | required | `POLLINATOR_STYLE.md` Core principles | repeated straightforward handler and command code | keep |
| F-06 | Optimize for author ergonomics and readability over abstraction depth. | foundation | `foundations/philosophy.md` | default | `POLLINATOR_STYLE.md` Core principles | file-local domain logic in service packages | keep |
| F-07 | Prefer domain-oriented naming so engineers can find behavior quickly. | foundation | `foundations/repository-layout.md` | required | `POLLINATOR_STYLE.md` Repository layout | service and database files named by domain | extract |
| F-08 | Keep related behavior local until size or clarity justifies a split. | foundation | `foundations/repository-layout.md` | default | `POLLINATOR_STYLE.md` Domain-oriented naming and file split | mixed types/methods/handlers in single domain files | extract |
| F-09 | Use `internal/` as the default home for application code. | foundation | `foundations/repository-layout.md` | default | `POLLINATOR_STYLE.md` Repository layout | present in most examples | keep |
| F-10 | Use `pkg/` only for deliberately reusable external APIs. | foundation | `subsystems/public-packages.md` | required | `POLLINATOR_STYLE.md` Public libraries | strongest in `consent` and `courier` | extract |
| F-11 | Keep error strings lowercase and unpunctuated. | foundation | `foundations/philosophy.md` | required | `POLLINATOR_STYLE.md` Code style and readability | visible across service/database code | keep |
| F-12 | Prefer explicit names over abbreviations. | foundation | `foundations/philosophy.md` | default | `POLLINATOR_STYLE.md` Code style and readability | visible across CLI and service code | keep |
| F-13 | Use one operation per statement and avoid dense chaining. | foundation | `foundations/philosophy.md` | default | `POLLINATOR_STYLE.md` Code style and readability | visible across commands and handlers | keep |
| F-14 | JSON tags should use `snake_case`. | foundation | `foundations/philosophy.md` | required | `POLLINATOR_STYLE.md` Code style and readability | repeated in service domain types | keep |
| F-15 | Use short, deterministic default test setups and avoid external dependencies in default suites. | foundation | `foundations/testing-philosophy.md` | required | `POLLINATOR_STYLE.md` Tests; `API_TEST_STYLE.md` Core principles | repeated `SetupTestEnv(t)` patterns | extract |
| F-16 | Keep the default test suite fast and hermetic; isolate true integrations behind explicit boundaries. | foundation | `foundations/testing-philosophy.md` | required | `POLLINATOR_STYLE.md` Tests | integration test split in `coffer` | extract |

## CLI command trees

| ID | Rule | Scope | Future Owner | Designation | Current Source | Example Signal | Capture |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CLI-01 | Use one root command in `cmd/<bin>/main.go`. | subsystem | `subsystems/cli-command-trees.md` | required | `POLLINATOR_STYLE.md` CLI structure | `coalition`, `coffer` main roots | extract |
| CLI-02 | Define `HelpOption` with short `-h` and long `--help`. | subsystem | `subsystems/cli-command-trees.md` | required | `POLLINATOR_STYLE.md` CLI structure | root command setup in `coalition`, `coffer` | extract |
| CLI-03 | Include environment/config integration as a root-level concern. | subsystem | `subsystems/cli-command-trees.md` | required | `POLLINATOR_STYLE.md` CLI structure; `COMMAND-GO-v040-MIGRATION.md` | `envs.Command(...)` in roots | extract |
| CLI-04 | Keep `serve` and `api` as top-level subcommands when the binary exposes both server and client roles. | subsystem | `subsystems/cli-command-trees.md` | default | `POLLINATOR_STYLE.md` CLI structure | repeated in `coalition`, `coffer`, `consent`, `courier` | rewrite |
| CLI-05 | Define each `args.Command` as a named global var, not via factory functions. | subsystem | `subsystems/cli-command-trees.md` | required | `POLLINATOR_STYLE.md` CLI structure | repeated `var ...Cmd = &args.Command` pattern | extract |
| CLI-06 | Define each command in its own named var and include subcommands by name rather than inline nesting. | subsystem | `subsystems/cli-command-trees.md` | required | `POLLINATOR_STYLE.md` CLI structure | strong in `coffer` and `cosign` | extract |
| CLI-07 | Split command files by concern: root, serve, api root, and resource-specific subcommands. | subsystem | `subsystems/cli-command-trees.md` | default | `POLLINATOR_STYLE.md` Canonical CLI layout | clear in `coffer` and `coalition` | extract |
| CLI-08 | Structure command handlers by phases: extract inputs, validate/hygiene, setup, execute, format output. | subsystem | `subsystems/cli-command-trees.md` | required | `POLLINATOR_STYLE.md` Command handler style | clear in `coffer` ledger commands | extract |
| CLI-09 | Use small helpers for repeated option/env/config resolution. | subsystem | `subsystems/config-and-credentials.md` | default | `POLLINATOR_STYLE.md` CLI structure; Configuration and environment | `resolveOption`, `loadCredential`, `addParams`, `writeJSON` | extract |
| CLI-10 | Keep command handlers inline on the command definition unless there is a compelling readability reason otherwise. | subsystem | `subsystems/cli-command-trees.md` | default | `POLLINATOR_STYLE.md` Command handler style | repeated in resource command files | extract |
| CLI-11 | Align CLI resource trees with API resource paths where possible. | subsystem | `subsystems/cli-command-trees.md` | default | `POLLINATOR_STYLE.md` Core principles | visible across `api` subcommands | rewrite |
| CLI-12 | Add a top-level `init` command when the system has explicit mutable bootstrap work to perform. | subsystem | `subsystems/cli-command-trees.md` | default | `COMMAND-GO-v040-MIGRATION.md`; `CONFIG-SYSTEM-DESIGN.md` | explicit `init` flow emerging in command-go v0.4.0 | extract |
| CLI-13 | Keep `config` as its own command subtree when the application has a real config subsystem. | subsystem | `subsystems/cli/with-config.md` | default | `CONFIG-SYSTEM-DESIGN.md` | config doc introduces `config init/show/resource` tree | extract |

## Config systems

| ID | Rule | Scope | Future Owner | Designation | Current Source | Example Signal | Capture |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CFG-01 | Treat config as a subsystem, not a helper. | subsystem | `subsystems/config/README.md` | required | `CONFIG-SYSTEM-DESIGN.md` | new dedicated config design doc | extract |
| CFG-02 | Create an `internal/config` package that owns schema, defaults, validation, resolution, resources, secret loading, and bootstrap behavior. | subsystem | `subsystems/config/README.md` | required | `CONFIG-SYSTEM-DESIGN.md` | explicit package shape | extract |
| CFG-03 | Separate authored config from resolved runtime. | subsystem | `subsystems/config/README.md` | required | `CONFIG-SYSTEM-DESIGN.md` | `Config` vs `Runtime` split | extract |
| CFG-04 | Resolve precedence in one place with a clear order: defaults, config file, env, CLI overrides. | subsystem | `subsystems/config/runtime-resolution.md` | required | `CONFIG-SYSTEM-DESIGN.md` | central `Resolve()` guidance | extract |
| CFG-05 | Keep config-dir and data-dir as separate concerns. | subsystem | `subsystems/config/README.md` | required | `CONFIG-SYSTEM-DESIGN.md` | explicit filesystem split | extract |
| CFG-06 | Generate a runnable local baseline natively in Go rather than through shell templates. | subsystem | `subsystems/config/initialization.md` | default | `CONFIG-SYSTEM-DESIGN.md` | `config init` baseline generation | extract |
| CFG-07 | Treat config-backed resource families as first-class files rather than embedding everything into one large root config file. | subsystem | `subsystems/config/resources.md` | default | `CONFIG-SYSTEM-DESIGN.md` | resource directories and CRUD guidance | extract |
| CFG-08 | Be non-destructive by default and require explicit force semantics for overwrites. | subsystem | `subsystems/config/initialization.md` | required | `CONFIG-SYSTEM-DESIGN.md` | explicit safe-write behavior | extract |
| CFG-09 | Provide both authored-config inspection and resolved-runtime inspection views. | subsystem | `subsystems/config/runtime-resolution.md` | default | `CONFIG-SYSTEM-DESIGN.md` | `config show` and `config show --resolved` | extract |
| CFG-10 | Separate config generation from mutable operational initialization. | subsystem | `subsystems/config/initialization.md` | required | `CONFIG-SYSTEM-DESIGN.md`; `COMMAND-GO-v040-MIGRATION.md` | `config init` vs top-level `init` | extract |
| CFG-11 | Keep root path options like `--config-dir` and `--data-dir` global so every command resolves the same environment shape. | subsystem | `subsystems/cli/with-config.md` | required | `CONFIG-SYSTEM-DESIGN.md` | explicit CLI shape | extract |
| CFG-12 | `Resolve()` should be the only place that merges config file, env, CLI overrides, secrets, resources, and derived paths. | subsystem | `subsystems/config/runtime-resolution.md` | required | `CONFIG-SYSTEM-DESIGN.md` | explicit single-owner model | extract |
| CFG-13 | Keep secrets out of the main config file and support environment override first, then file fallback. | subsystem | `subsystems/config/runtime-resolution.md` | required | `CONFIG-SYSTEM-DESIGN.md` | secret handling principles | extract |
| CFG-14 | Use strict decoding and fail early on unknown or invalid config. | subsystem | `subsystems/config/runtime-resolution.md` | required | `CONFIG-SYSTEM-DESIGN.md` | validation and failure philosophy | extract |
| CFG-15 | Commands should translate CLI input into config package calls; services should consume resolved runtime, not re-open config sources. | subsystem | `subsystems/config/README.md` | required | `CONFIG-SYSTEM-DESIGN.md` | explicit boundary rule | extract |
| CFG-16 | Use CLI option -> env var -> default precedence for root path inputs. | subsystem | `subsystems/config/runtime-resolution.md` | required | `CONFIG-SYSTEM-DESIGN.md`; `POLLINATOR_STYLE.md` | root path resolution rule | extract |
| CFG-17 | Keep simple invocation-specific flags on the command itself, even when a full config subsystem exists. | subsystem | `subsystems/cli/with-config.md` | default | `CONFIG-SYSTEM-DESIGN.md` | host/port serve overrides remain command-local | extract |

## Service construction and initialization

| ID | Rule | Scope | Future Owner | Designation | Current Source | Example Signal | Capture |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SVC-01 | The service package is the core of the app and owns business logic plus HTTP handlers. | subsystem | `subsystems/service-construction.md` | required | `POLLINATOR_STYLE.md` Service layer | repeated in service packages | extract |
| SVC-02 | Prefer a concrete `Service` struct with an `Options` constructor. | subsystem | `subsystems/service-construction.md` | required | `POLLINATOR_STYLE.md` Service layer | repeated `New(opts)` patterns | extract |
| SVC-03 | Validate required dependencies in `New(...)` and fail fast. | subsystem | `subsystems/service-construction.md` | required | `POLLINATOR_STYLE.md` Service layer | `compass` and service constructors | extract |
| SVC-04 | Keep service dependencies explicit: store, auth, cors, clock, logger, health hooks, and similar modules. | subsystem | `subsystems/service-construction.md` | required | `POLLINATOR_STYLE.md` Service layer | options structs across service/app packages | extract |
| SVC-05 | Provide `Start()` and `Stop()` only when background processing requires lifecycle hooks. | subsystem | `subsystems/service-construction.md` | optional pattern | `POLLINATOR_STYLE.md` Service layer | present in several services, absent elsewhere | rewrite |
| SVC-06 | Expose a `Serve(...)` entry point that handles serving concerns outside router composition. | subsystem | `subsystems/service-construction.md` | default | `POLLINATOR_STYLE.md` Service layer | `Serve()` methods with base-path mounting | extract |
| SVC-07 | Keep business logic and HTTP handlers together when they share domain types and validation. | subsystem | `subsystems/service-construction.md` | default | `POLLINATOR_STYLE.md` Service layer | repeated domain files in service packages | extract |
| SVC-08 | Use separate production and test composition roots. | subsystem | `subsystems/service-construction.md` | required | `POLLINATOR_STYLE.md` Composition roots | repeated `SetupTestEnv(t)` and constructor use | extract |
| SVC-09 | Declare key permissions centrally and reuse the same permission objects across middleware, init, and tests. | subsystem | `subsystems/service-construction.md` | required | `COMMAND-GO-v040-MIGRATION.md` | permission sets emerging in newer services | extract |
| SVC-10 | Key/bootstrap initialization should be explicit and idempotent rather than implicit during `serve` startup. | subsystem | `subsystems/service-construction.md` | required | `COMMAND-GO-v040-MIGRATION.md` | two-step `init` then `serve` flow | extract |

## Store contracts

| ID | Rule | Scope | Future Owner | Designation | Current Source | Example Signal | Capture |
| --- | --- | --- | --- | --- | --- | --- | --- |
| STO-01 | Define store interfaces in the service/domain layer, not in infrastructure packages. | subsystem | `subsystems/store-contracts.md` | required | `POLLINATOR_STYLE.md` Store contracts | explicit in `coffer`, `coalition`, `consent`, `cosign`, `compass` | extract |
| STO-02 | Define domain structs in the service/domain layer first, then write store methods in terms of them. | subsystem | `subsystems/store-contracts.md` | required | `POLLINATOR_STYLE.md` Store contracts | repeated service-owned domain types | extract |
| STO-03 | Keep store methods expressed in domain operations, not SQL concepts. | subsystem | `subsystems/store-contracts.md` | required | `POLLINATOR_STYLE.md` Store contracts | repeated `InsertX`, `GetX`, `ListX` methods | extract |
| STO-04 | Parameter names should reveal storage representation when relevant, such as unix timestamps or encoded values. | subsystem | `subsystems/store-contracts.md` | default | `POLLINATOR_STYLE.md` Store contracts | explicit in store examples | keep |
| STO-05 | The service layer is the translation boundary between API/domain types and persistence-friendly values. | subsystem | `subsystems/store-contracts.md` | required | `POLLINATOR_STYLE.md` Store contracts | time conversion and wrapper patterns | extract |
| STO-06 | Wrap persistence failures in typed service-layer database errors. | subsystem | `subsystems/http-resource-handlers.md` | default | `POLLINATOR_STYLE.md` Error strategy | repeated database error wrapping | extract |
| STO-07 | Keep handlers free of store-specific translation logic. | subsystem | `subsystems/store-contracts.md` | required | `POLLINATOR_STYLE.md` Store contracts | thin handler/service split | extract |

## HTTP router composition

| ID | Rule | Scope | Future Owner | Designation | Current Source | Example Signal | Capture |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RTR-01 | Build one root router as the composition layer. | subsystem | `subsystems/http-router-composition.md` | required | `POLLINATOR_STYLE.md` Router composition | repeated `http.NewServeMux()` roots | extract |
| RTR-02 | Compose domain routers into the root mux additively. | subsystem | `subsystems/http-router-composition.md` | required | `POLLINATOR_STYLE.md` Router composition | `buildXRouter` and `registerXRoutes` patterns | extract |
| RTR-03 | Use explicit method+path patterns, not method switches inside handlers. | subsystem | `subsystems/http-router-composition.md` | required | `POLLINATOR_STYLE.md` HTTP/API design | repeated across service and app routers | extract |
| RTR-04 | Use handler-first router builders that return `http.Handler` for mountable route groups. | subsystem | `subsystems/http-router-composition.md` | required | `COMMAND-GO-v040-MIGRATION.md` | newer `wire.Subrouter` usage in `courier` and `cosign` | extract |
| RTR-05 | Mount subrouters with `wire.Subrouter` rather than ad hoc strip-prefix mount helpers. | subsystem | `subsystems/http-router-composition.md` | required | `COMMAND-GO-v040-MIGRATION.md` | strong in `courier` and `cosign` | extract |
| RTR-06 | Use scoped child routers at boundaries like `/admin`, `/settings`, or resource group prefixes. | subsystem | `subsystems/http-router-composition.md` | default | `POLLINATOR_STYLE.md` Router composition; `COMMAND-GO-v040-MIGRATION.md` | strongest in `courier` and `cosign` | extract |
| RTR-07 | Apply middleware at the highest safe boundary, not ad hoc per route. | subsystem | `subsystems/http-router-composition.md` | required | `POLLINATOR_STYLE.md` Router composition | strong in `courier` and `coalition` | extract |
| RTR-08 | Distinguish handler-level middleware wrappers from handlerfunc-level wrappers and use each at the right registration boundary. | subsystem | `subsystems/http-router-composition.md` | required | `COMMAND-GO-v040-MIGRATION.md` | `WithAuth` vs `WithAuthFunc`, `WithCORS` vs `WithCORSFunc` | extract |
| RTR-09 | Build middleware bundles from `Service` dependencies during router composition. | subsystem | `subsystems/http-router-composition.md` | required | `POLLINATOR_STYLE.md` Router composition | repeated `Middleware` structs | extract |
| RTR-10 | Keep deployment base-path mounting outside inner router composition. | subsystem | `subsystems/http-router-composition.md` | required | `POLLINATOR_STYLE.md` Router composition | repeated outer mounts in `Serve()` | extract |
| RTR-11 | Keep startup/listen concerns out of route registration. | subsystem | `subsystems/http-router-composition.md` | required | `POLLINATOR_STYLE.md` Router composition | repeated `BuildRouter()` vs `Serve()` split | keep |
| RTR-12 | Treat auth, CORS, rate limiting, and similar concerns as injected middleware modules. | subsystem | `subsystems/http-router-composition.md` | required | `POLLINATOR_STYLE.md` HTTP/API design | strong in `courier` and `coalition` | extract |
| RTR-13 | Mount package-provided settings handlers directly when a subsystem exposes its own admin/settings API. | subsystem | `subsystems/http-router-composition.md` | default | `COMMAND-GO-v040-MIGRATION.md` | `s.keys.Handler()` and `s.cors.Handler()` in current code | extract |

## HTTP resource handlers and API design

| ID | Rule | Scope | Future Owner | Designation | Current Source | Example Signal | Capture |
| --- | --- | --- | --- | --- | --- | --- | --- |
| API-01 | Base API paths should be explicit and versioned when appropriate. | subsystem | `subsystems/http-resource-handlers.md` | required | `POLLINATOR_STYLE.md` HTTP/API design | repeated `/api/v1` usage | keep |
| API-02 | Keep handlers thin: decode -> validate -> call service -> encode response. | subsystem | `subsystems/http-resource-handlers.md` | required | `POLLINATOR_STYLE.md` Store contracts; HTTP/API design | repeated service handlers | extract |
| API-03 | Define request and response structs close to the service/handler code that owns them and export them only when external packages truly need them. | subsystem | `subsystems/http-resource-handlers.md` | default | `POLLINATOR_STYLE.md` HTTP/API design | visible in service and CLI coupling | rewrite |
| API-04 | Bias toward resource routes returning the JSON representation of the resource itself when that keeps the contract simple. | subsystem | `subsystems/http-resource-handlers.md` | default | `POLLINATOR_STYLE.md` HTTP/API design | repeated in service APIs | rewrite |
| API-05 | Map service errors to HTTP status codes in a small helper. | subsystem | `subsystems/http-resource-handlers.md` | required | `POLLINATOR_STYLE.md` Error strategy | repeated or implied across services | extract |
| API-06 | Use path values and explicit query parsing rather than hidden routing abstractions. | subsystem | `subsystems/http-resource-handlers.md` | required | `POLLINATOR_STYLE.md` HTTP/API design | repeated `r.PathValue(...)` and pagination parsing | keep |
| API-07 | Register explicit OPTIONS routes where CORS/preflight behavior requires it. | subsystem | `subsystems/http-router-composition.md` | default | `POLLINATOR_STYLE.md` HTTP/API design | visible in admin routers | extract |
| API-08 | Reflect modern command-go key-management payload shapes in handler and client expectations rather than assuming raw token strings. | subsystem | `subsystems/http-resource-handlers.md` | optional pattern | `COMMAND-GO-v040-MIGRATION.md` | library-backed settings endpoints | decide |

## Database adapters and SQL-interfacing code

| ID | Rule | Scope | Future Owner | Designation | Current Source | Example Signal | Capture |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DB-01 | Keep the database package or runtime store layer thin and mechanical. | subsystem | `subsystems/database-adapters.md` | required | `POLLINATOR_STYLE.md` Database layer | repeated database/runtime package layout | extract |
| DB-02 | Provide explicit open/init/migration entry points. | subsystem | `subsystems/database-adapters.md` | required | `POLLINATOR_STYLE.md` Database layer | repeated `database.go` or `store.go` plus schema setup | extract |
| DB-03 | Open SQLite with explicit connection settings suitable for serialized local operation. | subsystem | `subsystems/database-adapters.md` | default | `POLLINATOR_STYLE.md` Database layer; SQL examples | `composer` sets max open/idle conns to 1 | rewrite |
| DB-04 | Enable SQLite foreign keys during store initialization. | subsystem | `subsystems/database-adapters.md` | required | `POLLINATOR_STYLE.md` Database layer; SQL examples | explicit in `consent` and `composer` | extract |
| DB-05 | Use ordered migrations defined in Go, not scattered schema side effects. | subsystem | `subsystems/database-adapters.md` | required | `POLLINATOR_STYLE.md` Database layer | strongest in `composer` schema migrations | extract |
| DB-06 | Use positional SQL parameters. | subsystem | `subsystems/database-adapters.md` | required | `POLLINATOR_STYLE.md` Database layer | repeated query style across `coffer`, `consent`, `composer` | keep |
| DB-07 | Prefer explicit `INSERT ... ON CONFLICT` upserts for idempotent writes. | subsystem | `subsystems/database-adapters.md` | default | `POLLINATOR_STYLE.md` Database layer | strong in `coffer` and `consent` | extract |
| DB-08 | Store timestamps in mechanical persistence formats and convert them at boundaries. | subsystem | `subsystems/database-adapters.md` | required | `POLLINATOR_STYLE.md` Database layer | unix and formatted-time conversion patterns | extract |
| DB-09 | Add a compile-time conformance check from the adapter to the service-owned interface when the adapter implements a service contract. | subsystem | `subsystems/database-adapters.md` | required | `POLLINATOR_STYLE.md` Store implementation integration | repeated interface conformance checks | extract |
| DB-10 | Do not leak SQL driver types into service APIs. | subsystem | `subsystems/database-adapters.md` | required | `POLLINATOR_STYLE.md` Store implementation integration | repeated separation patterns | keep |
| DB-11 | Database code should read as query/scan/convert/return, not as a second business layer. | subsystem | `subsystems/database-adapters.md` | required | `POLLINATOR_STYLE.md` Store implementation integration | visible across database files | extract |
| DB-12 | Use transactions for multi-step state changes and for operations that need a consistent view across multiple SQL steps. | subsystem | `subsystems/database-adapters.md` | required | SQL examples in `coffer`, `consent`, `composer` | strongest in `composer` runtime store | extract |
| DB-13 | Begin a transaction early, `defer` rollback immediately, and make commit the explicit success path. | subsystem | `subsystems/database-adapters.md` | required | SQL examples in `consent` and `composer` | repeated `BeginTx` + deferred rollback + commit | extract |
| DB-14 | When an operation spans many SQL statements, factor the public method into small `sql*Tx` helpers that operate on `*sql.Tx`. | subsystem | `subsystems/database-adapters.md` | default | SQL examples in `composer` | `sqlListTasksTx`, `sqlUpdateRunStatusTx`, etc. | extract |
| DB-15 | Use `QueryContext`, `QueryRowContext`, and `ExecContext` when a context is available at the store boundary. | subsystem | `subsystems/database-adapters.md` | required | SQL examples in `composer` | consistent context-aware runtime store methods | extract |
| DB-16 | Scan rows into local primitives and `sql.Null*` values, then construct domain values explicitly. | subsystem | `subsystems/database-adapters.md` | required | SQL examples in `coffer`, `consent`, `composer` | repeated local scan variables then domain assembly | extract |
| DB-17 | Check `rows.Err()` after iteration. | subsystem | `subsystems/database-adapters.md` | required | SQL examples in `consent` and `composer` | explicit in list methods | extract |
| DB-18 | Wrap SQL errors with operation-specific context using `%w` when preserving the underlying error matters. | subsystem | `subsystems/database-adapters.md` | required | SQL examples in `coffer`, `consent`, `composer` | repeated `fmt.Errorf("op: %w", err)` patterns | extract |
| DB-19 | Build dynamic WHERE fragments and argument lists explicitly and locally when queries need optional filters. | subsystem | `subsystems/database-adapters.md` | default | SQL examples in `composer` | `hasOperator`, `hasStatus`, local args slice | extract |
| DB-20 | Keep schema constraints explicit in SQL with `NOT NULL`, `CHECK`, `UNIQUE`, and foreign keys instead of relying on application code alone. | subsystem | `subsystems/database-adapters.md` | required | SQL examples in `consent` and `composer` | strong migration/schema definitions | extract |
| DB-21 | Keep store-level time creation centralized when persistent timestamps must be consistent within an operation. | subsystem | `subsystems/database-adapters.md` | default | SQL examples in `composer` | `nowFmt()` helper and shared operation timestamps | extract |

## Database tests

| ID | Rule | Scope | Future Owner | Designation | Current Source | Example Signal | Capture |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DBT-01 | Database tests should verify observable adapter behavior through public store methods, not private SQL helpers. | subsystem | `subsystems/database-tests.md` | required | `POLLINATOR_STYLE.md` Tests | repeated `database_test` packages calling adapter methods in `coalition`, `consent`, `courier`, `composer` | extract |
| DBT-02 | Keep database tests alongside the package they exercise and use external test packages by default. | subsystem | `subsystems/database-tests.md` | required | `POLLINATOR_STYLE.md` Tests | dominant `package database_test` / `package runtime_test` pattern; public-package variant would use `package mylib_test` | extract |
| DBT-03 | Use a real isolated SQLite database for default adapter tests, usually in-memory and temp-file backed only when reopen behavior matters. | subsystem | `subsystems/database-tests.md` | required | `POLLINATOR_STYLE.md` Tests | repeated `:memory:` setups plus `composer` temp-path reopen tests | extract |
| DBT-04 | Own database lifecycle in setup helpers or `t.Cleanup()` so each test gets isolated state and explicit cleanup. | subsystem | `subsystems/database-tests.md` | required | `POLLINATOR_STYLE.md` Tests; `API_TEST_STYLE.md` internal/testutil responsibilities | repeated `SetupTestDB`, `openTestStore`, and `t.Cleanup()` patterns | extract |
| DBT-05 | Use test-only helpers for lifecycle and deterministic seeding when they shorten tests, but keep adapter calls and assertions visible in the test. | subsystem | `subsystems/database-tests.md` | default | `API_TEST_STYLE.md` internal/testutil responsibilities | `internal/testutil` in internal packages; same-directory `_test.go` helpers for public-package variants | extract |
| DBT-06 | Seed through adapter methods by default; use service-level setup helpers only when realistic multi-table state would otherwise be noisy to arrange. | subsystem | `subsystems/database-tests.md` | default | example repos | direct adapter setup dominates in `coalition`, `consent`, `courier`; service-assisted seeding appears in `coffer` | rewrite |
| DBT-07 | Verify writes with follow-up reads at the narrowest sensible boundary: adapter reads for behavior, raw SQL only for storage mechanics the adapter API does not expose cleanly. | subsystem | `subsystems/database-tests.md` | required | example repos | read-back assertions in `consent` and `composer`; raw SQL inspection in `coalition`; schema inspection in `coffer` migrations tests | extract |
| DBT-08 | Add focused open/init/migration tests that verify schema readiness and version transitions through observable effects. | subsystem | `subsystems/database-tests.md` | required | `POLLINATOR_STYLE.md` Database layer; example repos | `consent` open/schema tests, `courier` health/open tests, `coffer` migration/version test | extract |
| DBT-09 | Cover the persistence behaviors that matter for each method: not-found and constraint cases, idempotent upserts, null handling, ordering/filter semantics, and transactional outcomes where applicable. | subsystem | `subsystems/database-tests.md` | required | `POLLINATOR_STYLE.md` Tests | repeated duplicate/not-found/upsert/list semantics across `consent`, `coalition`, `composer`, and `coffer` | extract |
| DBT-10 | Use `t.Parallel()` only when each test has isolated database state and helpers do not rely on unsafe shared mutable state. | subsystem | `subsystems/database-tests.md` | default | `POLLINATOR_STYLE.md` Tests | heavy use in isolated `consent` tests, omitted in less isolated suites | extract |
| DBT-11 | Use internal-package tests only for intentionally internal migration or initialization helpers; otherwise prefer black-box adapter tests. | subsystem | `subsystems/database-tests.md` | default | example repos | `coffer/internal/database/migrations_test.go` is the main internal-package exception | extract |

## API tests and testutil

| ID | Rule | Scope | Future Owner | Designation | Current Source | Example Signal | Capture |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TST-01 | API tests should verify observable HTTP behavior, not private internals. | subsystem | `subsystems/api/testing.md` | required | `API_TEST_STYLE.md` Core principles | repeated router-driven API tests | keep |
| TST-02 | Each test should focus on one scenario. | subsystem | `subsystems/api/testing.md` | required | `API_TEST_STYLE.md` Core principles | strong in current examples, uneven in older ones | keep |
| TST-03 | Use Arrange -> Act -> Assert ordering with explicit chunk comments. | subsystem | `subsystems/api/testing.md` | required | `API_TEST_STYLE.md` Canonical test structure | partially present in examples | extract |
| TST-04 | Assert status first, then payload/error, then side effects. | subsystem | `subsystems/api/testing.md` | required | `API_TEST_STYLE.md` Core principles | repeated result helper usage | keep |
| TST-05 | Keep setup deterministic and local. | subsystem | `subsystems/api/testing.md` | required | `API_TEST_STYLE.md` Core principles | repeated `SetupTestEnv(t)` pattern | keep |
| TST-06 | Use `internal/testutil` as the test composition root. | subsystem | `subsystems/api/testing.md` | required | `API_TEST_STYLE.md` internal/testutil responsibilities | repeated across service/database tests | extract |
| TST-07 | `internal/testutil` should own lifecycle and cleanup. | subsystem | `subsystems/api/testing.md` | required | `API_TEST_STYLE.md` Recommended `TestEnv` shape | repeated in setup helpers | extract |
| TST-08 | Seed helpers should be deterministic and encode scenario intent. | subsystem | `subsystems/api/testing.md` | required | `API_TEST_STYLE.md` Seed helpers | repeated seed helper patterns | extract |
| TST-09 | Scenario helpers may help setup, but should not hide assertions. | subsystem | `subsystems/api/testing.md` | required | `API_TEST_STYLE.md` Scenario helpers | visible in testutil usage | keep |
| TST-10 | Use `wire.TestX` helpers and typed response assertions where they clarify intent. | subsystem | `subsystems/api/testing.md` | default | `API_TEST_STYLE.md` Standard packages and helpers | repeated in API tests | extract |
| TST-11 | Table-driven tests should be used only when they improve readability. | subsystem | `subsystems/api/testing.md` | default | `API_TEST_STYLE.md` Single-scenario vs table-driven | mixed quality in examples | keep |
| TST-12 | Do not use `t.Parallel()` by default; only when isolation is clearly safe. | subsystem | `subsystems/api/testing.md` | default | `API_TEST_STYLE.md` Parallelism policy | examples vary | extract |
| TST-13 | Non-empty JSON request bodies should use pretty-printed raw string literals and empty objects should use exactly `"{}"` when this materially improves scanability. | subsystem | `subsystems/api/testing.md` | default | `API_TEST_STYLE.md` Coding style conventions | not yet consistent in all examples | rewrite |
| TST-14 | Request body, URL, and headers should be spelled out in their own visible setup statements. | subsystem | `subsystems/api/testing.md` | required | `API_TEST_STYLE.md` Canonical test structure | strong in many API tests | extract |
| TST-15 | Prefer in-process router tests over real network listeners. | subsystem | `subsystems/api/testing.md` | required | `API_TEST_STYLE.md` Scope; `POLLINATOR_STYLE.md` Tests | repeated across examples | keep |
| TST-16 | Update CORS preflight tests to include the method request header expected by newer command-go behavior. | subsystem | `subsystems/api/testing.md` | default | `COMMAND-GO-v040-MIGRATION.md` | newer library behavior | extract |

## Server-rendered HTMX UI and app view models

| ID | Rule | Scope | Future Owner | Designation | Current Source | Example Signal | Capture |
| --- | --- | --- | --- | --- | --- | --- | --- |
| FE-01 | Render HTML on the server and use HTMX for fragment updates. | subsystem | `subsystems/server-rendered-htmx-ui.md` | required | `FRONT_END_STYLE.md` Core principles | strongest in `compass` and `cosign` | extract |
| FE-02 | Keep progressive enhancement so every interaction has a non-HTMX fallback. | subsystem | `subsystems/server-rendered-htmx-ui.md` | required | `FRONT_END_STYLE.md` Core principles | explicit in docs, partial in examples | extract |
| FE-03 | Treat the server as the source of truth and re-render from domain state after writes. | subsystem | `subsystems/server-rendered-htmx-ui.md` | required | `FRONT_END_STYLE.md` Core principles | handler/re-render patterns | extract |
| FE-04 | Keep client-side JavaScript minimal and focused on enhancement. | subsystem | `subsystems/server-rendered-htmx-ui.md` | default | `FRONT_END_STYLE.md` Core principles | light JS in frontend examples | keep |
| FE-05 | Use explicit view models between domain data and templates. | subsystem | `subsystems/app-view-models.md` | required | `FRONT_END_STYLE.md` Core principles; View module contract | strong in `compass` and `cosign` | extract |
| FE-06 | Organize UI code by ownership boundaries, with one presentation module per concern. | subsystem | `subsystems/app-view-models.md` | required | `FRONT_END_STYLE.md` Recommended package shape; View module contract | repeated `view_*.go` structure | extract |
| FE-07 | Handlers should orchestrate, view builders should shape data, and templates should render. | subsystem | `subsystems/server-rendered-htmx-ui.md` | required | `FRONT_END_STYLE.md` Recommended package shape | repeated server/renderer/view split | extract |
| FE-08 | Keep one renderer boundary so handlers call renderer methods, not template names directly. | subsystem | `subsystems/server-rendered-htmx-ui.md` | required | `FRONT_END_STYLE.md` View module contract | strongest in `compass` and `cosign` renderer setup | extract |
| FE-09 | Maintain both full-page render paths and fragment render paths. | subsystem | `subsystems/server-rendered-htmx-ui.md` | required | `FRONT_END_STYLE.md` Rendering architecture | repeated detail/list flow patterns | extract |
| FE-10 | Break templates into reusable named fragments with stable replaceable IDs. | subsystem | `subsystems/server-rendered-htmx-ui.md` | default | `FRONT_END_STYLE.md` Fragment composition | repeated in frontend templates | extract |
| FE-11 | Parse HTMX headers into a request-context struct. | subsystem | `subsystems/server-rendered-htmx-ui.md` | default | `FRONT_END_STYLE.md` HTMX request handling pattern | explicit context files in frontend apps | extract |
| FE-12 | After mutations, prefer authoritative re-rendering of the smallest consistent container. | subsystem | `subsystems/server-rendered-htmx-ui.md` | required | `FRONT_END_STYLE.md` Partial update strategy | repeated handler behavior | extract |
| FE-13 | Use out-of-band swaps intentionally when multiple regions must stay in sync. | subsystem | `subsystems/server-rendered-htmx-ui.md` | default | `FRONT_END_STYLE.md` Partial update strategy | visible in richer examples | extract |
| FE-14 | Keep templates declarative and move formatting into Go presentation code. | subsystem | `subsystems/app-view-models.md` | required | `FRONT_END_STYLE.md` View-model-first templates | repeated view builder pattern | extract |
| FE-15 | Add focused tests around view mapping and render-path parity. | subsystem | `subsystems/server-rendered-htmx-ui.md` | default | `FRONT_END_STYLE.md` Testing | some frontend test coverage in examples | rewrite |

## Public packages

| ID | Rule | Scope | Future Owner | Designation | Current Source | Example Signal | Capture |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PKG-01 | Use `pkg/` only when the package is intentionally reusable outside the application. | subsystem | `subsystems/public-packages.md` | required | `POLLINATOR_STYLE.md` Public libraries | strongest in `consent` and `courier` | extract |
| PKG-02 | Public packages should include `doc.go` with package-level documentation and usage guidance. | subsystem | `subsystems/public-packages.md` | required | `POLLINATOR_STYLE.md` Public libraries | clear in `consent/pkg/*` | extract |
| PKG-03 | Keep public interfaces small and documented. | subsystem | `subsystems/public-packages.md` | required | `POLLINATOR_STYLE.md` Public libraries | visible in `pkg/client` and `pkg/tokens` | extract |

## Build and project action surface

| ID | Rule | Scope | Future Owner | Designation | Current Source | Example Signal | Capture |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BLD-01 | Provide `build`, `test`, and `install` targets at minimum. | subsystem | `subsystems/project-actions.md` or `foundations/repository-layout.md` | default | `POLLINATOR_STYLE.md` Build and automation conventions | repeated `Makefile` shape | decide |
| BLD-02 | Use the `Makefile` as the primary local action surface. | subsystem | `subsystems/project-actions.md` or `foundations/repository-layout.md` | default | `POLLINATOR_STYLE.md` Build and automation conventions | repeated across examples | decide |
| BLD-03 | Prefer thin automation that composes public CLI commands over private setup scripts. | subsystem | `subsystems/project-actions.md` | default | `CONFIG-SYSTEM-DESIGN.md` | `make init` guidance | extract |

## Legacy and anti-pattern rules

| ID | Rule | Scope | Future Owner | Designation | Current Source | Example Signal | Capture |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A-01 | Avoid package-level mutable state for stores and services. | foundation | `foundations/philosophy.md` | required | `POLLINATOR_STYLE.md` Legacy patterns to avoid | mostly absent from newer examples | extract |
| A-02 | Avoid deep or overly generic abstractions when direct code is clearer. | foundation | `foundations/philosophy.md` | required | `POLLINATOR_STYLE.md` Legacy patterns to avoid | repeated direct patterns across examples | keep |
| A-03 | Avoid custom JSON endpoints when HTML fragment responses already satisfy a server-rendered UI interaction. | subsystem | `subsystems/server-rendered-htmx-ui.md` | default | `FRONT_END_STYLE.md` Practical guardrails | frontend apps lean toward HTML fragments | extract |
| A-04 | Avoid per-route ad hoc response styles and standardize around a small set of response patterns. | subsystem | `subsystems/http-resource-handlers.md` | required | `FRONT_END_STYLE.md` Practical guardrails; `POLLINATOR_STYLE.md` HTTP/API design | repeated envelope and render conventions | rewrite |
| A-05 | Avoid giant helper APIs that hide test Arrange/Act/Assert intent. | subsystem | `subsystems/api/testing.md` | required | `API_TEST_STYLE.md` internal/testutil responsibilities | repeated guidance | keep |
| A-06 | Do not re-implement config precedence logic in individual commands. | subsystem | `subsystems/cli/with-config.md` | required | `CONFIG-SYSTEM-DESIGN.md` | central `Resolve()` rule | extract |
| A-07 | Do not bootstrap mutable auth/key state implicitly during normal `serve` startup. | subsystem | `subsystems/service-construction.md` | required | `COMMAND-GO-v040-MIGRATION.md` | explicit init flow replaces bootstrap token startup | extract |

## Early conclusions from the updated matrix

### 1. `POLLINATOR_STYLE.md` is source material, not a future final shape

It still contains rules for many distinct future guides, and the new config and command-go inputs widen that gap further.

### 2. Config systems now clearly deserve their own first-class subsystem guide

This is not just an addendum to CLI or environment handling anymore. It has its own package boundary, runtime contract, init flow, and testing expectations.

### 3. Router composition rules have materially changed with newer command-go usage

The matrix now needs to treat these as current style rules:

- handler-first route-group builders
- `wire.Subrouter` mounts
- handler vs handlerfunc middleware separation
- package-provided settings handlers
- explicit init flow for key/bootstrap state

### 4. SQL style is stronger and more specific than the original docs suggested

The code in `coffer`, `consent`, and `composer` adds real style rules around:

- transactional boundaries
- helper layering around `*sql.Tx`
- dynamic query construction
- context-aware SQL methods
- migration structure
- schema constraint explicitness
- scan/convert discipline

### 5. The matrix is now ready to drive extraction work

With designations added, this document can now act as the intermediate control plane between the old docs and the future guide set.

## Rules that most need rewrite before temporary examples disappear

These still depend most heavily on project-shaped evidence and should be genericized early:

- `CLI-04` top-level `serve`/`api` guidance
- `CLI-11` CLI tree aligns to API tree
- `API-03` request/response struct placement
- `API-04` resource-return guidance
- `DB-03` SQLite open/default tuning guidance
- `TST-13` JSON body formatting rule
- `FE-15` frontend testing expectations
- `A-04` standardized response patterns

## Suggested next pass after review

1. finalize any designation changes you want to make
2. choose the first extraction set
3. write new guides from this matrix, not from the old documents directly
4. start generic example generation alongside each new guide so temporary source projects can be removed safely
