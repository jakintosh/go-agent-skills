# Middleware Boundaries

This guide defines how to apply middleware in a composed route tree.

Use it when you need to decide whether auth, CORS, or similar behavior should wrap one direct route or an entire mounted subtree.

## Required

- Apply middleware at the highest safe boundary.
- Distinguish handler-level wrappers from handlerfunc-level wrappers.
- Build middleware bundles from dependencies of the owning HTTP surface during router composition.
- Keep the applied protection obvious at the registration site.

## Local shape

Prefer a bundle that supports both subtree and direct-route wrapping:

```go
type Middleware struct {
	auth     func(http.Handler, ...keys.Permission) http.Handler
	authFunc func(http.HandlerFunc, ...keys.Permission) http.HandlerFunc
	cors     func(http.Handler) http.Handler
	corsFunc func(http.HandlerFunc) http.HandlerFunc
}
```

Use handler-level wrappers when the whole mounted group shares one boundary:

```go
wire.Subrouter(root, "/admin", mw.auth(a.buildAdminRouter(mw), service.PermissionAdmin))
```

Use func-level wrappers when the boundary belongs to one direct route inside a local group:

```go
mux.HandleFunc("POST /", mw.authFunc(a.handleCreateDocument, service.PermissionWrite))
```

This keeps the composition code easy to scan:

- subtree protection is visible at the mount point
- per-route protection is visible at the direct registration

## Focused example

```go
func (a *API) Router() http.Handler {
	mw := Middleware{
		auth:     a.keys.WithAuth,
		authFunc: a.keys.WithAuthFunc,
		cors:     a.cors.WithCORS,
		corsFunc: a.cors.WithCORSFunc,
	}

	root := http.NewServeMux()
	wire.Subrouter(root, "/documents", a.buildDocumentRouter(mw))
	wire.Subrouter(root, "/settings", mw.auth(a.buildSettingsRouter(mw), service.PermissionAdmin))
	return root
}

func (a *API) buildDocumentRouter(
	mw Middleware,
) http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /", mw.corsFunc(a.handleListDocuments))
	mux.HandleFunc("OPTIONS /", mw.corsFunc(a.handleListDocuments))
	mux.HandleFunc("POST /", mw.authFunc(a.handleCreateDocument, service.PermissionWrite))
	return mux
}
```

When a whole group shares the same rule, wrap the group once instead of repeating the same middleware on every route.
