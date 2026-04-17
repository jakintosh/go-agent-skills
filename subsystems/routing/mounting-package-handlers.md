# Mounting Package Handlers

This guide defines how to compose package-owned HTTP handlers into your route tree.

Use it when a subsystem already exposes its own `http.Handler` and your service needs to decide where that handler lives and what boundary protects it.

## Required

- Mount package-provided handlers directly instead of rebuilding their routes manually.
- Use your service router to decide the mount path.
- Apply auth or other cross-cutting middleware at the boundary where the package handler is mounted.
- Keep ownership clear between the package that defines the handler and the service that exposes it.

## Local flow

The normal pattern is:

1. build the service's local router for the area
2. mount package-owned handlers with `wire.Subrouter`
3. protect the containing subtree at the service boundary when needed

## Focused example

```go
func (s *Service) BuildRouter() http.Handler {
	mw := Middleware{
		auth: s.keys.WithAuth,
	}

	root := http.NewServeMux()
	wire.Subrouter(root, "/settings", mw.auth(s.buildSettingsRouter(), &PermissionAdmin))
	return root
}

func (s *Service) buildSettingsRouter() http.Handler {
	mux := http.NewServeMux()

	wire.Subrouter(mux, "/keys", s.keys.Handler())
	wire.Subrouter(mux, "/cors", s.cors.Handler())

	return mux
}
```

This keeps the split obvious:

- the package owns its own route details
- your service owns where that handler is mounted
- your service owns who can reach that mounted area
