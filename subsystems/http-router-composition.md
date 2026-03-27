# HTTP Router Composition

This guide defines the standard shape for composing HTTP routers in this style system.

It focuses on how route trees are built, mounted, and wrapped with middleware.

The goal is to make router structure:

- easy to scan
- easy to extend
- easy to test in-process
- explicit about where auth, CORS, and other cross-cutting behavior apply

## When to use this guide

Use this guide when you are:

- building an HTTP API tree
- adding a new resource group or admin/settings area
- deciding where middleware should be applied
- mounting package-provided handlers like keys or CORS settings APIs
- wiring a service's `BuildRouter()` and `Serve()` flow

## Non-goals

This guide does not define:

- request and response payload design
- domain/service method design
- config system behavior
- frontend HTMX rendering flows

Those should live in their own subsystem guides.

## Core rules

- Build one root router as the top-level composition layer.
- Keep startup and listen concerns outside route registration.
- Use explicit method+path patterns for direct route registration.
- Compose route groups additively instead of building one giant registration function.
- Return `http.Handler` from mountable route-group builders.
- Mount child routers with `wire.Subrouter`.
- Apply middleware at the highest safe boundary.
- Distinguish handler-level middleware from handlerfunc-level middleware.
- Build middleware bundles from `Service` dependencies during composition.
- Keep deployment base-path mounting outside the inner API tree.
- Mount package-provided settings handlers directly when a subsystem already exposes its own handler.

## Canonical shape

The expected layering is:

1. `BuildRouter()` constructs the API tree.
2. Domain or area-specific builder methods return `http.Handler`.
3. `Serve()` mounts that router under any deployment base path and starts the server.

Typical files:

```text
internal/service/
  service.go
  router.go
  health.go
  users.go
  settings.go
```

The important boundary is:

- `router.go` owns composition
- domain files own their own route groups
- `Serve()` owns outer serving concerns

## Middleware model

Router composition should make middleware boundaries obvious.

Prefer a bundle like this:

```go
type Middleware struct {
	auth     func(http.Handler, *keys.Permission) http.Handler
	authFunc func(http.HandlerFunc, *keys.Permission) http.HandlerFunc
	cors     func(http.Handler) http.Handler
	corsFunc func(http.HandlerFunc) http.HandlerFunc
}
```

Why this shape works:

- route-group mounts can use handler-level wrappers
- direct `HandleFunc` registrations can use func-level wrappers
- composition code shows exactly what protection is applied where

## Canonical composition flow

### 1. Build middleware from service dependencies

Do this inside router composition, not through package globals.

```go
func (s *Service) BuildRouter() http.Handler {
	mw := Middleware{
		auth:     s.keys.WithAuth,
		authFunc: s.keys.WithAuthFunc,
		cors:     s.cors.WithCORS,
		corsFunc: s.cors.WithCORSFunc,
	}

	root := http.NewServeMux()

	wire.Subrouter(root, "/health", s.buildHealthRouter(mw))
	wire.Subrouter(root, "/projects", s.buildProjectRouter(mw))
	wire.Subrouter(root, "/admin", mw.auth(s.buildAdminRouter(mw), &PermissionAdmin))
	wire.Subrouter(root, "/settings", mw.auth(s.buildSettingsRouter(mw), &PermissionAdmin))

	return root
}
```

### 2. Keep route groups local

A route group should own one coherent area.

```go
func (s *Service) buildProjectRouter(
	mw Middleware,
) http.Handler {
	mux := http.NewServeMux()

	mux.HandleFunc("GET /", mw.corsFunc(s.handleListProjects))
	mux.HandleFunc("POST /", mw.authFunc(s.handleCreateProject, &PermissionWrite))
	mux.HandleFunc("GET /{project_id}", mw.corsFunc(s.handleGetProject))
	mux.HandleFunc("DELETE /{project_id}", mw.authFunc(s.handleDeleteProject, &PermissionWrite))

	return mux
}
```

Use direct `HandleFunc` registration when:

- the routes are small and local
- the middleware boundary is per-route

Return a mounted child handler when:

- the whole group shares a boundary
- the group has its own nested structure
- the group is easier to read as a self-contained subtree

### 3. Mount package handlers directly

