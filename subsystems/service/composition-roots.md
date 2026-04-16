# Composition Roots

This guide defines how to wire a service from outer layers in production code and tests

Use it when you are constructing a service in `main`, CLI handlers, server startup, or test helpers

Separate composition roots make it easier to:

- keep runtime setup out of domain code
- swap real dependencies for deterministic test doubles
- test the service directly without going through the CLI or full server startup
- change infrastructure wiring without changing service behavior

## Required

- Keep config resolution outside `internal/service`
- Open databases and external clients before calling `service.New(...)`
- Use separate production and test composition roots
- Keep production-vs-test branching out of the service package itself

## Production composition root

The production composition root should:

1. resolve config
2. open stores and external clients
3. construct the service
4. call the top-level entry point such as `Serve(...)`

```go
func run() error {
	cfgOpts := config.ResolveOptions{}
	runtime, err := config.Resolve(cfgOpts)
	if err != nil {
		return err
	}

	dbOpts := database.Options {
		Path: runtime.DatabasePath
	}
	store, err := sqlite.Open(dbOpts)
	if err != nil {
		return err
	}
	defer store.Close()

	svc, err := service.New(service.Options{
		Store: store,
		Clock: time.Now,
	})
	if err != nil {
		return err
	}

	return svc.Serve(runtime.Host, runtime.Port, runtime.BasePath)
}
```

The outer layer owns resource setup and cleanup. The service package should receive ready-to-use dependencies

## Test composition root

The test composition root should:

1. create deterministic ephemeral dependencies
2. construct the service with test wiring
3. own cleanup
4. expose only what tests regularly need

```go
type TestService struct {
	Service *service.Service
	Store   *service.Store
}

func NewTestService(t *testing.T) TestService {
	t.Helper()

	store := service.NewStore(":memory:")
	opts := service.Options {
		Store: store,
		Clock: func() time.Time {
			return time.Date(2024, 1, 15, 10, 30, 0, 0, time.UTC)
		},
	}
	svc, err := service.New(opts)
	if err != nil {
		t.Fatalf("new service: %v", err)
	}

	return TestService{
		Service: svc,
		Store:   store,
	}
}
```

This keeps tests explicit and makes production wiring differences irrelevant to most service behavior tests
