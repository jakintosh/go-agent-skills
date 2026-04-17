# Deployment Mounting

This guide defines how to expose a composed API under deployment-specific serving concerns.

Use it when the application needs to mount its inner API under a base path, or when you need to keep `Serve()` clearly separate from `BuildRouter()`.

## Required

- Keep route composition inside `BuildRouter()`.
- Keep deployment base-path mounting outside the inner API tree.
- Keep listen and startup concerns out of route registration.
- Treat the built router as the deployable API surface.

## Local shape

The default split is:

1. `BuildRouter()` returns the inner API handler
2. outer serving code optionally mounts that handler under a deployment base path
3. outer serving code starts the HTTP server

## Focused example

```go
func (s *Service) Serve(host string, port int, basePath string) error {
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

This keeps the boundary obvious:

- `BuildRouter()` defines the API tree
- deployment mounting defines where that tree is exposed
- serving code defines how the process listens
