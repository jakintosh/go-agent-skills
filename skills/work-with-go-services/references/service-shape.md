# Defining a Service

This guide defines the default shape of an `internal/service` package.

Use it when you are creating the application's core domain package, defining a `Service` constructor, or deciding what belongs inside the application's main behavioral boundary.

The service package is the domain behavior boundary for the project. It defines domain behavior, domain types, service errors, service-owned store contracts, permission declarations, and explicit bootstrap or lifecycle hooks when the domain needs them. Pair this guide with the [API skill](../../work-with-go-http-apis/SKILL.md) for HTTP contracts and the [server skill](../../work-with-go-servers/SKILL.md) for production serving composition.

## Contents

- [Required](#required)
- [Canonical Package Shape](#canonical-package-shape)
- [Constructor Pattern](#constructor-pattern)
- [Domain Locality](#domain-locality)
- [DTO Boundary](#dto-boundary)
- [Default Flow](#default-flow)
- [Optional Branches](#optional-branches)
- [Testing Expectations](#testing-expectations)

## Required

- Treat `internal/service` as the application core.
- Use a concrete `Service` struct with an explicit `Options` constructor.
- Validate required dependencies in `New(...)`.
- Keep domain behavior and domain types together.
- Validate domain meaning in service methods, not raw ingress formatting.
- Keep config resolution and external dependency setup outside the service package.
- Define store interfaces in `internal/service`.
- Keep service types separate from API DTOs.
- Keep permission constants in `internal/service` when they express domain authorization.
- Keep HTTP handlers, route composition, listen behavior, and deployment mounting in the API or server layer.
- When API-key permissions are used, keep the permission vocabulary in `internal/service` and wire enforcement in `internal/api`.

## Canonical Package Shape

Use a layout like:

```text
internal/service/
  service.go
  store.go
  errors.go
  permissions.go
  documents.go
```

The exact filenames may vary. The ownership split should stay clear:

- `service.go` owns `Service`, `Options`, and `New(...)`.
- `store.go` owns service-facing persistence contracts.
- `errors.go` owns service errors.
- domain files own one coherent domain area each.

## Constructor Pattern

Use `Options` to name the service's real dependencies directly.

```go
package service

import (
	"errors"
	"log"
	"time"
)

type Store interface {
	ListDocuments(limit int, offset int) ([]Document, error)
	CreateDocument(document *Document) error
}

type Options struct {
	Store  Store
	Clock  func() time.Time
	Logger *log.Logger
}

type Service struct {
	store Store
	clock func() time.Time
	log   *log.Logger
}

func New(
	opts Options,
) (
	*Service,
	error,
) {
	if opts.Store == nil {
		return nil, errors.New("service: store required")
	}
	if opts.Clock == nil {
		return nil, errors.New("service: clock required")
	}

	return &Service{
		store: opts.Store,
		clock: opts.Clock,
		log:   opts.Logger,
	}, nil
}
```

This keeps the constructor honest:

- outer layers provide dependencies
- `New(...)` validates them early
- the constructed service is ready for domain use immediately

## Domain Locality

Keep domain behavior, domain types, store-facing update types, and validation rules together.

API handlers, CLI commands, config loaders, and other entry points parse and normalize request-shaped inputs before calling the service. Service methods should receive already-shaped values, validate their domain meaning, coordinate behavior, and call service-owned contracts. For example, trim raw text at the HTTP, CLI, or config boundary so the service can treat its inputs as intentional domain values.

For example, `documents.go` may own:

- `Document`
- `DocumentUpdate`
- `CreateDocument(...)`
- `GetDocument(...)`
- `ListDocuments(...)`
- document-specific validation helpers

Keep service mutations readable by making their phases visible:

1. validate the requested domain intent and inputs that do not depend on current persisted state
2. coordinate reads or external work that need not be atomic with the mutation
3. call a domain-named store operation that atomically enforces persisted-state preconditions and returns its domain result
4. map store outcomes to service errors and continue orchestration

```go
package service

import (
	"errors"
	"time"
)

var (
	ErrInvalidDocument = errors.New("invalid document")
	ErrDocumentExists  = errors.New("document already exists")
)

type Document struct {
	ID        string
	Title     string
	CreatedAt time.Time
}

type DocumentUpdate struct {
	Title *string
}

func (s *Service) CreateDocument(
	id string,
	title string,
) (
	*Document,
	error,
) {
	if id == "" || title == "" {
		return nil, ErrInvalidDocument
	}

	doc := &Document{
		ID:        id,
		Title:     title,
		CreatedAt: s.clock(),
	}
	if err := s.store.CreateDocument(doc); err != nil {
		return nil, mapStoreDocumentError(err)
	}

	return doc, nil
}
```

Split a domain across more files only when that domain stops being easy to read in one place.

## DTO Boundary

Do not treat service domain types as the API contract. `internal/api` should define exported DTOs and explicit conversions to and from service types.

Service types should express the domain in Go terms. API DTOs should express the HTTP contract with JSON tags and transport-shaped names.

## Default Flow

The normal runtime flow is:

1. `internal/server` or another outer layer resolves config and opens dependencies.
2. the outer layer constructs `service.Service` with explicit `Options`.
3. the outer layer constructs `api.API` with the service and API-specific dependencies.
4. `internal/server` mounts the API router and any other HTTP surfaces.
5. `internal/server` owns listen, shutdown, and deployment mounting.

Keep that flow simple by making `internal/service` the core behavior boundary, not the HTTP boundary.

## Optional Branches

Some services need additional structure beyond the default path.

- If startup must initialize durable mutable state explicitly, read [bootstrap-initialization.md](bootstrap-initialization.md).
- If the service owns long-lived background work, read [lifecycle-hooks.md](lifecycle-hooks.md).
- If domain data belongs to logged-in users, read the [Consent user skill](../../work-with-consent-users/SKILL.md) for account records, local account IDs, and account-scoped service inputs.
- If you need JSON HTTP endpoint structure or `command-go/pkg/keys`, read the [API skill](../../work-with-go-http-apis/SKILL.md).
- If you need production serving composition, read the [server skill](../../work-with-go-servers/SKILL.md).

## Testing Expectations

At minimum, tests should make it easy to verify:

- required dependency validation in `New(...)`
- deterministic construction with test-owned dependencies
- domain behavior without reaching through API or server layers
- service errors before they are translated into HTTP responses

Keep API contract tests in the API test suite, using `internal/api` DTOs and the API router.
