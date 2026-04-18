# Implementing a Store Contract in the Database Layer

This guide defines the default shape for implementing a service-owned store contract in `internal/database`.

Use it when you are writing adapter methods for a store interface, adding a compile-time conformance check, or deciding where row scanning and storage-format conversion should happen.

## Required

- Implement store interfaces from `internal/service` without changing their method names or signatures.
- Add a compile-time conformance check in the database package.
- Keep database methods mechanical: query or exec, scan, convert, return.
- Scan into local primitives or `sql.Null*` values, then build service domain values explicitly.
- Wrap adapter errors with operation-specific context.
- Keep SQL driver types inside `internal/database`.

## Local Shape

Use a layout like:

```
internal/database/
  database.go
  documents.go
```

The usual flow inside one adapter method is:

1. run a parameterized query or exec
2. scan into local storage-shaped values
3. convert those values into service-owned domain types
4. return the result or a wrapped error

## Focused Example

```go
package database

import (
	"database/sql"
	"fmt"
	"time"

	"example/internal/service"
)

type DB struct {
	Conn *sql.DB
}

var _ service.TransactionStore = (*DB)(nil)

func (db *DB) GetTransactions(
	ledger string,
	limit int,
	offset int,
) (
	[]service.Transaction,
	error,
) {
	rows, err := db.Conn.Query(`
		SELECT id, amount, date_unix, label
		FROM transactions
		WHERE ledger = ?1
		ORDER BY date_unix DESC
		LIMIT ?2 OFFSET ?3`,
		ledger,
		limit,
		offset,
	)
	if err != nil {
		return nil, fmt.Errorf("query transactions: %w", err)
	}
	defer rows.Close()

	var out []service.Transaction
	for rows.Next() {
		var tx service.Transaction
		var dateUnix int64

		if err := rows.Scan(&tx.ID, &tx.Amount, &dateUnix, &tx.Label); err != nil {
			return nil, fmt.Errorf("scan transaction: %w", err)
		}

		tx.Ledger = ledger
		tx.Date = time.Unix(dateUnix, 0)
		out = append(out, tx)
	}

	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("iterate transactions: %w", err)
	}

	return out, nil
}
```

This is the default feel to preserve:

- the interface remains service-owned
- the adapter method matches the service contract exactly
- SQL and scan details stay local to `internal/database`
- conversion back into domain values happens before returning

## More Examples

A write method should keep the same mechanical shape:

```go
func (db *DB) InsertDocument(
	doc *Document,
) error {
	_, err := db.Conn.Exec(
		`INSERT INTO documents (id, title, created_at_unix)
		 VALUES (?1, ?2, ?3)`,
		doc.ID,
		doc.Title,
		doc.CreatedAt.Unix(),
	)
	if err != nil {
		return fmt.Errorf("insert document: %w", err)
	}

	return nil
}
```

A read method can also scan local storage values and then build the service type explicitly:

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

	var doc service.Document
	var createdAtUnix int64

	if err := row.Scan(&doc.ID, &doc.Title, &createdAtUnix); err != nil {
		return nil, fmt.Errorf("get document %q: %w", id, err)
	}

	doc.CreatedAt = time.Unix(createdAtUnix, 0)

	return &doc, nil
}
```

## Touchpoints

- Read `./README.md` for contract ownership and service-side translation rules.
- Read `../database/README.md` for default database adapter shape.
- Read `../database/migrations.md` for schema change guidance.
- Read `../database/query-methods.md` for read and write method shape.
- Read `../database/transactions.md` for multi-step database operations.