If a subsystem already exposes its own handler, compose that handler instead of rebuilding its routes manually.

```go
func (s *Service) buildSettingsRouter(
	mw Middleware,
) http.Handler {
	mux := http.NewServeMux()

	wire.Subrouter(mux, "/keys", s.keys.Handler())
	wire.Subrouter(mux, "/cors", s.cors.Handler())

	return mux
}
```

This keeps ownership clear:

- the keys package owns key-management routes
- the CORS package owns CORS-management routes
- your service owns where those handlers are mounted and who can access them

### 4. Keep outer serving concerns outside the API tree

`Serve()` should mount the built router under any deployment base path.

```go
func (s *Service) Serve(
	host string,
	port int,
	basePath string,
) error {
	api := s.BuildRouter()

	var handler http.Handler = api
	if basePath != "" && basePath != "/" {
		root := http.NewServeMux()
		wire.Subrouter(root, basePath, api)
		handler = root
	}

	addr := net.JoinHostPort(host, strconv.Itoa(port))
	return http.ListenAndServe(addr, handler)
}
```

This keeps:

- route composition inside `BuildRouter()`
- deployment path concerns inside `Serve()`

## Handler vs handlerfunc middleware

This distinction matters.

Use handler-level wrappers when wrapping a mounted subtree:

```go
wire.Subrouter(root, "/admin", mw.auth(s.buildAdminRouter(mw), &PermissionAdmin))
```

Use func-level wrappers when registering a direct route:

```go
mux.HandleFunc("POST /", mw.authFunc(s.handleCreateProject, &PermissionWrite))
```

Do not blur these two patterns. The split makes it much easier to see whether protection applies to:

- one route
- one route group

## What a good route tree should feel like

A good composed router should let a reader answer these questions quickly:

- What are the top-level route groups?
- Which groups are public?
- Which groups require auth?
- Which groups require admin access?
- Which routes are package-provided?
- Where does the deployment base path get mounted?

If those answers are spread across several unrelated files or hidden inside helper indirection, the router is too opaque.

## Testing expectations

Router composition should be easy to test in-process.

At minimum, tests should make it easy to verify:

- the built router registers expected route groups
- public routes remain reachable without auth
- protected groups reject missing or insufficient permissions
- settings/admin mounts are protected at the correct boundary
- CORS and preflight behavior works for the intended routes
- deployment base-path mounting preserves route behavior

Prefer tests that exercise `BuildRouter()` directly rather than starting network listeners.

## Anti-patterns

- one giant registration function for the entire API
- ad hoc prefix mounting with manual strip-prefix helpers when `wire.Subrouter` already solves the problem
- applying auth per route when the whole subtree shares the same access boundary
- applying auth globally when only one subtree needs it
- hiding middleware application inside package-level globals
- mixing listen/startup concerns into route registration code
- rebuilding keys or CORS settings routes manually instead of mounting package handlers
- using method switches inside handlers instead of explicit method+path registration

## Generic example

This is the target feel for a compact router composition module:

```go
func (s *Service) BuildRouter() http.Handler {
	mw := Middleware{
		auth:     s.keys.WithAuth,
		authFunc: s.keys.WithAuthFunc,
		cors:     s.cors.WithCORS,
		corsFunc: s.cors.WithCORSFunc,
	}

	root := http.NewServeMux()

	wire.Subrouter(root, "/health", s.buildHealthRouter(mw))
	wire.Subrouter(root, "/documents", s.buildDocumentRouter(mw))
	wire.Subrouter(root, "/admin", mw.auth(s.buildAdminRouter(mw), &PermissionAdmin))

	return root
}

func (s *Service) buildDocumentRouter(
	mw Middleware,
) http.Handler {
	mux := http.NewServeMux()

	mux.HandleFunc("GET /", mw.corsFunc(s.handleListDocuments))
	mux.HandleFunc("POST /", mw.authFunc(s.handleCreateDocument, &PermissionWrite))
	mux.HandleFunc("GET /{document_id}", mw.corsFunc(s.handleGetDocument))

	return mux
}
```

## Related guides

- `subsystems/http-resource-handlers.md`
- `subsystems/service-construction.md`
- `subsystems/config-systems.md`
- `subsystems/api-tests.md`
