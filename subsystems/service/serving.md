# Serving

This guide defines what an HTTP-facing service should own in `Serve(...)`.

Use it when the service exposes HTTP directly and needs a clear boundary between router composition and outer serving concerns.

## Required

- Keep route composition inside `BuildRouter()`.
- Keep listen and deployment concerns inside `Serve(...)`.
- Mount deployment base paths outside the inner API tree.
- Keep mutable bootstrap work outside `Serve(...)`.

## Serving boundary

`Serve(...)` should own serving concerns such as:

- host and port inputs
- deployment base-path mounting
- HTTP server startup
- shutdown behavior when needed

It should not rebuild route composition, resolve config precedence, or perform one-time mutable initialization.

If you need the route-composition details themselves, read `../http-router-composition.md`.

## Canonical shape

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

This keeps the split obvious:

- `BuildRouter()` defines the service's HTTP surface
- `Serve(...)` defines how that surface is exposed in a deployment

## With explicit shutdown

If the service needs shutdown coordination, keep that concern local to `Serve(...)` or to the outer process runner.

```go
func (s *Service) Serve(ctx context.Context, host string, port int, basePath string) error {
	api := s.BuildRouter()

	var handler http.Handler = api
	if basePath != "" && basePath != "/" {
		root := http.NewServeMux()
		wire.Subrouter(root, basePath, api)
		handler = root
	}

	server := &http.Server{
		Addr:    net.JoinHostPort(host, strconv.Itoa(port)),
		Handler: handler,
	}

	errCh := make(chan error, 1)
	go func() {
		errCh <- server.ListenAndServe()
	}()

	select {
	case <-ctx.Done():
		return server.Shutdown(context.Background())
	case err := <-errCh:
		return err
	}
}
```

Choose one serving shape per project and apply it consistently.

## Testing expectations

Serving tests should make it easy to verify:

- base-path mounting preserves route behavior
- shutdown behavior works when the serving shape includes it

Prefer tests that exercise the built handler in-process when possible.
