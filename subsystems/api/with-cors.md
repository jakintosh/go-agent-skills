# Integrating CORS Origin Management

**Package:** `git.sr.ht/~jakintosh/command-go@v0.5.0`

Use this guide when an API uses `command-go/pkg/cors` for dynamic CORS origin whitelisting, CORS middleware, HTTP management routes, and remote CLI management.

The application owns where CORS management appears in its API tree and which routes need CORS behavior. The `cors` package owns origin validation, storage mechanics, middleware behavior, and the package-owned management handler.

## Required

- Initialize the SQL-backed CORS store in `internal/database.Open(...)`.
- Construct `cors.Service` in `internal/api.New(...)` from API dependencies.
- Build CORS middleware into the API middleware bundle.
- Apply CORS at the highest safe route or subtree boundary.
- Mount `cors.Handler()` as a package-owned handler under a protected settings or admin subtree.
- Run initial origin bootstrap through an explicit init path or startup hook that handles already-initialized state.
- Mount the pre-built CLI command with the full API collection path when remote CORS management is needed.

## Database Store

Create the CORS store alongside other SQL-backed stores during database open.

```go
type DB struct {
	Conn      *sql.DB
	CORSStore *cors.SQLStore
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

	corsStore, err := cors.NewSQL(conn)
	if err != nil {
		conn.Close()
		return nil, fmt.Errorf("open cors store: %w", err)
	}

	return &DB{
		Conn:      conn,
		CORSStore: corsStore,
	}, nil
}
```

`cors.NewSQL(...)` owns its package schema and migrations. The database package owns when that store is attached to the application adapter.

## API Construction

Construct `cors.Service` in the API constructor because CORS is HTTP transport behavior.

```go
type Options struct {
	Service *service.Service
	CORS    cors.Store
}

type API struct {
	service *service.Service
	cors    *cors.Service
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
	if opts.CORS == nil {
		return nil, errors.New("api: cors store required")
	}

	corsOpts := cors.Options{
		Store: opts.CORS,
	}
	corsSvc, err := cors.New(corsOpts)
	if err != nil {
		return nil, err
	}

	return &API{
		service: opts.Service,
		cors:    corsSvc,
	}, nil
}
```

## Middleware and Route Mounting

Add CORS middleware to the API middleware bundle and apply it where browser callers need it.

```go
type Middleware struct {
	auth     func(http.Handler, ...keys.PermissionKey) http.Handler
	cors     func(http.Handler) http.Handler
	corsFunc func(http.HandlerFunc) http.HandlerFunc
}

func (a *API) Router() http.Handler {
	mw := Middleware{
		auth:     a.keys.WithAuth,
		cors:     a.cors.WithCORS,
		corsFunc: a.cors.WithCORSFunc,
	}

	root := http.NewServeMux()
	wire.Subrouter(root, "/documents", a.buildDocumentRouter(mw))
	wire.Subrouter(root, "/settings", mw.auth(a.buildSettingsRouter(), service.PermissionAdmin))
	return root
}

func (a *API) buildDocumentRouter(
	mw Middleware,
) http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /", mw.corsFunc(a.handleListDocuments))
	mux.HandleFunc("OPTIONS /", mw.corsFunc(a.handleListDocuments))
	return mux
}

func (a *API) buildSettingsRouter() http.Handler {
	mux := http.NewServeMux()
	wire.Subrouter(mux, "/cors", a.cors.Handler())
	return mux
}
```

If the project uses method-specific `http.ServeMux` patterns, make sure preflight `OPTIONS` requests reach the CORS middleware for the route being protected.

## Bootstrap Origins

Bootstrap origins are mutable state. Run initialization explicitly and treat already-initialized state as successful when that is the intended operation.

```go
func InitCORS(
	store cors.Store,
	origins []string,
) error {
	corsOpts := cors.Options{
		Store: store,
	}
	corsSvc, err := cors.New(corsOpts)
	if err != nil {
		return err
	}

	if err := corsSvc.Init(origins); err != nil {
		if !errors.Is(err, cors.ErrAlreadyInitialized) {
			return err
		}
	}
	return nil
}
```

Origins should be complete URLs beginning with `http://` or `https://`.

## CLI Management

Mount the pre-built command tree when the CLI should manage the remote whitelist.

```go
import corscmd "git.sr.ht/~jakintosh/command-go/pkg/cors/cmd"

var settingsCommand = &args.Command{
	Name: "settings",
	Help: "manage settings",
	Subcommands: []*args.Command{
		corscmd.Command(DEFAULT_CFG, "/api/v1/settings/cors"),
	},
}
```

The collection path must match the path a remote caller sees after server mounting. If `internal/server` mounts `api.Router()` at `/api/v1` and `internal/api` mounts CORS management at `/settings/cors`, pass `/api/v1/settings/cors`.

## Testing Expectations

Cover:

- API construction rejects missing CORS store dependencies.
- allowed origins receive CORS headers.
- disallowed preflight requests return the expected failure status.
- preflight tests include `Origin` and `Access-Control-Request-Method` headers.
- package handler routes are mounted at the intended settings path.
- CLI CORS commands receive the same collection path exposed by the server.
