# Service Construction

This guide defines the standard shape for constructing application services in this style system.

It focuses on the service package boundary, dependency wiring, lifecycle hooks, and the split between explicit bootstrap work and normal runtime startup.

The goal is to make services:

- explicit about what they depend on
- easy to compose in production and tests
- easy to reason about as the application's behavioral core
- safe about initialization of mutable state

## When to use this guide

Use this guide when you are:

- creating an `internal/service` package
- designing a `Service` constructor and dependency model
- deciding where HTTP handlers and domain logic should live
- adding lifecycle hooks or startup behavior
- separating explicit initialization from normal `serve` startup

## Non-goals

This guide does not define:

- detailed store interface design
- HTTP route tree composition
- config resolution mechanics
- SQL adapter implementation

Those belong in adjacent subsystem guides.

## Core rules

- Treat the service package as the core of the application.
- Prefer a concrete `Service` struct with an `Options` constructor.
- Validate required dependencies in `New(...)` and fail fast.
- Keep dependencies explicit in the options struct.
- Keep business logic and HTTP handlers together when they share domain types and validation.
- Use separate production and test composition roots.
- Expose `Serve(...)` for serving concerns outside router composition.
- Add `Start()` and `Stop()` only when background processing truly requires lifecycle hooks.
- Declare key permissions centrally and reuse them everywhere.
- Keep bootstrap initialization explicit and idempotent rather than implicit during `serve`.

## What this subsystem owns

The service package should own:

- domain types
- business logic
- store contracts
- HTTP handlers
- router composition entry points
- permission declarations used across middleware and initialization

It should not own:

- raw config file loading
- SQL details
- command tree structure
- build automation

## Canonical package shape

Use a layout like:

```text
internal/service/
  service.go
  store.go
  router.go
  health.go
  documents.go
  settings.go
```

The shape matters more than the filenames:

- `service.go` owns the `Service` type, `Options`, constructor, and shared lifecycle methods
- domain files own domain-specific types, methods, and handlers
- `router.go` owns router composition

## Constructor shape

Prefer a concrete service with explicit options:

```go
type Options struct {
	Store       Store
	KeysOptions keys.Options
	CORSOptions cors.Options
	Clock       func() time.Time
	Logger      *log.Logger
	HealthCheck func() error
}

type Service struct {
	store Store
	keys  *keys.Service
	cors  *cors.Service
	clock func() time.Time
	log   *log.Logger
}

func New(opts Options) (*Service, error) {
	if opts.Store == nil {
		return nil, errors.New("store is required")
	}
	if opts.Clock == nil {
		return nil, errors.New("clock is required")
	}

	keysSvc, err := keys.New(opts.KeysOptions)
	if err != nil {
		return nil, err
	}
	corsSvc, err := cors.New(opts.CORSOptions)
	if err != nil {
		return nil, err
	}

	return &Service{
		store: opts.Store,
		keys:  keysSvc,
		cors:  corsSvc,
		clock: opts.Clock,
		log:   opts.Logger,
	}, nil
}
```

The main rule is simple: if the service needs something, the constructor should say so plainly.

Do not hide required dependencies behind package globals or deferred late binding.

## Dependency model

A good `Options` struct names real dependencies directly.

Typical dependencies include:

- store or repository contracts
- auth/key services
- CORS service
- clock
- logger
- health check hooks
- background workers or queue clients, when needed

Validate required dependencies in `New(...)` so failure happens early and locally.

## Domain locality

Keep business logic and HTTP handlers together when they share the same domain types and validation rules.

For example, `documents.go` may reasonably contain:

- `Document` types
- `CreateDocument(...)`
- `handleCreateDocument(...)`
- `handleGetDocument(...)`

This keeps:

- validation near the behavior it protects
- handler and service flows easy to compare
- domain code easier to find

Split by concern only when the file stops being easy to read. Do not pre-emptively fragment domains into many tiny files.

## Composition roots

Use separate composition roots for production and tests.

