# Lifecycle Hooks

This guide defines when and how to add `Start()` and `Stop()` to a service

Use it only when the service owns long-lived background work that needs coordinated startup and shutdown

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

If the service only handles in-process request/response behavior, a constructor plus router or serving entry point is usually enough

## Canonical shape

```go
type Service struct {
	store  Store
	clock  func() time.Time
	jobs   *Worker
	cancel context.CancelFunc
	wg     sync.WaitGroup
}

func (s *Service) Start(ctx context.Context) error {
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

## Outer-layer usage

The outer layer should own process lifetime and call lifecycle hooks explicitly

```go
func run() error {
	opts := service.Options{
		Store: store,
		Clock: time.Now,
	}
	svc, err := service.New(opts)
	if err != nil {
		return err
	}

	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt)
	defer stop()

	if err := svc.Start(ctx); err != nil {
		return err
	}
	defer svc.Stop()

	return svc.Serve(host, port, basePath)
}
```
