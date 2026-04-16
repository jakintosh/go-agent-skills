# Bootstrap Initialization

This guide defines how to handle explicit mutable initialization for a service

Use it when the application needs an `init` command or another explicit startup path that creates durable state before normal runtime behavior begins

## Required

- Keep mutable bootstrap work separate from normal `serve` startup
- Use an explicit initialization entry point
- Make repeated safe runs succeed when practical
- Keep declared permissions or bootstrap constants centralized when multiple entry points reuse them

## When to add explicit initialization

Add an explicit initialization path when the application needs durable setup such as:

- database schema creation
- key or auth bootstrap state
- seed records required for first use
- API-side initialization that should not happen on every startup

This work belongs in a dedicated top-level path such as `<app> init`, not inside `New(...)` or routine `Serve(...)` startup

## Canonical flow

The default initialization flow is:

1. outer layer opens the required dependencies
2. outer layer constructs the service with explicit options
3. the service runs one explicit initialization method
4. the method treats already-initialized state as success when repetition is safe

```go
func runInit() error {
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

	opts := service.Options{
		Store: store,
		Clock: time.Now,
	}
	svc, err := service.New(opts)
	if err != nil {
		return err
	}

	return svc.Initialize()
}
```

## Initialization method shape

Keep the initialization method focused on one-time mutable setup

```go
func (s *Service) Initialize() error {
	if err := s.store.CreateSchema(); err != nil {
		return err
	}

	if err := s.ensureAdminKeyspace(); err != nil {
		return err
	}

	return nil
}
```

The important boundary is simple:

- `New(...)` constructs the service
- `Initialize()` performs explicit mutable setup
- `Serve(...)` starts normal runtime behavior

## Declared bootstrap constants

When initialization and runtime behavior share permission declarations or similar constants, declare them once in the service package and reuse them everywhere

```go
var (
	PermissionRead  = keys.Permission{Name: "read"}
	PermissionWrite = keys.Permission{Name: "write"}
	PermissionAdmin = keys.Permission{Name: "admin"}
)

func AllKeyPermissions() []*keys.Permission {
	return []*keys.Permission{
		&PermissionRead,
		&PermissionWrite,
		&PermissionAdmin,
	}
}
```

This keeps middleware, initialization, and tests aligned on the same permission vocabulary

## Testing expectations

Initialization tests should make it easy to verify:

- initialization performs required durable setup
- repeated safe runs succeed when the state is already initialized
- normal service construction does not perform the same work implicitly
