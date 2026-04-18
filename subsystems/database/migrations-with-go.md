# Database Migrations With Go

This guide defines the advanced migration shape for projects that have outgrown SQL-string migration bodies.

Use it when one migration needs reads, loops, batching, or conditional steps, or when a project already using SQL-string migrations needs to upgrade to a programmable migration body.

## Required Instructions

- Keep the same ordered migration list and `PRAGMA user_version` model.
- Upgrade to `Run(tx)` only when a migration needs procedural coordination.
- Keep one transaction per migration.
- Keep Go-backed migrations mechanical and storage-focused.
- Do not move business logic into migrations.
- After the refactor, keep simple migrations simple inside the new shape.

## Why To Upgrade From SQL Strings

The default migration model is a SQL string because it is the easiest shape to read and imitate.

Upgrade when a migration needs behavior that does not fit one clear SQL block, such as:

- read-then-write transformations
- chunked or iterative backfills
- conditional repair based on existing database state
- multi-step sequencing where Go is clearer than one large SQL string

The upgrade changes how migration bodies are represented. It does not change the migration protocol.

## Refactoring The Migration Type

Start from the default shape:

```go
type Migration struct {
	Version int
	Name    string
	SQL     string
}
```

Refactor it to:

```go
type Migration struct {
	Version int
	Name    string
	Run     func(*sql.Tx) error
}
```

This refactor does not change:

- migration ordering
- `PRAGMA user_version`
- one transaction per migration
- migration execution during `Open(...)`

It changes only the migration body from a SQL string to a programmable function.

## Refactoring The Runner

The migration runner keeps the same structure:

1. begin the transaction
2. run the migration body
3. set `user_version`
4. commit

The only mechanical change is replacing `tx.Exec(m.SQL)` with `m.Run(tx)`.

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

		if err := m.Run(tx); err != nil {
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

## Focused Examples

After the refactor, simple migrations can still stay simple:

```go
{
	Version: 3,
	Name:    "add document summary column",
	Run: func(tx *sql.Tx) error {
		_, err := tx.Exec(`
			ALTER TABLE documents ADD COLUMN summary TEXT NOT NULL DEFAULT ''
		`)
		return err
	},
}
```

Use the `Run(tx)` form when a migration needs read-then-write behavior that would be awkward or unclear in one SQL block:

```go
{
	Version: 4,
	Name:    "normalize project slugs",
	Run: func(tx *sql.Tx) error {
		rows, err := tx.Query(`
			SELECT id, name
			FROM projects`
		)
		if err != nil {
			return err
		}
		defer rows.Close()

		for rows.Next() {
			var id string
			var name string
			if err := rows.Scan(
				&id,
				&name,
			); err != nil {
				return err
			}

			slug := normalizeSlug(name)

			if _, err := tx.Exec(`
				UPDATE projects
				SET slug = ?1
				WHERE id = ?2`,
				slug,
				id,
			); err != nil {
				return err
			}
		}

		return rows.Err()
	},
}
```

This kind of migration is still mechanical. It translates existing stored data into a new storage shape. It does not introduce service-layer validation or business policy.
