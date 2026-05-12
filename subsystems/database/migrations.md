# Database Migrations

This guide defines the default shape for schema changes in `internal/database`.

Use it when you are adding or changing tables, indexes, constraints, or other durable schema state, and the migration body is expressible as SQL.

## Required Instructions

- Keep one ordered migration list in `migrations.go`.
- Track schema version with `PRAGMA user_version`.
- Run missing migrations in order during `Open(...)`.
- Keep one responsibility per migration.
- Keep the default migration body as SQL.
- Run each migration in a transaction.
- Advance `user_version` only after the migration succeeds.
- Keep schema changes and closely related mechanical backfills in migrations.
- Keep runtime seed data and business bootstrap out of migrations.
- If a migration needs reads, batching, or conditional steps, read `./migrations-with-go.md`.

## Migration Ownership

`migrations.go` owns the durable upgrade path for the database file.

The default questions it should answer are:

- what schema versions exist
- what each version changed
- when migrations run
- how version advancement is recorded

Do not scatter schema creation across unrelated adapter methods.

## Default Migration Model

The default migration is a named SQL block.

Use this model as long as the schema change is clear and mechanical in SQL. Do not start with a `Run(tx)` migration shape unless a migration actually needs procedural coordination.

## Canonical Shape

Use one explicit migration list:

```go
type Migration struct {
	Version int
	Name    string
	SQL     string
}

var migrations = []Migration{
	{
		Version: 1,
		Name:    "create documents table",
		SQL: `
			CREATE TABLE documents (
				id TEXT PRIMARY KEY,
				title TEXT NOT NULL,
				created_at_unix INTEGER NOT NULL
			);
		`,
	},
	{
		Version: 2,
		Name:    "add project slug and unique index",
		SQL: `
			ALTER TABLE projects ADD COLUMN slug TEXT NOT NULL DEFAULT '';
			CREATE UNIQUE INDEX projects_slug_idx ON projects(slug);
		`,
	},
}
```

This keeps version order explicit in code review and keeps the migration body easy to scan.

## Canonical Runner

The normal migration runner does this:

1. read `PRAGMA user_version`
2. skip already-applied migrations
3. run each missing migration in order
4. set `user_version` inside the same transaction
5. stop on the first failure

```go
func (db *DB) migrate() error {
	current, err := db.userVersion()
	if err != nil {
		return fmt.Errorf("read schema version: %w", err)
	}

	for _, m := range migrations {
		if m.Version <= current {
			continue
		}

		tx, err := db.Conn.Begin()
		if err != nil {
			return fmt.Errorf("begin migration %d %q: %w", m.Version, m.Name, err)
		}

		if _, err := tx.Exec(m.SQL); err != nil {
			tx.Rollback()
			return fmt.Errorf("run migration %d %q: %w", m.Version, m.Name, err)
		}
		if _, err := tx.Exec(fmt.Sprintf("PRAGMA user_version = %d", m.Version)); err != nil {
			tx.Rollback()
			return fmt.Errorf("set schema version %d: %w", m.Version, err)
		}
		if err := tx.Commit(); err != nil {
			return fmt.Errorf("commit migration %d %q: %w", m.Version, m.Name, err)
		}

		current = m.Version
	}

	return nil
}
```

## What Belongs In Migrations

Keep migrations focused on durable schema evolution:

- table creation
- index creation
- constraints and foreign keys
- additive columns
- straightforward table rebuild SQL
- small mechanical backfills that stay clear as SQL

Move other startup work elsewhere:

- runtime seed data belongs in explicit initialization or bootstrap flows
- normal adapter methods should not perform hidden schema repair

## When To Upgrade To `Run(tx)`

Upgrade from SQL-string migrations when any migration needs procedural coordination instead of one clear SQL block.

Common signals are:

- the migration needs to read existing rows before deciding what to write
- the migration needs to loop or batch through data
- the migration needs conditional steps based on existing database state
- the migration needs a transformation that is clearer in Go than in SQL
- forcing everything into one SQL block would make the migration harder to review

If that happens, read `./migrations-with-go.md`.

## Focused Example

Use `PRAGMA user_version` as the version record for simple local SQLite applications:

```go
func (db *DB) userVersion() (int, error) {
	var version int
	if err := db.Conn.QueryRow(`PRAGMA user_version`).Scan(&version); err != nil {
		return 0, err
	}
	return version, nil
}
```

That keeps schema state inside the database file and avoids a separate migrations table when the application only needs one linear local upgrade path.

## Leaf Docs

- If a migration needs reads, batching, or conditional steps, read `./migrations-with-go.md`.
- If you are testing open behavior, schema readiness, or version advancement, read `./testing.md`.
