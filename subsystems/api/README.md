# Defining an API

This guide defines the default shape for JSON HTTP APIs in `internal/api`.

Use it when you are adding or revising API endpoints, deciding what a handler should own, defining API DTOs, or composing the API route tree.

The API package is the HTTP contract boundary for the project. It defines the concrete API constructor, exported DTOs, DTO conversion, route composition, handlers, response writing, service-error-to-HTTP mapping, and transport-specific helper services such as API key middleware.

Keep domain rules in `internal/service` and persistence mechanics in store implementations.

## Required

- Use a concrete `API` struct with explicit `Options` and `New(...)`.
- Expose `Router() http.Handler` as the API route entry point.
- Keep API DTOs separate from service domain types, even when their fields currently match.
- Export API DTOs so tests, clients, and other project packages can reuse the API contract.
- Implement explicit conversion functions or methods between API DTOs and service types.
- Keep handlers thin: decode, validate request-local shape, convert, call the service, encode the response.
- Model resource updates as an explicit update request passed to one service method for that resource.
- Use explicit path values and query parsing in handlers.
- Use one small set of response helpers across the API surface.
- Use the `wire` response envelope for JSON success and error responses.
- Use `wire.ParsePagination(...)` for conventional `limit` and `offset` query parsing.
- Keep service-to-HTTP error translation in a package-level helper unless a project proves that is too large.
- Keep deployment base-path mounting and listen behavior outside `internal/api`.

## Canonical Package Shape

Use a layout like:

```text
internal/api/
  api.go
  http.go
  documents.go
  projects.go
```

The ownership split should stay clear:

- `api.go` owns `API`, `Options`, `New(...)`, and `Router()`.
- `http.go` owns shared decode, response, and error-mapping helpers.
- domain files own local DTOs, conversions, route groups, and handlers.

## Constructor Pattern

`internal/api` receives the domain service and any API-specific dependencies. It may construct transport-specific helper services from those dependencies.

```go
package api

import (
	"errors"
	"net/http"

	"example/internal/service"
	"git.sr.ht/~jakintosh/command-go/pkg/keys"
	"git.sr.ht/~jakintosh/command-go/pkg/wire"
)

type Options struct {
	Service *service.Service
	Keys    keys.Store
}

type API struct {
	service *service.Service
	keys    *keys.Service
}

func New(
	opts Options,
) (
	*API,
	error,
) {
	if opts.Service == nil {
		return nil, errors.New("api: service required")
	}
	if opts.Keys == nil {
		return nil, errors.New("api: keys store required")
	}

	keyOpts := keys.Options{
		Store:       opts.Keys,
		Permissions: service.KeyPermissions,
	}
	keysSvc, err := keys.New(keyOpts)
	if err != nil {
		return nil, err
	}

	return &API{
		service: opts.Service,
		keys:    keysSvc,
	}, nil
}

func (a *API) Router() http.Handler {
	root := http.NewServeMux()
	wire.Subrouter(root, "/documents", a.buildDocumentRouter())
	wire.Subrouter(root, "/admin", a.keys.WithAuth(a.buildAdminRouter(), service.PermissionAdmin))
	return root
}
```

This keeps the split obvious:

- service owns behavior and permissions
- API owns HTTP exposure and middleware placement
- server owns where the API is mounted in the process router

## DTO Boundary

API DTOs are the HTTP contract. Service types are the domain contract.

Even when the fields are the same today, define explicit DTOs and conversion methods so API drift is visible and intentional.

```go
package api

import "example/internal/service"

type UserDTO struct {
	ID    string `json:"id"`
	Name  string `json:"name"`
	Email string `json:"email"`
}

func UserDTOFromService(
	u service.User,
) UserDTO {
	return UserDTO{
		ID:    u.ID,
		Name:  u.Name,
		Email: u.Email,
	}
}

func (u UserDTO) ToService() (
	service.User,
	error,
) {
	return service.User{
		ID:    u.ID,
		Name:  u.Name,
		Email: u.Email,
	}, nil
}
```

Use names that make the contract obvious. `UserDTO`, `CreateUserRequest`, and `UpdateUserRequest` are all acceptable when they describe the API shape clearly.

## Canonical Handler Flow

The normal handler flow is:

1. read and normalize path, query, header, or body inputs
2. validate request-local shape
3. convert DTO input into service-shaped input when needed
4. call one service method with shaped values
5. map service errors
6. write the response DTO

```go
func (a *API) handleCreateDocument(
	w http.ResponseWriter,
	r *http.Request,
) {
	var req CreateDocumentRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		wire.WriteError(w, http.StatusBadRequest, "malformed json")
		return
	}
	if req.ID == "" || req.Title == "" {
		wire.WriteError(w, http.StatusBadRequest, "id and title are required")
		return
	}

	doc, err := a.service.CreateDocument(req.ID, req.Title)
	if err != nil {
		writeServiceError(w, err)
		return
	}

	wire.WriteData(w, http.StatusCreated, DocumentDTOFromService(*doc))
}
```

This is the default feel to preserve:

- request parsing is direct and local
- handlers call one service method each
- status behavior is obvious
- response writing stays consistent across routes
- API response types are exported and reusable

## Wire Helpers

`command-go/pkg/wire` is the standard HTTP wire-format package for JSON APIs.

Use:

- `wire.WriteData(w, status, data)` for success responses
- `wire.WriteData(w, http.StatusNoContent, nil)` for status-only success responses
- `wire.WriteError(w, status, message)` for error responses
- `wire.ParsePagination(r)` for shared `limit` and `offset` query parsing
- `wire.Subrouter(...)` for mounting route groups

The response envelope is:

```json
{"data": <value>}
```

or:

```json
{"error": {"message": "..."}}
```

For paginated list endpoints, keep the parsing at the top of the handler:

```go
func (a *API) handleListDocuments(
	w http.ResponseWriter,
	r *http.Request,
) {
	limit, offset, err := wire.ParsePagination(r)
	if err != nil {
		wire.WriteError(w, http.StatusBadRequest, err.Error())
		return
	}

	docs, err := a.service.ListDocuments(limit, offset)
	if err != nil {
		writeServiceError(w, err)
		return
	}

	wire.WriteData(w, http.StatusOK, DocumentsDTOFromService(docs))
}
```

When verifying route wiring, middleware, request decoding, response DTOs, or status behavior, test the built router in-process; read `./testing.md`.

## Related Guides

- Read `./error-mapping.md` for service-to-HTTP error translation.
- Read `./testing.md` for in-process API test shape.
- Read `./with-keys.md` when the API exposes key management or uses API-key auth.
- Read `./with-cors.md` when the API needs runtime CORS origin management.
- Read `../routing/README.md` for route-group composition.
- Read `../server/README.md` for production serving and deployment mounting.
- Read `../service/README.md` for domain service boundaries.
