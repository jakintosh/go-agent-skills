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
- API-adjacent initialization, such as key bootstrap state, that should not happen on every startup

This work belongs in a dedicated top-level path such as `<app> init`, not inside `New(...)` or routine `server.Serve(...)` startup

## Canonical flow

The default initialization flow is:

1. outer layer resolves config
2. outer layer opens the dependencies needed for initialization
3. outer layer calls one explicit service initialization function or method
4. the function treats already-initialized state as success when repetition is safe

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

	initOpts := service.InitOptions{
		Store: store,
	}
	return service.Init(initOpts)
}
```

## Initialization method shape

Keep the initialization method focused on one-time mutable setup

```go
func Init(
	opts InitOptions,
) error {
	if opts.Store == nil {
		return errors.New("service: store required")
	}

	if err := opts.Store.CreateSchema(); err != nil {
		return err
	}

	if err := ensureAdminKeyspace(opts.Store); err != nil {
		return err
	}

	return nil
}
```

The important boundary is simple:

- `New(...)` constructs the service
- `Init(...)` or another explicit initialization entry point performs mutable setup
- `server.Serve(...)` starts normal runtime behavior

## Declared bootstrap constants

When initialization and runtime behavior share permission declarations or similar constants, declare them once in the service package and reuse them everywhere

```go
const (
	PermissionRead  keys.Permission = "read"
	PermissionWrite keys.Permission = "write"
	PermissionAdmin keys.Permission = "admin"
)

var KeyCatalog = keys.MustCatalog(
	keys.PermissionDef{
		Key:         PermissionRead,
		Display:     "Read",
		Description: "Read project data",
	},
	keys.PermissionDef{
		Key:         PermissionWrite,
		Display:     "Write",
		Description: "Create and update project data",
	},
	keys.PermissionDef{
		Key:         PermissionAdmin,
		Display:     "Admin",
		Description: "Manage settings and API keys",
	},
)
```

This keeps middleware, initialization, and tests aligned on the same permission vocabulary

## Testing expectations

Initialization tests should make it easy to verify:

- initialization performs required durable setup
- repeated safe runs succeed when the state is already initialized
- normal service construction and normal server startup do not perform the same work implicitly
