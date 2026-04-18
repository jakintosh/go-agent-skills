# Defining a Store Contract

This guide defines the default shape for store contracts between `internal/service` and persistence adapters

Use it when you are defining `Store` or `<Domain>Store`, deciding what belongs in `internal/service` versus `internal/database`, or deciding where domain values should be converted into persistence-shaped values

## Owns

The store subsystem owns:

- the service-owned persistence contract
- the domain vocabulary used by persistence operations
- the boundary where service code converts rich domain values into persistence-shaped values

## Required

- Define store interfaces in `internal/service`
- Define domain structs before defining store methods
- Name store methods as domain operations
- Keep SQL, driver, and transport types out of store contracts
- Use explicit parameter names for persistence-shaped values
- Keep handlers free of store-specific translation work

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

1. a handler decodes request inputs and calls a service method
2. the service validates domain inputs
3. the service calls any domain functionality
4. the service calls the store contract
5. the database adapter implements that contract mechanically

If you are implementing the adapter side of this boundary in `internal/database`, read `./with-database.md`

## Canonical Example

```go
package service

import "time"

type Document struct {
	ID        string    `json:"id"`
	Title     string    `json:"title"`
	CreatedAt time.Time `json:"created_at"`
}

type Store interface {
	InsertDocument(document *Document) error
	GetDocument(id string) (*Document, error)
	ListDocuments(limit int, offset int) ([]Document, error)
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
- the store interface uses domain operation names
- the service performs validation and conversion before the store call

## More Examples

Use names that describe the domain operation directly:

```go
type Store interface {
	InsertEntry(entry *Entry) error
	GetEntry(id string) (*Entry, error)
	GetProjectSnapshot(project string, sinceUnix int64, untilUnix int64) (*Snapshot, error)
}
```

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

## Leaf Docs

- If you are implementing the contract in `internal/database`, read `./with-database.md`

## Common Touchpoints

- `subsystems/service/README.md` for service package ownership and constructor shape
- `subsystems/api-handlers/README.md` for api handler responsibilities
- `subsystems/database/README.md` for SQL adapter mechanics

## Testing Expectations

Store contracts should make it easy to test:

- service validation before store calls
- service-side value conversion before store calls
- persistence failures wrapped in service-layer errors
- handlers staying free of persistence-specific translation
