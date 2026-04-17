# Composing an HTTP Router

This guide defines the default shape for composing an HTTP route tree in this style system.

Use it when you are building `BuildRouter()`, adding a new resource group, or deciding how route groups should be mounted into one HTTP surface.

## Required

- Build one root router as the top-level composition layer.
- Keep route composition inside `BuildRouter()` or another single router-construction entry point.
- Use explicit method+path registrations for direct routes.
- Compose route groups additively instead of building one giant registration function.
- Return `http.Handler` from mountable route-group builders.
- Mount child routers with `wire.Subrouter`.
- Keep startup and listen concerns out of route registration.

## Canonical shape

The default routing shape is:

1. `BuildRouter()` creates the root mux.
2. Each coherent area exposes one mountable route-group builder.
3. The root mux mounts those route groups additively.

Typical files:

```
internal/service/
  router.go
  health.go
  documents.go
  settings.go
```

Keep the ownership split clear:

- `router.go` owns top-level composition.
- domain files own their local route groups.
- outer serving code owns base-path mounting and listen behavior.

## Canonical flow

The normal flow is:

1. build any router-local middleware bundle from service dependencies
2. create one root mux
3. mount public and protected route groups into that root mux
4. return the completed handler

If you need to decide where auth or CORS should wrap a subtree versus a single route, read `./middleware-boundaries.md`.

If a subsystem already exposes its own handler and you need to mount it without rebuilding its routes, read `./mounting-package-handlers.md`.

If you need to mount the API under a deployment base path or keep `Serve()` separate from route composition, read `./deployment-mounting.md`.

## Canonical example

```go
func (s *Service) BuildRouter() http.Handler {
	mw := Middleware{
		auth:     s.keys.WithAuth,
		authFunc: s.keys.WithAuthFunc,
		cors:     s.cors.WithCORS,
		corsFunc: s.cors.WithCORSFunc,
	}

	root := http.NewServeMux()

	wire.Subrouter(root, "/health", s.buildHealthRouter())
	wire.Subrouter(root, "/documents", s.buildDocumentRouter(mw))
	wire.Subrouter(root, "/admin", mw.auth(s.buildAdminRouter(mw), &PermissionAdmin))

	return root
}

func (s *Service) buildDocumentRouter(mw Middleware) http.Handler {
	mux := http.NewServeMux()

	mux.HandleFunc("GET /", mw.corsFunc(s.handleListDocuments))
	mux.HandleFunc("POST /", mw.authFunc(s.handleCreateDocument, &PermissionWrite))
	mux.HandleFunc("GET /{document_id}", mw.corsFunc(s.handleGetDocument))

	return mux
}
```

This is the default feel to preserve:

- one readable root composition layer
- one route-group builder per coherent area
- direct registrations kept local to the group that owns them
- subtree mounting done with `wire.Subrouter`

## Testing expectations

Router composition should make it easy to verify:

- the built router exposes the intended top-level groups
- public groups remain reachable without unrelated protection
- protected groups are mounted at the correct boundary

Prefer tests that exercise the built handler in-process rather than starting a listener.
