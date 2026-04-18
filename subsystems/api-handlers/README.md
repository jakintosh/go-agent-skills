# API Handlers

This guide defines the default shape for JSON HTTP handlers in `internal/service`

Use it when you are adding or revising API endpoints, deciding what a handler should own, or reviewing whether HTTP code is doing too much work

## Owns

API handlers own:

- decoding request bodies
- reading path and query inputs
- validating request-local shape
- calling service methods
- writing HTTP status codes and JSON responses
- translating service errors into HTTP responses

Keep domain rules in service methods and persistence mechanics in store implementations

## Required

- Keep handlers thin: decode, validate request-local shape, call the service, encode the response
- Keep request and response types close to-or inside-the domain file that owns the handler
- Keep request and response types exported so other packages can use them directly
- Use explicit path values and query parsing in the handler
- Use one small set of response helpers across the API surface
- Return the resource representation directly when that keeps the contract simple
- Keep service-to-HTTP error translation in one small helper near the handlers that use it
- Keep routing and base-path mounting outside individual handlers

## Canonical Shape

The default shape is one domain file in `internal/service` that keeps the HTTP contract close to the service behavior it exposes

Typical package shape:

```
internal/service/
  service.go
  router.go
  documents.go
  projects.go
```

For one domain file, keep this ownership split together:

- domain types
- public request and response types used by that domain
- service methods for that domain
- handlers for that domain
- a small local error-mapping helper when needed

## Canonical Flow

The normal handler flow is:

1. read path, query, or body inputs
2. validate request-local shape
3. call a service method
4. map service errors
5. write the response

If error mapping needs more than a simple inline check, read `./error-mapping.md`

## Canonical Example

```go
package service

import (
	"encoding/json"
	"errors"
	"net/http"

	"git.sr.ht/~jakintosh/command-go/pkg/wire"
)

type Document struct {
	ID    string `json:"id"`
	Title string `json:"title"`
}

type CreateDocumentRequest struct {
	Title string `json:"title"`
}

func (s *Service) GetDocument(id string) (*Document, error) {
	return s.store.GetDocument(id)
}

func (s *Service) ListDocuments(limit int, offset int) ([]Document, error) {
	if limit <= 0 {
		limit = 100
	}
	offset = max(offset, 0)
	return s.store.ListDocuments(limit, offset)
}

func (s *Service) CreateDocument(title string) (*Document, error) {
	return s.store.CreateDocument(title)
}

func (s *Service) handleGetDocument(w http.ResponseWriter, r *http.Request) {
	documentID := r.PathValue("document_id")

	doc, err := s.GetDocument(documentID)
	if err != nil {
		writeDocumentError(w, err)
		return
	}

	wire.WriteData(w, http.StatusOK, doc)
}

func (s *Service) handleListDocuments(w http.ResponseWriter, r *http.Request) {
	limit, offset, err := wire.ParsePagination(r)
	if err != nil {
		wire.WriteError(w, http.StatusBadRequest, err.Error())
		return
	}

	docs, err := s.ListDocuments(limit, offset)
	if err != nil {
		writeDocumentError(w, err)
		return
	}

	wire.WriteData(w, http.StatusOK, docs)
}

func (s *Service) handleCreateDocument(w http.ResponseWriter, r *http.Request) {
	var req CreateDocumentRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		wire.WriteError(w, http.StatusBadRequest, "invalid json")
		return
	}

	if req.Title == "" {
		wire.WriteError(w, http.StatusBadRequest, "title is required")
		return
	}

	doc, err := s.CreateDocument(req.Title)
	if err != nil {
		writeDocumentError(w, err)
		return
	}

	wire.WriteData(w, http.StatusCreated, doc)
}

func writeDocumentError(w http.ResponseWriter, err error) {
	switch {
	case errors.Is(err, ErrDocumentNotFound):
		wire.WriteError(w, http.StatusNotFound, "document not found")
	case errors.Is(err, ErrInvalidTitle):
		wire.WriteError(w, http.StatusBadRequest, "invalid title")
	default:
		wire.WriteError(w, http.StatusInternalServerError, "internal server error")
	}
}
```

This is the default feel to preserve:

- request parsing is direct and local
- handlers call one service method each
- status behavior is obvious
- response writing stays consistent across routes

## Leaf Docs

- If multiple handlers in one domain need the same service-to-HTTP translation rules, read `./error-mapping.md`

## Common Touchpoints

- `subsystems/service/README.md` for service package ownership and domain locality
- `subsystems/routing/README.md` for route-group composition and mounting
- `subsystems/store/README.md` for service-facing store contracts
