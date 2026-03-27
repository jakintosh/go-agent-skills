# HTTP Resource Handlers

This guide defines the standard shape for HTTP resource handlers in this style system.

It focuses on handler responsibilities, request and response types, error mapping, and the boundary between HTTP concerns and service-layer behavior.

The goal is to make handlers:

- thin and predictable
- easy to scan for API behavior
- consistent about response style
- free of business and persistence leakage

## When to use this guide

Use this guide when you are:

- adding or revising JSON HTTP endpoints
- deciding where request and response structs should live
- mapping service errors to HTTP status codes
- reviewing whether handlers are doing too much work

## Non-goals

This guide does not define:

- top-level router composition
- store interface design
- full API testing strategy
- server-rendered HTML flows

## Core rules

- Use explicit and versioned base API paths when appropriate.
- Keep handlers thin: decode, validate, call the service, encode the response.
- Define request and response structs close to the handler or service code that owns them.
- Export request or response types only when another package truly needs them.
- Bias toward returning the resource representation itself when that keeps the contract simple.
- Map service errors to HTTP status codes in a small helper.
- Use path values and explicit query parsing rather than hidden routing abstractions.
- Standardize around a small set of response patterns instead of ad hoc per-route styles.

## Canonical shape

HTTP resource handlers usually belong beside the domain behavior they expose:

```text
internal/service/
  service.go
  router.go
  documents.go
  projects.go
```

For example, `documents.go` may contain:

- document request and response types
- `handleListDocuments(...)`
- `handleGetDocument(...)`
- `handleCreateDocument(...)`
- related service methods

This keeps the domain's API contract close to the behavior it triggers.

## Base path and routing assumptions

Use explicit API paths, and version them when the API is meant to be a stable external contract.

Good examples:

- `/api/v1/documents`
- `/api/v1/projects/{project_id}`

Within the handler, prefer standard-library request access patterns such as:

- `r.PathValue("project_id")`
- explicit query parsing
- `wire.ParsePagination(r)` when pagination helpers are appropriate

Do not hide simple request parsing behind large routing abstractions.

## Handler flow

The normal handler shape is:

1. decode request inputs
2. validate request-local shape
3. call a service method
4. map service errors if needed
5. encode the response

For example:

```go
func (s *Service) handleCreateDocument(
	w http.ResponseWriter,
	r *http.Request,
) {
	var req CreateDocumentRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		wire.WriteError(w, http.StatusBadRequest, "invalid json")
		return
	}

	doc, err := s.CreateDocument(req.ID, req.Title)
	if err != nil {
		writeServiceError(w, err)
		return
	}

	wire.WriteData(w, http.StatusCreated, doc)
}
```

The handler should read like transport glue, not like a second service layer.

## Request and response types

Define request and response structs close to the handler or service file that owns them.

That keeps:

- contract changes local
- tests easier to find
- CLI or client reuse explicit instead of accidental

Export these types only when another package genuinely needs them.

A practical default is:

- keep request types unexported unless shared
- export response or domain types only when external consumers need them

Do not create globally shared API type packages by default.

## Response style

Prefer a small number of consistent response patterns.

For JSON APIs, a strong default is:

- success responses through one helper style
- error responses through one helper style
- resource endpoints returning the resource representation itself when that is the clearest contract

This keeps clients from having to learn a different response shape for every route.

Avoid per-route ad hoc response formats unless there is a clear contract reason.

## Error mapping

Service errors should map to HTTP status codes in a small helper.

For example:

```go
func writeServiceError(w http.ResponseWriter, err error) {
	switch {
	case errors.Is(err, ErrNotFound):
		wire.WriteError(w, http.StatusNotFound, "not found")
	case errors.Is(err, ErrConflict):
		wire.WriteError(w, http.StatusConflict, "conflict")
	case errors.Is(err, ErrInvalidTitle):
		wire.WriteError(w, http.StatusBadRequest, "invalid title")
	default:
		wire.WriteError(w, http.StatusInternalServerError, "internal server error")
	}
}
```

This keeps status behavior:

- easy to audit
- easy to test
- consistent across handlers

Do not duplicate large status-mapping switches in every route.

## Boundary with service and store layers

Handlers should not:

- enforce deep domain invariants that belong in service methods
- convert domain values into persistence formats
- know about SQL or driver details

The service layer should own domain validation and translation.

The store or database layer should own SQL mechanics.

## Testing expectations

HTTP handler structure should make it easy to test:

- malformed JSON and invalid query handling
- service error to HTTP status mapping
- success responses and payload shape
- path and query parsing behavior
- consistency of standard response patterns

Prefer in-process HTTP tests that exercise the real handler and router wiring.

## Anti-patterns

- handlers that contain business workflows several steps deep
- handlers that convert values into store-specific formats
- duplicated status-mapping logic across many files
- request and response types hidden far away from the code that owns them
- route-specific bespoke response envelopes without a strong reason
- method switches inside a single handler for multi-method endpoints

## Generic example

```go
type CreateProjectRequest struct {
	ID   string `json:"id"`
	Name string `json:"name"`
}

func (s *Service) handleGetProject(
	w http.ResponseWriter,
	r *http.Request,
) {
	projectID := r.PathValue("project_id")

	project, err := s.GetProject(projectID)
	if err != nil {
		writeServiceError(w, err)
		return
	}

	wire.WriteData(w, http.StatusOK, project)
}
```

This shape keeps the handler's job obvious:

- read HTTP inputs
- invoke the service
- map errors
- write the response

## Related guides

- `http-router-composition.md`
- `service-construction.md`
- `store-contracts.md`
- `api-tests.md`
