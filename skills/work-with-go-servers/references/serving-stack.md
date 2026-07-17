# Defining a Server

This guide defines the default shape of an `internal/server` package.

Use it when an application needs to construct the production serving stack, mount API and UI surfaces, apply deployment base paths, or own listen and shutdown behavior.

The server package is the production serving composition boundary. It receives resolved runtime config, opens runtime dependencies, constructs service/API/web packages, mounts route trees into one process router, applies deployment base paths, owns listen and shutdown behavior, and cleans up resources it opens. Pair this guide with the [config skill](../../work-with-go-config/SKILL.md) for runtime resolution, the [service skill](../../work-with-go-services/SKILL.md) for domain behavior, the [API skill](../../work-with-go-http-apis/SKILL.md) for JSON HTTP contracts, and the [web UI skill](../../work-with-go-web-uis/SKILL.md) for server-rendered browser UIs.

If the serving stack needs Consent-backed user accounts, read the [Consent user skill](../../work-with-consent-users/SKILL.md) for the auth-client wiring, account resolution, and package-handler mounts that belong in the composition root.

## Contents

- [Required](#required)
- [Canonical Package Shape](#canonical-package-shape)
- [Canonical Flow](#canonical-flow)
- [Deployment Mounting](#deployment-mounting)
- [With Explicit Shutdown](#with-explicit-shutdown)
- [Testing Expectations](#testing-expectations)

## Required

- Keep config resolution outside `internal/server`; pass resolved runtime into server options.
- Open databases and external clients before constructing service and API packages.
- Construct `service.Service` before `api.API`.
- Mount the API router as one route tree, usually under a versioned path such as `/api/v1`.
- Mount deployment base paths outside the inner API tree.
- Keep listen and shutdown concerns in `internal/server`, not `internal/service`.
- Keep command handlers thin: resolve runtime, then call the server entry point.

## Canonical Package Shape

Use a small package by default:

```text
internal/server/
  server.go
```

Add files only when the serving stack has meaningful sub-areas, such as separate auth-client construction or shutdown coordination.

## Canonical Flow

The normal production flow is:

1. a command resolves `config.Runtime`
2. `server.Serve(...)` receives the resolved runtime
3. the server opens the database and other runtime dependencies
4. the server constructs `service.Service`
5. the server constructs `api.API`
6. the server constructs web UI surfaces when present
7. the server mounts all route trees into one root router
8. the server listens and coordinates shutdown when needed

```go
package server

import (
	"net/http"

	"example/internal/api"
	"example/internal/config"
	"example/internal/database"
	"example/internal/service"
	"example/internal/web"
	"git.sr.ht/~jakintosh/command-go/pkg/wire"
)

type Options struct {
	Runtime config.Runtime
}

func Serve(
	opts Options,
) error {
	dbOpts := database.Options{
		Path: opts.Runtime.Paths.DatabaseFile,
	}
	db, err := database.Open(dbOpts)
	if err != nil {
		return err
	}
	defer db.Close()

	svcOpts := service.Options{
		Store: db,
		Clock: opts.Runtime.Clock,
	}
	svc, err := service.New(svcOpts)
	if err != nil {
		return err
	}

	apiOpts := api.Options{
		Service: svc,
		Keys:    db.KeysStore,
	}
	apiServer, err := api.New(apiOpts)
	if err != nil {
		return err
	}

	webOpts := web.Options{
		Service: svc,
	}
	webServer, err := web.New(webOpts)
	if err != nil {
		return err
	}

	mux := http.NewServeMux()
	wire.Subrouter(mux, "/", webServer.Router())
	wire.Subrouter(mux, "/api/v1", apiServer.Router())

	return http.ListenAndServe(opts.Runtime.Server.ListenAddress, mux)
}
```

This keeps the split obvious:

- service defines behavior
- API defines the JSON HTTP surface
- web defines the rendered browser surface
- server exposes those surfaces in one running process

## Deployment Mounting

Treat API and web routers as inner route trees. Deployment-specific mounting belongs in `internal/server`.

```go
func mountBasePath(
	basePath string,
	handler http.Handler,
) http.Handler {
	if basePath == "" || basePath == "/" {
		return handler
	}

	root := http.NewServeMux()
	wire.Subrouter(root, basePath, handler)
	return root
}
```

Do not bake deployment base paths into `api.Router()` or service methods. The same API router should be testable in-process without knowing where production exposes it.

## With Explicit Shutdown

When the project needs coordinated shutdown, keep it in `internal/server` or a closely related process runner.

In larger projects, it can be useful to split handler construction from listening so shutdown tests can exercise the built handler without opening a real listener.

```go
func Serve(
	ctx context.Context,
	opts Options,
) error {
	handler, cleanup, err := BuildHandler(opts)
	if err != nil {
		return err
	}
	defer cleanup()

	server := &http.Server{
		Addr:    opts.Runtime.Server.ListenAddress,
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

## Testing Expectations

Server tests should make it easy to verify:

- the API tree is mounted at the intended production path
- UI and API surfaces can coexist without route collisions
- auth package handlers are mounted at the intended paths when the app uses user accounts
- deployment base-path mounting preserves route behavior
- shutdown behavior works when the serving shape includes it

Prefer API tests against `api.Router()` for endpoint behavior. Use server tests for process-level mounting and serving behavior.
