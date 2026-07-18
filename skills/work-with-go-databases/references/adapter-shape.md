# Database Adapter Shape

This guide defines the default shape of `internal/database`

Use it when creating a database package, opening a SQLite-backed adapter, implementing store contracts from `internal/service`, or reviewing the subsystem boundary and composition.

The database subsystem opens database connections, applies required connection setup, runs schema migrations, implements service-owned store contracts, handles SQL queries and scans, coordinates multi-step storage work, and enforces durable invariants through schema and storage behavior.

## Contents

- [Canonical shape](#canonical-shape)
- [Opening the database](#opening-the-database)
- [Canonical flow](#canonical-flow)
- [Canonical example](#canonical-example)

## Canonical Shape

Use a layout like:

```
internal/database/
  database.go
  migrations.go
  documents.go
  projects.go
```

Keep the ownership split clear:

- `database.go` owns `DB`, `Options`, `Open(...)`, and `Close()`
- `migrations.go` owns ordered schema changes and the migration runner
- domain files own store-method implementations

## Opening The Database

`Open(...)` is the subsystem entry point

The default flow is:

1. open the SQL connection
2. apply required connection settings
3. build the `DB` value
4. run migrations
5. initialize any attached SQL-backed helpers
6. return a handle ready for normal use

For local SQLite services, the default setup is:

- `SetMaxOpenConns(1)` when serialized writes are the intended model
- `PRAGMA foreign_keys = ON`
- `PRAGMA busy_timeout = 5000`
- optional WAL when the database is file-backed

If you are changing schema behavior, read [migrations.md](./migrations.md). That guide keeps SQL-string migrations as the default path and links to a deeper guide when a migration needs procedural steps. Test open and migration behavior with [testing.md](./testing.md).

Schema constraints, foreign keys, conditional statements, and transactionally coordinated writes should make invalid persistence operations fail through the adapter. The service defines policy through its store contract and may validate inputs independent of persisted state before the call; the adapter atomically enforces contract preconditions that depend on current durable state so direct adapter callers cannot bypass them.

## Canonical Flow

The normal runtime flow is:

1. an outer layer calls `database.Open(...)`
2. `Open(...)` configures SQLite and runs migrations
3. the outer layer passes `*database.DB` into `internal/service`
4. service methods call store contracts owned by `internal/service`
5. adapter methods execute SQL mechanically and return service-owned values

## Canonical Example

```go
package database

import (
	"database/sql"
	"fmt"
	"time"

	"example/internal/service"
	_ "modernc.org/sqlite"
)

type Options struct {
	Path string
	WAL  bool
}

type DB struct {
	Conn *sql.DB
}

var _ service.DocumentStore = (*DB)(nil)

func Open(
	opts Options,
) (
	*DB,
	error,
) {
	conn, err := sql.Open("sqlite", opts.Path)
	if err != nil {
		return nil, fmt.Errorf("open database: %w", err)
	}

	conn.SetMaxOpenConns(1)

	if _, err := conn.Exec("PRAGMA foreign_keys = ON;"); err != nil {
		conn.Close()
		return nil, fmt.Errorf("enable foreign keys: %w", err)
	}
	if _, err := conn.Exec("PRAGMA busy_timeout = 5000;"); err != nil {
		conn.Close()
		return nil, fmt.Errorf("set busy timeout: %w", err)
	}
	if opts.WAL {
		if _, err := conn.Exec("PRAGMA journal_mode = WAL;"); err != nil {
			conn.Close()
			return nil, fmt.Errorf("enable wal mode: %w", err)
		}
	}

	db := &DB{Conn: conn}
	if err := db.migrate(); err != nil {
		conn.Close()
		return nil, fmt.Errorf("run migrations: %w", err)
	}

	return db, nil
}

func (db *DB) GetDocument(
	id string,
) (
	*service.Document,
	error,
) {
	row := db.Conn.QueryRow(`
		SELECT id, title, created_at_unix
		FROM documents
		WHERE id = ?1`,
		id,
	)

	var out service.Document
	var createdAtUnix int64
	if err := row.Scan(
		&out.ID,
		&out.Title,
		&createdAtUnix,
	); err != nil {
		return nil, fmt.Errorf("get document %q: %w", id, err)
	}

	out.CreatedAt = time.Unix(createdAtUnix, 0)
	return &out, nil
}
```

This is the default shape to preserve:

- callers get a ready-to-use adapter from `Open(...)`
- schema setup happens before the adapter is returned
- the adapter satisfies a service-owned interface
- method logic stays mechanical, storage-focused, and honest about constraint failures
