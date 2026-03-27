# Store Contracts

This guide defines the standard shape for store contracts between the service layer and persistence adapters.

It focuses on where store interfaces live, how methods should be expressed, and where translation between domain values and persistence-friendly values should happen.

The goal is to make store contracts:

- owned by the service layer
- expressed in domain language
- stable enough for multiple adapter implementations
- free of transport and SQL leakage

## When to use this guide

Use this guide when you are:

- defining a `Store` interface or domain-specific store interface
- deciding what belongs in the service layer versus the database layer
- translating API or domain values into persistence-friendly values
- reviewing whether handlers or stores are doing too much conversion work

## Non-goals

This guide does not define:

- SQL query style
- database migration structure
- HTTP status mapping
- router composition

Those belong in adjacent subsystem guides.

## Core rules

- Define store interfaces in the service or domain layer, not in infrastructure packages.
- Define domain structs in the service layer first, then write store methods in terms of them.
- Keep store methods expressed in domain operations, not SQL concepts.
- Use parameter names that reveal storage representation when that matters.
- Treat the service layer as the translation boundary between domain values and persistence-friendly values.
- Keep handlers free of store-specific translation logic.

## Ownership boundary

The service layer owns the persistence contract.

That means it decides:

- which operations it needs
- which domain types those operations use
- which persistence-shaped values are acceptable at the boundary

The database adapter implements that contract. It does not invent it.

This keeps business needs in control of the storage API instead of letting the database package dictate service shape.

## Canonical shape

A typical layout looks like:

```text
internal/service/
  store.go
  documents.go

internal/database/
  database.go
  documents.go
```

The important split is:

- `internal/service` owns the interface and domain types
- `internal/database` owns the concrete implementation

## Domain-first contract design

Define domain structs before designing the adapter methods that load and store them.

For example:

```go
type Document struct {
	ID        string    `json:"id"`
	Title     string    `json:"title"`
	CreatedAt time.Time `json:"created_at"`
}

type Store interface {
	InsertDocument(id, title string, createdAtUnix int64) error
	GetDocument(id string) (*Document, error)
	ListDocuments(limit, offset int) ([]Document, error)
}
```

This contract is still service-owned even though one parameter uses a persistence-friendly representation.

The store method names describe domain operations:

- `InsertDocument`
- `GetDocument`
- `ListDocuments`

They do not describe SQL mechanics such as:

- `ExecInsertDocumentRow`
- `SelectDocumentsByQuery`
- `RunDocumentTxn`

## Translation boundary

The service layer should translate between rich domain values and persistence-friendly values.

That often means:

- validating domain input
- converting `time.Time` to unix seconds or formatted strings
- translating enums or wrappers into stored representations
- wrapping persistence failures into service-layer database errors

For example:

```go
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

	if err := s.store.InsertDocument(id, title, createdAt.Unix()); err != nil {
		return DatabaseError{Err: err}
	}

	return nil
}
```

This keeps the service layer in charge of domain meaning while the adapter stays mechanical.

## Parameter naming

When a method uses a persistence-oriented representation, the parameter name should say so.

Good examples:

- `createdAtUnix`
- `sinceUnix`
- `encodedToken`

This makes the contract honest about where representation conversion happens.

Do not hide mechanical formats behind vague names when the distinction matters.

## Handler boundary

Handlers should not do store-specific translation work.

Handlers should usually:

1. decode the request
2. validate request-local shape issues
3. call a service method
4. encode the response

They should not:

- convert times into unix formats for the store
- know about encoded persistence representations
- map database-specific quirks directly

That work belongs in the service layer.

## What a good store contract should feel like

A good store contract lets a reader answer these questions quickly:

- what operations does the service need from persistence?
- which types are true domain types?
- where do representation conversions happen?
- where does database-specific knowledge start?

If those answers are blurry, the contract boundary is too weak.

## Testing expectations

Store contract design should make it easy to test:

- service methods translating domain inputs correctly before store calls
- persistence failures being wrapped in service-layer errors
- handlers staying free of persistence-specific translation
- adapter conformance to the service-owned interface

Prefer tests that reinforce the boundary rather than duplicating SQL behavior in service tests.

## Anti-patterns

- defining interfaces in `internal/database`
- store methods that expose `*sql.DB`, `*sql.Tx`, rows, or driver types
- method names that describe SQL mechanics instead of domain operations
- handlers converting domain values into persistence formats
- database adapters inventing extra contract behavior the service did not ask for
- store contracts that carry HTTP or JSON concerns

## Generic example

```go
type Snapshot struct {
	OpeningCount int `json:"opening_count"`
	ClosingCount int `json:"closing_count"`
}

type Store interface {
	InsertEntry(id, project string, createdAtUnix int64) error
	GetEntry(id string) (*Entry, error)
	GetProjectSnapshot(project string, sinceUnix, untilUnix int64) (*Snapshot, error)
}
```

This contract works because:

- the domain vocabulary is obvious
- persistence representation is explicit where needed
- the adapter can stay mechanical
- the service remains the place where meaning and validation live

## Related guides

- `service-construction.md`
- `database-adapters.md`
- `http-resource-handlers.md`
