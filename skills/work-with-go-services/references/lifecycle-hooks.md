# Lifecycle Hooks

This guide defines when and how to add `Start()` and `Stop()` to a service

Use it only when the service owns long-lived background work that needs coordinated startup and shutdown

## Contents

- [Required](#required)
- [When lifecycle hooks are useful](#when-lifecycle-hooks-are-useful)
- [Canonical shape](#canonical-shape)
- [Server Usage](#server-usage)

## Required

- Add lifecycle hooks only when the service owns background processing
- Keep constructor work separate from long-lived runtime work
- Make shutdown explicit and coordinated
- Let outer layers control process lifetime

## When lifecycle hooks are useful

Good reasons to add lifecycle hooks include:

- polling loops
- queue consumers
- background refreshers
- metrics or health goroutines that need coordinated shutdown

If the service only handles request/response domain behavior, a constructor is usually enough. HTTP routing belongs in `internal/api`, and process serving belongs in `internal/server`.

## Canonical shape

```go
type Service struct {
	store  Store
	clock  func() time.Time
	jobs   *Worker
	cancel context.CancelFunc
	wg     sync.WaitGroup
}

func (s *Service) Start(
	ctx context.Context,
) error {
	ctx, cancel := context.WithCancel(ctx)
	s.cancel = cancel

	s.wg.Add(1)
	go func() {
		defer s.wg.Done()
		s.jobs.Run(ctx)
	}()

	return nil
}

func (s *Service) Stop() error {
	if s.cancel != nil {
		s.cancel()
	}

	s.wg.Wait()
	return nil
}
```

The lifecycle boundary should stay obvious:

- `New(...)` constructs dependencies
- `Start(...)` begins background work
- `Stop()` shuts that work down cleanly

## Server Usage

The server package should own process lifetime and call lifecycle hooks explicitly when it constructs the service.

```go
func Serve(
	ctx context.Context,
	opts server.Options,
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

	if err := svc.Start(ctx); err != nil {
		return err
	}
	defer svc.Stop()

	apiOpts := api.Options{
		Service: svc,
		Keys:    db.KeysStore,
	}
	apiServer, err := api.New(apiOpts)
	if err != nil {
		return err
	}

	return serveHTTP(ctx, opts.Runtime.Server.ListenAddress, apiServer.Router())
}
```