Production composition root responsibilities:

- resolve config
- open databases and external clients
- construct the service
- invoke `Serve(...)` or other top-level entry points

Test composition root responsibilities:

- create deterministic ephemeral dependencies
- construct the service with test wiring
- own lifecycle cleanup
- expose only what tests use regularly

This keeps domain behavior stable while allowing production and test wiring to differ cleanly.

## Permissions and bootstrap initialization

Declare key permissions centrally and reuse the same permission objects across:

- auth middleware
- explicit initialization flows
- tests
- client and admin helpers when needed

For example:

```go
var (
	PermissionRead = keys.Permission{Name: "read"}
	PermissionWrite = keys.Permission{Name: "write"}
	PermissionAdmin = keys.Permission{Name: "admin"}
)

func AllKeyPermissions() []*keys.Permission {
	return []*keys.Permission{
		&PermissionRead,
		&PermissionWrite,
		&PermissionAdmin,
	}
}
```

Bootstrap initialization must be explicit.

Prefer a dedicated top-level `init` command or initialization entry point that:

- opens the required stores
- constructs the keys or auth subsystem with declared permissions
- initializes bootstrap state explicitly
- treats already-initialized state as success when repetition is safe

Do not bootstrap mutable auth or key state implicitly during `serve` startup.

## Lifecycle hooks

Only add `Start()` and `Stop()` when the service actually owns background processing or long-lived lifecycle work.

Good reasons include:

- polling loops
- queue consumers
- background refreshers
- metrics or health goroutines that need coordinated shutdown

If the service only handles in-process request/response behavior, a constructor plus `Serve(...)` is usually enough.

## `Serve(...)` boundary

`Serve(...)` should own serving concerns outside router composition.

That typically includes:

- host and port inputs
- deployment base path mounting
- listen and shutdown behavior

It should not own:

- business initialization side effects
- config precedence logic
- low-level route registration details

Those belong elsewhere.

## Canonical flow

The normal shape is:

1. outer layer resolves config and opens dependencies
2. outer layer constructs `Service` with explicit `Options`
3. service builds its router internally
4. `Serve(...)` mounts deployment-specific outer concerns
5. explicit `init` handles mutable bootstrap work separately from serving

That separation keeps runtime startup predictable and makes tests easier to compose in-process.

## Testing expectations

Service construction should be easy to test for:

- required dependency validation in `New(...)`
- correct construction of middleware or auth modules from options
- explicit init behavior and idempotency
- separation between normal serve startup and mutable bootstrap work
- test composition root setup and cleanup
- lifecycle hook behavior, when `Start()` and `Stop()` exist

Prefer tests that construct the service directly instead of reaching through a CLI command when the constructor contract is the real behavior under test.

## Anti-patterns

- package-level mutable service state
- constructors that silently fill in critical dependencies
- config file reading inside domain methods
- bootstrapping auth or key state during every `serve`
- spreading one domain's types, methods, and handlers across many tiny files without a readability benefit
- adding `Start()` and `Stop()` to services that do not own background work
- separate production and test behavior hidden behind conditionals in the service package itself

## Generic example

```go
type Options struct {
	Store       Store
	KeysOptions keys.Options
	Clock       func() time.Time
}

func New(opts Options) (*Service, error) {
	if opts.Store == nil {
		return nil, errors.New("store is required")
	}
	if opts.Clock == nil {
		return nil, errors.New("clock is required")
	}

	keysSvc, err := keys.New(opts.KeysOptions)
	if err != nil {
		return nil, err
	}

	return &Service{
		store: opts.Store,
		keys:  keysSvc,
		clock: opts.Clock,
	}, nil
}

func (s *Service) Serve(host string, port int, basePath string) error {
	api := s.BuildRouter()
	return serveHTTP(host, port, basePath, api)
}
```

This shape keeps the constructor honest, the service boundary obvious, and the startup flow easy to follow.

## Related guides

- `store-contracts.md`
- `http-router-composition.md`
- `config-systems.md`
