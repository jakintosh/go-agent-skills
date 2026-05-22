# Mounting Package Handlers

This guide defines how to compose package-owned HTTP handlers into your route tree.

Use it when a subsystem already exposes its own `http.Handler` and your API or server package needs to decide where that handler lives and what boundary protects it.

Common examples include `command-go/pkg/keys` and `command-go/pkg/cors`, which expose package-owned management handlers that should be mounted into the application's API tree. Consent-backed applications also mount auth package handlers such as `/auth/callback`, `/auth/logout`, and `/.well-known/consent-integration`; read `../users/README.md` for that account setup path.

## Required

- Mount package-provided handlers directly instead of rebuilding their routes manually.
- Use your API router to decide API-local mount paths.
- Apply auth or other cross-cutting middleware at the boundary where the package handler is mounted.
- Keep ownership clear between the package that defines the handler and the API or server package that exposes it.

## Local flow

The normal pattern is:

1. build the API's local router for the area
2. mount package-owned handlers with `wire.Subrouter`
3. protect the containing subtree at the API boundary when needed

## Focused example

```go
func (a *API) Router() http.Handler {
	mw := Middleware{
		auth: a.keys.WithAuth,
	}

	root := http.NewServeMux()
	wire.Subrouter(root, "/settings", mw.auth(a.buildSettingsRouter(), service.PermissionAdmin))
	return root
}

func (a *API) buildSettingsRouter() http.Handler {
	mux := http.NewServeMux()

	wire.Subrouter(mux, "/keys", a.keys.Handler())
	wire.Subrouter(mux, "/cors", a.cors.Handler())

	return mux
}
```

This keeps the split obvious:

- the package owns its own route details
- your API owns where that handler is mounted inside the API tree
- your API owns who can reach that mounted area
- your server owns where the complete API tree is mounted in production

When the mounted handler also has a CLI command, pass the full API collection path to that command. For example, if `internal/server` mounts `api.Router()` at `/api/v1` and `internal/api` mounts `keys.Handler()` at `/settings/keys`, the CLI command should receive `/api/v1/settings/keys`.
