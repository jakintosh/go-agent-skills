# Defining a Store Contract

This guide defines the default shape for store contracts between `internal/service` and persistence adapters

Use it when you are defining `Store` or `<Domain>Store`, deciding what belongs in `internal/service` versus `internal/database`, or deciding where domain values should be converted into persistence-shaped values.

The store contract is the service-owned persistence boundary. It uses domain vocabulary for persistence operations and keeps service-side conversion from rich domain values into persistence-shaped values explicit.

## Contents

- [Required](#required)
- [Canonical Shape](#canonical-shape)
- [Canonical Flow](#canonical-flow)
- [Canonical Example](#canonical-example)
- [More Examples](#more-examples)
- [Leaf Docs](#leaf-docs)
- [Common Touchpoints](#common-touchpoints)
- [Testing Expectations](#testing-expectations)

## Required

- Define store interfaces in `internal/service`
- Define domain structs before defining store methods
- Name store methods as domain operations
- Use current domain vocabulary at the service/store boundary
- Keep SQL, driver, and transport types out of store contracts
- Use explicit parameter names for persistence-shaped values
- Keep API handlers free of store-specific translation work
- Do not pass API DTOs into store contracts

## Canonical Shape

Use a layout like:

```
internal/service/
  store.go
  documents.go

internal/database/
  database.go
  documents.go
```

Keep the ownership split clear:

- `internal/service` owns the interface and domain types
- `internal/database` owns the concrete implementation

## Canonical Flow

The default flow is:

1. an API handler decodes DTO inputs and calls a service method
2. the service validates domain inputs
3. the service applies any domain functionality
4. the service calls the store contract with domain-shaped values
5. the database adapter implements that contract mechanically

If you are implementing the adapter side of this boundary in `internal/database`, read [database-adapters.md](database-adapters.md).

## Canonical Example

```go
package service

import "time"

type Document struct {
	ID        string
	Title     string
	CreatedAt time.Time
}

type Store interface {
	InsertDocument(document *Document) error
	GetDocument(id string) (*Document, error)
	UpdateDocument(id string, update DocumentUpdate) (*Document, error)
	ListDocuments(limit int, offset int) ([]Document, error)
}

type DocumentUpdate struct {
	Title *string
}

func (s *Service) CreateDocument(
	id string,
	title string,
	createdAt time.Time,
) error {
	if id == "" {
		return ErrInvalidDocumentID
	}
	if title == "" {
		return ErrInvalidTitle
	}

	document := &Document{
		ID: id,
		Title: title,
		CreatedAt: createdAt,
	}
	if err := s.store.InsertDocument(document); err != nil {
		return DatabaseError{Err: err}
	}

	return nil
}
```

This is the default shape to preserve:

- the service owns `Document`
- the store interface uses current domain operation names
- the service performs validation and conversion before the store call
- store reads and writes return service-owned domain values when the caller needs the updated state

## More Examples

Use names that describe the domain operation directly, and let transitional names, storage-era records, or redundant suffixes fall away once the domain concept is clear:

```go
type Store interface {
	InsertEntry(entry *Entry) error
	GetEntry(id string) (*Entry, error)
	UpdateEntry(id string, update EntryUpdate) (*Entry, error)
	GetProjectSnapshot(project string, sinceUnix int64, untilUnix int64) (*Snapshot, error)
}
```

For ordinary resource editing, define one update-shaped input for the resource and let the store method apply the fields present in that input. Give distinct domain actions their own methods when the action has its own meaning or lifecycle.

Another good shape is a domain-specific interface when the contract is intentionally split:

```go
type ProjectStore interface {
	CreateProject(project *Project) error
	GetProject(id string) (*Project, error)
	ListProjects(limit int, offset int) ([]Project, error)
}
```

Keep the same rules in both cases:

- methods describe domain work
- persistence-shaped parameters are named honestly
- domain result types stay service-owned
- sensitive values move through explicit capabilities instead of ordinary returned struct fields

## Leaf Docs

- If you are implementing the contract in `internal/database`, read [database-adapters.md](database-adapters.md).

## Common Touchpoints

- [service-shape.md](service-shape.md) for service package ownership and constructor shape
- The [API skill](../../work-with-go-http-apis/SKILL.md) for API handler and DTO responsibilities
- The [database skill](../../work-with-go-databases/SKILL.md) for SQL adapter mechanics and selectively loaded database references
- The [Consent user skill](../../work-with-consent-users/SKILL.md) for account-scoped store methods and local account IDs

## Testing Expectations

Store contracts should make it easy to test:

- service validation before store calls
- service-side value conversion before store calls
- persistence failures wrapped in service-layer errors
- API handlers staying free of persistence-specific translation
