# Composing an HTTP Router

This guide defines the default shape for composing an HTTP route tree in this style system.

Use it when you are building an API or web `Router()`, adding a new resource group, or deciding how route groups should be mounted into one HTTP surface.

## Contents

- [Required](#required)
- [Canonical shape](#canonical-shape)
- [Canonical flow](#canonical-flow)
- [Canonical example](#canonical-example)
- [Testing expectations](#testing-expectations)

## Required

- Build one root router as the local composition layer for each HTTP surface.
- Keep local route composition inside `Router()` or another single router-construction entry point in the owning package.
- Use explicit method+path registrations for direct routes.
- Compose route groups additively instead of building one giant registration function.
- Return `http.Handler` from mountable route-group builders.
- Mount child routers with `wire.Subrouter`.
- Keep startup, listen, and deployment mounting concerns out of local route registration.

## Canonical shape

The default routing shape, shown here for an API surface, is:

1. `Router()` creates the local root mux.
2. Each coherent area exposes one mountable route-group builder.
3. The local root mux mounts those route groups additively.
4. `internal/server` mounts completed API or web routers into the process router.

Typical files:

```
internal/api/
  api.go
  health.go
  documents.go
  settings.go
```

Keep the ownership split clear:

- the owning package's entry-point file owns top-level local composition.
- domain files own their local route groups.
- `internal/server` owns base-path mounting and listen behavior.

## Canonical flow

The normal flow is:

1. build any router-local middleware bundle from dependencies of the owning HTTP surface
2. create one root mux
3. mount public and protected route groups into that root mux
4. return the completed handler

If you need to decide where auth or CORS should wrap a subtree versus a single route, read [middleware boundaries](middleware-boundaries.md).

If a subsystem already exposes its own handler and you need to mount it without rebuilding its routes, read [mounting package handlers](mounting-package-handlers.md).

If you need to mount the API under a deployment base path or keep serving separate from route composition, read [work-with-go-servers](../../work-with-go-servers/SKILL.md).

## Canonical example

```go
func (a *API) Router() http.Handler {
	mw := Middleware{
		auth:     a.keys.WithAuth,
		authFunc: a.keys.WithAuthFunc,
		cors:     a.cors.WithCORS,
		corsFunc: a.cors.WithCORSFunc,
	}

	root := http.NewServeMux()

	wire.Subrouter(root, "/health", a.buildHealthRouter())
	wire.Subrouter(root, "/documents", a.buildDocumentRouter(mw))
	wire.Subrouter(root, "/admin", mw.auth(a.buildAdminRouter(mw), service.PermissionAdmin))

	return root
}

func (a *API) buildDocumentRouter(
	mw Middleware,
) http.Handler {
	mux := http.NewServeMux()

	mux.HandleFunc("GET /", mw.corsFunc(a.handleListDocuments))
	mux.HandleFunc("OPTIONS /", mw.corsFunc(a.handleListDocuments))
	mux.HandleFunc("POST /", mw.authFunc(a.handleCreateDocument, service.PermissionWrite))
	mux.HandleFunc("GET /{document_id}", mw.corsFunc(a.handleGetDocument))
	mux.HandleFunc("OPTIONS /{document_id}", mw.corsFunc(a.handleGetDocument))

	return mux
}
```

This is the default feel to preserve:

- one readable local composition layer
- one route-group builder per coherent area
- direct registrations kept local to the group that owns them
- subtree mounting done with `wire.Subrouter`

## Testing expectations

Router composition should make it easy to verify:

- the built local router exposes the intended top-level groups
- public groups remain reachable without unrelated protection
- protected groups are mounted at the correct boundary

Prefer tests that exercise the built handler in-process rather than starting a listener.
