# Database Adapters

This guide defines the standard shape for SQL-interfacing database adapters in this style system.

It focuses on the database package boundary, migrations, query style, transactions, and the discipline that keeps adapter code mechanical instead of business-heavy.

The goal is to make database adapters:

- thin and explicit
- easy to audit for schema and query behavior
- aligned with service-owned store contracts
- predictable under transactional state changes

## When to use this guide

Use this guide when you are:

- building `internal/database` or a runtime store layer
- implementing a service-owned store interface
- writing migrations and initialization logic
- reviewing whether SQL code has started to absorb business logic

## Non-goals

This guide does not define:

- the store contract itself
- service-layer validation rules
- API handler behavior
- database vendor benchmarking or deployment architecture

## Core rules

- Keep the database package thin and mechanical.
- Provide an explicit open entry point, with migration happening during open.
- Enable foreign keys during SQLite initialization.
- Use ordered migrations defined in Go.
- Use positional SQL parameters.
- Prefer explicit upserts for idempotent writes when they fit the operation.
- Store timestamps in mechanical formats and convert them at boundaries.
- Add compile-time conformance checks to service-owned interfaces.
- Keep SQL driver types out of service APIs.
- Make database code read as query, scan, convert, return.
- Use transactions for multi-step state changes or consistent multi-query reads.
- Begin transactions early, defer rollback immediately, and make commit the explicit success path.
- Use context-aware SQL methods when the store boundary has a context.
- Scan into local primitives and `sql.Null*` values, then build domain values explicitly.
- Check `rows.Err()` after iteration.
- Wrap SQL errors with operation-specific context.
- Keep schema constraints explicit in SQL.

## Package boundary

The database package implements store contracts owned by the service layer.

That means:

- the service layer defines the interface
- the database package satisfies it
- SQL concerns stay in the adapter
- domain meaning stays in the service layer

Do not let the adapter become a second service layer.

## Canonical package shape

Use a layout like:

```text
internal/database/
  database.go
  migrations.go
  documents.go
  projects.go
```

The important ownership split is:

- `database.go` owns open and initialization behavior
- `migrations.go` owns ordered schema changes
- domain adapter files own store-method implementations

## Open and initialization entry points

Provide explicit entry points for:

- opening the database connection
- enabling required pragmas or connection settings
- running migrations as part of open or initialization

A typical shape is:

```go
type Options struct {
	Path string
	WAL  bool
}

func Open(opts Options) (*DB, error)
func (db *DB) Init() error
```

For SQLite-backed local services, a strong default is to set connection behavior explicitly for serialized local operation.

That often includes:

- foreign keys on
- busy timeout
- optional WAL
- one open connection when serialized writes are the intended model

`Open(...)` should leave the returned database handle ready for normal use.

That means connection setup and schema migration should happen there, rather than requiring callers to remember a second migration step before the adapter is safe to use.

## Migration model

Keep migrations ordered and explicit in Go.

Do not scatter schema creation side effects across random methods or package initialization.

A good migration system should make it easy to answer:

- what schema versions exist
- what changed at each step
- when migration runs

Prefer one linear migration list owned by `migrations.go`.

For SQLite-backed applications, `PRAGMA user_version` is a good default version tracker because it keeps the schema version inside the database file without requiring a separate migrations table for simple local services.

The normal shape is:

1. read the current schema version
2. compare it to the ordered migration list
3. run each missing migration in order
4. update `user_version` only after a migration succeeds

That keeps migration state explicit and avoids hidden one-off schema side effects.

## Canonical migration shape

A practical migration definition looks like:

```go
type Migration struct {
	Version int
	Name    string
	Run     func(*sql.Tx) error
}

var migrations = []Migration{
	{
		Version: 1,
		Name:    "create documents table",
		Run: func(tx *sql.Tx) error {
			_, err := tx.Exec(`
				CREATE TABLE documents (
					id TEXT PRIMARY KEY,
					title TEXT NOT NULL,
					created_at_unix INTEGER NOT NULL
				)
			`)
			return err
		},
	},
	{
		Version: 2,
		Name:    "add unique project slug",
		Run: func(tx *sql.Tx) error {
			_, err := tx.Exec(`
				ALTER TABLE projects ADD COLUMN slug TEXT NOT NULL DEFAULT '';
			`)
			if err != nil {
				return err
			}
			_, err = tx.Exec(`
				CREATE UNIQUE INDEX projects_slug_idx ON projects(slug);
			`)
			return err
		},
	},
}
```

This works well because:

- versions are explicit
- migration order is obvious in code review
- each migration has one clear responsibility
- multi-statement migrations stay grouped together

## Migration behavior during open

Run each migration inside a transaction when the underlying statements support it.

A good runner should:

- start from the current `user_version`
- apply only higher-numbered migrations
- wrap each migration failure with the version and name
- stop immediately on the first failure
- leave already-applied migrations untouched

For example:

```go
func Open(opts Options) (*DB, error) {
	conn, err := sql.Open("sqlite", opts.Path)
	if err != nil {
		return nil, fmt.Errorf("open database: %w", err)
	}

	db := &DB{conn: conn}

	current, err := db.userVersion()
	if err != nil {
		conn.Close()
		return nil, fmt.Errorf("read schema version: %w", err)
	}

	for _, m := range migrations {
		if m.Version <= current {
			continue
		}

		tx, err := db.conn.Begin()
		if err != nil {
			conn.Close()
			return nil, fmt.Errorf("begin migration %d %q: %w", m.Version, m.Name, err)
		}

		if err := m.Run(tx); err != nil {
			tx.Rollback()
			conn.Close()
			return nil, fmt.Errorf("run migration %d %q: %w", m.Version, m.Name, err)
		}
		if _, err := tx.Exec(fmt.Sprintf("PRAGMA user_version = %d", m.Version)); err != nil {
			tx.Rollback()
			conn.Close()
			return nil, fmt.Errorf("set schema version %d: %w", m.Version, err)
		}
		if err := tx.Commit(); err != nil {
			conn.Close()
			return nil, fmt.Errorf("commit migration %d %q: %w", m.Version, m.Name, err)
		}

		current = m.Version
	}

	return db, nil
}
```

