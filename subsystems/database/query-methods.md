# Database Query Methods

This guide defines the default shape for implementing store methods in `internal/database`.

Use it when you are adding a read method, write method, upsert, or query with optional filters.

## Required Instructions

- Keep adapter methods mechanical.
- Use positional SQL parameters.
- Scan into local primitives or `sql.Null*` values.
- Build service-owned values explicitly after scanning.
- Wrap errors with operation-specific context.
- Check `rows.Err()` after iteration.
- Keep dynamic query construction local and readable.
- Apply update inputs without rewriting unchanged state.

## Read Method Shape

The default read flow is:

1. define the query
2. execute it
3. scan storage-shaped values
4. convert into service-owned values
5. return

```go
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
		if errors.Is(err, sql.ErrNoRows) {
			return nil, nil
		}
		return nil, fmt.Errorf("get document %q: %w", id, err)
	}

	out.CreatedAt = time.Unix(createdAtUnix, 0)
	return &out, nil
}
```

## Row Iteration Shape

For list methods, keep the same sequence visible and check iteration errors after the loop.

```go
func (db *DB) ListDocuments(
	limit int,
	offset int,
) (
	[]service.Document,
	error,
) {
	rows, err := db.Conn.Query(`
		SELECT id, title, created_at_unix
		FROM documents
		ORDER BY created_at_unix DESC
		LIMIT ?1 OFFSET ?2`,
		limit,
		offset,
	)
	if err != nil {
		return nil, fmt.Errorf("list documents: %w", err)
	}
	defer rows.Close()

	var out []service.Document
	for rows.Next() {
		var doc service.Document
		var createdAtUnix int64

		if err := rows.Scan(
			&doc.ID,
			&doc.Title,
			&createdAtUnix,
		); err != nil {
			return nil, fmt.Errorf("scan document row: %w", err)
		}

		doc.CreatedAt = time.Unix(createdAtUnix, 0)
		out = append(out, doc)
	}

	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("iterate document rows: %w", err)
	}

	return out, nil
}
```

## Null And Conversion Handling

Use `sql.Null*` values when the schema can return `NULL`, then convert explicitly.

```go
func (db *DB) GetPatron(
	id string,
) (
	*service.Patron,
	error,
) {
	row := db.Conn.QueryRow(`
		SELECT id, name, created_at_unix, updated_at_unix
		FROM patrons
		WHERE id = ?1`,
		id,
	)

	var patronID string
	var name sql.NullString
	var createdAtUnix int64
	var updatedAtUnix sql.NullInt64
	if err := row.Scan(
		&patronID,
		&name,
		&createdAtUnix,
		&updatedAtUnix,
	); err != nil {
		return nil, fmt.Errorf("get patron %q: %w", id, err)
	}

	out := &service.Patron{
		ID:        patronID,
		Name:      name.String,
		CreatedAt: time.Unix(createdAtUnix, 0),
		UpdatedAt: time.Unix(createdAtUnix, 0),
	}
	if updatedAtUnix.Valid {
		out.UpdatedAt = time.Unix(updatedAtUnix.Int64, 0)
	}

	return out, nil
}
```

## Write, Update, And Upsert Shape

Writes should keep the same direct shape: execute SQL, wrap errors, return.

```go
func (db *DB) InsertDocument(
	doc *service.Document,
	) error {
	_, err := db.Conn.Exec(`
		INSERT INTO documents (id, title, created_at_unix)
		VALUES (?1, ?2, ?3)
		ON CONFLICT (id) DO UPDATE SET
			title = excluded.title`,
		doc.ID,
		doc.Title,
		doc.CreatedAt.Unix(),
	)
	if err != nil {
		return fmt.Errorf("insert document %q: %w", doc.ID, err)
	}

	return nil
}
```

Use upserts when the operation is naturally idempotent and the conflict behavior is part of the method's contract.

For ordinary resource updates, accept the update-shaped input from the service contract and apply only the fields present in that input. Preserve unspecified fields and unchanged relationships. For relationship sets, prefer targeted inserts, targeted deletes, upserts, or set-diff SQL over rewriting the whole relationship when only part of it changed.

Test query methods with `./testing.md`, especially storage invariants, not-found behavior, constraint failures, update preservation, ordering, filtering, and null conversion.

## Optional Filters

When a query has optional filters, build the SQL fragments and argument list locally so the final query remains visible.

```go
func (db *DB) ListProjects(
	activeOnly bool,
	limit int,
) (
	[]service.Project,
	error,
) {
	query := `SELECT id, name FROM projects`
	args := []any{}

	if activeOnly {
		query += ` WHERE archived_at_unix IS NULL`
	}

	query += ` ORDER BY name ASC LIMIT ?1`
	args = append(args, limit)

	rows, err := db.Conn.Query(query, args...)
	if err != nil {
		return nil, fmt.Errorf("list projects: %w", err)
	}
	defer rows.Close()

	var out []service.Project
	for rows.Next() {
		var project service.Project
		if err := rows.Scan(
			&project.ID,
			&project.Name,
		); err != nil {
			return nil, fmt.Errorf("scan project row: %w", err)
		}
		out = append(out, project)
	}

	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("iterate project rows: %w", err)
	}

	return out, nil
}
```

Keep this logic local unless several methods truly share the same query assembly.
