# Composition Roots

This guide defines how to wire the serving stack from outer layers in production code and tests.

Use it when you are constructing service, API, app, database, or other runtime dependencies in `internal/server`, CLI handlers, or `internal/testutil`.

Separate composition roots make it easier to:

- keep runtime setup out of domain code
- swap real dependencies for deterministic test doubles
- test the service directly without going through HTTP
- test the API directly without starting a listener
- change infrastructure wiring without changing service or API behavior

## Required

- Keep config resolution outside `internal/service` and `internal/api`.
- Open databases and external clients before calling `service.New(...)`.
- Construct `service.Service` before `api.API`.
- Use `internal/server` as the production serving composition root.
- Use `internal/testutil` as the test composition root.
- Keep production-vs-test branching out of `internal/service`.

## Production Composition Root

The production composition root should:

1. receive resolved runtime from `internal/config`
2. open stores and external clients
3. construct the service
4. construct the API
5. construct any other HTTP surfaces
6. mount route trees
7. call the top-level serving entry point

```go
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
		Clock: time.Now,
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

	mux := http.NewServeMux()
	wire.Subrouter(mux, "/api/v1", apiServer.Router())

	return http.ListenAndServe(opts.Runtime.Server.ListenAddress, mux)
}
```

The server package owns resource setup and cleanup. The service and API packages should receive ready-to-use dependencies.

## Test Composition Root

The test composition root should:

1. create deterministic ephemeral dependencies
2. run explicit bootstrap initialization when tests need initialized durable state
3. construct the service with test wiring
4. construct the API with test wiring
5. own cleanup
6. expose only what tests regularly need

```go
type TestEnv struct {
	DB      *database.DB
	Service *service.Service
	Router  http.Handler
}

func SetupTestEnv(
	t *testing.T,
) *TestEnv {
	t.Helper()

	db := SetupTestDB(t)

	initOpts := service.InitOptions{
		Store: db,
	}
	if err := service.Init(initOpts); err != nil {
		t.Fatalf("init service state: %v", err)
	}

	svcOpts := service.Options{
		Store: db,
		Clock: fixedClock,
	}
	svc, err := service.New(svcOpts)
	if err != nil {
		t.Fatalf("new service: %v", err)
	}

	apiOpts := api.Options{
		Service: svc,
		Keys:    db.KeysStore,
	}
	apiServer, err := api.New(apiOpts)
	if err != nil {
		t.Fatalf("new api: %v", err)
	}

	return &TestEnv{
		DB:      db,
		Service: svc,
		Router:  apiServer.Router(),
	}
}
```

This keeps tests explicit:

- service tests call `env.Service` directly
- API tests exercise `env.Router`
- database tests can use `env.DB` or a narrower database helper
- production wiring differences stay irrelevant to behavior tests
