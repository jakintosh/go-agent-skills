# Middleware Boundaries

This guide defines how to apply middleware in a composed route tree.

Use it when you need to decide whether auth, CORS, or similar behavior should wrap one direct route or an entire mounted subtree.

## Required

- Apply middleware at the highest safe boundary.
- Distinguish handler-level wrappers from handlerfunc-level wrappers.
- Build middleware bundles from service dependencies during router composition.
- Keep the applied protection obvious at the registration site.

## Local shape

Prefer a bundle that supports both subtree and direct-route wrapping:

```go
type Middleware struct {
	auth     func(http.Handler, *keys.Permission) http.Handler
	authFunc func(http.HandlerFunc, *keys.Permission) http.HandlerFunc
	cors     func(http.Handler) http.Handler
	corsFunc func(http.HandlerFunc) http.HandlerFunc
}
```

Use handler-level wrappers when the whole mounted group shares one boundary:

```go
wire.Subrouter(root, "/admin", mw.auth(s.buildAdminRouter(mw), &PermissionAdmin))
```

Use func-level wrappers when the boundary belongs to one direct route inside a local group:

```go
mux.HandleFunc("POST /", mw.authFunc(s.handleCreateDocument, &PermissionWrite))
```

This keeps the composition code easy to scan:

- subtree protection is visible at the mount point
- per-route protection is visible at the direct registration

## Focused example

```go
func (s *Service) BuildRouter() http.Handler {
	mw := Middleware{
		auth:     s.keys.WithAuth,
		authFunc: s.keys.WithAuthFunc,
		cors:     s.cors.WithCORS,
		corsFunc: s.cors.WithCORSFunc,
	}

	root := http.NewServeMux()
	wire.Subrouter(root, "/documents", s.buildDocumentRouter(mw))
	wire.Subrouter(root, "/settings", mw.auth(s.buildSettingsRouter(mw), &PermissionAdmin))
	return root
}

func (s *Service) buildDocumentRouter(mw Middleware) http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /", mw.corsFunc(s.handleListDocuments))
	mux.HandleFunc("POST /", mw.authFunc(s.handleCreateDocument, &PermissionWrite))
	return mux
}
```

When a whole group shares the same rule, wrap the group once instead of repeating the same middleware on every route.
