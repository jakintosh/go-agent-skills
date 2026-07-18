# Database Transactions

This guide defines the default shape for multi-step database operations in `internal/database`.

Use it when one operation spans multiple writes, several statements need one consistent view, or partial success would leave storage in the wrong state.

## Contents

- [Required instructions](#required-instructions)
- [Canonical flow](#canonical-flow)
- [Transaction helpers](#transaction-helpers)
- [Consistent multi-query reads](#consistent-multi-query-reads)

## Required Instructions

- Start a transaction before the first statement that must be coordinated.
- Defer rollback immediately after `BeginTx(...)` succeeds.
- Make `Commit()` the explicit success path.
- Keep transaction-scoped helper methods mechanical.
- Pass `*sql.Tx` into local helpers instead of hiding transaction state globally.
- Keep policy definition and validation independent of persisted state in the service; atomically enforce store-contract preconditions that depend on current durable state in the transaction body.
- Translate storage invariant failures into meaningful adapter errors.

## Canonical Flow

The default transaction flow is:

1. begin the transaction
2. defer rollback
3. run ordered transaction-scoped SQL helpers
4. commit on success
5. return the commit error if commit fails

```go
func (db *DB) PublishDocument(
	ctx context.Context,
	id string,
) error {
	tx, err := db.Conn.BeginTx(ctx, nil)
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

## Transaction Helpers

When an operation spans several statements, factor those statements into small `sql*Tx` helpers.

```go
func (db *DB) sqlMarkDocumentPublishedTx(
	ctx context.Context,
	tx *sql.Tx,
	id string,
) error {
	_, err := tx.ExecContext(ctx, `
		UPDATE documents
		SET published_at_unix = unixepoch()
		WHERE id = ?1`,
		id,
	)
	if err != nil {
		return fmt.Errorf("mark document published: %w", err)
	}

	return nil
}
```

This keeps the public method readable while keeping transaction state explicit. Prefer constraints, foreign keys, conditional writes, or a single statement when they can enforce the invariant clearly; use a transaction when several storage steps must succeed or fail together.

For stateful domain operations, keep transaction orchestration, ordered precondition checks, contract-outcome selection, and the single commit path visible in the public adapter method. Extract mechanical SQL and scanning into narrowly named helpers that accept `*sql.Tx`; do not hide the state transition behind vague policy-named helpers.

## Consistent Multi-Query Reads

Use the same pattern when several reads must observe one consistent snapshot.

```go
func (db *DB) GetLedgerSnapshot(
	ctx context.Context,
	ledger string,
) (
	*service.Snapshot,
	error,
) {
	tx, err := db.Conn.BeginTx(ctx, nil)
	if err != nil {
		return nil, fmt.Errorf("begin ledger snapshot tx: %w", err)
	}
	defer tx.Rollback()

	opening, err := db.sqlOpeningBalanceTx(ctx, tx, ledger)
	if err != nil {
		return nil, err
	}
	incoming, err := db.sqlIncomingFundsTx(ctx, tx, ledger)
	if err != nil {
		return nil, err
	}

	if err := tx.Commit(); err != nil {
		return nil, fmt.Errorf("commit ledger snapshot tx: %w", err)
	}

	return &service.Snapshot{
		OpeningBalance: opening,
		IncomingFunds:  incoming,
	}, nil
}
```

Use a transaction only when the coordinated read view matters. Do not wrap ordinary single-statement reads by default.

Test transaction behavior with [testing.md](./testing.md) by proving the durable effect at the adapter boundary, including failure cases where partial success would leave storage wrong.
