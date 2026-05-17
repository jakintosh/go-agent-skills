# Integrating API Key Management

**Package:** `git.sr.ht/~jakintosh/command-go@v0.5.0`

Use this guide when an API uses `command-go/pkg/keys` for API-key creation, verification, authorization, HTTP middleware, and remote CLI management.

The application owns where key management appears in its API tree and which domain permissions exist. The `keys` package owns token storage mechanics, hashing, verification, middleware, and the package-owned management handler.

## Required

- Declare the permission vocabulary in `internal/service`.
- Initialize the SQL-backed keys store in `internal/database.Open(...)`.
- Construct `keys.Service` in `internal/api.New(...)` from API dependencies.
- Mount `keys.Handler()` as a package-owned handler under a protected settings or admin subtree.
- Use `keys.WithAuth` or `keys.WithAuthFunc` at the route boundary that needs authentication.
- Run bootstrap token initialization through an explicit mutable init path, not ordinary service construction.
- Mount the pre-built CLI command with the full API collection path when remote key management is needed.

## Permission Vocabulary

Permissions express domain authorization, so keep their declarations in `internal/service`.

```go
const (
	PermissionRead  keys.PermissionKey = "read"
	PermissionWrite keys.PermissionKey = "write"
	PermissionAdmin keys.PermissionKey = "admin"
)

var KeyPermissions = keys.Permissions{
	{
		Key:         PermissionRead,
		Display:     "Read",
		Description: "Read documents",
	},
	{
		Key:         PermissionWrite,
		Display:     "Write",
		Description: "Create and update documents",
	},
	{
		Key:         PermissionAdmin,
		Display:     "Admin",
		Description: "Manage settings and API keys",
	},
}
```

## Database Store

Create the keys store alongside other SQL-backed stores during database open.

```go
type DB struct {
	Conn      *sql.DB
	KeysStore *keys.SQLStore
}

func Open(
	opts Options,
) (
	*DB,
	error,
) {
	conn, err := sql.Open("sqlite", opts.Path)
	if err != nil {
		return nil, err
	}

	keysStore, err := keys.NewSQL(conn)
	if err != nil {
		conn.Close()
		return nil, fmt.Errorf("open keys store: %w", err)
	}

	return &DB{
		Conn:      conn,
		KeysStore: keysStore,
	}, nil
}
```

`keys.NewSQL(...)` owns its package schema and migrations. The database package owns when that store is attached to the application adapter.

## API Construction

Construct `keys.Service` in the API constructor because it is HTTP transport support, while the permission vocabulary comes from the service layer.

```go
type Options struct {
	Service *service.Service
	Keys    keys.Store
}

type API struct {
	service *service.Service
	keys    *keys.Service
}

func New(
	opts Options,
) (
	*API,
	error,
) {
	if opts.Service == nil {
		return nil, errors.New("api: service required")
	}
	if opts.Keys == nil {
		return nil, errors.New("api: keys store required")
	}

	keysOpts := keys.Options{
		Store:       opts.Keys,
		Permissions: service.KeyPermissions,
	}
	keySvc, err := keys.New(keysOpts)
	if err != nil {
		return nil, err
	}

	return &API{
		service: opts.Service,
		keys:    keySvc,
	}, nil
}
```

## Route Mounting

Mount package-owned key routes inside the API tree and apply authorization at the containing boundary.

```go
type Middleware struct {
	auth     func(http.Handler, ...keys.PermissionKey) http.Handler
	authFunc func(http.HandlerFunc, ...keys.PermissionKey) http.HandlerFunc
}

func (a *API) Router() http.Handler {
	mw := Middleware{
		auth:     a.keys.WithAuth,
		authFunc: a.keys.WithAuthFunc,
	}

	root := http.NewServeMux()
	wire.Subrouter(root, "/documents", a.buildDocumentRouter(mw))
	wire.Subrouter(root, "/settings", mw.auth(a.buildSettingsRouter(), service.PermissionAdmin))
	return root
}

func (a *API) buildSettingsRouter() http.Handler {
	mux := http.NewServeMux()
	wire.Subrouter(mux, "/keys", a.keys.Handler())
	return mux
}
```

Use `WithAuth(..., permission)` for a whole subtree and `WithAuthFunc(..., permission)` for one direct route. Calling either without a permission authenticates any valid key.

## Bootstrap Initialization

Bootstrap keys are mutable state. Create them in an explicit init path.

```go
func runInit(
	opts InitOptions,
) error {
	keyOpts := keys.Options{
		Store:       opts.Keys,
		Permissions: service.KeyPermissions,
	}
	keySvc, err := keys.New(keysOpts)
	if err != nil {
		return err
	}

	return keySvc.Init(opts.BootstrapToken, service.PermissionAdmin)
}
```

Use `keys.GenerateBootstrapKey()` when the application needs to generate a bootstrap token. Store and load that token through the config or secret mechanism appropriate for the project.

## CLI Management

Mount the pre-built command tree when the CLI should manage remote keys.

```go
import keyscmd "git.sr.ht/~jakintosh/command-go/pkg/keys/cmd"

var settingsCommand = &args.Command{
	Name: "settings",
	Help: "manage settings",
	Subcommands: []*args.Command{
		keyscmd.Command(DEFAULT_CFG, "/api/v1/settings/keys"),
	},
}
```

The collection path must match the path a remote caller sees after server mounting. If `internal/server` mounts `api.Router()` at `/api/v1` and `internal/api` mounts keys at `/settings/keys`, pass `/api/v1/settings/keys`.

## Testing Expectations

Cover:

- API construction rejects missing keys store dependencies.
- protected routes reject missing, invalid, or under-permissioned keys.
- package handler routes are mounted at the intended settings path.
- bootstrap initialization is explicit and repeatable according to package behavior.
- CLI key commands receive the same collection path exposed by the server.