The exact helper structure can vary, but the key behavior should stay the same: ordered, idempotent application with version changes committed alongside the schema change itself, before `Open(...)` returns a usable adapter.

## What belongs in a migration

Migrations should own durable schema changes such as:

- table creation
- index creation
- foreign keys and other constraints
- additive columns
- mechanical backfills needed to make the new schema valid

They are not the place for:

- runtime seed data that belongs in explicit initialization flows
- ad hoc repair logic hidden in normal query methods
- application bootstrapping that should run through top-level `init`

Keep the migration job focused on schema evolution and closely related mechanical data movement.

## Schema evolution style

Prefer migrations that are:

- additive when possible
- explicit about constraints
- small enough to review confidently
- named clearly enough to understand later

When a change requires rebuilding data or reshaping tables, keep the steps visible in the migration rather than hiding them in helper indirection unless the SQL would otherwise become unreadable.

For local SQLite services, forward-only migrations are usually the right default. The main need is reliable upgrade behavior, not a broad rollback framework.

## Adapter conformance

When the adapter implements a service-owned interface, add a compile-time conformance check:

```go
var _ service.Store = (*DB)(nil)
```

This catches contract drift at build time and makes the ownership boundary explicit in the code.

## Query style

Database adapter code should read in a direct sequence:

1. define the query
2. execute it
3. scan local values
4. convert into domain values
5. return

For example:

```go
func (db *DB) GetDocument(
	ctx context.Context,
	id string,
) (
	*service.Document,
	error,
) {
	row := db.conn.QueryRowContext(
		ctx,
		`SELECT id, title, created_at_unix
		 FROM documents
		 WHERE id = ?1`,
		id,
	)

	var out service.Document
	var createdAtUnix int64
	if err := row.Scan(&out.ID, &out.Title, &createdAtUnix); err != nil {
		return nil, fmt.Errorf("get document: %w", err)
	}

	out.CreatedAt = time.Unix(createdAtUnix, 0)
	return &out, nil
}
```

Keep the logic mechanical. If the adapter is making business decisions, the boundary is drifting.

## Scan and conversion discipline

Prefer scanning into:

- local primitives
- `sql.Null*` types
- small local helper values

Then construct the domain value explicitly.

This keeps:

- null handling obvious
- conversions local
- domain assembly readable

Do not scan straight into half-populated domain objects and quietly patch them later.

## Transactions

Use transactions when:

- one operation spans multiple writes
- several SQL steps need one consistent view
- partial success would be incorrect

The default transactional shape is:

```go
func (db *DB) PublishDocument(
	ctx context.Context,
	id string,
) error {
	tx, err := db.conn.BeginTx(ctx, nil)
	if err != nil {
		return fmt.Errorf("begin publish document tx: %w", err)
	}
	defer tx.Rollback()

	if err := db.sqlMarkDocumentPublishedTx(ctx, tx, id); err != nil {
		return err
	}
	if err := db.sqlInsertAuditEventTx(ctx, tx, id); err != nil {
		return err
	}

	if err := tx.Commit(); err != nil {
		return fmt.Errorf("commit publish document tx: %w", err)
	}

	return nil
}
```

When a large operation spans many statements, factor the public method into smaller `sql*Tx` helpers that operate on `*sql.Tx`.

## Dynamic query construction

When queries need optional filters, build SQL fragments and argument lists explicitly and locally.

Keep this logic visible in the adapter method so a reader can see:

- which filters apply
- which arguments line up with which clauses
- what final ordering and limit behavior the query uses

Avoid generalized query builders when a few local slices are clearer.

## Error handling

Wrap SQL failures with operation-specific context using `%w` when preserving the underlying error matters:

- `fmt.Errorf("list documents: %w", err)`
- `fmt.Errorf("scan document row: %w", err)`
- `fmt.Errorf("commit publish document tx: %w", err)`

This makes debugging much easier than returning raw driver errors with no operation context.

## Schema discipline

Keep important constraints explicit in SQL itself:

- `NOT NULL`
- `UNIQUE`
- `CHECK`
- foreign keys

Application code should not be the only place enforcing invariants that the database can enforce directly.

## Testing expectations

Database adapter design should make it easy to test:

- open and initialization behavior
- migration order and version transitions
- interface conformance
- query and conversion behavior for representative methods
- transactional multi-step operations
- explicit constraint enforcement
- optional filter queries and row iteration behavior

At the method level, tests should verify observable storage behavior rather than re-testing service-layer validation rules.

## Anti-patterns

- SQL code that implements business policy instead of persistence mechanics
- schema creation hidden in unrelated adapter methods
- leaking `*sql.DB`, `*sql.Tx`, rows, or driver-specific types into service APIs
- scanning directly into domain values with unclear null or conversion handling
- multi-step writes performed without transactions
- silent constraint assumptions that only live in Go code
- generic query-builder indirection when a direct query is clearer

## Related guides

- `store-contracts.md`
- `service-construction.md`
- `api-tests.md`
