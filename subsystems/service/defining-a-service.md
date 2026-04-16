# Defining a Service

This guide defines the default shape of an `internal/service` package

Use it when you are creating the application's core service package, defining a `Service` constructor, or deciding what belongs inside the application's main behavioral boundary

## Required

- Treat `internal/service` as the application core
- Use a concrete `Service` struct with an explicit `Options` constructor
- Validate required dependencies in `New(...)`
- Keep domain behavior and closely related handlers together when they share types and validation
- Keep config resolution and external dependency setup outside the service package
- Keep router composition inside the service package

## Canonical package shape

Use a layout like:

```
internal/service/
  service.go
  router.go
  store.go
  health.go
  documents.go
```

The exact filenames may vary. The ownership split should stay clear:

- `service.go` owns `Service`, `Options`, and `New(...)`
- `router.go` owns `BuildRouter()`
- `store.go` owns service-facing contracts
- domain files own one coherent domain area each

## Constructor pattern

Use `Options` to name the service's real dependencies directly

```go
package service

import (
	"errors"
	"log"
	"net/http"
	"time"
)

type Store interface {
	ListDocuments() ([]Document, error)
	CreateDocument(title string) (Document, error)
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

func New(opts Options) (*Service, error) {
	if opts.Store == nil {
		return nil, errors.New("store is required")
	}
	if opts.Clock == nil {
		return nil, errors.New("clock is required")
	}

	return &Service{
		store: opts.Store,
		clock: opts.Clock,
		log:   opts.Logger,
	}, nil
}

func (s *Service) BuildRouter() http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /health", s.handleHealth)
	mux.HandleFunc("GET /documents", s.handleListDocuments)
	mux.HandleFunc("POST /documents", s.handleCreateDocument)
	return mux
}
```

This keeps the constructor honest:

- outer layers provide dependencies
- `New(...)` validates them early
- the constructed service is ready to use immediately

If you need to wire production dependencies in `main` and deterministic dependencies in tests, read `./composition-roots.md`

## Domain locality

Keep domain behavior and the handlers that expose it together when they share the same types and validation rules

For example, `documents.go` may own:

- `Document`
- `CreateDocumentRequest`
- `CreateDocument(...)`
- `handleListDocuments(...)`
- `handleCreateDocument(...)`

```go
package service

import (
	"encoding/json"
	"net/http"
)

type Document struct {
	ID    string `json:"id"`
	Title string `json:"title"`
}

type CreateDocumentRequest struct {
	Title string
}

func (s *Service) CreateDocument(title string) (Document, error) {
	return s.store.CreateDocument(title)
}

func (s *Service) handleListDocuments(w http.ResponseWriter, r *http.Request) {
	docs, err := s.store.ListDocuments()
	if err != nil {
		http.Error(w, "failed to list documents", http.StatusInternalServerError)
		return
	}

	_ = json.NewEncoder(w).Encode(docs)
}

func (s *Service) handleCreateDocument(w http.ResponseWriter, r *http.Request) {
	var input CreateDocumentRequest
	if err := json.NewDecoder(r.Body).Decode(&input); err != nil {
		http.Error(w, "invalid request", http.StatusBadRequest)
		return
	}

	doc, err := s.CreateDocument(input.Title)
	if err != nil {
		http.Error(w, "failed to create document", http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusCreated)
	_ = json.NewEncoder(w).Encode(doc)
}
```

Split a domain across more files only when that domain stops being easy to read in one place

## Default flow

The normal runtime flow is:

1. an outer layer resolves config and opens dependencies
2. the outer layer constructs `Service` with explicit `Options`
3. the service builds its router internally
4. an outer layer serves that router or exposes another top-level entry point

Keep that flow simple by making `internal/service` the core application boundary

If your service exposes HTTP directly and you need to define what `Serve(...)` should own, read `./serving.md`

## Optional branches

Some services need additional structure beyond the default path

- If you need separate production and test wiring, read `./composition-roots.md`
- If startup must initialize durable mutable state explicitly, read `./bootstrap-initialization.md`
- If the service owns long-lived background work, read `./lifecycle-hooks.md`
- If the service exposes HTTP serving concerns such as base-path mounting or listen/shutdown behavior, read `./serving.md`

## Testing expectations

At minimum, tests should make it easy to verify:

- required dependency validation in `New(...)`
- deterministic construction with test-owned dependencies
- domain behavior without reaching through unrelated outer layers

Keep more specialized tests with the feature that introduces them. For example, test bootstrap idempotency alongside explicit initialization, and test shutdown coordination alongside lifecycle hooks
